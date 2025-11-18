from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractBaseModel(models.Model):
    """
    Modelo abstracto base con campos comunes para auditoría.
    Todos los modelos deben heredar de este.
    """
    created_at = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True,
        help_text=_('Fecha y hora de creación del registro')
    )
    updated_at = models.DateTimeField(
        _('Fecha de actualización'),
        auto_now=True,
        help_text=_('Fecha y hora de última actualización')
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_('Indica si el registro está activo')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Eliminación lógica del registro."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restauración del registro eliminado lógicamente."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


__all__ = ['AbstractBaseModel']
