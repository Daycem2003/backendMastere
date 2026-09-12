from django.urls import path

from .views.decision_views import (
    ApproveCandidatureView,
    RejectCandidatureView,
    RequestRevisionView,
)

urlpatterns = [
    path("candidatures/<str:pubkey>/approve", ApproveCandidatureView.as_view(), name="coordinator-approve-candidature"),
    path("candidatures/<str:pubkey>/reject", RejectCandidatureView.as_view(), name="coordinator-reject-candidature"),
    path("candidatures/<str:pubkey>/request-revision", RequestRevisionView.as_view(), name="coordinator-request-revision"),
]
