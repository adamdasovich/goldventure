"""
API Views for GoldVenture Platform
"""

import logging

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
# HOMEPAGE HERO SECTION CARDS API
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def hero_section_data(request):
    """
    Get data for the three hero section cards on the homepage.

    GET /api/hero-section/

    Returns:
    - upcoming_events: Speaker events within the next 7 days
    - active_financings: Companies with active financing rounds
    - featured_property: The currently featured property listing
    """
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    seven_days_from_now = now + timedelta(days=7)
    one_hour_ago = now - timedelta(hours=1)

    # Card 1: Upcoming Speaking Events (next 7 days)
    # Show events scheduled within 7 days, remove events 1 hour after start
    upcoming_events = SpeakerEvent.objects.filter(
        Q(status='scheduled') | Q(status='live'),
        scheduled_start__lte=seven_days_from_now,
        scheduled_start__gte=one_hour_ago
    ).select_related('company').prefetch_related('speakers__user').order_by('scheduled_start')[:5]

    events_data = []
    for event in upcoming_events:
        # Determine if event is live or upcoming
        is_live = event.status == 'live' or (
            event.scheduled_start <= now <= event.scheduled_end if event.scheduled_end else False
        )
        events_data.append({
            'id': event.id,
            'title': event.title,
            'company_id': event.company.id,
            'company_name': event.company.name,
            'company_ticker': event.company.ticker_symbol,
            'scheduled_start': event.scheduled_start.isoformat(),
            'scheduled_end': event.scheduled_end.isoformat() if event.scheduled_end else None,
            'status': 'live' if is_live else 'upcoming',
            'format': event.format,
            'registered_count': event.registrations.count(),
        })

    # Card 2: Active Financing Opportunities
    active_financings = Financing.objects.filter(
        status__in=['announced', 'closing']
    ).select_related('company').order_by('-announced_date')[:5]

    financings_data = []
    for financing in active_financings:
        financings_data.append({
            'id': financing.id,
            'company_id': financing.company.id,
            'company_name': financing.company.name,
            'company_ticker': financing.company.ticker_symbol,
            'financing_type': financing.financing_type,
            'financing_type_display': financing.get_financing_type_display(),
            'amount_raised_usd': float(financing.amount_raised_usd) if financing.amount_raised_usd else None,
            'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            'status': financing.status,
        })

    # Card 3: Featured Property Listing
    featured_property = None
    config = FeaturedPropertyConfig.get_current_featured()

    # Check if we need to auto-rotate (it's past the next rotation date)
    if config.next_auto_rotation and now >= config.next_auto_rotation and not config.is_manual_selection:
        config = FeaturedPropertyConfig.rotate_featured_property()

    # If no property is set but there are active listings, pick one
    if not config.listing:
        active_listings = PropertyListing.objects.filter(status='active')
        if active_listings.exists():
            from random import choice
            config.listing = choice(list(active_listings))
            # Set next rotation to next Monday
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = (now + timedelta(days=days_until_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            config.next_auto_rotation = next_monday
            config.save()

    if config.listing:
        listing = config.listing
        # Get primary image
        primary_image = listing.media.filter(media_type='image', is_primary=True).first()
        if not primary_image:
            primary_image = listing.media.filter(media_type='image').first()

        featured_property = {
            'id': listing.id,
            'slug': listing.slug,
            'title': listing.title,
            'summary': listing.summary,
            'location': f"{listing.nearest_town}, {listing.province_state}" if listing.nearest_town else listing.province_state,
            'country': listing.get_country_display(),
            'primary_mineral': listing.get_primary_mineral_display(),
            'total_hectares': float(listing.total_hectares) if listing.total_hectares else None,
            'asking_price': float(listing.asking_price) if listing.asking_price else None,
            'price_currency': listing.price_currency,
            'listing_type': listing.get_listing_type_display(),
            'exploration_stage': listing.get_exploration_stage_display(),
            'primary_image_url': primary_image.file_url if primary_image else None,
            'next_rotation': config.next_auto_rotation.isoformat() if config.next_auto_rotation else None,
            'is_manual_selection': config.is_manual_selection,
        }

    return Response({
        'upcoming_events': events_data,
        'active_financings': financings_data,
        'featured_property': featured_property,
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_featured_property(request):
    """
    Set a specific property as featured (superuser only).

    POST /api/hero-section/set-featured/
    Body: { "listing_id": 123 }
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can set featured properties'},
            status=status.HTTP_403_FORBIDDEN
        )

    listing_id = request.data.get('listing_id')
    if not listing_id:
        return Response(
            {'error': 'listing_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        listing = PropertyListing.objects.get(id=listing_id, status='active')
    except PropertyListing.DoesNotExist:
        return Response(
            {'error': 'Property listing not found or not active'},
            status=status.HTTP_404_NOT_FOUND
        )

    from django.utils import timezone
    from datetime import timedelta

    config = FeaturedPropertyConfig.get_current_featured()
    config.listing = listing
    config.is_manual_selection = True
    config.selected_by = request.user
    # Next auto-rotation is still next Monday, but won't trigger since is_manual_selection=True
    now = timezone.now()
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    config.next_auto_rotation = next_monday
    config.save()

    return Response({
        'message': f'Featured property set to: {listing.title}',
        'listing_id': listing.id,
        'listing_title': listing.title,
        'next_auto_rotation': config.next_auto_rotation.isoformat(),
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_featured_property(request):
    """
    Reset featured property to auto-rotation mode (superuser only).

    POST /api/hero-section/reset-featured/
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can reset featured properties'},
            status=status.HTTP_403_FORBIDDEN
        )

    config = FeaturedPropertyConfig.rotate_featured_property()

    return Response({
        'message': 'Featured property reset to auto-rotation',
        'listing_id': config.listing.id if config.listing else None,
        'listing_title': config.listing.title if config.listing else None,
        'next_auto_rotation': config.next_auto_rotation.isoformat() if config.next_auto_rotation else None,
    })

