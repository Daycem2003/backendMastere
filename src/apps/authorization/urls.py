from django.urls import path

from .drf_api_views import (
	PermissionListView,
	RoleAssignmentCreateView,
	RoleAssignmentDeleteView,
	RoleDetailView,
	RoleListCreateView,
)

urlpatterns = [
	path("permissions", PermissionListView.as_view()),
	path("roles", RoleListCreateView.as_view()),
	path("roles/<str:pubkey>", RoleDetailView.as_view()),
	path("users/roles", RoleAssignmentCreateView.as_view()),
	path("users/<str:user_pubkey>/roles/<str:role_code>", RoleAssignmentDeleteView.as_view()),
]
