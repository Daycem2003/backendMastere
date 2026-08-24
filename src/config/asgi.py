import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings.development")
django_asgi_app = get_asgi_application()

from src.apps.websocket_events.middleware import JWTAuthMiddlewareStack  # noqa: E402
from src.apps.websocket_events.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
