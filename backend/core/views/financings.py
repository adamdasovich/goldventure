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

    def get_queryset(self):
        """Filter financings by company if company query param is provided"""
        # Note: is_deleted field requires migration 0041 to be applied
        queryset = Financing.objects.select_related('company').all()
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset.order_by('-announced_date')

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

