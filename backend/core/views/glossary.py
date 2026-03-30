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
# GLOSSARY VIEWSET
# ============================================================================

class GlossaryTermViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for mining glossary terms
    Provides read-only access to glossary (superuser can edit via admin)
    """
    queryset = GlossaryTerm.objects.all()
    serializer_class = GlossaryTermSerializer
    permission_classes = [permissions.AllowAny]  # Public access for SEO
    filterset_fields = ['category']
    search_fields = ['term', 'definition', 'keywords']
    ordering_fields = ['term', 'created_at', 'category']
    ordering = ['term']  # Default alphabetical ordering

    @action(detail=False, methods=['get'])
    def by_letter(self, request):
        """Get glossary terms grouped by first letter"""
        letter = request.query_params.get('letter', '').upper()
        if not letter or len(letter) != 1:
            return Response(
                {'error': 'Please provide a single letter parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        terms = self.queryset.filter(term__istartswith=letter)
        serializer = self.get_serializer(terms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_term(self, request):
        """Search for a specific term definition (for chatbot)"""
        term = request.query_params.get('term', '')
        if not term:
            return Response(
                {'error': 'Please provide a term parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try exact match first
        glossary_term = self.queryset.filter(term__iexact=term).first()
        if glossary_term:
            serializer = self.get_serializer(glossary_term)
            return Response(serializer.data)

        # Try partial match
        terms = self.queryset.filter(term__icontains=term)[:5]
        if terms:
            serializer = self.get_serializer(terms, many=True)
            return Response({
                'exact_match': False,
                'suggestions': serializer.data
            })

        return Response(
            {'error': 'Term not found', 'term': term},
            status=status.HTTP_404_NOT_FOUND
        )




class GlossaryTermSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user-submitted glossary terms
    - POST: Authenticated users can submit new terms
    - GET: Superusers can view pending submissions
    - PUT/PATCH: Superusers can approve or reject submissions
    """
    queryset = GlossaryTermSubmission.objects.all()
    filterset_fields = ['status', 'submitted_by', 'category']
    search_fields = ['term', 'definition']
    ordering_fields = ['submitted_at', 'term', 'status']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return GlossaryTermSubmissionCreateSerializer
        return GlossaryTermSubmissionSerializer

    def get_permissions(self):
        """
        - Create: Authenticated users
        - List/Retrieve/Update: Superusers only
        """
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        # Regular users can only see their own submissions
        return self.queryset.filter(submitted_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending(self, request):
        """Get all pending submissions (superuser only)"""
        pending_submissions = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending_submissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a submission and create GlossaryTerm (superuser only)"""
        submission = self.get_object()

        if submission.status != 'pending':
            return Response(
                {'error': f'Cannot approve submission with status: {submission.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            approved_term = submission.approve(reviewer=request.user)
            return Response({
                'message': 'Submission approved successfully',
                'approved_term_id': approved_term.id,
                'term': approved_term.term
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GlossaryTermSubmission approve error for submission {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to approve submission. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a submission (superuser only)"""
        submission = self.get_object()

        if submission.status != 'pending':
            return Response(
                {'error': f'Cannot reject submission with status: {submission.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rejection_reason = request.data.get('reason', 'No reason provided')

        try:
            submission.reject(reviewer=request.user, reason=rejection_reason)
            return Response({
                'message': 'Submission rejected successfully',
                'term': submission.term,
                'reason': rejection_reason
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"GlossaryTermSubmission reject error for submission {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to reject submission. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

