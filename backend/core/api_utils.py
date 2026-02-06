"""
API Utilities Module
Shared utility functions for external API integrations (Stripe, etc.)
"""

import stripe
from django.conf import settings


def get_stripe_api_key():
    """
    Get the Stripe API key and configure the stripe module.

    Returns:
        str or None: The Stripe API key if configured, None otherwise.
    """
    key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if key:
        stripe.api_key = key
    return key


def is_stripe_configured():
    """
    Check if Stripe is properly configured with a valid API key.

    Returns:
        bool: True if Stripe is configured with a test or live key.
    """
    key = get_stripe_api_key()
    return key and (key.startswith('sk_test_') or key.startswith('sk_live_'))
