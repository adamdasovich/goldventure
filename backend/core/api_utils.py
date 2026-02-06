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


def extract_url_slug(url: str) -> str:
    """
    Extract the meaningful slug from a news URL.

    Handles various URL patterns:
      /news/20260112-max-resource-enters... -> 20260112-max-resource-enters...
      /news/2026/20260112-max-resource... -> 20260112-max-resource...
      /press-releases/2026/01/some-news -> some-news

    Args:
        url: The URL to extract slug from

    Returns:
        Lowercase slug string
    """
    clean_url = url.split('?')[0].rstrip('/')
    parts = clean_url.split('/')
    slug = parts[-1] if parts else ''
    # If slug looks like a year (e.g., '2026'), try the second-to-last
    if slug.isdigit() and len(slug) == 4 and len(parts) > 1:
        slug = parts[-2]
    return slug.lower()
