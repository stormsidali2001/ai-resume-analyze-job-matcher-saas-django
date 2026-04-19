"""ASGI config for resumeai project."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# django.setup() is called inside get_asgi_application(); it must happen before
# importing consumers so models are ready when the consumer module is loaded.
from django.core.asgi import get_asgi_application  # noqa: E402
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from interfaces.websocket.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        URLRouter(websocket_urlpatterns)
    ),
})
