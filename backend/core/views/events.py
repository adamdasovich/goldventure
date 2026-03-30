"""
API Views for GoldVenture Platform
"""

import logging

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
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    User, Company,
)
from ..serializers import (
    SpeakerEventListSerializer, SpeakerEventDetailSerializer,
    SpeakerEventCreateSerializer, EventQuestionSerializer, EventReactionSerializer,
)


# ============================================================================
# GUEST SPEAKER EVENT VIEWSETS
# ============================================================================

class SpeakerEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing speaker events

    Endpoints:
    - GET /api/events/ - List all events (with filters)
    - GET /api/events/{id}/ - Get event details
    - POST /api/events/ - Create new event (company admins only)
    - PUT/PATCH /api/events/{id}/ - Update event
    - DELETE /api/events/{id}/ - Delete event
    - POST /api/events/{id}/register/ - Register for event
    - POST /api/events/{id}/unregister/ - Unregister from event
    - POST /api/events/{id}/start/ - Start event (change status to live)
    - POST /api/events/{id}/end/ - End event
    - GET /api/events/upcoming/ - Get upcoming events
    """

    def get_permissions(self):
        """Allow read for anyone, require auth for write operations"""
        if self.action in ['list', 'retrieve', 'upcoming']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = SpeakerEvent.objects.select_related('company', 'created_by').prefetch_related('speakers__user')

        # Filter by company
        company_id = self.request.query_params.get('company', None)
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by format
        format_param = self.request.query_params.get('format', None)
        if format_param:
            queryset = queryset.filter(format=format_param)

        return queryset.order_by('-scheduled_start')

    def get_serializer_class(self):
        if self.action == 'list':
            return SpeakerEventListSerializer
        elif self.action == 'create':
            return SpeakerEventCreateSerializer
        return SpeakerEventDetailSerializer

    def perform_create(self, serializer):
        """Set the created_by field to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register current user for an event"""
        event = self.get_object()

        # Check if event is open for registration
        if event.status != 'scheduled':
            return Response(
                {'error': 'Event is not open for registration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already registered
        if event.registrations.filter(user=request.user, status='registered').exists():
            return Response(
                {'error': 'Already registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check capacity
        if event.max_participants and event.registered_count >= event.max_participants:
            return Response(
                {'error': 'Event is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has a cancelled registration and reactivate it
        existing_registration = event.registrations.filter(user=request.user).first()
        if existing_registration:
            existing_registration.status = 'registered'
            existing_registration.save()
            registration = existing_registration
        else:
            # Create new registration
            registration = EventRegistration.objects.create(
                event=event,
                user=request.user,
                status='registered'
            )

        # Update event registered count
        event.registered_count += 1
        event.save(update_fields=['registered_count'])

        return Response(
            {'message': 'Successfully registered for event'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def unregister(self, request, pk=None):
        """Unregister current user from an event"""
        event = self.get_object()

        try:
            registration = event.registrations.get(user=request.user, status='registered')
            registration.status = 'cancelled'
            registration.save()

            # Update event registered count
            event.registered_count = max(0, event.registered_count - 1)
            event.save(update_fields=['registered_count'])

            return Response({'message': 'Successfully unregistered from event'})
        except EventRegistration.DoesNotExist:
            return Response(
                {'error': 'Not registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        """Start an event (change status to live)"""
        event = self.get_object()

        # Check if user is authorized (event creator or company admin)
        if event.created_by != request.user:
            return Response(
                {'error': 'Not authorized to start this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        if event.status != 'scheduled':
            return Response(
                {'error': 'Event must be scheduled to start'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.status = 'live'
        event.actual_start = datetime.now()
        event.save(update_fields=['status', 'actual_start'])

        return Response({'message': 'Event started successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def end(self, request, pk=None):
        """End an event"""
        event = self.get_object()

        # Check if user is authorized
        if event.created_by != request.user:
            return Response(
                {'error': 'Not authorized to end this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        if event.status != 'live':
            return Response(
                {'error': 'Event must be live to end'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.status = 'ended'
        event.actual_end = datetime.now()
        event.save(update_fields=['status', 'actual_end'])

        return Response({'message': 'Event ended successfully'})

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events across all companies"""
        from django.utils import timezone

        # Get events scheduled for the next 90 days or events that are scheduled (even if in near past)
        now = timezone.now()
        upcoming_events = SpeakerEvent.objects.filter(
            status='scheduled'
        ).select_related('company', 'created_by').prefetch_related('speakers__user').order_by('scheduled_start')[:10]

        serializer = SpeakerEventListSerializer(upcoming_events, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def registrations(self, request, pk=None):
        """Get list of registered users for an event (staff/admin only)"""
        event = self.get_object()

        # Check if user is staff, admin, or event creator
        if not (request.user.is_staff or request.user.is_superuser or event.created_by == request.user):
            return Response(
                {'error': 'Not authorized to view registrations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all registrations for this event
        registrations = event.registrations.filter(
            status__in=['registered', 'attended']
        ).select_related('user').order_by('-registered_at')

        # Serialize registration data
        registration_data = []
        for reg in registrations:
            registration_data.append({
                'id': reg.id,
                'user': {
                    'id': reg.user.id,
                    'username': reg.user.username,
                    'email': reg.user.email,
                    'full_name': reg.user.get_full_name() if hasattr(reg.user, 'get_full_name') else f"{reg.user.first_name} {reg.user.last_name}".strip() or reg.user.username,
                },
                'status': reg.status,
                'registered_at': reg.registered_at,
                'joined_at': reg.joined_at,
                'left_at': reg.left_at,
            })

        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'total_registrations': len(registration_data),
            'max_participants': event.max_participants,
            'registrations': registration_data
        })




class EventQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event questions

    Endpoints:
    - GET /api/event-questions/?event={event_id} - List questions for an event
    - POST /api/event-questions/ - Submit a question
    - PATCH /api/event-questions/{id}/ - Update question (moderate/answer)
    - POST /api/event-questions/{id}/upvote/ - Upvote a question
    """
    serializer_class = EventQuestionSerializer

    def get_permissions(self):
        """Require authentication for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upvote']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = EventQuestion.objects.select_related('user', 'answered_by')

        # Filter by event
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.order_by('-upvotes', '-created_at')

    def perform_create(self, serializer):
        """Set the user field to current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote a question - prevents duplicate votes from same user"""
        question = self.get_object()

        # SECURITY: Use QuestionUpvote model to prevent duplicate votes
        from core.models import QuestionUpvote
        upvote, created = QuestionUpvote.objects.get_or_create(
            question=question,
            user=request.user
        )

        if created:
            # Recalculate upvote count from the model (more accurate than incrementing)
            question.upvotes = question.upvotes_set.count() if hasattr(question, 'upvotes_set') else QuestionUpvote.objects.filter(question=question).count()
            question.save(update_fields=['upvotes'])

            # Update event questions count
            event = question.event
            event.questions_count = event.questions.count()
            event.save(update_fields=['questions_count'])

            return Response({'message': 'Question upvoted', 'upvotes': question.upvotes})
        else:
            return Response(
                {'message': 'You have already upvoted this question', 'upvotes': question.upvotes},
                status=status.HTTP_400_BAD_REQUEST
            )




class EventReactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event reactions

    Endpoints:
    - POST /api/event-reactions/ - Send a reaction
    - GET /api/event-reactions/?event={event_id} - Get reactions for an event
    """
    serializer_class = EventReactionSerializer

    def get_permissions(self):
        """Require authentication for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = EventReaction.objects.select_related('user')

        # Filter by event
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        return queryset.order_by('-timestamp')

    def perform_create(self, serializer):
        """Set the user field to current user"""
        serializer.save(user=self.request.user)


# ============================================================================
# USER AUTHENTICATION API
# ============================================================================

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

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

from ..models import User

