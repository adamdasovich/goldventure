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
from ..query_guard import guard_query_params

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
# CLOSED FINANCINGS API (For /closed-financings page)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@guard_query_params("company", "date_from", "date_to", "financing_type", "sort_by", "sort_order")
def closed_financings_list(request):
    """
    List all closed financings for display on the /closed-financings page.

    GET /api/closed-financings/

    Query Parameters:
    - company: Filter by company name (partial match)
    - financing_type: Filter by financing type
    - date_from: Filter by closing date (YYYY-MM-DD)
    - date_to: Filter by closing date (YYYY-MM-DD)
    - sort_by: Sort field (closed_at, company, amount, closing_date)
    - sort_order: asc or desc (default: desc)

    Access Control:
    - Currently: All authenticated users can access
    - Future: Set CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION = True to restrict to paying users
    """
    from core.models import Financing
    from django.db.models import Q

    # ========== ACCESS CONTROL ==========
    # Set this to True to restrict access to paying users only
    CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION = False

    if CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION:
        # Check if user has an active subscription
        # TODO: Implement subscription check when payment system is ready
        # Example: if not request.user.has_active_subscription:
        #     return Response({'error': 'Subscription required'}, status=403)
        pass
    # ====================================

    # Base queryset - only closed financings
    queryset = Financing.objects.filter(is_closed=True).select_related(
        'company',
        'closed_by',
        'source_news_flag__news_release'
    )

    # Apply filters
    company_filter = request.query_params.get('company')
    if company_filter:
        queryset = queryset.filter(company__name__icontains=company_filter)

    financing_type_filter = request.query_params.get('financing_type')
    if financing_type_filter:
        queryset = queryset.filter(financing_type=financing_type_filter)

    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(closing_date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(closing_date__lte=date_to)

    # Sorting
    sort_by = request.query_params.get('sort_by', 'closed_at')
    sort_order = request.query_params.get('sort_order', 'desc')

    sort_mapping = {
        'closed_at': 'closing_date',
        'company': 'company__name',
        'amount': 'amount_raised_usd',
        'closing_date': 'closing_date',
        'announced_date': 'announced_date',
    }

    sort_field = sort_mapping.get(sort_by, 'closed_at')
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'

    queryset = queryset.order_by(sort_field)

    # Build response
    data = []
    for financing in queryset:
        # Get source news release URL if available
        source_news_url = None
        source_news_title = None
        source_news_date = None

        if financing.source_news_flag and financing.source_news_flag.news_release:
            source_news_url = financing.source_news_flag.news_release.url
            source_news_title = financing.source_news_flag.news_release.title
            source_news_date = financing.source_news_flag.news_release.release_date
        elif financing.press_release_url:
            source_news_url = financing.press_release_url

        data.append({
            'id': financing.id,
            'company_id': financing.company.id,
            'company_slug': financing.company.slug,
            'company_name': financing.company.name,
            'company_ticker': financing.company.ticker_symbol,
            'company_exchange': financing.company.exchange,
            'financing_type': financing.financing_type,
            'financing_type_display': dict(Financing.FINANCING_TYPES).get(financing.financing_type, financing.financing_type),
            'status': financing.status,
            'amount_raised_usd': str(financing.amount_raised_usd) if financing.amount_raised_usd else None,
            'price_per_share': str(financing.price_per_share) if financing.price_per_share else None,
            'shares_issued': financing.shares_issued,
            'has_warrants': financing.has_warrants,
            'warrant_strike_price': str(financing.warrant_strike_price) if financing.warrant_strike_price else None,
            'warrant_expiry_date': financing.warrant_expiry_date.isoformat() if financing.warrant_expiry_date else None,
            'announced_date': financing.announced_date.isoformat() if financing.announced_date else None,
            'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            'closed_at': financing.closed_at.isoformat() if financing.closed_at else None,
            'closed_by': financing.closed_by.username if financing.closed_by else None,
            'lead_agent': financing.lead_agent,
            'use_of_proceeds': financing.use_of_proceeds,
            'source_news_url': source_news_url,
            'source_news_title': source_news_title,
            'source_news_date': source_news_date.isoformat() if source_news_date else None,
            'notes': financing.notes,
        })

    # Get available financing types for filter dropdown
    financing_types = [
        {'value': ft[0], 'label': ft[1]}
        for ft in Financing.FINANCING_TYPES
    ]

    return Response({
        'count': len(data),
        'results': data,
        'financing_types': financing_types,
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_closed_financing(request):
    """
    Create a new closed financing directly (for adding historical/past financings).

    POST /api/closed-financings/create/

    Request Body:
    {
        "company_id": 123,
        "financing_type": "private_placement",
        "amount_raised_usd": 5000000,
        "price_per_share": 0.15,
        "shares_issued": 33333333,
        "has_warrants": true,
        "warrant_strike_price": 0.20,
        "warrant_expiry_date": "2026-01-15",
        "announced_date": "2024-12-01",
        "closing_date": "2024-12-15",
        "lead_agent": "Agent Name",
        "use_of_proceeds": "Exploration activities",
        "press_release_url": "https://...",
        "notes": "Optional notes",
        "source_news_flag_id": 456  // Optional - links to news flag and triggers duplicate detection
    }

    When source_news_flag_id is provided:
    - Links the new financing to the news flag
    - Detects and removes duplicate 'announced' financing rounds for the same company
    - Updates the news flag status to 'reviewed_financing'

    Superuser access required.
    """
    from core.models import Financing, Company, NewsReleaseFlag
    from django.utils import timezone
    from decimal import Decimal
    from datetime import timedelta

    # Superuser check
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can add closed financings'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Validate required fields
    company_id = request.data.get('company_id')
    if not company_id:
        return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    financing_type = request.data.get('financing_type')
    if not financing_type:
        return Response({'error': 'financing_type is required'}, status=status.HTTP_400_BAD_REQUEST)

    amount_raised = request.data.get('amount_raised_usd')
    if not amount_raised:
        return Response({'error': 'amount_raised_usd is required'}, status=status.HTTP_400_BAD_REQUEST)

    closing_date = request.data.get('closing_date')
    if not closing_date:
        return Response({'error': 'closing_date is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Get company
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Parse dates
        from datetime import datetime
        if isinstance(closing_date, str):
            closing_date = datetime.strptime(closing_date, '%Y-%m-%d').date()

        announced_date = request.data.get('announced_date')
        if announced_date and isinstance(announced_date, str):
            announced_date = datetime.strptime(announced_date, '%Y-%m-%d').date()
        else:
            announced_date = closing_date  # Default to closing date

        warrant_expiry_date = request.data.get('warrant_expiry_date')
        if warrant_expiry_date and isinstance(warrant_expiry_date, str):
            warrant_expiry_date = datetime.strptime(warrant_expiry_date, '%Y-%m-%d').date()

        # Check for source_news_flag_id to link and handle duplicates
        source_news_flag_id = request.data.get('source_news_flag_id')
        source_news_flag = None
        duplicates_removed = 0

        if source_news_flag_id:
            try:
                source_news_flag = NewsReleaseFlag.objects.get(id=source_news_flag_id)
            except NewsReleaseFlag.DoesNotExist:
                # Log warning but don't fail - the flag might have been deleted
                logger.warning(f"NewsReleaseFlag {source_news_flag_id} not found")

        # Detect and remove duplicate financing rounds if this came from a news flag
        # Look for 'announced' status financings for the same company within a date range
        if source_news_flag:
            # Define date range for duplicate detection (±30 days from closing date)
            date_range_start = closing_date - timedelta(days=30)
            date_range_end = closing_date + timedelta(days=30)

            # Find potential duplicate financings (announced but not closed, same company, similar timeframe)
            duplicate_financings = Financing.objects.filter(
                company=company,
                status='announced',  # Only look at announced (not yet closed) financings
                is_closed=False,
            ).filter(
                # Match by announced_date OR closing_date within range
                announced_date__gte=date_range_start,
                announced_date__lte=date_range_end,
            )

            # Delete duplicates (must remove protected InvestmentInterestAggregate first)
            duplicates_removed = duplicate_financings.count()
            if duplicates_removed > 0:
                logger.info(f"Removing {duplicates_removed} duplicate announced financing(s) for {company.name}")
                for dup in duplicate_financings:
                    # Remove the aggregate record that references this financing via PROTECT FK
                    if hasattr(dup, 'interest_aggregate'):
                        dup.interest_aggregate.delete()
                    dup.delete()

        # Create the financing
        financing = Financing.objects.create(
            company=company,
            financing_type=financing_type,
            status='closed',
            amount_raised_usd=Decimal(str(amount_raised)),
            price_per_share=Decimal(str(request.data.get('price_per_share', 0))) if request.data.get('price_per_share') else None,
            shares_issued=request.data.get('shares_issued'),
            has_warrants=request.data.get('has_warrants', False),
            warrant_strike_price=Decimal(str(request.data.get('warrant_strike_price', 0))) if request.data.get('warrant_strike_price') else None,
            warrant_expiry_date=warrant_expiry_date,
            announced_date=announced_date,
            closing_date=closing_date,
            lead_agent=request.data.get('lead_agent', ''),
            use_of_proceeds=request.data.get('use_of_proceeds', ''),
            press_release_url=request.data.get('press_release_url', ''),
            notes=request.data.get('notes', ''),
            # Mark as closed
            is_closed=True,
            closed_at=timezone.now(),
            closed_by=request.user,
            # Link to source news flag if provided
            source_news_flag=source_news_flag,
        )

        # Update the news flag status if it was provided
        if source_news_flag:
            source_news_flag.status = 'reviewed_financing'
            source_news_flag.reviewed_by = request.user
            source_news_flag.reviewed_at = timezone.now()
            source_news_flag.created_financing = financing
            source_news_flag.review_notes = f'Closed financing created directly from flag (Amount: ${amount_raised:,.2f})'
            source_news_flag.save()

        # Duplicate 'announced' financings may have been removed, and the new
        # record is created as already-closed — either way, the homepage open
        # count is now stale.
        from django.core.cache import cache
        cache.delete('hero_section_data')

        return Response({
            'message': 'Closed financing created successfully',
            'financing': {
                'id': financing.id,
                'company_name': company.name,
                'company_ticker': company.ticker_symbol,
                'financing_type': financing.financing_type,
                'amount_raised_usd': str(financing.amount_raised_usd),
                'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            },
            'duplicates_removed': duplicates_removed,
            'news_flag_updated': source_news_flag is not None,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error creating closed financing: {str(e)}\nTraceback: {error_details}")
        logger.error(f"Request data: {request.data}")
        return Response({'error': f'Failed to create financing: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_closed_financing(request, financing_id):
    """
    Update an existing closed financing.

    PUT/PATCH /api/closed-financings/<id>/update/

    Request Body (all fields optional for PATCH):
    {
        "financing_type": "private_placement",
        "amount_raised_usd": 5000000,
        "price_per_share": 0.15,
        "shares_issued": 33333333,
        "has_warrants": true,
        "warrant_strike_price": 0.20,
        "warrant_expiry_date": "2026-01-15",
        "announced_date": "2024-12-01",
        "closing_date": "2024-12-15",
        "lead_agent": "Agent Name",
        "use_of_proceeds": "Exploration activities",
        "press_release_url": "https://...",
        "notes": "Optional notes",
        "status": "announced" | "closing" | "closed" | "cancelled",
        "is_closed": true
    }

    Despite the name, this operates on ANY financing by id — there is no
    is_closed filter on the lookup — so /open-financings edits through it too.
    `is_closed` is what decides which of the two pages a row appears on;
    setting it true here stamps closed_at/closed_by and moves the row from
    /open-financings to /closed-financings.

    Superuser access required.
    """
    from core.models import Financing
    from decimal import Decimal
    from django.utils import timezone

    # Superuser check
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can update financings'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get the financing
    try:
        financing = Financing.objects.get(id=financing_id)
    except Financing.DoesNotExist:
        return Response({'error': 'Financing not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Parse dates if provided
        from datetime import datetime

        # Update fields if provided
        if 'financing_type' in request.data:
            financing.financing_type = request.data['financing_type']

        if 'amount_raised_usd' in request.data:
            financing.amount_raised_usd = Decimal(str(request.data['amount_raised_usd']))

        if 'price_per_share' in request.data:
            price = request.data['price_per_share']
            financing.price_per_share = Decimal(str(price)) if price else None

        if 'shares_issued' in request.data:
            financing.shares_issued = request.data['shares_issued'] or None

        if 'has_warrants' in request.data:
            financing.has_warrants = request.data['has_warrants']

        if 'warrant_strike_price' in request.data:
            price = request.data['warrant_strike_price']
            financing.warrant_strike_price = Decimal(str(price)) if price else None

        if 'warrant_expiry_date' in request.data:
            date_str = request.data['warrant_expiry_date']
            if date_str and isinstance(date_str, str):
                financing.warrant_expiry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                financing.warrant_expiry_date = None

        if 'announced_date' in request.data:
            date_str = request.data['announced_date']
            if date_str and isinstance(date_str, str):
                financing.announced_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if 'closing_date' in request.data:
            date_str = request.data['closing_date']
            if date_str and isinstance(date_str, str):
                financing.closing_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if 'lead_agent' in request.data:
            financing.lead_agent = request.data['lead_agent'] or ''

        if 'use_of_proceeds' in request.data:
            financing.use_of_proceeds = request.data['use_of_proceeds'] or ''

        if 'press_release_url' in request.data:
            financing.press_release_url = request.data['press_release_url'] or ''

        if 'notes' in request.data:
            financing.notes = request.data['notes'] or ''

        if 'status' in request.data:
            new_status = request.data['status']
            valid = [choice[0] for choice in Financing.STATUS_CHOICES]
            if new_status not in valid:
                return Response(
                    {'error': f"Invalid status. Expected one of: {', '.join(valid)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            financing.status = new_status

        # is_closed is the flag the two public pages split on, so flipping it
        # is what moves a row between /open-financings and /closed-financings.
        # Only stamp closed_at/closed_by on the transition — re-saving an
        # already-closed financing must not rewrite who closed it or when.
        if 'is_closed' in request.data:
            now_closed = bool(request.data['is_closed'])
            if now_closed and not financing.is_closed:
                financing.closed_at = timezone.now()
                financing.closed_by = request.user
            elif not now_closed and financing.is_closed:
                financing.closed_at = None
                financing.closed_by = None
            financing.is_closed = now_closed

        financing.save()

        return Response({
            'message': 'Financing updated successfully',
            'financing': {
                'id': financing.id,
                'company_name': financing.company.name,
                'company_ticker': financing.company.ticker_symbol,
                'financing_type': financing.financing_type,
                'amount_raised_usd': str(financing.amount_raised_usd),
                'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
                'status': financing.status,
                'is_closed': financing.is_closed,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating financing {financing_id}: {str(e)}")
        return Response({'error': 'Failed to update financing. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

