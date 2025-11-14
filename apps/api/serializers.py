"""Re-export de serializers para compatibilidad de import.

Permite `from apps.api.serializers import ...` mientras mantenemos
la implementación en `apps.api.v1.serializers.serializers`.
"""

from .v1.serializers.serializers import *  # noqa: F401,F403
