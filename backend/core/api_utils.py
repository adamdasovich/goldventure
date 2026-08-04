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


def stripe_subscription_period(sub):
    """Return (current_period_start, current_period_end) as unix timestamps.

    Stripe's 2025 "Basil"/"dahlia" API moved these fields off the Subscription
    object and onto its subscription item(s). The pinned library version
    (2023-10-16) still returns them at the top level on ``retrieve`` calls, but
    webhook payloads render at the account's API version. Read whichever shape
    is present so handlers work across versions.
    """
    start = sub.get('current_period_start')
    end = sub.get('current_period_end')
    if start is None or end is None:
        items = (sub.get('items') or {}).get('data') or []
        if items:
            start = start if start is not None else items[0].get('current_period_start')
            end = end if end is not None else items[0].get('current_period_end')
    return start, end


def stripe_invoice_subscription_id(inv):
    """Return the subscription id for an invoice across Stripe API versions.

    Older API: ``invoice.subscription``. Basil/dahlia moved it to
    ``invoice.parent.subscription_details.subscription`` (with the line item's
    ``subscription_item_details`` as a further fallback).
    """
    sid = inv.get('subscription')
    if sid:
        return sid
    parent = inv.get('parent') or {}
    sd = parent.get('subscription_details') or {}
    if sd.get('subscription'):
        return sd['subscription']
    lines = (inv.get('lines') or {}).get('data') or []
    if lines:
        lp = lines[0].get('parent') or {}
        sid = (lp.get('subscription_item_details') or {}).get('subscription')
    return sid


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
