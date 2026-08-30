from django.urls import path

from .views.academic_record_views import (
    DiplomeView,
    LicenceYearListView,
    Master1YearView,
    RedoublementView,
)
from .views.candidate_profile_views import CandidateProfileDetailView, MyCandidateProfileView

urlpatterns = [
    path("me", MyCandidateProfileView.as_view()),
    path("me/licence-years", LicenceYearListView.as_view()),
    path("me/diplome", DiplomeView.as_view()),
    path("me/master1-year", Master1YearView.as_view()),
    path("me/redoublement", RedoublementView.as_view()),
    path("<str:pubkey>", CandidateProfileDetailView.as_view()),
]
