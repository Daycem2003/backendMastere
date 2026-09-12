from django.urls import path

from .views.master_views import (
    MasterAcceptedLicenceTypesView,
    MasterDetailView,
    MasterListView,
    MasterPasserellesView,
    MasterRequiredDocumentListView,
    MasterScoreFormulaView,
    PublishMasterView,
)

urlpatterns = [
    path("", MasterListView.as_view()),
    path("<str:pubkey>", MasterDetailView.as_view()),
    path("<str:pubkey>/publish", PublishMasterView.as_view()),
    path("<str:pubkey>/accepted-licence-types", MasterAcceptedLicenceTypesView.as_view()),
    path("<str:pubkey>/passerelles", MasterPasserellesView.as_view()),
    path("<str:pubkey>/required-documents", MasterRequiredDocumentListView.as_view()),
    path("<str:pubkey>/score-formula", MasterScoreFormulaView.as_view()),
]
