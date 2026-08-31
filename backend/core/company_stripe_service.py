"""
Stripe Service for Company Subscriptions.

The company plan: CA$50/month or CA$500/year, bought by a mining company so its
approved representative can edit its page - description, projects, resources and
speaking events.

Deliberately NOT a platform tier. Tiers describe what a *reader* can see;
this describes what a *company* may change about itself, and the two have
nothing to say to each other. A company representative can hold a Prospector
subscription for research and their employer can hold this one, independently.

Mirrors platform_stripe_service.py closely - same product-by-fixed-id pattern,
same amount-scoped price lookup, same webhook shape. Where the two differ:
the subscription is keyed on a Company rather than a User, so the Stripe
customer is the company and any approved representative can manage it.
"""

import logging
from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings

from .api_utils import (
    get_stripe_api_key,
    stripe_subscription_period,
    stripe_invoice_subscription_id,
)

logger = logging.getLogger(__name__)

# Pricing configuration (cents). The only place the company plan's price is
# written down; /api/company/plan/ reads it so the marketing copy cannot drift
# from what Stripe charges.
COMPANY_PRICING = {
    'month': 5000,    # $50/month
    'year': 50000,    # $500/year (10x monthly)
}

TRIAL_DAYS = 7

# A Stripe Price's currency is immutable, so this is baked into the price
# metadata and the lookup: changing it creates fresh prices rather than reusing
# stale ones of another currency.
PRICE_CURRENCY = 'cad'

# Fixed id, so "get or create" is a retrieve rather than a search. Product
# search is eventually consistent in Stripe and two near-simultaneous callers
# will each create their own - which is exactly how the platform products
# ended up duplicated on 2026-08-31.
PRODUCT_ID = 'jmi_company_listing'
PRODUCT_NAME = 'Junior Mining Intelligence — Company Listing'

_price_cache = {}


