from django.urls import path

from .views.application_views import (
    ApplicationDetailView,
    DecideApplicationView,
    MyApplicationListView,
    SubmitApplicationView,
    WithdrawApplicationView,
)
from .views.review_views import MasterApplicationListView

urlpatterns = [
    path("submit", SubmitApplicationView.as_view()),
    path("me", MyApplicationListView.as_view()),
    path("<str:pubkey>", ApplicationDetailView.as_view()),
    path("<str:pubkey>/withdraw", WithdrawApplicationView.as_view()),
    path("<str:pubkey>/decide", DecideApplicationView.as_view()),
    path("by-master/<str:master_pubkey>", MasterApplicationListView.as_view()),
]
