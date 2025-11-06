# your_project_name/routing.py or your_app_name/routing.py

from django.urls import re_path

from .consumers import ProductConsumer # Assuming ProductConsumer is in your consumers.py

websocket_urlpatterns = [
    re_path(r'ws/products/$', ProductConsumer.as_asgi()),
    # Add more WebSocket URL patterns here if needed
]