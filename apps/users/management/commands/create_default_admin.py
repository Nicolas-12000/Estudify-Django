from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config


class Command(BaseCommand):
    help = "Crea un usuario admin por defecto si no existe"

    def handle(self, *args, **options):
        User = get_user_model()
        username = config("ADMIN_USERNAME", default="admin")
        email = config("ADMIN_EMAIL", default="admin@example.com")
        password = config("ADMIN_PASSWORD", default="admin123")

        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Creando superusuario '{username}'..."))
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Superusuario creado."))
        else:
            # Si ya existe, actualizar la contraseña al valor de ADMIN_PASSWORD
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.WARNING(f"Superusuario '{username}' ya existía. Se actualizó la contraseña."))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"No se pudo actualizar la contraseña del superusuario: {exc}"))
