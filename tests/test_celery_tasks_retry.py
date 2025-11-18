import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.tasks import send_welcome_email


@pytest.mark.django_db
def test_send_welcome_email_retry_on_send_mail_failure(monkeypatch, settings):
    """Simula un fallo en send_mail la primera vez y éxito la segunda.

    El test comprueba que ante un fallo externo la tarea puede volver a
    ejecutarse y crear la notificación sólo cuando la llamada a `send_mail`
    termina correctamente.
    """
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    User = get_user_model()
    user = User.objects.create_user(username='retry_user', email='r@example.com', password='pass')

    call_state = {'n': 0}

    def flaky_send_mail(*args, **kwargs):
        call_state['n'] += 1
        if call_state['n'] == 1:
            raise Exception('SMTP temporarily down')
        return None

    monkeypatch.setattr('apps.notifications.tasks.send_mail', flaky_send_mail)

    # Primera ejecución falla por la excepción simulada
    with pytest.raises(Exception):
        send_welcome_email(user.id)

    # No debe haberse creado notificación
    assert Notification.objects.filter(user=user).count() == 0

    # Segunda ejecución (el monkeypatch permitirá éxito)
    result = send_welcome_email(user.id)
    assert result is True
    assert Notification.objects.filter(user=user).exists()
