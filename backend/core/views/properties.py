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
    Watchlist,

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
# PROSPECTOR PROPERTY EXCHANGE
# ============================================================================

class ProspectorProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prospector Profiles

    Endpoints:
    - GET /api/properties/prospectors/ - List all prospectors
    - GET /api/properties/prospectors/{id}/ - Get prospector profile
    - POST /api/properties/prospectors/ - Create prospector profile (authenticated)
    - PUT /api/properties/prospectors/{id}/ - Update profile (owner only)
    - GET /api/properties/prospectors/me/ - Get current user's profile
    """
    serializer_class = ProspectorProfileSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'agreement_text']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = ProspectorProfile.objects.select_related('user').prefetch_related('listings')

        # Filter by verified status
        is_verified = self.request.query_params.get('verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(display_name__icontains=search) |
                Q(company_name__icontains=search)
            )

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow owners to update their profile
        if serializer.instance.user != self.request.user:
            raise PermissionError("You can only update your own profile")
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get the current user's prospector profile"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response(
                {'detail': 'Prospector profile not found. Create one to list properties.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def agreement_text(self, request):
        """Get the current commission agreement text"""
        return Response({
            'version': ProspectorCommissionAgreement.AGREEMENT_VERSION,
            'commission_rate': str(ProspectorCommissionAgreement.COMMISSION_RATE),
            'agreement_text': ProspectorCommissionAgreement.get_agreement_text()
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept_agreement(self, request):
        """Accept the commission agreement"""
        from django.utils import timezone

        # Get or create prospector profile - auto-create if doesn't exist
        # Use get_full_name() method from AbstractUser, fallback to username
        display_name = request.user.get_full_name() or request.user.username
        profile, created = ProspectorProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'display_name': display_name,
            }
        )

        # Check if already accepted
        if profile.commission_agreement_accepted:
            return Response(
                {'detail': 'You have already accepted the commission agreement.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input
        serializer = ProspectorCommissionAgreementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get client IP - use secure function to prevent X-Forwarded-For spoofing
        from core.security_utils import get_client_ip
        ip_address = get_client_ip(request)

        # Create agreement record
        agreement = ProspectorCommissionAgreement.objects.create(
            prospector=profile,
            full_legal_name=serializer.validated_data['full_legal_name'],
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            agreement_text=ProspectorCommissionAgreement.get_agreement_text()
        )

        # Update profile
        profile.commission_agreement_accepted = True
        profile.commission_agreement_date = timezone.now()
        profile.commission_agreement_ip = ip_address
        profile.save()

        return Response({
            'detail': 'Commission agreement accepted successfully.',
            'agreement_id': agreement.id,
            'accepted_at': agreement.accepted_at,
            'can_list_properties': True
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_agreements(self, request):
        """Get the current user's commission agreements"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            agreements = profile.commission_agreements.all()
            serializer = ProspectorCommissionAgreementSerializer(agreements, many=True)
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response([])




class PropertyListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Listings

    Endpoints:
    - GET /api/properties/listings/ - List all active listings (public)
    - GET /api/properties/listings/{slug}/ - Get listing details (public)
    - POST /api/properties/listings/ - Create listing (prospector only)
    - PUT /api/properties/listings/{slug}/ - Update listing (owner only)
    - DELETE /api/properties/listings/{slug}/ - Delete listing (owner only)
    - GET /api/properties/listings/my-listings/ - Get current user's listings
    - GET /api/properties/listings/choices/ - Get all dropdown choices
    - POST /api/properties/listings/{slug}/view/ - Record a view
    """
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices', 'record_view']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyListingCreateSerializer
        return PropertyListingDetailSerializer

    def get_queryset(self):
        queryset = PropertyListing.objects.select_related('prospector', 'prospector__user').prefetch_related('media')

        # For list view, only show active listings to non-owners
        if self.action == 'list':
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(status='active')
            elif not self.request.user.is_staff:
                queryset = queryset.filter(
                    Q(status='active') | Q(prospector__user=self.request.user)
                )

        # Apply filters
        filters = {}

        # Mineral type filter
        mineral = self.request.query_params.get('mineral')
        if mineral:
            queryset = queryset.filter(
                Q(primary_mineral=mineral) | Q(secondary_minerals__contains=[mineral])
            )

        # Country filter
        country = self.request.query_params.get('country')
        if country:
            filters['country'] = country

        # Province/state filter
        province = self.request.query_params.get('province')
        if province:
            filters['province_state__icontains'] = province

        # Property type filter
        property_type = self.request.query_params.get('property_type')
        if property_type:
            filters['property_type'] = property_type

        # Exploration stage filter
        stage = self.request.query_params.get('stage')
        if stage:
            filters['exploration_stage'] = stage

        # Price range filters
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(asking_price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(asking_price__lte=max_price)

        # Size range filters (hectares)
        min_size = self.request.query_params.get('min_size')
        if min_size:
            queryset = queryset.filter(total_hectares__gte=min_size)

        max_size = self.request.query_params.get('max_size')
        if max_size:
            queryset = queryset.filter(total_hectares__lte=max_size)

        # Open to offers filter
        open_to_offers = self.request.query_params.get('open_to_offers')
        if open_to_offers is not None:
            filters['open_to_offers'] = open_to_offers.lower() == 'true'

        # Has NI 43-101 report
        has_report = self.request.query_params.get('has_43_101')
        if has_report is not None:
            filters['has_43_101_report'] = has_report.lower() == 'true'

        # Search in title and description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(location_description__icontains=search)
            )

        # Filter for user's own listings
        my_listings = self.request.query_params.get('my_listings')
        if my_listings and my_listings.lower() == 'true' and self.request.user.is_authenticated:
            try:
                profile = ProspectorProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(prospector=profile)
            except ProspectorProfile.DoesNotExist:
                queryset = queryset.none()

        # Filter by prospector ID
        prospector_id = self.request.query_params.get('prospector')
        if prospector_id:
            queryset = queryset.filter(prospector_id=prospector_id)

        queryset = queryset.filter(**filters)

        # Sorting
        sort = self.request.query_params.get('sort', '-created_at')
        valid_sorts = ['created_at', '-created_at', 'asking_price', '-asking_price',
                      'total_hectares', '-total_hectares', 'views_count', '-views_count']
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def perform_create(self, serializer):
        # Ensure user has a prospector profile
        try:
            profile = ProspectorProfile.objects.get(user=self.request.user)
        except ProspectorProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must create a prospector profile before listing properties"
            )

        # Check if commission agreement has been accepted
        if not profile.commission_agreement_accepted:
            raise serializers.ValidationError(
                "You must accept the 5% commission agreement before listing properties. "
                "This ensures free listings while supporting the platform through successful transactions."
            )

        serializer.save(prospector=profile)

    def perform_update(self, serializer):
        # Only allow owners to update their listings
        if serializer.instance.prospector.user != self.request.user:
            raise PermissionError("You can only update your own listings")
        serializer.save()

    def perform_destroy(self, instance):
        # Allow superusers to delete any listing, owners can only delete their own
        if not self.request.user.is_superuser and instance.prospector.user != self.request.user:
            raise PermissionError("You can only delete your own listings")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """Get the current user's property listings"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            listings = PropertyListing.objects.filter(prospector=profile).order_by('-created_at')
            serializer = PropertyListingListSerializer(listings, many=True, context={'request': request})
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response([])

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get all dropdown choice options for the listing form"""
        serializer = PropertyChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def record_view(self, request, slug=None):
        """Record a view for a listing"""
        listing = self.get_object()
        listing.views_count += 1
        listing.save(update_fields=['views_count'])
        return Response({'views_count': listing.views_count})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get all listings pending review (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to view pending listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listings = PropertyListing.objects.filter(
            status='pending_review'
        ).select_related('prospector', 'prospector__user').order_by('-created_at')

        serializer = PropertyListingListSerializer(listings, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, slug=None):
        """Approve a listing (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to approve listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listing = self.get_object()
        if listing.status != 'pending_review':
            return Response(
                {'detail': f'Listing is not pending review (current status: {listing.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        listing.status = 'active'
        listing.published_at = timezone.now()
        listing.save(update_fields=['status', 'published_at'])

        serializer = PropertyListingDetailSerializer(listing, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, slug=None):
        """Reject a listing (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to reject listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listing = self.get_object()
        if listing.status not in ['pending_review', 'active']:
            return Response(
                {'detail': f'Listing cannot be rejected (current status: {listing.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '')
        listing.status = 'rejected'
        listing.save(update_fields=['status'])

        # TODO: Send email notification to prospector with rejection reason

        return Response({
            'detail': 'Listing has been rejected',
            'slug': listing.slug,
            'reason': reason
        })




class PropertyMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Media (images, documents, videos)

    Endpoints:
    - POST /api/properties/media/ - Upload media to a listing
    - POST /api/properties/media/upload/ - Upload file and create media record
    - DELETE /api/properties/media/{id}/ - Delete media
    - PATCH /api/properties/media/{id}/ - Update media (e.g., set as primary)
    """
    serializer_class = PropertyMediaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only manage media for their own listings
        return PropertyMedia.objects.filter(
            listing__prospector__user=self.request.user
        ).select_related('listing')

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')
        if listing.prospector.user != self.request.user:
            raise PermissionError("You can only add media to your own listings")
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a file and create a media record
        POST /api/properties/media/upload/
        """
        import os
        import uuid
        from django.core.files.storage import default_storage
        from django.conf import settings

        file = request.FILES.get('file')
        listing_id = request.data.get('listing')
        category = request.data.get('category')
        title = request.data.get('title')
        description = request.data.get('description', '')
        media_type = request.data.get('media_type', 'document')

        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not listing_id or not category or not title:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate listing ownership
        try:
            listing = PropertyListing.objects.get(id=listing_id)
            if listing.prospector.user != request.user:
                return Response({'error': 'You can only upload to your own listings'}, status=status.HTTP_403_FORBIDDEN)
        except PropertyListing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate file size (50MB max)
        if file.size > 50 * 1024 * 1024:
            return Response({'error': 'File size must be less than 50MB'}, status=status.HTTP_400_BAD_REQUEST)

        # Get file extension and generate unique filename
        ext = os.path.splitext(file.name)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # Determine storage path based on media type
        storage_path = f"properties/{listing_id}/{media_type}s/{unique_filename}"

        # Save file
        try:
            saved_path = default_storage.save(storage_path, file)
            file_url = default_storage.url(saved_path)

            # If using local storage, prepend the domain
            if not file_url.startswith('http'):
                file_url = f"{settings.MEDIA_URL}{saved_path}"

            # Create media record
            media = PropertyMedia.objects.create(
                listing=listing,
                media_type=media_type,
                category=category,
                title=title,
                description=description,
                file_url=file_url,
                file_size_mb=round(file.size / (1024 * 1024), 2),
                file_format=ext.replace('.', ''),
                uploaded_by=request.user,
            )

            return Response(PropertyMediaSerializer(media).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to save property media file: {str(e)}")
            return Response({'error': 'Failed to save file. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        # Only allow owner to delete
        if instance.listing.prospector.user != self.request.user:
            raise PermissionError("You can only delete media from your own listings")

        # Delete the file from storage
        from django.core.files.storage import default_storage
        try:
            # Extract path from URL if needed
            file_path = instance.file_url
            if file_path.startswith('/media/'):
                file_path = file_path[7:]  # Remove /media/ prefix
            default_storage.delete(file_path)
        except (FileNotFoundError, OSError, IOError):
            pass  # File might not exist, continue with deletion

        instance.delete()




class PropertyInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Inquiries

    Endpoints:
    - GET /api/properties/inquiries/ - List inquiries (prospector sees received, others see sent)
    - POST /api/properties/inquiries/ - Send an inquiry
    - GET /api/properties/inquiries/{id}/ - Get inquiry details
    - PATCH /api/properties/inquiries/{id}/ - Update inquiry status (owner only)
    """
    serializer_class = PropertyInquirySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from ..serializers import PropertyInquiryCreateSerializer
        if self.action == 'create':
            return PropertyInquiryCreateSerializer
        return PropertyInquirySerializer

    def get_queryset(self):
        user = self.request.user

        # Check if user is a prospector
        try:
            profile = ProspectorProfile.objects.get(user=user)
            # Prospectors see inquiries received on their listings
            received = PropertyInquiry.objects.filter(listing__prospector=profile)
        except ProspectorProfile.DoesNotExist:
            received = PropertyInquiry.objects.none()

        # All users see inquiries they've sent
        sent = PropertyInquiry.objects.filter(inquirer=user)

        # Combine and return
        return (received | sent).distinct().select_related(
            'listing', 'inquirer', 'listing__prospector'
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Create a new inquiry"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            listing = serializer.validated_data.get('listing')

            # Can't inquire on own listing
            if listing.prospector.user == request.user:
                return Response(
                    {'error': 'You cannot inquire on your own listing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update listing inquiry count
            listing.inquiries_count += 1
            listing.save(update_fields=['inquiries_count'])

            # Save the inquiry
            inquiry = serializer.save(inquirer=request.user)

            # Return the full inquiry data
            response_serializer = PropertyInquirySerializer(inquiry)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating inquiry: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to create inquiry. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        # Only listing owner can update inquiry status
        if instance.listing.prospector.user != self.request.user:
            raise PermissionError("Only the listing owner can update inquiry status")
        serializer.save()

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        Respond to an inquiry (prospector only)
        POST /api/properties/inquiries/{id}/respond/
        """
        from ..serializers import PropertyInquiryResponseSerializer
        from django.utils import timezone

        inquiry = self.get_object()

        # Only listing owner can respond
        if inquiry.listing.prospector.user != request.user:
            return Response(
                {'error': 'Only the listing owner can respond to inquiries'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PropertyInquiryResponseSerializer(data=request.data)
        if serializer.is_valid():
            inquiry.response = serializer.validated_data['response']
            inquiry.status = 'responded'
            inquiry.responded_at = timezone.now()
            inquiry.save()

            return Response(PropertyInquirySerializer(inquiry).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark inquiry as read (prospector only)
        POST /api/properties/inquiries/{id}/mark_read/
        """
        inquiry = self.get_object()

        # Only listing owner can mark as read
        if inquiry.listing.prospector.user != request.user:
            return Response(
                {'error': 'Only the listing owner can mark inquiries as read'},
                status=status.HTTP_403_FORBIDDEN
            )

        if inquiry.status == 'new':
            inquiry.status = 'read'
            inquiry.save()

        return Response(PropertyInquirySerializer(inquiry).data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for an inquiry conversation
        GET /api/properties/inquiries/{id}/messages/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to view this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all messages for this inquiry
        messages = inquiry.messages.select_related('sender').order_by('created_at')

        # Mark messages from the other party as read
        messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        serializer = InquiryMessageSerializer(messages, many=True)
        return Response({
            'inquiry_id': inquiry.id,
            'messages': serializer.data,
            'total_count': messages.count()
        })

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a new message in an inquiry conversation
        POST /api/properties/inquiries/{id}/send_message/
        Body: { "message": "Your message here" }
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to send messages in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquiryMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Create the message
            message = InquiryMessage.objects.create(
                inquiry=inquiry,
                sender=user,
                message=serializer.validated_data['message']
            )

            # Update inquiry status if needed
            if inquiry.status == 'new':
                inquiry.status = 'read'
                inquiry.save(update_fields=['status'])

            return Response(
                InquiryMessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def conversation(self, request, pk=None):
        """
        Get full inquiry details with conversation thread
        GET /api/properties/inquiries/{id}/conversation/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to view this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark messages from the other party as read
        inquiry.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        serializer = PropertyInquiryWithMessagesSerializer(inquiry, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_messages_read(self, request, pk=None):
        """
        Mark all messages in a conversation as read for the current user
        POST /api/properties/inquiries/{id}/mark_messages_read/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to access this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark all messages from the other party as read
        updated = inquiry.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        return Response({
            'marked_read': updated,
            'message': f'{updated} messages marked as read'
        })




class PropertyWatchlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Watchlist

    Endpoints:
    - GET /api/properties/watchlist/ - List user's watchlisted properties
    - POST /api/properties/watchlist/ - Add to watchlist
    - DELETE /api/properties/watchlist/{id}/ - Remove from watchlist
    - POST /api/properties/watchlist/toggle/ - Toggle watchlist status for a listing
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'toggle']:
            from ..serializers import PropertyWatchlistCreateSerializer
            return PropertyWatchlistCreateSerializer
        return PropertyWatchlistSerializer

    def get_queryset(self):
        return PropertyWatchlist.objects.filter(
            user=self.request.user
        ).select_related('listing', 'listing__prospector').prefetch_related('listing__media')

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')

        # Check if already watchlisted
        if PropertyWatchlist.objects.filter(user=self.request.user, listing=listing).exists():
            raise serializers.ValidationError("This property is already in your watchlist")

        # Update listing watchlist count
        listing.watchlist_count += 1
        listing.save(update_fields=['watchlist_count'])

        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # Update listing watchlist count
        instance.listing.watchlist_count = max(0, instance.listing.watchlist_count - 1)
        instance.listing.save(update_fields=['watchlist_count'])
        instance.delete()

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle watchlist status for a listing"""
        listing_id = request.data.get('listing')
        if not listing_id:
            return Response(
                {'error': 'listing is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            listing = PropertyListing.objects.get(id=listing_id)
        except PropertyListing.DoesNotExist:
            return Response(
                {'error': 'Listing not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already watchlisted
        watchlist_item = PropertyWatchlist.objects.filter(
            user=request.user, listing=listing
        ).first()

        if watchlist_item:
            # Remove from watchlist
            listing.watchlist_count = max(0, listing.watchlist_count - 1)
            listing.save(update_fields=['watchlist_count'])
            watchlist_item.delete()
            return Response({
                'is_watchlisted': False,
                'watchlist_count': listing.watchlist_count,
                'message': 'Removed from watchlist'
            })
        else:
            # Add to watchlist
            listing.watchlist_count += 1
            listing.save(update_fields=['watchlist_count'])
            PropertyWatchlist.objects.create(user=request.user, listing=listing)
            return Response({
                'is_watchlisted': True,
                'watchlist_count': listing.watchlist_count,
                'message': 'Added to watchlist'
            })




class SavedPropertySearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Saved Property Searches

    Endpoints:
    - GET /api/properties/saved-searches/ - List user's saved searches
    - POST /api/properties/saved-searches/ - Save a search
    - DELETE /api/properties/saved-searches/{id}/ - Delete saved search
    - PATCH /api/properties/saved-searches/{id}/ - Update alert settings
    """
    serializer_class = SavedPropertySearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedPropertySearch.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

