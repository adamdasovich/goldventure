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

# Custom origin validator that allows our domains
class CustomOriginValidator(OriginValidator):
    """Custom origin validator for WebSocket connections"""

    def valid_origin(self, parsed_origin):
        """Check if origin is valid"""
        # Allow our production domain
        allowed_origins = [
            'juniorminingintelligence.com',
            'www.juniorminingintelligence.com',
            'api.juniorminingintelligence.com',
            'localhost:3000',
            '127.0.0.1:3000',
        ]

        # Check if the origin host is in our allowed list
        origin_host = parsed_origin.hostname
        if parsed_origin.port:
            origin_host = f"{origin_host}:{parsed_origin.port}"

        return origin_host in allowed_origins or super().valid_origin(parsed_origin)

# Configure ASGI application with WebSocket support
application = ProtocolTypeRouter({
    # HTTP requests go to Django's ASGI application
    "http": django_asgi_app,

    # WebSocket chat handler with JWT authentication
    "websocket": CustomOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
    ),
})
