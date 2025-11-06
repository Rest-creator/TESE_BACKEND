# teseapi/asgi.py

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# You might need to import your app's routing here if you have WebSocket consumers
# For example, if your app is 'teseapi' and has a 'routing.py'
# import teseapi.routing # <-- Keep this commented out or uncomment if you create routing.py

# Ensure this matches your project's main settings module name (teseapi.settings)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teseapp.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        # WebSocket handling:
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                # Provide an empty list if no WebSocket routes are defined yet
                URLRouter([]) # <--- THIS IS THE CHANGE
                # If you later define WebSocket routes in teseapi/routing.py:
                # URLRouter(teseapi.routing.websocket_urlpatterns)
            )
        ),
    }
)