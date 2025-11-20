from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    """
    Lista todas las notificaciones del usuario autenticado (recientes primero)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationMarkReadView(generics.UpdateAPIView):
    """
    Marca una notificación como leída (solo si es tuya)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def update(self, request, *args, **kwargs):
        notif = self.get_object()
        if notif.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save()
        return Response(self.get_serializer(notif).data)

class NotificationMarkAllReadView(generics.GenericAPIView):
    """
    Marca TODAS las notificaciones como leídas para el usuario autenticado.
    POST /api/notifications/mark_all_read/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        qs = Notification.objects.filter(user=request.user, is_read=False)
        now = timezone.now()
        updated = qs.update(is_read=True, read_at=now)
        return Response({"updated": updated}, status=status.HTTP_200_OK)
