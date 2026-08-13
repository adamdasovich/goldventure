"""
API Views for GoldVenture Platform
"""

import logging
from django.utils import timezone

from rest_framework import viewsets, status, permissions

from ..models import (
    Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, MarketData, NewsRelease, Document,
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    # Property Exchange models
    ProspectorProfile, PropertyListing, PropertyMedia, PropertyInquiry,
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement,
    InquiryMessage, FeaturedPropertyConfig,
    # News models
    NewsSource, NewsArticle, NewsScrapeJob,
    # Company Portal models
    CompanyResource, SpeakingEvent, CompanySubscription, SubscriptionInvoice,
    CompanyAccessRequest,
    # Investment Interest models
    InvestmentInterest, InvestmentInterestAggregate,
    # Store models
    StoreCategory, StoreProduct, StoreProductImage, StoreProductVariant,
    StoreDigitalAsset, StoreCart, StoreCartItem, StoreOrder, StoreOrderItem,
    StoreShippingRate, StoreProductShare, StoreRecentPurchase,
    StoreProductInquiry, UserStoreBadge,
    # Glossary
    GlossaryTerm, GlossaryTermSubmission,
)

from ..serializers import (
    CompanySerializer, CompanyDetailSerializer,
    ProjectSerializer, ProjectDetailSerializer,
    ResourceEstimateSerializer, EconomicStudySerializer,
    FinancingSerializer, InvestorSerializer,
    MarketDataSerializer, NewsReleaseSerializer, DocumentSerializer,
    SpeakerEventListSerializer, SpeakerEventDetailSerializer,
    SpeakerEventCreateSerializer, EventQuestionSerializer, EventReactionSerializer,
    # Property Exchange serializers
    ProspectorProfileSerializer, PropertyListingListSerializer,
    PropertyListingDetailSerializer, PropertyListingCreateSerializer,
    PropertyMediaSerializer, PropertyInquirySerializer, PropertyWatchlistSerializer,
    SavedPropertySearchSerializer, PropertyChoicesSerializer,
    ProspectorCommissionAgreementSerializer, ProspectorCommissionAgreementCreateSerializer,
    # Inquiry message serializers
    InquiryMessageSerializer, InquiryMessageCreateSerializer, PropertyInquiryWithMessagesSerializer,
    # Company Portal serializers
    CompanyResourceSerializer, CompanyResourceCreateSerializer, CompanyResourceChoicesSerializer,
    SpeakingEventSerializer, SpeakingEventCreateSerializer, SpeakingEventListSerializer,
    SpeakingEventChoicesSerializer, CompanySubscriptionSerializer, CompanySubscriptionStatusSerializer,
    SubscriptionInvoiceSerializer,
    # Company Access Request serializers
    CompanyAccessRequestSerializer, CompanyAccessRequestCreateSerializer,
    CompanyAccessRequestReviewSerializer, CompanyAccessRequestChoicesSerializer,
    # Investment Interest serializers
    InvestmentInterestSerializer, InvestmentInterestCreateSerializer,
    InvestmentInterestAggregateSerializer, InvestmentInterestStatusSerializer,
    # Store serializers
    StoreCategorySerializer, StoreProductListSerializer, StoreProductDetailSerializer,
    StoreCartSerializer, StoreCartItemSerializer, StoreOrderSerializer,
    StoreShippingRateSerializer, StoreRecentPurchaseSerializer,
    StoreProductShareSerializer, StoreProductInquirySerializer,
    StoreProductInquiryCreateSerializer, UserStoreBadgeSerializer,
    AddToCartSerializer, UpdateCartItemSerializer, CheckoutSerializer,
    # Store Admin serializers
    StoreCategoryAdminSerializer, StoreProductAdminListSerializer,
    StoreProductAdminDetailSerializer, StoreProductAdminCreateSerializer,
    StoreProductImageAdminSerializer, StoreProductVariantAdminSerializer,
    StoreDigitalAssetAdminSerializer, StoreOrderAdminSerializer,
    # Glossary serializers
    GlossaryTermSerializer, GlossaryTermSubmissionSerializer,
    GlossaryTermSubmissionCreateSerializer,
)


# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q





