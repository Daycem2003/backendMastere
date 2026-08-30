import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes", "django.contrib.staticfiles",
    "rest_framework",
    "src.apps.users.apps.UsersConfig", "src.apps.candidate_profile.apps.CandidateProfileConfig",
    "src.apps.coordinator.apps.CoordinatorConfig", "src.apps.administrator.apps.AdministratorConfig",
    "src.apps.masters.apps.MastersConfig", "src.apps.documents.apps.DocumentsConfig",
    "src.apps.eligibility.apps.EligibilityConfig", "src.apps.scoring.apps.ScoringConfig",
    "src.apps.applications.apps.ApplicationsConfig", "src.apps.authorization.apps.AuthorizationConfig",
    "src.apps.notifications.apps.NotificationsConfig", "src.apps.websocket_events.apps.WebsocketEventsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "src.config.urls"
WSGI_APPLICATION = "src.config.wsgi.application"
ASGI_APPLICATION = "src.config.asgi.application"
DATABASE_URL = os.getenv("DATABASE_URL", "")
_database_url = urlparse(DATABASE_URL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _database_url.path.lstrip("/") or os.getenv("POSTGRES_DB", "mastere"),
        "USER": _database_url.username or os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": _database_url.password or os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": _database_url.hostname or os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": _database_url.port or os.getenv("POSTGRES_PORT", "5432"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
AUTH_USER_MODEL = "users.User"
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Tunis")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["src.apps.authentication.drf_authentication.JWTAuthentication"], "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "UNAUTHENTICATED_USER": None}
