from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications-list'),
    path('<int:pk>/mark_read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark_all_read/', NotificationMarkAllReadView.as_view(), name='notifications-mark-all-read'),
]