class CompanyStripeService:
    """Stripe operations for the company plan."""

    @staticmethod
    def is_configured():
        key = get_stripe_api_key()
        if not key:
            return False
        return key.startswith('sk_test_') or key.startswith('sk_live_')

    @staticmethod
    def _get_or_create_product():
        get_stripe_api_key()

        product_id = getattr(settings, 'STRIPE_COMPANY_PRODUCT_ID', '') or PRODUCT_ID

        try:
            return stripe.Product.retrieve(product_id)
        except stripe.error.InvalidRequestError:
            pass  # Not created yet.

        try:
            product = stripe.Product.create(
                id=product_id,
                name=PRODUCT_NAME,
                description="Manage your company's profile on Junior Mining Intelligence",
                metadata={'type': 'company_subscription'},
            )
        except stripe.error.InvalidRequestError:
            # Lost a race; the id being taken is the outcome we wanted.
            return stripe.Product.retrieve(product_id)

        logger.info(f"Created Stripe product {product.id} for company subscriptions")
        return product

    @staticmethod
    def get_or_create_price(interval='month'):
        get_stripe_api_key()
        amount = COMPANY_PRICING.get(interval)
        if not amount:
            raise ValueError(f"Invalid interval: {interval}")

        cache_key = f"company_{interval}_{amount}_{PRICE_CURRENCY}"
        if cache_key in _price_cache:
            return _price_cache[cache_key]

        product = CompanyStripeService._get_or_create_product()

        # Scoped by product, currency AND amount: unit_amount and currency are
        # immutable on a Price, so a price change has to make a new one, and an
        # unscoped search would hand back the old amount forever.
        prices = stripe.Price.search(
            query=(
                f"product:'{product.id}' AND metadata['interval']:'{interval}' "
                f"AND metadata['currency']:'{PRICE_CURRENCY}' AND metadata['amount']:'{amount}'"
            )
        )
        if prices.data:
            _price_cache[cache_key] = prices.data[0].id
            return prices.data[0].id

        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=PRICE_CURRENCY,
            recurring={'interval': interval},
            metadata={
                'type': 'company_subscription',
                'interval': interval,
                'currency': PRICE_CURRENCY,
                'amount': str(amount),
            },
        )
        logger.info(f"Created Stripe price {price.id} for company/{interval}")
        _price_cache[cache_key] = price.id
        return price.id

    @staticmethod
    def has_used_trial(company):
        """True if `company` has already had a subscription, so no new trial.

        Without this, cancel-and-resubscribe is a free week every time.
        """
        from .models import CompanySubscription

        sub = CompanySubscription.objects.filter(company=company).first()
        if sub and sub.stripe_subscription_id:
            return True

        if not sub or not sub.stripe_customer_id:
            return False

        try:
            existing = stripe.Subscription.list(
                customer=sub.stripe_customer_id, status='all', limit=1
            )
            return bool(existing.data)
        except Exception as e:
            # Never block a legitimate checkout over a failed lookup.
            logger.warning(f"Could not check trial history for company {company.id}: {e}")
            return False

    @staticmethod
    def create_checkout_session(company, user, interval, success_url, cancel_url):
        """Start checkout for `company`, paid by `user` on its behalf."""
        if interval not in COMPANY_PRICING:
            raise ValueError(f"Invalid interval: {interval}")

        get_stripe_api_key()
        from .models import CompanySubscription

        price_id = CompanyStripeService.get_or_create_price(interval)

        sub = CompanySubscription.objects.filter(company=company).first()
        customer_id = sub.stripe_customer_id if sub and sub.stripe_customer_id else ''

        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=company.name,
                metadata={
                    'company_id': str(company.id),
                    'company_slug': company.slug,
                    'subscription_type': 'company',
                    # Who bought it, for support. Not an authorisation record -
                    # any approved representative can manage the subscription.
                    'purchased_by_user_id': str(user.id),
                },
            )
            customer_id = customer.id
            if sub:
                sub.stripe_customer_id = customer_id
                sub.save(update_fields=['stripe_customer_id'])

        subscription_data = {
            'metadata': {
                'company_id': str(company.id),
                'interval': interval,
                'subscription_type': 'company',
            }
        }
        if not CompanyStripeService.has_used_trial(company):
            subscription_data['trial_period_days'] = TRIAL_DAYS

        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            # Managed Payments is on by default for new Stripe accounts and
            # rejects payment_method_types while demanding product tax codes.
            managed_payments={'enabled': False},
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            allow_promotion_codes=True,
            subscription_data=subscription_data,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'company_id': str(company.id),
                'interval': interval,
                'subscription_type': 'company',
            },
        )

    @staticmethod
    def create_billing_portal_session(customer_id, return_url):
        get_stripe_api_key()
        return stripe.billing_portal.Session.create(
            customer=customer_id, return_url=return_url
        )

    @staticmethod
    def construct_webhook_event(payload, sig_header):
        get_stripe_api_key()
        secret = getattr(settings, 'STRIPE_COMPANY_WEBHOOK_SECRET', '')
        if not secret:
            raise ValueError('STRIPE_COMPANY_WEBHOOK_SECRET is not configured')
        return stripe.Webhook.construct_event(payload, sig_header, secret)


def plan_from_stripe_subscription(stripe_sub):
    """Resolve (plan_type, price_cents, price_id, interval) from a subscription.

    Read from the price the subscription currently carries, not from metadata
    stamped at checkout: metadata is never rewritten, so after a switch from
    monthly to annual in the portal it still says 'month' and the database
    would record the wrong plan against the right money.
    """
    items = (stripe_sub.get('items') or {}).get('data') or []
    if not items:
        return None

    price = items[0].get('price') or {}
    price_id = price.get('id') or ''
    amount = price.get('unit_amount')
    interval = (price.get('metadata') or {}).get('interval') or (
        price.get('recurring') or {}
    ).get('interval')

    if interval not in COMPANY_PRICING:
        # Unknown price - identify by amount before giving up.
        for candidate, candidate_amount in COMPANY_PRICING.items():
            if amount == candidate_amount:
                interval = candidate
                break
        else:
            return None

    plan_type = 'annual' if interval == 'year' else 'monthly'
    return plan_type, amount, price_id, interval