# ============================================================================
# STRIPE SUBSCRIPTION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for a new subscription.

    POST /api/company-portal/subscriptions/create-checkout/
    Body: {
        "success_url": "https://...",
        "cancel_url": "https://..."
    }

    Returns:
        checkout_url: URL to redirect user to Stripe Checkout
        session_id: Stripe session ID
    """
    from ..stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company to subscribe'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not StripeService.is_configured():
        return Response(
            {'error': 'Payment system is not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    success_url = request.data.get('success_url')
    cancel_url = request.data.get('cancel_url')

    if not success_url or not cancel_url:
        return Response(
            {'error': 'success_url and cancel_url are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Stripe sends the customer to these after payment, so they must point at
    # an origin we control - otherwise this is an open redirect off a payment.
    from ..security_utils import validate_checkout_redirect
    for label, candidate in (('success_url', success_url), ('cancel_url', cancel_url)):
        ok, reason = validate_checkout_redirect(candidate)
        if not ok:
            logger.warning(
                f"Rejected {label} from user {request.user.id}: {reason} ({candidate!r})"
            )
            return Response(
                {'error': f'Invalid {label}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Check if company already has an active subscription
    try:
        existing_sub = CompanySubscription.objects.get(company=request.user.company)
        if existing_sub.is_active:
            return Response(
                {'error': 'Company already has an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except CompanySubscription.DoesNotExist:
        pass

    try:
        session = StripeService.create_checkout_session(
            company=request.user.company,
            user=request.user,
            success_url=success_url,
            cancel_url=cancel_url
        )
        return Response({
            'checkout_url': session.url,
            'session_id': session.id
        })
    except Exception as e:
        # SECURITY: Log full error but return generic message to prevent info leakage
        logger.error(f"Checkout session creation failed for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to create checkout session. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_billing_portal(request):
    """
    Create a Stripe billing portal session for subscription management.

    POST /api/company-portal/subscriptions/billing-portal/
    Body: {
        "return_url": "https://..."
    }

    Returns:
        portal_url: URL to redirect user to Stripe Billing Portal
    """
    from ..stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_customer_id:
            return Response(
                {'error': 'No billing account found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    return_url = request.data.get('return_url')
    if not return_url:
        return Response(
            {'error': 'return_url is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from ..security_utils import validate_checkout_redirect
    ok, reason = validate_checkout_redirect(return_url)
    if not ok:
        logger.warning(
            f"Rejected return_url from user {request.user.id}: {reason} ({return_url!r})"
        )
        return Response({'error': 'Invalid return_url'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = StripeService.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )
        return Response({
            'portal_url': session.url
        })
    except Exception as e:
        # SECURITY: Log full error but return generic message
        logger.error(f"Billing portal creation failed for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to access billing portal. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """
    Cancel the company's subscription.

    POST /api/company-portal/subscriptions/cancel/
    Body: {
        "immediate": false  # Optional, defaults to canceling at period end
    }

    Returns:
        success: true
        cancel_at_period_end: boolean
    """
    from ..stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    immediate = request.data.get('immediate', False)

    try:
        stripe_sub = StripeService.cancel_subscription(
            subscription_id=subscription.stripe_subscription_id,
            at_period_end=not immediate
        )

        # Update local record
        if immediate:
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
        else:
            subscription.cancel_at_period_end = True
        subscription.save()

        return Response({
            'success': True,
            'cancel_at_period_end': not immediate,
            'status': subscription.status
        })
    except Exception as e:
        # SECURITY: Log full error but return generic message
        logger.error(f"Subscription cancellation failed for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to cancel subscription. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reactivate_subscription(request):
    """
    Reactivate a subscription that was set to cancel at period end.

    POST /api/company-portal/subscriptions/reactivate/

    Returns:
        success: true
    """
    from ..stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not subscription.cancel_at_period_end:
            return Response(
                {'error': 'Subscription is not set to cancel'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        StripeService.reactivate_subscription(subscription.stripe_subscription_id)

        # Update local record
        subscription.cancel_at_period_end = False
        subscription.save(update_fields=['cancel_at_period_end'])

        return Response({
            'success': True,
            'status': subscription.status
        })
    except Exception as e:
        # SECURITY: Log full error but return generic message
        logger.error(f"Subscription reactivation failed for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to reactivate subscription. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.

    POST /api/company-portal/webhooks/stripe/

    This endpoint verifies the webhook signature and processes
    subscription events from Stripe.
    """
    from ..stripe_service import StripeService, process_subscription_webhook
    import json

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not sig_header:
        return Response(
            {'error': 'Missing Stripe signature'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        event = StripeService.construct_webhook_event(payload, sig_header)
    except ValueError:
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # SECURITY: Log full error but return generic message (don't reveal webhook secrets)
        logger.error(f"Stripe webhook verification failed: {str(e)}")
        return Response(
            {'error': 'Webhook verification failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Process the event
    result = process_subscription_webhook(event)

    if result.get('success'):
        return Response({'received': True, 'event_type': result.get('event_type')})
    else:
        return Response(
            {'error': result.get('error')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

