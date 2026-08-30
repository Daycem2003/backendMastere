from django.urls import path

from .views import (
    ChangePasswordView,
    CurrentUserView,
    UserActivateView,
    UserDeactivateView,
    UserDetailView,
    UserListView,
    UserRestoreView,
    UserSoftDeleteView,
)

urlpatterns = [
    path("me", CurrentUserView.as_view(), name="user-me"),
    path("me/change-password", ChangePasswordView.as_view(), name="user-change-password"),
    path("", UserListView.as_view(), name="user-list"),
    path("<str:pubkey>", UserDetailView.as_view(), name="user-detail"),
    path("<str:pubkey>/activate", UserActivateView.as_view(), name="user-activate"),
    path("<str:pubkey>/deactivate", UserDeactivateView.as_view(), name="user-deactivate"),
    path("<str:pubkey>/delete", UserSoftDeleteView.as_view(), name="user-delete"),
    path("<str:pubkey>/restore", UserRestoreView.as_view(), name="user-restore"),
]
