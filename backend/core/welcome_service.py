"""
Welcome onboarding for GoldVenture Platform users.

Ties together the two things that happen the first time we greet a user:
  1. Grant the early-access gift — one free month of Prospector access
     (comp grant, no Stripe; reverts to Explorer when it expires).
  2. Send the one-time welcome email from info@.

Both new registrations and the existing-user backfill batch call
``deliver_welcome`` so the behavior stays identical.
"""

import logging

from django.conf import settings
from django.utils import timezone

from .models import PlatformSubscription
from .email_service import EmailService

logger = logging.getLogger(__name__)


def deliver_welcome(user, grant_free_month=None):
    """
    Grant the free month (optional), send the welcome email, and stamp the user.

    ``grant_free_month``:
      - None (default): follow the ``WELCOME_FREE_MONTH_ENABLED`` setting. Used
        by the registration path so the promo can be switched off via env.
      - True/False: explicit override, used by the backfill command.

    The user is only stamped (``welcome_email_sent_at``) when the email actually
    sends, so a failed send stays eligible for a later retry / batch re-run.

    Returns True if the welcome email was sent.
    """
    if grant_free_month is None:
        grant_free_month = getattr(settings, 'WELCOME_FREE_MONTH_ENABLED', True)

    if grant_free_month:
        try:
            _sub, granted = PlatformSubscription.grant_free_month(user)
            if not granted:
                logger.info(
                    f"Skipped free-month grant for user {user.id} "
                    f"(already has a paid subscription)"
                )
        except Exception as e:
            # A grant failure must not block the welcome email.
            logger.error(f"Failed to grant free month to user {user.id}: {e}")

    sent = EmailService.send_welcome_email(user)
    if sent:
        user.welcome_email_sent_at = timezone.now()
        user.save(update_fields=['welcome_email_sent_at'])
    return sent
