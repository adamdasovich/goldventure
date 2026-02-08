"""
Security headers middleware for GoldVenture Platform.

Adds Content-Security-Policy (CSP) and Permissions-Policy headers
to all responses as defense-in-depth against XSS and feature abuse.
"""


class SecurityHeadersMiddleware:
    """
    Adds security headers to all HTTP responses.

    - Content-Security-Policy: Restricts what resources the browser can load
    - Permissions-Policy: Restricts browser features (camera, mic, geolocation)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy
        # Restricts sources for scripts, styles, images, connections, etc.
        csp_directives = [
            "default-src 'self'",
            # Scripts: self + Google Tag Manager + inline (for Next.js hydration)
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com",
            # Styles: self + inline (for component libraries)
            "style-src 'self' 'unsafe-inline'",
            # Images: self + data URIs + HTTPS (for external images/CDN)
            "img-src 'self' data: https:",
            # API connections: self + API domain + WebSocket
            "connect-src 'self' https://api.juniorminingintelligence.com wss://api.juniorminingintelligence.com https://www.google-analytics.com",
            # Fonts: self
            "font-src 'self'",
            # Frames: none (prevent clickjacking)
            "frame-src 'none'",
            # Base URI: self only (prevent base tag hijacking)
            "base-uri 'self'",
            # Form actions: self only
            "form-action 'self'",
            # Object/embed: none
            "object-src 'none'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        # Permissions-Policy
        # Disable browser features not needed by this application
        response['Permissions-Policy'] = (
            'camera=(), '
            'microphone=(), '
            'geolocation=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )

        return response
