"""
Stripe Service for Platform User Subscriptions

Handles user-level subscription tiers:
- Explorer: Free (no Stripe)
- Prospector: $29/month or $249/year
- Miner: $79/month or $699/year

Mirrors the pattern in stripe_service.py (company subscriptions).
"""

import stripe
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
import logging
from .api_utils import (
    get_stripe_api_key,
    stripe_subscription_period,
    stripe_invoice_subscription_id,
)

logger = logging.getLogger(__name__)

# Pricing configuration (cents)
TIER_PRICING = {
    'prospector': {
        'month': 1500,   # $15/month
        'year': 15000,   # $150/year (10x monthly)
    },
    'miner': {
        'month': 5000,   # $50/month
        'year': 50000,   # $500/year (10x monthly)
    },
}

TRIAL_DAYS = 7  # 7-day free trial for paid tiers

# Billing currency. A Stripe Price's currency is immutable, so this is baked
# into the price metadata + lookup — changing it creates fresh prices rather
# than reusing stale ones of another currency.
PRICE_CURRENCY = 'cad'

# Stripe product/price cache (populated on first use)
_price_cache = {}


class PlatformStripeService:
    """Service class for platform user subscription operations."""

    @staticmethod
    def is_configured():
        key = get_stripe_api_key()
        if not key:
            return False
        return key.startswith('sk_test_') or key.startswith('sk_live_')

    @staticmethod
    def _get_or_create_product():
        """Get or create the Stripe Product for platform subscriptions."""
        get_stripe_api_key()
        # Search for existing product by metadata
        products = stripe.Product.search(
            query="metadata['type']:'platform_subscription'"
        )
        if products.data:
            return products.data[0]

        product = stripe.Product.create(
            name="Junior Mining Intelligence Platform",
            description="AI-powered mining research and investor tools",
            metadata={'type': 'platform_subscription'}
        )
        logger.info(f"Created Stripe product {product.id} for platform subscriptions")
        return product

    @staticmethod
    def get_or_create_price(tier, interval='month'):
        """Get or create a Stripe Price for a given tier and interval."""
        get_stripe_api_key()
        amount = TIER_PRICING.get(tier, {}).get(interval)
        if not amount:
            raise ValueError(f"Invalid tier/interval: {tier}/{interval}")

        cache_key = f"{tier}_{interval}_{amount}_{PRICE_CURRENCY}"
        if cache_key in _price_cache:
            return _price_cache[cache_key]

        # Search for existing price scoped by currency AND amount, so changing
        # the price (or currency) creates a fresh Stripe Price instead of
        # reusing a stale one (Price.unit_amount/currency are immutable).
        prices = stripe.Price.search(
            query=f"metadata['tier']:'{tier}' AND metadata['interval']:'{interval}' AND metadata['currency']:'{PRICE_CURRENCY}' AND metadata['amount']:'{amount}'"
        )
        if prices.data:
            _price_cache[cache_key] = prices.data[0].id
            return prices.data[0].id

        product = PlatformStripeService._get_or_create_product()
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=PRICE_CURRENCY,
            recurring={'interval': interval},
            metadata={'tier': tier, 'interval': interval, 'currency': PRICE_CURRENCY, 'amount': str(amount)}
        )
        logger.info(f"Created Stripe price {price.id} for {tier}/{interval}")
        _price_cache[cache_key] = price.id
        return price.id

    @staticmethod
    def create_checkout_session(user, tier, interval, success_url, cancel_url):
        """
        Create a Stripe Checkout Session for a platform subscription.

        Args:
            user: User model instance
            tier: 'prospector' or 'miner'
            interval: 'month' or 'year'
            success_url: redirect URL on success
            cancel_url: redirect URL on cancel

        Returns:
            Stripe Checkout Session object
        """
        if tier not in TIER_PRICING:
            raise ValueError(f"Invalid tier: {tier}")
        if interval not in ('month', 'year'):
            raise ValueError(f"Invalid interval: {interval}")

        get_stripe_api_key()
        from .models import PlatformSubscription

        price_id = PlatformStripeService.get_or_create_price(tier, interval)

        # Get or create Stripe customer
        try:
            sub = PlatformSubscription.objects.get(user=user)
            if sub.stripe_customer_id:
                customer_id = sub.stripe_customer_id
            else:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}".strip() or user.username,
                    metadata={
                        'user_id': str(user.id),
                        'username': user.username,
                        'subscription_type': 'platform',
                    }
                )
                customer_id = customer.id
                sub.stripe_customer_id = customer_id
                sub.save(update_fields=['stripe_customer_id'])
        except PlatformSubscription.DoesNotExist:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                    'subscription_type': 'platform',
                }
            )
            customer_id = customer.id

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            # Managed Payments is enabled by default on new Stripe accounts and
            # rejects payment_method_types + requires product tax codes. Disable
            # it per-session to keep classic card Checkout behavior.
            managed_payments={'enabled': False},
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            subscription_data={
                'trial_period_days': TRIAL_DAYS,
                'metadata': {
                    'user_id': str(user.id),
                    'tier': tier,
                    'interval': interval,
                    'subscription_type': 'platform',
                }
            },
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user.id),
                'tier': tier,
                'interval': interval,
                'subscription_type': 'platform',
            }
        )
        logger.info(f"Created platform checkout session {session.id} for user {user.id} ({tier}/{interval})")
        return session

    @staticmethod
    def create_billing_portal_session(customer_id, return_url):
        """Create a Stripe Billing Portal session for subscription management."""
        get_stripe_api_key()
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session

    @staticmethod
    def cancel_subscription(subscription_id, at_period_end=True):
        """Cancel a platform subscription."""
        get_stripe_api_key()
        if at_period_end:
            return stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return stripe.Subscription.delete(subscription_id)

    @staticmethod
    def reactivate_subscription(subscription_id):
        """Reactivate a subscription set to cancel at period end."""
        get_stripe_api_key()
        return stripe.Subscription.modify(subscription_id, cancel_at_period_end=False)

    @staticmethod
    def construct_webhook_event(payload, sig_header):
        """Verify and construct a Stripe webhook event."""
        webhook_secret = getattr(settings, 'STRIPE_PLATFORM_WEBHOOK_SECRET', None)
        if not webhook_secret:
            # Fall back to general webhook secret
            webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        if not webhook_secret:
            raise ValueError("Platform webhook secret not configured")
        return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)


