"""
API Views for GoldVenture Platform
"""

import logging
import requests

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
# COMPANY PORTAL VIEWSETS (Resources, Events, Subscriptions)
# ============================================================================

def _require_company_management(user, company, verb):
    """Raise unless `user` may edit `company`, naming what they were denied.

    Editing rights need an approved representative link AND an active company
    subscription - see core/company_access.py. Every write path in this module
    goes through here so the rule is stated once; it used to be written out by
    hand six times, all of them testing the link alone.
    """
    from rest_framework.exceptions import PermissionDenied
    from ..company_access import access_state

    state = access_state(user, company)
    if state['can_edit']:
        return

    if state['requires_subscription']:
        raise PermissionDenied({
            'error': 'subscription_required',
            'detail': (
                f"{company.name} needs an active company subscription before "
                f"you can {verb} it."
            ),
            'requires_subscription': True,
        })

    raise PermissionDenied(f"You can only {verb} your own company.")

class CompanyResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company Resources (documents, images, videos)

    Endpoints:
    - GET /api/company-portal/resources/ - List all resources for a company
    - GET /api/company-portal/resources/{id}/ - Get resource details
    - POST /api/company-portal/resources/ - Upload a new resource (company rep only)
    - PUT /api/company-portal/resources/{id}/ - Update resource (company rep only)
    - DELETE /api/company-portal/resources/{id}/ - Delete resource (company rep only)
    - POST /api/company-portal/resources/upload/ - Upload file and create resource
    - GET /api/company-portal/resources/choices/ - Get dropdown choices
    """
    serializer_class = CompanyResourceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CompanyResourceCreateSerializer
        return CompanyResourceSerializer

    def get_queryset(self):
        queryset = CompanyResource.objects.select_related('company', 'project', 'uploaded_by')

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by project if provided
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by resource type if provided
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Non-public resources only visible to company reps
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        elif self.request.user.company_id:
            queryset = queryset.filter(
                Q(is_public=True) | Q(company=self.request.user.company)
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)

        return queryset.order_by('sort_order', '-uploaded_at')

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, company, 'add resources to')
        serializer.save(uploaded_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, instance.company, 'update resources for')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, instance.company, 'delete resources for')
        instance.delete()

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for resource forms"""
        serializer = CompanyResourceChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_resources(self, request):
        """Get resources for the current user's company"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.company:
            return Response(
                {'results': [], 'count': 0, 'message': 'You are not associated with a company'}
            )

        queryset = CompanyResource.objects.filter(
            company=request.user.company
        ).select_related('company', 'project', 'uploaded_by').order_by('sort_order', '-uploaded_at')

        serializer = CompanyResourceSerializer(queryset, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a file and create a resource record
        POST /api/company-portal/resources/upload/
        """
        import os
        import uuid
        from django.core.files.storage import default_storage
        from django.conf import settings

        file = request.FILES.get('file')
        company_id = request.data.get('company')
        category = request.data.get('category')
        title = request.data.get('title')
        description = request.data.get('description', '')
        resource_type = request.data.get('resource_type', 'document')
        project_id = request.data.get('project')
        is_public = request.data.get('is_public', 'true').lower() == 'true'

        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not company_id or not category or not title:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate company access
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff:
            from ..company_access import access_state
            state = access_state(request.user, company)
            if not state['can_edit']:
                return Response(
                    {
                        'error': 'subscription_required' if state['requires_subscription']
                                 else 'permission_denied',
                        'detail': (
                            f'{company.name} needs an active company subscription '
                            f'before you can upload resources for it.'
                            if state['requires_subscription']
                            else 'You can only upload resources for your own company.'
                        ),
                        'requires_subscription': state['requires_subscription'],
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # Generate unique filename
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"company_resources/{company_id}/{uuid.uuid4().hex}{ext}"

        # Save file
        try:
            saved_path = default_storage.save(filename, file)
            file_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)

            # Calculate file size
            file_size_mb = file.size / (1024 * 1024)

            # Create resource record
            resource = CompanyResource.objects.create(
                company=company,
                resource_type=resource_type,
                category=category,
                title=title,
                description=description,
                file_url=file_url,
                file_size_mb=round(file_size_mb, 2),
                file_format=ext.lstrip('.').upper(),
                is_public=is_public,
                project_id=project_id if project_id else None,
                uploaded_by=request.user
            )

            return Response(
                CompanyResourceSerializer(resource).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Company resource file upload failed: {str(e)}")
            return Response(
                {'error': 'File upload failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class SpeakingEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Speaking Events

    Endpoints:
    - GET /api/company-portal/events/ - List all events (filterable by company, status, date)
    - GET /api/company-portal/events/{id}/ - Get event details
    - POST /api/company-portal/events/ - Create a new event (company rep only)
    - PUT /api/company-portal/events/{id}/ - Update event (company rep only)
    - DELETE /api/company-portal/events/{id}/ - Delete event (company rep only)
    - GET /api/company-portal/events/choices/ - Get dropdown choices
    - GET /api/company-portal/events/upcoming/ - Get upcoming events across all companies
    """
    serializer_class = SpeakingEventSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices', 'upcoming']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SpeakingEventCreateSerializer
        if self.action == 'list':
            return SpeakingEventListSerializer
        return SpeakingEventSerializer

    def get_queryset(self):
        queryset = SpeakingEvent.objects.select_related('company', 'created_by')

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by status if provided
        event_status = self.request.query_params.get('status')
        if event_status:
            queryset = queryset.filter(status=event_status)

        # Filter by event type if provided
        event_type = self.request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by featured
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        # Filter by date range
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')
        if from_date:
            queryset = queryset.filter(start_datetime__gte=from_date)
        if to_date:
            queryset = queryset.filter(start_datetime__lte=to_date)

        return queryset.order_by('-start_datetime')

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, company, 'create events for')
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, instance.company, 'update events for')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            _require_company_management(self.request.user, instance.company, 'delete events for')
        instance.delete()

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for event forms"""
        serializer = SpeakingEventChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events across all companies"""
        from django.utils import timezone

        queryset = SpeakingEvent.objects.filter(
            status__in=['upcoming', 'live'],
            start_datetime__gte=timezone.now()
        ).select_related('company').order_by('start_datetime')[:20]

        serializer = SpeakingEventListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events for the current user's company"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.company:
            return Response(
                {'results': [], 'count': 0, 'message': 'You are not associated with a company'}
            )

        queryset = SpeakingEvent.objects.filter(
            company=request.user.company
        ).select_related('company', 'created_by').order_by('-start_datetime')

        serializer = SpeakingEventSerializer(queryset, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})




class CompanyAccessRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company Access Requests

    Endpoints:
    - GET /api/company-portal/access-requests/ - List requests (own for users, all for admins)
    - POST /api/company-portal/access-requests/ - Create new request
    - GET /api/company-portal/access-requests/{id}/ - Get request details
    - DELETE /api/company-portal/access-requests/{id}/ - Cancel a pending request
    - GET /api/company-portal/access-requests/my_request/ - Get current user's pending request
    - GET /api/company-portal/access-requests/choices/ - Get dropdown choices
    - POST /api/company-portal/access-requests/{id}/review/ - Admin: approve/reject request
    - GET /api/company-portal/access-requests/pending/ - Admin: list all pending requests
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyAccessRequestCreateSerializer
        if self.action == 'review':
            return CompanyAccessRequestReviewSerializer
        if self.action == 'choices':
            return CompanyAccessRequestChoicesSerializer
        return CompanyAccessRequestSerializer

    def get_queryset(self):
        user = self.request.user

        # Staff can see all requests
        if user.is_staff:
            return CompanyAccessRequest.objects.all().select_related(
                'user', 'company', 'reviewer'
            )

        # Regular users can only see their own requests
        return CompanyAccessRequest.objects.filter(user=user).select_related(
            'user', 'company', 'reviewer'
        )

    def perform_destroy(self, instance):
        """Users can only cancel their own pending requests"""
        if instance.user != self.request.user:
            raise PermissionError("You can only cancel your own requests")
        if instance.status != 'pending':
            raise PermissionError("You can only cancel pending requests")

        instance.status = 'cancelled'
        instance.save()

    @action(detail=False, methods=['get'])
    def my_request(self, request):
        """Get current user's pending request if any"""
        pending_request = CompanyAccessRequest.objects.filter(
            user=request.user,
            status='pending'
        ).select_related('company').first()

        if pending_request:
            serializer = CompanyAccessRequestSerializer(pending_request)
            return Response(serializer.data)

        return Response({
            'has_pending_request': False,
            'has_company': request.user.company is not None,
            'company_name': request.user.company.name if request.user.company else None
        })

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for request forms"""
        serializer = CompanyAccessRequestChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Admin: List all pending requests"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        pending = CompanyAccessRequest.objects.filter(
            status='pending'
        ).select_related('user', 'company').order_by('-created_at')

        serializer = CompanyAccessRequestSerializer(pending, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Admin: Approve or reject a request"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        access_request = self.get_object()

        if access_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CompanyAccessRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        if action == 'approve':
            access_request.approve(reviewer=request.user, notes=notes)
            message = f"Request approved. {access_request.user.username} is now associated with {access_request.company.name}."
        else:
            access_request.reject(reviewer=request.user, notes=notes)
            message = "Request rejected."

        return Response({
            'message': message,
            'request': CompanyAccessRequestSerializer(access_request).data
        })

