from django.urls import include, path

urlpatterns = [
    path("api/v1/auth/", include("src.apps.authentication.urls")),
    path("api/v1/users/", include("src.apps.users.urls")),
    path("api/v1/reference-data/", include("src.apps.reference_data.urls")),
    path("api/v1/authorization/", include("src.apps.authorization.urls")),
    path("api/v1/documents/", include("src.apps.documents.urls")),
    path("api/v1/notifications/", include("src.apps.notifications.urls")),
    path("api/v1/candidates/", include("src.apps.candidate_profile.urls")),
    path("api/v1/masters/", include("src.apps.masters.urls")),
    path("api/v1/eligibility/", include("src.apps.eligibility.urls")),
    path("api/v1/applications/", include("src.apps.applications.urls")),
    path("api/v1/coordinator/", include("src.apps.coordinator.urls")),
]