def plan_from_stripe_subscription(stripe_sub):
    """Resolve (tier, interval, price_cents, price_id) from a Stripe subscription.

    Read the *price* the subscription currently carries rather than the tier
    recorded in its metadata. Metadata is stamped once at checkout and is never
    rewritten, so after a plan change through the billing portal it still names
    the tier the customer started on - which is how a Miner ends up billed $50
    while the database still calls them a Prospector.

    Falls back to matching amount+interval against TIER_PRICING for prices that
    predate the metadata convention. Returns None when the plan can't be
    identified, so callers can leave the stored tier alone rather than guess.
    """
    items = (stripe_sub.get('items') or {}).get('data') or []
    if not items:
        return None

    price = items[0].get('price') or {}
    price_id = price.get('id') or ''
    amount = price.get('unit_amount')
    metadata = price.get('metadata') or {}
    interval = metadata.get('interval') or (price.get('recurring') or {}).get('interval')

    tier = metadata.get('tier')
    if tier not in TIER_PRICING:
        # Older prices carry no tier metadata - identify them by their amount.
        tier = None
        for candidate, intervals in TIER_PRICING.items():
            for candidate_interval, candidate_amount in intervals.items():
                if amount == candidate_amount and (
                    interval is None or interval == candidate_interval
                ):
                    tier, interval = candidate, candidate_interval
                    break
            if tier:
                break

    if not tier or interval not in ('month', 'year'):
        logger.warning(
            f"Could not resolve plan for subscription {stripe_sub.get('id')} "
            f"(price={price_id}, amount={amount}, interval={interval})"
        )
        return None

    return tier, interval, amount if amount is not None else TIER_PRICING[tier][interval], price_id


