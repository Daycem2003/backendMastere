from django.urls import path

from src.apps.documents.views.document_views import (
    CandidateDocumentsListView,
    DocumentDetailView,
    DocumentRejectView,
    DocumentReviewView,
    DocumentUploadView,
    MyDocumentListView,
    MySlotListView,
    PendingDocumentListView,
)

app_name = "documents"

urlpatterns = [
    path("me/slots/", MySlotListView.as_view(), name="my-slots"),
    path("me/documents/", MyDocumentListView.as_view(), name="my-documents"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("pending/", PendingDocumentListView.as_view(), name="document-pending"),
    path(
        "candidates/<str:candidate_pubkey>/",
        CandidateDocumentsListView.as_view(),
        name="candidate-documents",
    ),
    path("<str:pubkey>/", DocumentDetailView.as_view(), name="document-detail"),
    path(
        "<str:pubkey>/approve/",
        DocumentReviewView.as_view(),
        name="document-approve",
    ),
    path(
        "<str:pubkey>/reject/",
        DocumentRejectView.as_view(),
        name="document-reject",
    ),
]