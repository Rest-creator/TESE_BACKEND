# teseapp/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import messaging.routing # We will create this next

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teseapp.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            messaging.routing.websocket_urlpatterns
        )
    ),
})