def process_platform_webhook(event):
    """
    Process Stripe webhook events for platform user subscriptions.
    Only handles events with metadata['subscription_type'] == 'platform'.

    The whole handler runs in one transaction alongside a ProcessedStripeEvent
    row, so a redelivered event is skipped and a failing handler rolls back its
    own claim and stays eligible for Stripe's retry.
    """
    from django.db import IntegrityError, transaction

    from .models import ProcessedStripeEvent

    event_id = getattr(event, 'id', None)
    event_type = event.type

    if event_id and ProcessedStripeEvent.objects.filter(event_id=event_id).exists():
        logger.info(f"Skipping already-processed platform event {event_id} ({event_type})")
        return {'success': True, 'skipped': 'duplicate', 'event_type': event_type}

    try:
        with transaction.atomic():
            if event_id:
                ProcessedStripeEvent.objects.create(
                    event_id=event_id, event_type=event_type, handler='platform'
                )
            return _dispatch_platform_event(event)
    except IntegrityError:
        # Lost a race with a concurrent delivery of the same event.
        logger.info(f"Concurrent delivery of platform event {event_id}; skipping")
        return {'success': True, 'skipped': 'duplicate', 'event_type': event_type}
    except Exception as e:
        logger.error(f"Error processing platform webhook {event_type}: {str(e)}")
        return {'success': False, 'error': 'Webhook processing failed'}


