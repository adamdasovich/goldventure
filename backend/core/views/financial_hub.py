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
    AccreditedInvestorQualification, SubscriptionAgreement, PaymentInstruction, DRSDocument, InvestmentTransaction, ModuleCompletion, EducationalModule, FinancingAggregate,

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
    # Financial Hub serializers
    EducationalModuleSerializer, ModuleCompletionSerializer,
    AccreditedInvestorQualificationSerializer,
    SubscriptionAgreementSerializer, SubscriptionAgreementDetailSerializer,
    InvestmentTransactionSerializer, FinancingAggregateSerializer,
    PaymentInstructionSerializer, DRSDocumentSerializer,
)


# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q





class EducationalModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Educational Modules

    Endpoints:
    - GET /api/education/modules/ - List all published modules
    - GET /api/education/modules/{id}/ - Get module details
    - POST /api/education/modules/{id}/complete/ - Mark module as complete
    """
    serializer_class = EducationalModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EducationalModule.objects.filter(is_published=True)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a module as completed"""
        module = self.get_object()
        user = request.user

        # Get or create completion record
        completion, created = ModuleCompletion.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'time_spent_seconds': request.data.get('time_spent_seconds', 0),
                'passed': request.data.get('passed', True),
            }
        )

        if not created:
            # Update existing completion
            completion.time_spent_seconds += request.data.get('time_spent_seconds', 0)
            completion.passed = request.data.get('passed', True)

        # Mark as completed
        if not completion.completed_at:
            completion.completed_at = timezone.now()

        completion.save()

        return Response({
            'message': 'Module marked as complete',
            'completion': ModuleCompletionSerializer(completion).data
        }, status=status.HTTP_200_OK)




class ModuleCompletionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Module Completions

    Endpoints:
    - GET /api/education/completions/ - List user's completions
    """
    serializer_class = ModuleCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ModuleCompletion.objects.filter(user=self.request.user).select_related('module')




class AccreditedInvestorQualificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Accredited Investor Qualifications

    Endpoints:
    - GET /api/qualifications/ - List user's qualifications
    - POST /api/qualifications/ - Submit qualification
    - GET /api/qualifications/status/ - Get current qualification status
    """
    serializer_class = AccreditedInvestorQualificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AccreditedInvestorQualification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get user's current qualification status"""
        qualification = AccreditedInvestorQualification.objects.filter(
            user=request.user
        ).order_by('-created_at').first()

        if qualification:
            return Response(
                AccreditedInvestorQualificationSerializer(qualification).data,
                status=status.HTTP_200_OK
            )

        return Response({
            'status': 'pending',
            'criteria_met': None,
            'qualified_at': None
        }, status=status.HTTP_200_OK)




class SubscriptionAgreementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subscription Agreements

    Endpoints:
    - GET /api/agreements/ - List user's agreements
    - GET /api/agreements/{id}/ - Get agreement details
    - POST /api/agreements/ - Create new agreement
    - PATCH /api/agreements/{id}/ - Update agreement
    - POST /api/agreements/{id}/sign/ - Sign agreement
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionAgreementDetailSerializer
        return SubscriptionAgreementSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = SubscriptionAgreement.objects.select_related(
            'investor', 'financing', 'company'
        )

        # If user is investor, show their agreements
        if user.user_type == 'investor':
            queryset = queryset.filter(investor=user)
        # If user is company, show their company's agreements
        elif user.user_type == 'company' and user.company:
            queryset = queryset.filter(company=user.company)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Sign a subscription agreement"""
        agreement = self.get_object()

        # Verify user is the investor
        if agreement.investor != request.user:
            return Response(
                {'error': 'Only the investor can sign this agreement'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already signed
        if agreement.investor_signed_at:
            return Response(
                {'error': 'Agreement already signed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sign the agreement
        agreement.investor_signed_at = timezone.now()
        agreement.investor_ip_address = request.META.get('REMOTE_ADDR')
        agreement.status = 'signed'
        agreement.save(update_fields=['investor_signed_at', 'investor_ip_address', 'status'])

        return Response({
            'message': 'Agreement signed successfully',
            'agreement': SubscriptionAgreementSerializer(agreement).data
        }, status=status.HTTP_200_OK)




class InvestmentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Investment Transactions

    Endpoints:
    - GET /api/investments/transactions/ - List user's transactions
    - GET /api/investments/transactions/{id}/ - Get transaction details
    """
    serializer_class = InvestmentTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InvestmentTransaction.objects.filter(
            user=self.request.user
        ).select_related('subscription_agreement', 'financing', 'user')




class FinancingAggregateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Financing Aggregates

    Endpoints:
    - GET /api/investments/aggregates/ - List financing aggregates
    - GET /api/investments/aggregates/{id}/ - Get aggregate details
    """
    serializer_class = FinancingAggregateSerializer
    permission_classes = [IsAuthenticated]
    queryset = FinancingAggregate.objects.select_related('financing')




class PaymentInstructionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Payment Instructions

    Endpoints:
    - GET /api/investments/payment-instructions/ - List user's payment instructions
    - GET /api/investments/payment-instructions/{id}/ - Get payment instruction details
    """
    serializer_class = PaymentInstructionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentInstruction.objects.filter(
            subscription_agreement__investor=self.request.user
        ).select_related('subscription_agreement', 'company')




class DRSDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for DRS Documents

    Endpoints:
    - GET /api/drs/documents/ - List user's DRS documents
    - GET /api/drs/documents/{id}/ - Get document details
    """
    serializer_class = DRSDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DRSDocument.objects.filter(
            user=self.request.user
        ).select_related('subscription_agreement', 'company', 'user')

