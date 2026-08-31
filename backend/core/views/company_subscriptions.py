"""
API views for the company plan - the subscription a mining company buys so its
approved representative can edit its own page.

The gate is two-part and both halves live elsewhere: identity comes from
``user.company`` (set only when staff approve a CompanyAccessRequest) and
payment from CompanySubscription. ``core.company_access`` combines them; these
views only sell and report.
"""

import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..company_access import (
    access_state,
    company_subscription_active,
    has_live_subscription,
)
from ..company_stripe_service import (
    COMPANY_PRICING,
    TRIAL_DAYS,
    CompanyStripeService,
    process_company_webhook,
    sync_checkout_session,
)
from ..models import Company, CompanySubscription
from ..security_utils import validate_checkout_redirect

logger = logging.getLogger(__name__)


def _money(cents):
    """$50 / $500 - whole dollars, since the plan is priced that way."""
    return f"${cents // 100:,}"


def _subscription_payload(company):
    """What the caller needs to render the state of one company's plan.

    Accepts None (a user who represents nobody) and returns the same keys, all
    empty, so callers never branch on the shape.
    """
    sub = (
        CompanySubscription.objects.filter(company=company).first()
        if company
        else None
    )
    if not sub:
        return {
            'has_subscription': False,
            'is_active': False,
            'status': None,
            'plan_type': None,
            'price_cents': 0,
            'trial_end': None,
            'current_period_end': None,
            'cancel_at_period_end': False,
            'has_billing_account': False,
            'trial_eligible': True,
        }
    return {
        'has_subscription': True,
        'is_active': sub.is_active,
        'status': sub.status,
        'plan_type': sub.plan_type,
        'price_cents': sub.price_cents,
        'trial_end': sub.trial_end.isoformat() if sub.trial_end else None,
        'current_period_end': (
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        'cancel_at_period_end': sub.cancel_at_period_end,
        # No Stripe customer means no billing portal to send them to.
        'has_billing_account': bool(sub.stripe_customer_id),
        'trial_eligible': not CompanyStripeService.has_used_trial(company),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def company_plan(request):
    """
    GET /api/company/plan/

    Public pricing for the company plan, read from COMPANY_PRICING so the
    pricing page cannot drift from what Stripe charges. Not a platform tier -
    see /api/platform/tiers/ for those.
    """
    return Response({
        'id': 'company',
        'name': 'Company',
        'tagline': 'For mining companies managing their own profile',
        'audience': 'company',
        'monthly_price_cents': COMPANY_PRICING['month'],
        'annual_price_cents': COMPANY_PRICING['year'],
        'monthly_price': _money(COMPANY_PRICING['month']),
        'annual_price': _money(COMPANY_PRICING['year']),
        'annual_savings': _money(COMPANY_PRICING['month'] * 12 - COMPANY_PRICING['year']),
        'trial_days': TRIAL_DAYS,
        'currency': 'CAD',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_subscription_status(request):
    """
    GET /api/company/subscription/

    The caller's own company plan. Answers "may I edit, and if not, why not",
    which is the question the company page needs to render its edit controls.
    """
    company = request.user.company
    if not company:
        # Not a representative of anything: the same shape, all false, so the
        # frontend never has to special-case a missing body.
        return Response({
            'company': None,
            'is_representative': False,
            'can_edit': False,
            'requires_subscription': False,
            **_subscription_payload(None),
        })

    state = access_state(request.user, company)
    return Response({
        'company': {
            'id': company.id,
            'name': company.name,
            'slug': company.slug,
        },
        'is_representative': state['is_representative'],
        'can_edit': state['can_edit'],
        'requires_subscription': state['requires_subscription'],
        **_subscription_payload(company),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_create_checkout(request):
    """
    POST /api/company/checkout/
    Body: { "interval": "month"|"year" }

    Only an approved representative may buy. Approval is the identity check -
    without it anyone could subscribe against any company and take over its
    page, which is precisely the thing the access-request flow exists to stop.
    """
    interval = request.data.get('interval', 'month')
    if interval not in COMPANY_PRICING:
        return Response(
            {'error': 'Invalid interval. Must be "month" or "year".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    company = request.user.company
    if not company:
        return Response(
            {
                'error': 'no_company_access',
                'detail': (
                    'Request access to your company first. Once an administrator '
                    'approves you, you can subscribe on its behalf.'
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if not CompanyStripeService.is_configured():
        return Response(
            {'error': 'Payment processing is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Refuse whenever a live Stripe subscription exists, not merely an *active*
    # one. A past_due subscription is not active — the card failed — but it is
    # very much still there, and letting them check out again would leave the
    # company paying for two. Repairing the card belongs in the billing portal.
    if has_live_subscription(company):
        subscription_active = company_subscription_active(company)
        return Response(
            {
                'error': 'subscription_exists',
                'detail': (
                    f'{company.name} already has a subscription. Use the billing '
                    f'portal to change plans.'
                    if subscription_active
                    else f"{company.name}'s subscription needs a payment method "
                         f'updating. Use the billing portal rather than '
                         f'subscribing again.'
                ),
                'needs_billing_portal': True,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    base_url = request.data.get('base_url', 'https://juniorminingintelligence.com')
    ok, reason = validate_checkout_redirect(base_url)
    if not ok:
        logger.warning(
            f"Rejected base_url from user {request.user.id}: {reason} ({base_url!r})"
        )
        return Response({'error': 'Invalid base_url'}, status=status.HTTP_400_BAD_REQUEST)

    base_url = base_url.rstrip('/')
    success_url = (
        f"{base_url}/companies/{company.slug}"
        f"?company_subscription=success&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{base_url}/companies/{company.slug}?company_subscription=canceled"

    try:
        session = CompanyStripeService.create_checkout_session(
            company=company,
            user=request.user,
            interval=interval,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return Response({'checkout_url': session.url, 'session_id': session.id})
    except Exception as e:
        logger.error(f"Company checkout error for {company.id}: {e}")
        return Response(
            {'error': 'Failed to create checkout session. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_confirm_checkout(request):
    """
    POST /api/company/checkout/confirm/
    Body: { "session_id": "cs_..." }

    Reconcile a just-completed checkout rather than waiting on the webhook, so
    the edit controls appear as soon as they land back on their page.
    """
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    import stripe
    from ..api_utils import get_stripe_api_key

    get_stripe_api_key()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        logger.warning(f"Could not retrieve company checkout session {session_id!r}: {e}")
        return Response({'error': 'Unknown checkout session'}, status=status.HTTP_404_NOT_FOUND)

    if session.get('payment_status') not in ('paid', 'no_payment_required'):
        # Trials complete with no payment taken, hence the second case.
        return Response(
            {'status': 'pending', 'detail': 'Checkout is not complete yet.'},
            status=status.HTTP_202_ACCEPTED,
        )

    try:
        sub = sync_checkout_session(session, expected_user=request.user)
    except PermissionError:
        logger.warning(
            f"User {request.user.id} tried to confirm a company session for another company"
        )
        return Response({'error': 'Unknown checkout session'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Company checkout confirm failed: {e}")
        return Response(
            {'error': 'Could not confirm this checkout.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({'status': sub.status, 'is_active': sub.is_active})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_billing_portal(request):
    """
    POST /api/company/billing-portal/

    Any approved representative of the company can manage its billing - the
    subscription belongs to the company, not to whoever happened to buy it.
    """
    company = request.user.company
    if not company:
        return Response({'error': 'No company access.'}, status=status.HTTP_403_FORBIDDEN)

    sub = CompanySubscription.objects.filter(company=company).first()
    if not sub or not sub.stripe_customer_id:
        return Response({'error': 'No billing account found.'}, status=status.HTTP_404_NOT_FOUND)

    return_url = request.data.get(
        'return_url', f'https://juniorminingintelligence.com/companies/{company.slug}'
    )
    ok, reason = validate_checkout_redirect(return_url)
    if not ok:
        logger.warning(
            f"Rejected return_url from user {request.user.id}: {reason} ({return_url!r})"
        )
        return Response({'error': 'Invalid return_url'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = CompanyStripeService.create_billing_portal_session(
            sub.stripe_customer_id, return_url
        )
        return Response({'portal_url': session.url})
    except Exception as e:
        logger.error(f"Company billing portal error: {e}")
        return Response(
            {'error': 'Failed to open billing portal.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def company_stripe_webhook(request):
    """
    POST /api/company/webhook/

    Its own endpoint and its own signing secret, separate from the platform and
    store webhooks: one secret per endpoint is how Stripe issues them, and
    sharing one would mean a rotation on any endpoint silently breaking the
    others.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = CompanyStripeService.construct_webhook_event(payload, sig_header)
    except ValueError as e:
        logger.error(f"Company webhook not configured or bad payload: {e}")
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Company webhook signature verification failed: {e}")
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = process_company_webhook(event)
    except Exception as e:
        # 500 so Stripe retries; a swallowed error here loses a payment state.
        logger.error(f"Company webhook handler failed for {event['type']}: {e}", exc_info=True)
        return Response({'error': 'Handler failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(result)