def sync_checkout_session(session, expected_user=None):
    """Apply a completed Checkout Session to the local CompanySubscription.

    Shared by the webhook and the post-checkout confirm endpoint, because the
    webhook arrives asynchronously and a representative redirected back from
    Stripe would otherwise be told their page is still read-only seconds after
    paying for it.

    Idempotent - an update_or_create keyed on the company, so whichever path
    runs second rewrites the same values.

    ``expected_user`` guards the caller-facing path: the session id travels in
    a URL, so the endpoint must refuse to apply a session for a company the
    caller does not represent.
    """
    from .models import Company, CompanySubscription

    metadata = session.get('metadata') or {}
    if metadata.get('subscription_type') != 'company':
        raise ValueError('Not a company checkout session')

    company_id = metadata.get('company_id')
    subscription_id = session.get('subscription')
    if not company_id or not subscription_id:
        raise ValueError('Session has no company_id or subscription')

    company = Company.objects.filter(id=company_id).first()
    if not company:
        raise ValueError(f'Unknown company {company_id}')

    if expected_user is not None and not (
        getattr(expected_user, 'is_superuser', False)
        or expected_user.company_id == company.id
    ):
        raise PermissionError('Checkout session belongs to another company')

    stripe_sub = stripe.Subscription.retrieve(subscription_id)
    period_start, period_end = stripe_subscription_period(stripe_sub)

    plan_type = 'monthly'
    price_cents = COMPANY_PRICING['month']
    price_id = ''
    plan = plan_from_stripe_subscription(stripe_sub)
    if plan:
        plan_type, price_cents, price_id, _interval = plan

    sub, created = CompanySubscription.objects.update_or_create(
        company=company,
        defaults={
            'stripe_customer_id': session.get('customer') or '',
            'stripe_subscription_id': subscription_id,
            'stripe_price_id': price_id,
            'plan_type': plan_type,
            'status': stripe_sub.status,
            'price_cents': price_cents,
            'trial_start': datetime.fromtimestamp(stripe_sub.trial_start, tz=dt_timezone.utc) if stripe_sub.trial_start else None,
            'trial_end': datetime.fromtimestamp(stripe_sub.trial_end, tz=dt_timezone.utc) if stripe_sub.trial_end else None,
            'current_period_start': datetime.fromtimestamp(period_start, tz=dt_timezone.utc),
            'current_period_end': datetime.fromtimestamp(period_end, tz=dt_timezone.utc),
            'cancel_at_period_end': False,
            'canceled_at': None,
        },
    )
    logger.info(
        f"Company subscription {'created' if created else 'updated'} for "
        f"{company.name} ({plan_type}, {stripe_sub.status})"
    )
    return sub


def process_company_webhook(event):
    """Handle one verified Stripe event for the company plan."""
    from .models import CompanySubscription

    event_type = event['type']
    obj = event['data']['object']

    if event_type == 'checkout.session.completed':
        if (obj.get('metadata') or {}).get('subscription_type') != 'company':
            return {'handled': False, 'reason': 'not a company session'}
        sync_checkout_session(obj)
        return {'handled': True}

    if event_type in ('customer.subscription.updated', 'customer.subscription.deleted'):
        sub = CompanySubscription.objects.filter(
            stripe_subscription_id=obj.get('id') or ''
        ).first()
        if not sub:
            return {'handled': False, 'reason': 'unknown subscription'}

        sub.status = 'canceled' if event_type.endswith('deleted') else obj.get('status', sub.status)
        sub.cancel_at_period_end = bool(obj.get('cancel_at_period_end'))

        period_start, period_end = stripe_subscription_period(obj)
        if period_start and period_end:
            sub.current_period_start = datetime.fromtimestamp(period_start, tz=dt_timezone.utc)
            sub.current_period_end = datetime.fromtimestamp(period_end, tz=dt_timezone.utc)

        plan = plan_from_stripe_subscription(obj)
        if plan:
            sub.plan_type, sub.price_cents, sub.stripe_price_id, _ = plan

        sub.save()
        return {'handled': True}

    if event_type == 'invoice.paid':
        subscription_id = stripe_invoice_subscription_id(obj)
        sub = CompanySubscription.objects.filter(
            stripe_subscription_id=subscription_id or ''
        ).first()
        if not sub:
            return {'handled': False, 'reason': 'unknown subscription'}
        # A paid invoice is the clearest signal a lapsed plan is live again.
        if sub.status not in ('active', 'trialing'):
            sub.status = 'active'
            sub.save(update_fields=['status', 'updated_at'])
        return {'handled': True}

    if event_type == 'invoice.payment_failed':
        subscription_id = stripe_invoice_subscription_id(obj)
        sub = CompanySubscription.objects.filter(
            stripe_subscription_id=subscription_id or ''
        ).first()
        if not sub:
            return {'handled': False, 'reason': 'unknown subscription'}
        sub.status = 'past_due'
        sub.save(update_fields=['status', 'updated_at'])
        return {'handled': True}

    return {'handled': False, 'reason': f'unhandled event {event_type}'}
