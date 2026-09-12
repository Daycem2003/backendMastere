from django.urls import path

from .views.user_views import MeView, SetUserActiveStatusView, UserDetailView, UserListView

urlpatterns = [
    path("me", MeView.as_view()),
    path("", UserListView.as_view()),
    path("<str:pubkey>", UserDetailView.as_view()),
    path("<str:pubkey>/active-status", SetUserActiveStatusView.as_view()),
]
