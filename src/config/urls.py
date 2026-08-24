from django.urls import include, path

urlpatterns = [
    path("api/v1/auth/", include("src.apps.authentication.urls")),
    path("api/v1/authorization/", include("src.apps.authorization.urls")),
    path("api/v1/documents/", include("src.apps.documents.urls")),
    path("api/v1/notifications/", include("src.apps.notifications.urls")),
]
