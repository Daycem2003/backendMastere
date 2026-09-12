from django.urls import path

from .views.application_views import (
    AllApplicationListView,
    ApplicationDetailView,
    DecideApplicationView,
    MyApplicationListView,
    SubmitApplicationView,
    WithdrawApplicationView,
)
from .views.review_views import MasterApplicationListView

urlpatterns = [
    path("", AllApplicationListView.as_view()),
    path("all", AllApplicationListView.as_view()),
    path("all/", AllApplicationListView.as_view()),
    path("submit", SubmitApplicationView.as_view()),
    path("submit/", SubmitApplicationView.as_view()),
    path("me", MyApplicationListView.as_view()),
    path("me/", MyApplicationListView.as_view()),
    path("<str:pubkey>", ApplicationDetailView.as_view()),
    path("<str:pubkey>/", ApplicationDetailView.as_view()),
    path("<str:pubkey>/withdraw", WithdrawApplicationView.as_view()),
    path("<str:pubkey>/withdraw/", WithdrawApplicationView.as_view()),
    path("<str:pubkey>/decide", DecideApplicationView.as_view()),
    path("<str:pubkey>/decide/", DecideApplicationView.as_view()),
    path("by-master/<str:master_pubkey>", MasterApplicationListView.as_view()),
    path("by-master/<str:master_pubkey>/", MasterApplicationListView.as_view()),
]
