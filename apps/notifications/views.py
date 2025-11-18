from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.notifications.models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(generics.UpdateAPIView):
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
    """Mark all unread notifications for the authenticated user as read.

    POST /api/notifications/mark_all_read/
    Returns JSON with the number of notifications updated.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        qs = Notification.objects.filter(user=request.user, is_read=False)
        now = timezone.now()
        updated = qs.update(is_read=True, read_at=now)
        return Response({"updated": updated}, status=status.HTTP_200_OK)

# Create your views here.
