import os
from pathlib import Path
from urllib.parse import urlparse
from corsheaders.defaults import default_headers

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "src.apps.reference_data.apps.ReferenceDataConfig",
    "src.apps.authentication.apps.AuthenticationConfig",
    "src.apps.users.apps.UsersConfig",
    "src.apps.candidate_profile.apps.CandidateProfileConfig",
    "src.apps.coordinator.apps.CoordinatorConfig",
    "src.apps.administrator.apps.AdministratorConfig",
    "src.apps.masters.apps.MastersConfig",
    "src.apps.documents.apps.DocumentsConfig",
    "src.apps.eligibility.apps.EligibilityConfig",
    "src.apps.scoring.apps.ScoringConfig",
    "src.apps.applications.apps.ApplicationsConfig",
    "src.apps.authorization.apps.AuthorizationConfig",
    "src.apps.notifications.apps.NotificationsConfig",
    "src.apps.websocket_events.apps.WebsocketEventsConfig",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "src.shared.middleware.cache_control_middleware.PrivateNoCacheAPIMiddleware",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-onboarding-token",
]
CORS_ALLOW_CREDENTIALS = True
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
ROOT_URLCONF = "src.config.urls"
WSGI_APPLICATION = "src.config.wsgi.application"
ASGI_APPLICATION = "src.config.asgi.application"
DATABASE_URL = os.getenv("DATABASE_URL", "")
_database_url = urlparse(DATABASE_URL)

R2_MAX_STORAGE_GB = int(os.getenv("R2_MAX_STORAGE_GB", "10"))
R2_STORAGE_WARNING_PERCENT = int(os.getenv("R2_STORAGE_WARNING_PERCENT", "70"))
R2_STORAGE_CRITICAL_PERCENT = int(os.getenv("R2_STORAGE_CRITICAL_PERCENT", "85"))
R2_STORAGE_BLOCK_PERCENT = int(os.getenv("R2_STORAGE_BLOCK_PERCENT", "95"))

R2_MAX_CLASS_A = int(os.getenv("R2_MAX_CLASS_A", "1000000"))
R2_CLASS_A_WARNING_PERCENT = int(os.getenv("R2_CLASS_A_WARNING_PERCENT", "70"))
R2_CLASS_A_CRITICAL_PERCENT = int(os.getenv("R2_CLASS_A_CRITICAL_PERCENT", "85"))
R2_CLASS_A_BLOCK_PERCENT = int(os.getenv("R2_CLASS_A_BLOCK_PERCENT", "95"))

R2_MAX_CLASS_B = int(os.getenv("R2_MAX_CLASS_B", "10000000"))
R2_CLASS_B_WARNING_PERCENT = int(os.getenv("R2_CLASS_B_WARNING_PERCENT", "70"))
R2_CLASS_B_CRITICAL_PERCENT = int(os.getenv("R2_CLASS_B_CRITICAL_PERCENT", "85"))
R2_CLASS_B_BLOCK_PERCENT = int(os.getenv("R2_CLASS_B_BLOCK_PERCENT", "95"))

R2_MAX_FILE_SIZE_MB = int(os.getenv("R2_MAX_FILE_SIZE_MB", "5"))


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
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["src.apps.authentication.drf_authentication.JWTAuthentication"], "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "UNAUTHENTICATED_USER": None}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "src" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@mastertn.tn")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8081")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

