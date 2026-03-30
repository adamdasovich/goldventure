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
# STORE ADMIN VIEWS
# ============================================================================

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin/staff users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        """Admin users have permission on all objects"""
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )




class StoreAdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin API for store categories.
    Requires admin/staff authentication.

    GET    /api/admin/store/categories/        - List all categories
    POST   /api/admin/store/categories/        - Create category
    GET    /api/admin/store/categories/{id}/   - Get category
    PUT    /api/admin/store/categories/{id}/   - Update category
    DELETE /api/admin/store/categories/{id}/   - Delete category
    """
    queryset = StoreCategory.objects.all().order_by('display_order', 'name')
    serializer_class = StoreCategoryAdminSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]




class StoreAdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin API for store products.
    Requires admin/staff authentication.

    GET    /api/admin/store/products/          - List all products (with filters)
    POST   /api/admin/store/products/          - Create product
    GET    /api/admin/store/products/{id}/     - Get product with details
    PUT    /api/admin/store/products/{id}/     - Update product
    DELETE /api/admin/store/products/{id}/     - Delete product
    POST   /api/admin/store/products/{id}/images/    - Add image
    POST   /api/admin/store/products/{id}/variants/  - Add variant
    """
    queryset = StoreProduct.objects.all().select_related('category').prefetch_related(
        'images', 'variants', 'digital_assets'
    ).order_by('-created_at')
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'list':
            return StoreProductAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StoreProductAdminCreateSerializer
        return StoreProductAdminDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search by name/SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by product type
        product_type = self.request.query_params.get('type')
        if product_type in ['physical', 'digital']:
            queryset = queryset.filter(product_type=product_type)

        # Filter by stock status
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(
                    Q(inventory_count__gt=0) | Q(product_type='digital')
                )
            else:
                queryset = queryset.filter(inventory_count=0, product_type='physical')

        return queryset

    @action(detail=True, methods=['post'])
    def images(self, request, pk=None):
        """Add image to product"""
        product = self.get_object()
        serializer = StoreProductImageAdminSerializer(data=request.data)

        if serializer.is_valid():
            # If this is set as primary, unset other primary images
            if serializer.validated_data.get('is_primary'):
                product.images.update(is_primary=False)

            image = StoreProductImage.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreProductImageAdminSerializer(image).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def variants(self, request, pk=None):
        """Add variant to product"""
        product = self.get_object()
        serializer = StoreProductVariantAdminSerializer(data=request.data)

        if serializer.is_valid():
            variant = StoreProductVariant.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreProductVariantAdminSerializer(variant).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def digital_assets(self, request, pk=None):
        """Add digital asset to product"""
        product = self.get_object()
        serializer = StoreDigitalAssetAdminSerializer(data=request.data)

        if serializer.is_valid():
            asset = StoreDigitalAsset.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreDigitalAssetAdminSerializer(asset).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a product"""
        product = self.get_object()

        # Create new product with copied data
        new_product = StoreProduct.objects.create(
            category=product.category,
            name=f"{product.name} (Copy)",
            slug=f"{product.slug}-copy-{StoreProduct.objects.count()}",
            description=product.description,
            short_description=product.short_description,
            price_cents=product.price_cents,
            compare_at_price_cents=product.compare_at_price_cents,
            product_type=product.product_type,
            inventory_count=0,
            weight_grams=product.weight_grams,
            is_active=False,  # Start as inactive
            is_featured=False,
            badges=product.badges,
            provenance_info=product.provenance_info,
            authentication_docs=product.authentication_docs,
            min_price_for_inquiry=product.min_price_for_inquiry,
        )

        # Copy images
        for image in product.images.all():
            StoreProductImage.objects.create(
                product=new_product,
                image_url=image.image_url,
                alt_text=image.alt_text,
                display_order=image.display_order,
                is_primary=image.is_primary,
            )

        # Copy variants
        for variant in product.variants.all():
            StoreProductVariant.objects.create(
                product=new_product,
                name=variant.name,
                sku=f"{variant.sku}-copy" if variant.sku else None,
                price_cents_override=variant.price_cents_override,
                inventory_count=0,
                is_active=variant.is_active,
                display_order=variant.display_order,
            )

        return Response(
            StoreProductAdminDetailSerializer(new_product).data,
            status=status.HTTP_201_CREATED
        )




class StoreAdminImageViewSet(viewsets.ModelViewSet):
    """
    Admin API for product images.
    For updating/deleting individual images.

    PUT    /api/admin/store/images/{id}/    - Update image
    DELETE /api/admin/store/images/{id}/    - Delete image
    """
    queryset = StoreProductImage.objects.all()
    serializer_class = StoreProductImageAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]




class StoreAdminVariantViewSet(viewsets.ModelViewSet):
    """
    Admin API for product variants.
    For updating/deleting individual variants.

    PUT    /api/admin/store/variants/{id}/    - Update variant
    DELETE /api/admin/store/variants/{id}/    - Delete variant
    """
    queryset = StoreProductVariant.objects.all()
    serializer_class = StoreProductVariantAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]




class StoreAdminDigitalAssetViewSet(viewsets.ModelViewSet):
    """
    Admin API for digital assets.
    For updating/deleting individual assets.

    PUT    /api/admin/store/digital-assets/{id}/    - Update asset
    DELETE /api/admin/store/digital-assets/{id}/    - Delete asset
    """
    queryset = StoreDigitalAsset.objects.all()
    serializer_class = StoreDigitalAssetAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]




class StoreAdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin API for store orders.
    Requires admin/staff authentication.

    GET    /api/admin/store/orders/         - List all orders
    GET    /api/admin/store/orders/{id}/    - Get order details
    PUT    /api/admin/store/orders/{id}/    - Update order (status, tracking)
    """
    queryset = StoreOrder.objects.all().select_related('user').prefetch_related(
        'items'
    ).order_by('-created_at')
    serializer_class = StoreOrderAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)

        # Search by email or order ID
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer_email__icontains=search) |
                Q(id__icontains=search) |
                Q(tracking_number__icontains=search)
            )

        return queryset

    def partial_update(self, request, *args, **kwargs):
        """Handle order status updates with email notifications"""
        order = self.get_object()
        old_status = order.status

        response = super().partial_update(request, *args, **kwargs)

        # Send shipping notification if status changed to shipped
        order.refresh_from_db()
        if old_status != 'shipped' and order.status == 'shipped':
            from ..email_service import EmailService
            EmailService.send_shipping_notification(order)

        return response

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get order statistics for dashboard"""
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        paid_statuses = ['paid', 'processing', 'shipped', 'delivered']
        agg = StoreOrder.objects.aggregate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(status='paid')),
            processing_orders=Count('id', filter=Q(status='processing')),
            shipped_orders=Count('id', filter=Q(status='shipped')),
            delivered_orders=Count('id', filter=Q(status='delivered')),
            total_revenue_cents=Sum('total_cents', filter=Q(status__in=paid_statuses)),
            last_30_days_orders=Count('id', filter=Q(created_at__date__gte=thirty_days_ago)),
            last_30_days_revenue_cents=Sum('total_cents', filter=Q(
                created_at__date__gte=thirty_days_ago, status__in=paid_statuses
            )),
        )
        stats = {k: v or 0 for k, v in agg.items()}

        # Convert cents to dollars
        stats['total_revenue_dollars'] = stats['total_revenue_cents'] / 100
        stats['last_30_days_revenue_dollars'] = stats['last_30_days_revenue_cents'] / 100

        return Response(stats)