def _dispatch_platform_event(event):
    from .models import PlatformSubscription, PlatformSubscriptionInvoice, User

    event_type = event.type
    data = event.data.object
    logger.info(f"Processing platform webhook: {event_type}")

    if event_type == 'checkout.session.completed':
        # Checkout completed - create/update local subscription
        if data.metadata.get('subscription_type') != 'platform':
            return {'success': True, 'skipped': True}

        user_id = data.metadata.get('user_id')
        tier = data.metadata.get('tier', 'prospector')
        interval = data.metadata.get('interval', 'month')

        if not user_id or not data.subscription:
            return {'success': False, 'error': 'Missing user_id or subscription'}

        user = User.objects.get(id=user_id)
        stripe_sub = stripe.Subscription.retrieve(data.subscription)
        period_start, period_end = stripe_subscription_period(stripe_sub)

        # Prefer the plan the subscription actually carries; the session
        # metadata is only a fallback for prices with no tier metadata.
        price_cents = TIER_PRICING.get(tier, {}).get(interval, 0)
        price_id = stripe_sub['items']['data'][0]['price']['id'] if stripe_sub['items']['data'] else ''
        plan = plan_from_stripe_subscription(stripe_sub)
        if plan:
            tier, interval, price_cents, price_id = plan

        sub, created = PlatformSubscription.objects.update_or_create(
            user=user,
            defaults={
                'tier': tier,
                'status': stripe_sub.status,
                'stripe_customer_id': data.customer,
                'stripe_subscription_id': data.subscription,
                'stripe_price_id': price_id,
                'plan_interval': interval,
                'price_cents': price_cents,
                'trial_start': datetime.fromtimestamp(stripe_sub.trial_start, tz=dt_timezone.utc) if stripe_sub.trial_start else None,
                'trial_end': datetime.fromtimestamp(stripe_sub.trial_end, tz=dt_timezone.utc) if stripe_sub.trial_end else None,
                'current_period_start': datetime.fromtimestamp(period_start, tz=dt_timezone.utc),
                'current_period_end': datetime.fromtimestamp(period_end, tz=dt_timezone.utc),
                'cancel_at_period_end': False,
                'canceled_at': None,
            }
        )

        # Update AI usage limits based on tier
        from .models import UserAIUsage
        ai_usage, _ = UserAIUsage.objects.get_or_create(user=user)
        if tier in ('prospector', 'miner'):
            ai_usage.daily_message_limit = 0  # unlimited
            ai_usage.daily_token_limit = 0
        ai_usage.save()

        logger.info(f"Platform subscription {'created' if created else 'updated'} for user {user_id}: {tier}")

    elif event_type == 'customer.subscription.updated':
        sub_id = data.id
        # Check if this is a platform subscription
        if data.metadata.get('subscription_type') != 'platform':
            return {'success': True, 'skipped': True}

        try:
            sub = PlatformSubscription.objects.get(stripe_subscription_id=sub_id)
            period_start, period_end = stripe_subscription_period(data)
            sub.status = data.status
            sub.cancel_at_period_end = data.cancel_at_period_end
            sub.current_period_start = datetime.fromtimestamp(period_start, tz=dt_timezone.utc)
            sub.current_period_end = datetime.fromtimestamp(period_end, tz=dt_timezone.utc)
            if data.canceled_at:
                sub.canceled_at = datetime.fromtimestamp(data.canceled_at, tz=dt_timezone.utc)

            # A plan change made through the billing portal arrives as an
            # update carrying the new price. Without this the customer is
            # billed the new amount while their entitlements stay on the old
            # tier - the pricing page advertises portal upgrades, so this is
            # the path most plan changes take.
            plan = plan_from_stripe_subscription(data)
            if plan:
                new_tier, new_interval, new_price_cents, new_price_id = plan
                if new_tier != sub.tier:
                    logger.info(
                        f"Platform subscription {sub_id} changed plan: "
                        f"{sub.tier}/{sub.plan_interval} -> {new_tier}/{new_interval}"
                    )
                sub.tier = new_tier
                sub.plan_interval = new_interval
                sub.price_cents = new_price_cents
                sub.stripe_price_id = new_price_id

            sub.save()
            logger.info(f"Updated platform subscription {sub_id} -> {data.status}")
        except PlatformSubscription.DoesNotExist:
            logger.warning(f"Platform subscription {sub_id} not found")

    elif event_type == 'customer.subscription.deleted':
        sub_id = data.id
        if data.metadata.get('subscription_type') != 'platform':
            return {'success': True, 'skipped': True}

        try:
            sub = PlatformSubscription.objects.get(stripe_subscription_id=sub_id)
            sub.status = 'canceled'
            sub.tier = 'explorer'  # Downgrade to free
            sub.canceled_at = timezone.now()
            sub.save()

            # Reset AI usage limits to free tier
            from .models import UserAIUsage
            ai_usage, _ = UserAIUsage.objects.get_or_create(user=sub.user)
            ai_usage.daily_message_limit = 50
            ai_usage.daily_token_limit = 100000
            ai_usage.save()

            logger.info(f"Platform subscription {sub_id} canceled, user downgraded to explorer")
        except PlatformSubscription.DoesNotExist:
            logger.warning(f"Platform subscription {sub_id} not found")

    elif event_type == 'invoice.paid':
        subscription_id = stripe_invoice_subscription_id(data)
        if not subscription_id:
            return {'success': True, 'skipped': True}

        try:
            sub = PlatformSubscription.objects.get(stripe_subscription_id=subscription_id)
            PlatformSubscriptionInvoice.objects.update_or_create(
                stripe_invoice_id=data.id,
                defaults={
                    'subscription': sub,
                    'stripe_payment_intent_id': data.get('payment_intent') or '',
                    'status': 'paid',
                    'amount_cents': data.amount_paid,
                    'currency': data.currency,
                    'invoice_date': datetime.fromtimestamp(data.created, tz=dt_timezone.utc),
                    'paid_at': datetime.fromtimestamp(
                        data.status_transitions.paid_at, tz=dt_timezone.utc
                    ) if data.status_transitions.paid_at else timezone.now(),
                    'invoice_pdf_url': data.invoice_pdf or '',
                    'hosted_invoice_url': data.hosted_invoice_url or '',
                }
            )
            logger.info(f"Recorded platform invoice {data.id}")
        except PlatformSubscription.DoesNotExist:
            pass  # Not a platform subscription invoice

    elif event_type == 'invoice.payment_failed':
        subscription_id = stripe_invoice_subscription_id(data)
        if not subscription_id:
            return {'success': True, 'skipped': True}
        try:
            sub = PlatformSubscription.objects.get(stripe_subscription_id=subscription_id)
            sub.status = 'past_due'
            sub.save(update_fields=['status'])
            logger.info(f"Platform subscription {subscription_id} marked past_due")
        except PlatformSubscription.DoesNotExist:
            pass

    return {'success': True, 'event_type': event_type}
