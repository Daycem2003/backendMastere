from django.urls import path

from .views.eligibility_views import (
    CheckCandidateEligibilityView,
    EligibilityRuleDetailView,
    MasterEligibilityRuleListView,
)

urlpatterns = [
    path("masters/<str:master_pubkey>/rules", MasterEligibilityRuleListView.as_view()),
    path("masters/<str:master_pubkey>/check", CheckCandidateEligibilityView.as_view()),
    path("rules/<str:pubkey>", EligibilityRuleDetailView.as_view()),
]
