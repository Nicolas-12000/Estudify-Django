from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.core.models import AbstractBaseModel


class Notification(AbstractBaseModel):
    """Persistent notification for a user.

    Can be linked to any object via a GenericForeignKey (optional).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
    )
    title = models.CharField(_("Title"), max_length=255)
    message = models.TextField(_("Message"))
    is_read = models.BooleanField(_("Is read"), default=False)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)

    # Generic relation to link notification to other models (grade, course, etc.)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    notification_type = models.CharField(
        _("Type"), max_length=50, blank=True, default="generic"
    )

    # Optional URL the frontend can navigate to when the notification is opened
    target_url = models.CharField(
        "Target URL", max_length=512, null=True, blank=True, default=None
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Notification for {self.user}: {self.title}"
