"""
API Views for GoldVenture Platform
"""

import logging
from django.core.cache import cache
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





# =============================================================================
# NEWS RELEASE FINANCING FLAG VIEWS
# =============================================================================

class NewsReleaseFlagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reviewing news releases flagged for potential financing announcements.
    Superusers can review and create financing records from flagged news.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Will define serializer inline
    queryset = None  # Will define in get_queryset()

    def get_queryset(self):
        from core.models import NewsReleaseFlag

        # Only superusers can access
        if not self.request.user.is_superuser:
            return NewsReleaseFlag.objects.none()

        queryset = NewsReleaseFlag.objects.all().select_related(
            'news_release__company',
            'reviewed_by',
            'created_financing'
        )

        # The status filter only applies to the list view. Detail actions
        # (mark-reviewed, dismiss, close-financing) must be able to look up a
        # flag in ANY status — otherwise get_object() 404s on, e.g., a
        # reviewed_financing flag because the default filter is 'pending'.
        if self.action == 'list':
            status_filter = self.request.query_params.get('status', 'pending')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            # The "Reviewed Financing" tab is a work queue of confirmed
            # financings that are still open. Once a financing is closed it
            # belongs on /closed-financings, so drop its flag from the queue.
            if status_filter == 'reviewed_financing':
                queryset = queryset.exclude(created_financing__is_closed=True)

        return queryset

    def list(self, request, *args, **kwargs):
        """List all flagged news releases with filtering"""
        flags = self.get_queryset()

        # Build response
        data = []
        for flag in flags:
            data.append({
                'id': flag.id,
                'company_name': flag.news_release.company.name,
                'company_id': flag.news_release.company.id,
                'news_release_id': flag.news_release.id,
                'news_title': flag.news_release.title,
                'news_url': flag.news_release.url,
                'news_date': flag.news_release.release_date,
                'detected_keywords': flag.detected_keywords,
                'status': flag.status,
                'flagged_at': flag.flagged_at,
                'reviewed_by': flag.reviewed_by.username if flag.reviewed_by else None,
                'reviewed_at': flag.reviewed_at,
                'created_financing_id': flag.created_financing.id if flag.created_financing else None,
                'review_notes': flag.review_notes
            })

        return Response(data)

    @action(detail=True, methods=['post'], url_path='create-financing')
    def create_financing(self, request, pk=None):
        """
        Create a Financing record from a flagged news release.
        Marks the flag as 'reviewed_financing'.
        """
        from core.models import NewsReleaseFlag, Financing
        from decimal import Decimal
        from datetime import datetime

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get financing details from request
        financing_data = request.data

        try:
            # Parse announced date
            announced_date = financing_data.get('announced_date')
            if isinstance(announced_date, str):
                announced_date = datetime.strptime(announced_date, '%Y-%m-%d').date()

            # Create Financing record
            financing = Financing.objects.create(
                company=flag.news_release.company,
                financing_type=financing_data.get('financing_type', 'private_placement'),
                status=financing_data.get('status', 'announced'),
                announced_date=announced_date or flag.news_release.release_date,
                amount_raised_usd=Decimal(financing_data.get('amount_raised_usd', 0)),
                price_per_share=Decimal(financing_data.get('price_per_share', 0)) if financing_data.get('price_per_share') else None,
                shares_issued=financing_data.get('shares_issued'),
                has_warrants=financing_data.get('has_warrants', False),
                warrant_strike_price=Decimal(financing_data.get('warrant_strike_price', 0)) if financing_data.get('warrant_strike_price') else None,
                use_of_proceeds=financing_data.get('use_of_proceeds', ''),
                lead_agent=financing_data.get('lead_agent', ''),
                press_release_url=flag.news_release.url,
                notes=financing_data.get('notes', '')
            )

            # Mark flag as reviewed and link financing
            flag.mark_as_financing(
                reviewer=request.user,
                financing_record=financing,
                notes=financing_data.get('review_notes', 'Financing created from flagged news release')
            )

            # New open financing -> homepage teaser count is now stale.
            cache.delete('hero_section_data')

            return Response({
                'message': 'Financing created successfully',
                'financing_id': financing.id,
                'flag_id': flag.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating financing from flag: {str(e)}")
            return Response(
                {'error': 'Failed to create financing. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss_flag(self, request, pk=None):
        """
        Dismiss a flagged news release as a false positive.
        """
        from core.models import NewsReleaseFlag

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', 'Dismissed as false positive')

        try:
            flag.dismiss_as_false_positive(
                reviewer=request.user,
                notes=notes
            )

            return Response({
                'message': 'Flag dismissed successfully',
                'flag_id': flag.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error dismissing flag {flag.id}: {str(e)}")
            return Response(
                {'error': 'Failed to dismiss flag. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='mark-reviewed')
    def mark_reviewed(self, request, pk=None):
        """
        Mark a flagged news release as reviewed after financing was created separately.
        Used when CreateFinancingModal creates financing via /api/financings/ endpoint.
        """
        from core.models import NewsReleaseFlag

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', 'Financing created from news flag')
        financing_id = request.data.get('financing_id')

        try:
            # Mark as reviewed and link the created financing record so the
            # flag <-> financing relationship matches the company-page flow.
            # Without this link the "Close Financing" action cannot find the
            # financing, leaving it stuck on the homepage Financing Opportunities.
            flag.status = 'reviewed_financing'
            flag.reviewed_by = request.user
            flag.reviewed_at = timezone.now()
            flag.review_notes = notes

            if financing_id:
                from core.models import Financing
                try:
                    financing = Financing.objects.get(id=financing_id)
                    flag.created_financing = financing
                    # Back-link the source flag on the financing too, so the
                    # closed-financings page can surface the source news.
                    if not financing.source_news_flag:
                        financing.source_news_flag = flag
                        financing.save(update_fields=['source_news_flag'])
                except Financing.DoesNotExist:
                    logger.warning(
                        f"Financing {financing_id} not found when marking flag {flag.id} reviewed"
                    )

            flag.save()

            # An externally-created financing was linked through this path;
            # the homepage card may have missed it on the previous tick.
            cache.delete('hero_section_data')

            return Response({
                'message': 'Flag marked as reviewed',
                'flag_id': flag.id,
                'created_financing_id': flag.created_financing.id if flag.created_financing else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error marking flag {flag.id} as reviewed: {str(e)}")
            return Response(
                {'error': 'Failed to mark flag as reviewed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='close-financing')
    def close_financing(self, request, pk=None):
        """
        Mark an existing financing as closed and remove from the news-flags queue.
        Used when a financing announcement has been confirmed closed.

        The financing record is NOT deleted - it's marked as closed with is_closed=True
        and will appear on the /closed-financings page.
        """
        from core.models import NewsReleaseFlag, Financing

        flag = self.get_object()

        # Check if flag has a linked financing
        if not flag.created_financing:
            return Response(
                {'error': 'This flag does not have an associated financing record. Create a financing first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            financing = flag.created_financing

            # Update closing_date if provided
            closing_date = request.data.get('closing_date')
            if closing_date:
                from datetime import datetime
                if isinstance(closing_date, str):
                    closing_date = datetime.strptime(closing_date, '%Y-%m-%d').date()
                financing.closing_date = closing_date

            # Mark financing as closed
            financing.mark_as_closed(user=request.user)

            # Link the source news flag
            financing.source_news_flag = flag
            financing.save()

            # Update flag notes if provided
            notes = request.data.get('notes', '')
            if notes:
                flag.review_notes = (flag.review_notes or '') + f'\n[Closed] {notes}'
                flag.save()

            # Financing left the open set -> homepage teaser count is now stale.
            cache.delete('hero_section_data')

            return Response({
                'message': 'Financing marked as closed successfully',
                'financing_id': financing.id,
                'flag_id': flag.id,
                'closed_at': financing.closed_at.isoformat() if financing.closed_at else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error closing financing for flag {flag.id}: {str(e)}")
            return Response(
                {'error': 'Failed to close financing. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

