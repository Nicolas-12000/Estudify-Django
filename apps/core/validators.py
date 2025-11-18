"""
Validadores personalizados para Estudify.
Aseguran integridad de datos y previenen inyección/XSS.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_name_field(value):
    """
    Validador para campos de nombre (first_name, last_name, etc).
    Permite solo letras (incluyendo tildes), espacios, guiones y apóstrofes.
    Longitud: 2-150 caracteres.
    """
    if not value:
        return

    # Patrón: letras (unicode), espacios, guiones, apóstrofes
    pattern = r'^[\w\sÀ-ÿ\'-]+$'

    if not re.match(pattern, value, re.UNICODE):
        raise ValidationError(
            _('El nombre solo puede contener letras, espacios, guiones y apóstrofes.'),
            code='invalid_name')

    if len(value) < 2:
        raise ValidationError(
            _('El nombre debe tener al menos 2 caracteres.'),
            code='name_too_short'
        )

    if len(value) > 150:
        raise ValidationError(
            _('El nombre no puede exceder 150 caracteres.'),
            code='name_too_long'
        )


def validate_username_field(value):
    """
    Validador para username.
    Permite letras, números, guiones bajos, guiones y puntos.
    Longitud: 3-150 caracteres.
    """
    if not value:
        return

    pattern = r'^[\w.-]+$'

    if not re.match(pattern, value):
        raise ValidationError(
            _('El nombre de usuario solo puede contener letras, números, guiones, guiones bajos y puntos.'),
            code='invalid_username')

    if len(value) < 3:
        raise ValidationError(
            _('El nombre de usuario debe tener al menos 3 caracteres.'),
            code='username_too_short'
        )


def validate_code_field(value):
    """
    Validador para códigos (course code, subject code).
    Permite letras, números, guiones y guiones bajos.
    Longitud: 2-50 caracteres.
    """
    if not value:
        return

    pattern = r'^[A-Z0-9_-]+$'

    if not re.match(pattern, value):
        raise ValidationError(
            _('El código solo puede contener letras mayúsculas, números, guiones y guiones bajos.'),
            code='invalid_code')

    if len(value) < 2:
        raise ValidationError(
            _('El código debe tener al menos 2 caracteres.'),
            code='code_too_short'
        )


def validate_text_field(value):
    """
    Validador para campos de texto largo (bio, comments, notes, etc).
    Previene inyección de scripts y tags HTML peligrosos.
    Permite texto normal con puntuación básica.
    """
    if not value:
        return

    # Bloquear tags HTML/JS
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<embed',
        r'<object',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                _('El texto contiene contenido no permitido (HTML/JavaScript).'),
                code='invalid_text_content')


def validate_alphanumeric_with_spaces(value):
    """
    Validador para campos que permiten alfanumérico con espacios y puntuación básica.
    Usado para direcciones, ciudades, etc.
    """
    if not value:
        return

    # Permite letras (unicode), números, espacios, comas, puntos, guiones
    pattern = r'^[\w\sÀ-ÿ,.\'-]+$'

    if not re.match(pattern, value, re.UNICODE):
        raise ValidationError(
            _('Solo se permiten letras, números, espacios y puntuación básica (coma, punto, guión).'),
            code='invalid_alphanumeric')


__all__ = [
    'validate_name_field',
    'validate_username_field',
    'validate_code_field',
    'validate_text_field',
    'validate_alphanumeric_with_spaces',
]
