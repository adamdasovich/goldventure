"""
API Views for Platform User Subscriptions.
Handles checkout, status, cancellation, billing portal, and webhooks.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..entitlements import CHAT_LIMITS, FREE_TOOLS, MINER_TOOLS
from ..models import PlatformSubscription, PlatformSubscriptionInvoice
from ..platform_stripe_service import (
    PlatformStripeService,
    process_platform_webhook,
    TIER_PRICING,
    TRIAL_DAYS,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def platform_subscription_tiers(request):
    """
    GET /api/platform/tiers/
    Public endpoint returning available subscription tiers and pricing.
    """
    def money(cents):
        """$15 / $150 - whole dollars, since every plan is priced that way."""
        return f"${cents // 100:,}"

    prospector = TIER_PRICING['prospector']
    miner = TIER_PRICING['miner']

    tiers = [
        {
            'id': 'explorer',
            'name': 'Explorer',
            'tagline': 'Get started with mining intelligence',
            'monthly_price_cents': 0,
            'annual_price_cents': 0,
            'monthly_price': 'Free',
            'annual_price': 'Free',
            'trial_days': 0,
            'features': {
                'daily_chat_limit': CHAT_LIMITS['explorer'],
                'investor_tools': list(FREE_TOOLS),
                'full_company_data': False,
            }
        },
        {
            'id': 'prospector',
            'name': 'Prospector',
            'tagline': 'Full access for serious investors',
            'monthly_price_cents': prospector['month'],
            'annual_price_cents': prospector['year'],
            'monthly_price': money(prospector['month']),
            'annual_price': money(prospector['year']),
            'annual_savings': money(prospector['month'] * 12 - prospector['year']),
            'trial_days': TRIAL_DAYS,
            'features': {
                'daily_chat_limit': CHAT_LIMITS['prospector'],
                'investor_tools': {'excludes': list(MINER_TOOLS)},
                'full_company_data': True,
            }
        },
        {
            'id': 'miner',
            'name': 'Miner',
            'tagline': 'Maximum power for professionals',
            'monthly_price_cents': miner['month'],
            'annual_price_cents': miner['year'],
            'monthly_price': money(miner['month']),
            'annual_price': money(miner['year']),
            'annual_savings': money(miner['month'] * 12 - miner['year']),
            'trial_days': TRIAL_DAYS,
            'features': {
                'daily_chat_limit': CHAT_LIMITS['miner'],
                'investor_tools': 'all',
                'miner_only_tools': list(MINER_TOOLS),
                'full_company_data': True,
            }
        },
    ]
    return Response({'tiers': tiers})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def platform_subscription_status(request):
    """
    GET /api/platform/subscription/
    Get the current user's subscription status and feature flags.
    """
    user = request.user
    try:
        sub = PlatformSubscription.objects.get(user=user)
        data = {
            'tier': sub.tier,
            'effective_tier': sub.effective_tier,
            # Local check only - no Stripe round-trip on a hot endpoint. Lets
            # the pricing page stop promising a trial to returning customers,
            # who no longer get one at checkout.
            'trial_eligible': not PlatformStripeService.has_used_trial(user),
            'status': sub.status,
            'is_active': sub.is_active,
            'plan_interval': sub.plan_interval,
            'price_cents': sub.price_cents,
            'trial_end': sub.trial_end.isoformat() if sub.trial_end else None,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            'cancel_at_period_end': sub.cancel_at_period_end,
            'features': sub.features,
        }
    except PlatformSubscription.DoesNotExist:
        # User has no subscription record -> explorer
        data = {
            'tier': 'explorer',
            'effective_tier': 'explorer',
            # No record at all means no prior Stripe subscription.
            'trial_eligible': True,
            'status': 'active',
            'is_active': True,
            'plan_interval': None,
            'price_cents': 0,
            'trial_end': None,
            'current_period_end': None,
            'cancel_at_period_end': False,
            'features': {
                'tier': 'explorer',
                'daily_chat_limit': CHAT_LIMITS['explorer'],
                'investor_tools': list(FREE_TOOLS),
                'miner_only_tools': list(MINER_TOOLS),
                'full_company_data': False,
            }
        }

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def platform_create_checkout(request):
    """
    POST /api/platform/checkout/
    Body: { "tier": "prospector"|"miner", "interval": "month"|"year" }
    Creates a Stripe Checkout Session and returns the URL.
    """
    tier = request.data.get('tier')
    interval = request.data.get('interval', 'month')

    if tier not in ('prospector', 'miner'):
        return Response(
            {'error': 'Invalid tier. Must be "prospector" or "miner".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if interval not in ('month', 'year'):
        return Response(
            {'error': 'Invalid interval. Must be "month" or "year".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not PlatformStripeService.is_configured():
        return Response(
            {'error': 'Payment processing is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # Check if user already has an active paid subscription
    try:
        existing = PlatformSubscription.objects.get(user=request.user)
        if existing.is_active and existing.is_paid_tier:
            return Response(
                {'error': 'You already have an active subscription. Use the billing portal to change plans.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except PlatformSubscription.DoesNotExist:
        pass

    base_url = request.data.get('base_url', 'https://juniorminingintelligence.com')
    success_url = f"{base_url}/pricing?success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/pricing?canceled=true"

    try:
        session = PlatformStripeService.create_checkout_session(
            user=request.user,
            tier=tier,
            interval=interval,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return Response({
            'checkout_url': session.url,
            'session_id': session.id,
        })
    except Exception as e:
        logger.error(f"Platform checkout error: {str(e)}")
        return Response(
            {'error': 'Failed to create checkout session. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def platform_billing_portal(request):
    """
    POST /api/platform/billing-portal/
    Creates a Stripe Billing Portal session for managing subscription.
    """
    try:
        sub = PlatformSubscription.objects.get(user=request.user)
        if not sub.stripe_customer_id:
            return Response(
                {'error': 'No billing account found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    except PlatformSubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    base_url = request.data.get('return_url', 'https://juniorminingintelligence.com/pricing')

    try:
        session = PlatformStripeService.create_billing_portal_session(
            sub.stripe_customer_id, base_url
        )
        return Response({'portal_url': session.url})
    except Exception as e:
        logger.error(f"Billing portal error: {str(e)}")
        return Response(
            {'error': 'Failed to open billing portal.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def platform_cancel_subscription(request):
    """
    POST /api/platform/cancel/
    Cancel the current user's subscription at period end.
    """
    try:
        sub = PlatformSubscription.objects.get(user=request.user)
        if not sub.stripe_subscription_id:
            return Response({'error': 'No active subscription to cancel.'}, status=status.HTTP_400_BAD_REQUEST)
    except PlatformSubscription.DoesNotExist:
        return Response({'error': 'No subscription found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        PlatformStripeService.cancel_subscription(sub.stripe_subscription_id, at_period_end=True)
        sub.cancel_at_period_end = True
        sub.save(update_fields=['cancel_at_period_end'])
        return Response({'message': 'Subscription will cancel at end of billing period.'})
    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        return Response({'error': 'Failed to cancel subscription.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def platform_reactivate_subscription(request):
    """
    POST /api/platform/reactivate/
    Reactivate a subscription that was set to cancel at period end.
    """
    try:
        sub = PlatformSubscription.objects.get(user=request.user)
        if not sub.cancel_at_period_end:
            return Response({'error': 'Subscription is not set to cancel.'}, status=status.HTTP_400_BAD_REQUEST)
    except PlatformSubscription.DoesNotExist:
        return Response({'error': 'No subscription found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        PlatformStripeService.reactivate_subscription(sub.stripe_subscription_id)
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        sub.save(update_fields=['cancel_at_period_end', 'canceled_at'])
        return Response({'message': 'Subscription reactivated.'})
    except Exception as e:
        logger.error(f"Reactivate error: {str(e)}")
        return Response({'error': 'Failed to reactivate.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def platform_stripe_webhook(request):
    """
    POST /api/platform/webhooks/stripe/
    Stripe webhook endpoint for platform subscription events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = PlatformStripeService.construct_webhook_event(payload, sig_header)
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    result = process_platform_webhook(event)

    if result.get('success'):
        return Response({'status': 'ok'})
    return Response({'error': result.get('error', 'Processing failed')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
