from django.urls import path

from .views.document_views import (
    DocumentDetailView,
    DocumentRejectView,
    DocumentReviewView,
    DocumentUploadView,
    MyDocumentListView,
    PendingDocumentListView,
)

urlpatterns = [
    path("me", MyDocumentListView.as_view()),
    path("upload", DocumentUploadView.as_view()),
    path("review/pending", PendingDocumentListView.as_view()),
    path("<str:pubkey>/approve", DocumentReviewView.as_view()),
    path("<str:pubkey>/reject", DocumentRejectView.as_view()),
    path("<str:pubkey>", DocumentDetailView.as_view()),
]
