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
from ..query_guard import GuardedListParamsMixin





# ============================================================================
# PROJECT VIEWSET
# ============================================================================

class ProjectViewSet(GuardedListParamsMixin, viewsets.ModelViewSet):
    """API endpoint for projects"""
    # Warn-only: unknown params are logged, not rejected. Flip to True
    # once a week of logs shows nothing real is missing from this list.
    ALLOWED_LIST_PARAMS = frozenset({'commodity', 'company'})
    STRICT_LIST_PARAMS = False
    queryset = Project.objects.all()

    WRITE_ACTIONS = ('create', 'update', 'partial_update', 'destroy')

    def get_permissions(self):
        """Anyone may read. Writes need authentication; which company you may
        write to is settled per-object in the perform_* hooks below.

        This was IsAdminUser, which meant the "+ Add Project" button a company
        representative could see on their own page would have 403'd. Nobody
        had ever been granted a company link, so it was never hit.
        """
        if self.action in self.WRITE_ACTIONS:
            return [IsAuthenticated()]
        return [AllowAny()]

    def _check_company(self, company):
        """Staff edit anything; a representative edits their own paid company."""
        from rest_framework.exceptions import PermissionDenied
        from ..company_access import access_state

        user = self.request.user
        if user.is_staff:
            return

        state = access_state(user, company)
        if state['can_edit']:
            return

        if state['requires_subscription']:
            raise PermissionDenied({
                'error': 'subscription_required',
                'detail': (
                    f'{company.name} needs an active company subscription before '
                    f'its projects can be edited.'
                ),
                'requires_subscription': True,
            })
        raise PermissionDenied('You can only edit projects for your own company.')

    def perform_create(self, serializer):
        self._check_company(serializer.validated_data.get('company'))
        serializer.save()

    def perform_update(self, serializer):
        # Check the company it belongs to now, and the one it would move to.
        self._check_company(serializer.instance.company)
        target = serializer.validated_data.get('company')
        if target and target != serializer.instance.company:
            self._check_company(target)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_company(instance.company)
        instance.delete()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True)

        # Filter by company
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by commodity
        commodity = self.request.query_params.get('commodity')
        if commodity:
            queryset = queryset.filter(primary_commodity=commodity)

        return queryset.select_related('company').order_by('-is_flagship', 'name')

