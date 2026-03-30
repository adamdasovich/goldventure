"""
API Views for GoldVenture Platform
"""

import logging
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import viewsets, status, permissions

# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
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
    User,

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







@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user account
    POST /api/auth/register/
    Body: {
        "username": "string",
        "email": "string",
        "password": "string",
        "full_name": "string",
        "user_type": "investor|mining_company|prospector|student" (required)
    }
    Returns: {
        "user": {...},
        "access": "token",
        "refresh": "token"
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('full_name', '')
    user_type = request.data.get('user_type', '')

    # Validation
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email, and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate user_type is required and valid
    valid_user_types = ['investor', 'mining_company', 'prospector', 'student']
    if not user_type:
        return Response(
            {'error': 'User type is required. Please select: Investor, Mining Company, Prospector, or Student'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if user_type not in valid_user_types:
        return Response(
            {'error': f'Invalid user type. Must be one of: {", ".join(valid_user_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password strength using Django's built-in validators
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response(
            {'error': ' '.join(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type
        )

        # Set full name (split into first and last name)
        if full_name:
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Get full name
        user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user_full_name,
                'user_type': user.user_type,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"register_user error: {str(e)}")
        return Response(
            {'error': 'Registration failed. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login and get JWT tokens
    POST /api/auth/login/
    Body: {
        "username": "string",
        "password": "string"
    }
    Returns: {
        "user": {...},
        "access": "token",
        "refresh": "token"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    # Get full name
    user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user_full_name,
            'user_type': user.user_type,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user info
    GET /api/auth/me/
    Headers: Authorization: Bearer <access_token>
    Returns: {
        "id": int,
        "username": "string",
        "email": "string",
        "full_name": "string",
        "user_type": "string",
        "company_id": int | null,
        "company_name": "string" | null
    }
    """
    user = request.user

    # Get full name
    user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user_full_name,
        'user_type': user.user_type,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'company_id': user.company_id,
        'company_name': user.company.name if user.company else None,
    }, status=status.HTTP_200_OK)


# ============================================================================
# FINANCIAL HUB API
# ============================================================================

from ..models import (
    EducationalModule, ModuleCompletion, AccreditedInvestorQualification,
    SubscriptionAgreement, InvestmentTransaction, FinancingAggregate,
    PaymentInstruction, DRSDocument
)
from ..serializers import (
    EducationalModuleSerializer, ModuleCompletionSerializer,
    AccreditedInvestorQualificationSerializer, SubscriptionAgreementSerializer,
    SubscriptionAgreementDetailSerializer, InvestmentTransactionSerializer,
    FinancingAggregateSerializer, PaymentInstructionSerializer, DRSDocumentSerializer
)
from django.utils import timezone

