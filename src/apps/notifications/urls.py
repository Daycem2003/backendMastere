from django.urls import path

from .views.broadcast_views import (
    BroadcastNotificationView,
    NotificationAttachmentDownloadView,
    NotifyTopRankedView,
)
from .views.notification_views import (
    MarkNotificationReadView,
    MyNotificationListView,
    MyUnreadNotificationCountView,
    NotifyDocumentIssueView,
)

urlpatterns = [
    path("broadcast", BroadcastNotificationView.as_view()),
    path("broadcast/", BroadcastNotificationView.as_view()),
    path("broadcasts", BroadcastNotificationView.as_view()),
    path("broadcasts/", BroadcastNotificationView.as_view()),
    path("notify-top-ranked", NotifyTopRankedView.as_view()),
    path("notify-top-ranked/", NotifyTopRankedView.as_view()),
    path("<str:pubkey>/attachment-url", NotificationAttachmentDownloadView.as_view()),
    path("<str:pubkey>/attachment-url/", NotificationAttachmentDownloadView.as_view()),
    path("notify/document-issue", NotifyDocumentIssueView.as_view()),
    path("me", MyNotificationListView.as_view()),
    path("me/", MyNotificationListView.as_view()),
    path("me/unread-count", MyUnreadNotificationCountView.as_view()),
    path("<str:pubkey>/read", MarkNotificationReadView.as_view()),
    path("<str:pubkey>/read/", MarkNotificationReadView.as_view()),
]

