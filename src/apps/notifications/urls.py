from django.urls import path

from .views.notification_views import (
    MarkNotificationReadView,
    MyNotificationListView,
    MyUnreadNotificationCountView,
    NotifyDocumentIssueView,
)

urlpatterns = [
    path("notify/document-issue", NotifyDocumentIssueView.as_view()),
    path("me", MyNotificationListView.as_view()),
    path("me/unread-count", MyUnreadNotificationCountView.as_view()),
    path("<str:pubkey>/read", MarkNotificationReadView.as_view()),
]
