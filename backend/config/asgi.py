"""
ASGI config for GoldVenture Platform with WebSocket support.

This module contains the ASGI application used by Django's development server
and any production ASGI deployments. It exposes the ASGI callable as a
module-level variable named ``application``.
"""

import os
from django.core.asgi import get_asgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Now import channels and routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from core import routing
from core.middleware import JWTAuthMiddlewareStack

# Configure allowed origins for WebSocket connections
# Can be overridden via WEBSOCKET_ALLOWED_ORIGINS environment variable (comma-separated)
_default_ws_origins = [
    'juniorminingintelligence.com',
    'www.juniorminingintelligence.com',
    'api.juniorminingintelligence.com',
    'localhost:3000',
    '127.0.0.1:3000',
]
_env_origins = os.environ.get('WEBSOCKET_ALLOWED_ORIGINS', '')
ALLOWED_WEBSOCKET_ORIGINS = _env_origins.split(',') if _env_origins else _default_ws_origins

# Configure ASGI application with WebSocket support
application = ProtocolTypeRouter({
    # HTTP requests go to Django's ASGI application
    "http": django_asgi_app,

    # WebSocket chat handler with JWT authentication
    "websocket": OriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
        ALLOWED_WEBSOCKET_ORIGINS
    ),
})
