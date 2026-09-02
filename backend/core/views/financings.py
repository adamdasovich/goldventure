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
    # Additional models for this module
    FinancingAggregate,

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
# OTHER VIEWSETS
# ============================================================================

class ResourceEstimateViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceEstimateSerializer

    def get_permissions(self):
        """Allow read for anyone, require auth for write operations"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Optimize queries with select_related for project FK"""
        return ResourceEstimate.objects.select_related('project', 'project__company').all()




class FinancingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financings (private placements, etc.)

    - GET /api/financings/ - List all financings (public)
    - GET /api/financings/{id}/ - Get financing details (public)
    - POST /api/financings/ - Create financing (superuser or company rep)
    - PUT/PATCH /api/financings/{id}/ - Update financing (superuser or company rep)
    - DELETE /api/financings/{id}/ - Delete financing (superuser only)
    """
    serializer_class = FinancingSerializer

    # Params this endpoint understands. Anything else is rejected rather than
    # ignored: ?status=open used to be dropped silently and return all 297
    # financings, which reads as "297 open rounds" when there are 21. A filter
    # that quietly does nothing is worse than one that errors, because the
    # caller believes the answer.
    ALLOWED_LIST_PARAMS = frozenset({
        'company', 'status', 'is_closed',
        # DRF infrastructure: pagination, search, ordering, format suffix.
        'page', 'page_size', 'search', 'ordering', 'format',
    })

    _TRUE = frozenset({'true', '1', 'yes'})
    _FALSE = frozenset({'false', '0', 'no'})

    def get_queryset(self):
        """Financings, optionally narrowed by company and open/closed state."""
        # Note: is_deleted field requires migration 0041 to be applied
        queryset = Financing.objects.select_related('company').all()
        params = self.request.query_params

        # `company` is an id. A non-numeric one used to reach the ORM and die
        # in int() as a 500 — ?company=Portofino was a server error on a public
        # endpoint. list() rejects it with a 400; here it is simply ignored,
        # because get_queryset also serves the detail routes, where raising
        # would turn a valid /financings/{id}/ into an error over a stray
        # query string.
        company_id = (params.get('company') or '').strip()
        if company_id.isdigit():
            queryset = queryset.filter(company_id=int(company_id))

        # "status" is the friendly spelling; "is_closed" mirrors the column.
        status_param = (params.get('status') or '').strip().lower()
        if status_param == 'open':
            queryset = queryset.filter(is_closed=False)
        elif status_param == 'closed':
            queryset = queryset.filter(is_closed=True)

        is_closed_param = (params.get('is_closed') or '').strip().lower()
        if is_closed_param in self._TRUE:
            queryset = queryset.filter(is_closed=True)
        elif is_closed_param in self._FALSE:
            queryset = queryset.filter(is_closed=False)

        return queryset.order_by('-announced_date')

    def list(self, request, *args, **kwargs):
        """Validate the query string before answering it."""
        unknown = sorted(set(request.query_params) - self.ALLOWED_LIST_PARAMS)
        if unknown:
            return Response(
                {
                    'error': 'unknown_query_parameter',
                    'detail': (
                        'Unrecognised query parameter(s): '
                        + ', '.join(unknown)
                        + '. This endpoint would otherwise ignore them and '
                        'return every financing, which reads as a filtered '
                        'result.'
                    ),
                    'unknown': unknown,
                    'supported': sorted(self.ALLOWED_LIST_PARAMS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bad = {}
        company_param = (request.query_params.get('company') or '').strip()
        if company_param and not company_param.isdigit():
            bad['company'] = (
                "expected a numeric company id. To look a company up by name "
                "or ticker, call /api/companies/?search=<term> first."
            )
        status_param = (request.query_params.get('status') or '').strip().lower()
        if status_param and status_param not in ('open', 'closed'):
            bad['status'] = "expected 'open' or 'closed'"
        is_closed_param = (
            request.query_params.get('is_closed') or ''
        ).strip().lower()
        if is_closed_param and is_closed_param not in (self._TRUE | self._FALSE):
            bad['is_closed'] = "expected 'true' or 'false'"
        if bad:
            return Response(
                {'error': 'invalid_query_parameter', 'detail': bad},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        """Allow read for anyone, require auth for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        """Create a new financing - only superuser or company rep can create"""
        user = request.user
        company_id = request.data.get('company')

        if not company_id:
            return Response({'error': 'Company ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate company_id is numeric
        try:
            company_id_int = int(company_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid company ID format'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has permission (superuser, staff, or company rep)
        if not user.is_superuser and not user.is_staff:
            if not hasattr(user, 'company_id') or user.company_id != company_id_int:
                return Response(
                    {'error': 'You do not have permission to create financings for this company'},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update a financing - only superuser or company rep can update"""
        user = request.user
        financing = self.get_object()

        if not user.is_superuser and not user.is_staff:
            if not hasattr(user, 'company_id') or user.company_id != financing.company_id:
                return Response(
                    {'error': 'You do not have permission to update this financing'},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a financing - only superuser or authorized company rep can delete"""
        user = request.user
        financing = self.get_object()

        # Check permissions first
        has_permission = False
        if user.is_superuser or user.is_staff:
            has_permission = True
        elif hasattr(user, 'company_id') and user.company_id == financing.company_id:
            has_permission = True

        if not has_permission:
            return Response(
                {'error': 'You do not have permission to delete this financing'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check for actual investment records that should NOT be auto-deleted
        if financing.investment_interests.exists():
            return Response(
                {'error': 'Cannot delete financing with existing investment interests. Please remove them first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if financing.subscription_agreements.exists():
            return Response(
                {'error': 'Cannot delete financing with existing subscription agreements. Please remove them first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if financing.investment_transactions.exists():
            return Response(
                {'error': 'Cannot delete financing with existing investment transactions. Please remove them first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Safe to delete aggregate stats (they're just computed data, not actual records)
        # Delete InvestmentInterestAggregate if exists
        if hasattr(financing, 'interest_aggregate'):
            financing.interest_aggregate.delete()
        # Delete FinancingAggregate if exists
        if hasattr(financing, 'aggregate_data'):
            financing.aggregate_data.delete()

        return super().destroy(request, *args, **kwargs)

