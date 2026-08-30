from django.urls import path

from .drf_api_views import (
    PermissionListView,
    RoleAssignmentCreateView,
    RoleAssignmentDeleteView,
    RoleDetailView,
    RoleListCreateView,
    RolePermissionManagementView,
    UserRoleListView,
)

urlpatterns = [
    path("permissions", PermissionListView.as_view(), name="permission-list"),
    path("roles", RoleListCreateView.as_view(), name="role-list-create"),
    path("roles/<str:pubkey>", RoleDetailView.as_view(), name="role-detail"),
    path(
        "roles/<str:pubkey>/permissions/<str:permission_code>",
        RolePermissionManagementView.as_view(),
        name="role-permission-manage",
    ),
    path("users/roles", RoleAssignmentCreateView.as_view(), name="role-assignment-create"),
    path(
        "users/<str:user_pubkey>/roles/<str:role_code>",
        RoleAssignmentDeleteView.as_view(),
        name="role-assignment-delete",
    ),
    path(
        "users/<str:user_pubkey>/roles",
        UserRoleListView.as_view(),
        name="user-role-list",
    ),
]
