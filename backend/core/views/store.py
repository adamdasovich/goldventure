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
# STORE MODULE API
# ============================================================================

class StoreCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for store categories.

    GET /api/store/categories/           - List all active categories
    GET /api/store/categories/{slug}/    - Get category by slug
    """
    queryset = StoreCategory.objects.filter(is_active=True)
    serializer_class = StoreCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'




class StoreProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for store products.

    GET /api/store/products/            - List all active products
    GET /api/store/products/{slug}/     - Get product by slug
    GET /api/store/products/featured/   - Get featured products
    GET /api/store/products/by-category/{category_slug}/ - Get products by category
    """
    queryset = StoreProduct.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related('images', 'variants')
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoreProductDetailSerializer
        return StoreProductListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by product type
        product_type = self.request.query_params.get('type')
        if product_type in ['physical', 'digital']:
            queryset = queryset.filter(product_type=product_type)

        # Filter by badge
        badge = self.request.query_params.get('badge')
        if badge:
            queryset = queryset.filter(badges__contains=[badge])

        # Price range (with safe conversion)
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price_cents__gte=int(float(min_price) * 100))
            except (ValueError, TypeError):
                pass  # Ignore invalid price filter

        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price_cents__lte=int(float(max_price) * 100))
            except (ValueError, TypeError):
                pass  # Ignore invalid price filter

        # Sorting
        sort = self.request.query_params.get('sort', '-created_at')
        if sort == 'price_asc':
            queryset = queryset.order_by('price_cents')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price_cents')
        elif sort == 'popular':
            queryset = queryset.order_by('-total_sold')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-is_featured', '-created_at')

        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = StoreProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_slug>[^/.]+)')
    def by_category(self, request, category_slug=None):
        """Get products by category slug"""
        products = self.get_queryset().filter(category__slug=category_slug)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = StoreProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StoreProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def share(self, request, slug=None):
        """Track product share to chat"""
        product = self.get_object()
        shared_to = request.data.get('shared_to', 'forum')
        destination_id = request.data.get('destination_id', '')

        share = StoreProductShare.objects.create(
            user=request.user,
            product=product,
            shared_to=shared_to,
            destination_id=destination_id
        )

        return Response({
            'success': True,
            'share_id': share.id,
            'message': f'Product shared successfully'
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def inquire(self, request, slug=None):
        """Create inquiry for high-value product"""
        product = self.get_object()

        if not product.requires_inquiry:
            return Response(
                {'error': 'This product does not require an inquiry'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StoreProductInquiryCreateSerializer(
            data={**request.data, 'product': product.id},
            context={'request': request}
        )

        if serializer.is_valid():
            inquiry = serializer.save()
            return Response(
                StoreProductInquirySerializer(inquiry).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class StoreCartViewSet(viewsets.ViewSet):
    """
    API for shopping cart management.
    Supports both authenticated users and guest carts (via session).

    GET  /api/store/cart/           - Get current user's cart
    POST /api/store/cart/add/       - Add item to cart
    PUT  /api/store/cart/items/{id}/ - Update cart item quantity
    DELETE /api/store/cart/items/{id}/ - Remove item from cart
    POST /api/store/cart/clear/     - Clear entire cart
    """
    permission_classes = [AllowAny]

    def get_or_create_cart(self, request):
        """Get or create cart for user or guest session"""
        if request.user.is_authenticated:
            cart, created = StoreCart.objects.get_or_create(user=request.user)
        else:
            # Guest cart using session
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            cart, created = StoreCart.objects.get_or_create(session_key=session_key, user=None)
        return cart

    def list(self, request):
        """Get current cart"""
        cart = self.get_or_create_cart(request)
        serializer = StoreCartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_or_create_cart(request)
        product_id = serializer.validated_data['product_id']
        variant_id = serializer.validated_data.get('variant_id')
        quantity = serializer.validated_data['quantity']

        product = StoreProduct.objects.get(id=product_id)
        variant = None
        if variant_id:
            variant = StoreProductVariant.objects.get(id=variant_id)

        # Check if item already in cart
        existing_item = cart.items.filter(product=product, variant=variant).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            item = existing_item
        else:
            item = StoreCartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )

        # Update cart timestamp
        cart.save()

        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })

    @action(detail=False, methods=['put', 'delete'], url_path='items/(?P<item_id>[^/.]+)')
    def item(self, request, item_id=None):
        """Update or remove cart item.

        PUT: Update cart item quantity
        DELETE: Remove item from cart
        """
        cart = self.get_or_create_cart(request)
        try:
            item = cart.items.get(id=item_id)
        except StoreCartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'DELETE':
            # Remove item
            item.delete()
        else:
            # Update quantity (PUT)
            serializer = UpdateCartItemSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            quantity = serializer.validated_data['quantity']
            if quantity == 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        cart.save()  # Update timestamp
        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear entire cart"""
        cart = self.get_or_create_cart(request)
        cart.items.all().delete()
        cart.save()
        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })




class StoreOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for viewing user orders.

    GET /api/store/orders/          - List user's orders
    GET /api/store/orders/{id}/     - Get order details
    """
    serializer_class = StoreOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StoreOrder.objects.filter(
            user=self.request.user
        ).prefetch_related('items', 'items__product', 'items__variant')




class StoreShippingRateViewSet(viewsets.ViewSet):
    """
    API for shipping rates.

    GET /api/store/shipping-rates/  - Get available shipping rates
    """
    permission_classes = [AllowAny]

    def list(self, request):
        """Get all active shipping rates"""
        country = request.query_params.get('country', 'US')
        rates = StoreShippingRate.objects.filter(
            is_active=True,
            countries__contains=[country]
        )
        serializer = StoreShippingRateSerializer(rates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate shipping rate based on cart contents"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        cart = StoreCart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        country = request.data.get('country', 'US')
        if country not in ['US', 'CA']:
            return Response(
                {'error': 'Shipping only available to US and Canada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total weight
        total_weight = sum(
            item.product.weight_grams * item.quantity
            for item in cart.items.filter(product__product_type='physical')
        )

        # Get applicable rates
        rates = StoreShippingRate.objects.filter(
            is_active=True,
            countries__contains=[country],
            min_weight_grams__lte=total_weight,
            max_weight_grams__gte=total_weight
        )

        serializer = StoreShippingRateSerializer(rates, many=True)
        return Response({
            'total_weight_grams': total_weight,
            'rates': serializer.data
        })




@api_view(['GET'])
@permission_classes([AllowAny])
def store_ticker(request):
    """
    Get recent purchases for The Ticker social proof feed.

    GET /api/store/ticker/

    Only returns purchases over $100 threshold.
    """
    # Get recent purchases above threshold (10000 cents = $100)
    recent = StoreRecentPurchase.objects.filter(
        amount_cents__gte=10000
    ).select_related('product').order_by('-created_at')[:20]

    serializer = StoreRecentPurchaseSerializer(recent, many=True)
    return Response(serializer.data)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_store_badges(request):
    """
    Get current user's store badges.

    GET /api/store/badges/
    """
    badges = UserStoreBadge.objects.filter(user=request.user)
    serializer = UserStoreBadgeSerializer(badges, many=True)
    return Response(serializer.data)




# ============================================================================
# COMPANY FORUM DISCUSSION
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_discussion(request, company_id):
    """
    Get or create the main forum discussion for a company.

    GET /api/companies/<company_id>/discussion/

    Returns the discussion ID for the company's main forum thread.
    Creates one if it doesn't exist.
    """
    from core.models import Company, ForumDiscussion

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get or create the main discussion for this company
    discussion, created = ForumDiscussion.objects.get_or_create(
        company=company,
        is_archived=False,
        defaults={
            'title': f'{company.name} Community Discussion',
            'description': f'Main discussion thread for {company.name} investors and analysts.',
            'created_by': request.user,
            'is_active': True,
            'is_pinned': True,
        }
    )

    return Response({
        'discussion_id': discussion.id,
        'title': discussion.title,
        'description': discussion.description,
        'message_count': discussion.message_count,
        'participant_count': discussion.participant_count,
        'created': created,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_company_forum_preview(request, company_id):
    """
    Public read-only preview of the company forum.

    GET /api/companies/<company_id>/forum-preview/

    Returns the most recent non-deleted messages so anonymous visitors can
    see that the forum is alive before they sign up. No write access; no
    real-time updates; intentionally lightweight so it can be called on every
    company-page load without auth.
    """
    from core.models import Company, ForumDiscussion, ForumMessage

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    discussion = ForumDiscussion.objects.filter(
        company=company,
        is_archived=False,
    ).order_by('-is_pinned', '-updated_at').first()

    if not discussion:
        return Response({
            'has_discussion': False,
            'message_count': 0,
            'participant_count': 0,
            'recent_messages': [],
        })

    preview_limit = 3
    recent_qs = (
        ForumMessage.objects
        .filter(discussion=discussion, is_deleted=False)
        .select_related('user')
        .order_by('-created_at')[:preview_limit]
    )
    # Oldest -> newest so the UI reads top-down like the live forum.
    recent = list(reversed(list(recent_qs)))

    recent_payload = []
    for msg in recent:
        # Initials only — never leak real names to anonymous visitors. They
        # see proof of life (timestamp, content) but have to sign up for
        # author identity.
        full_name = msg.user.get_full_name() or msg.user.username or ''
        initials = ''.join(
            part[0] for part in full_name.split() if part
        )[:2].upper() or 'A'
        recent_payload.append({
            'id': msg.id,
            'initials': initials,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_pinned': msg.is_pinned,
        })

    return Response({
        'has_discussion': True,
        'message_count': discussion.message_count,
        'participant_count': discussion.participant_count,
        'last_message_at': discussion.last_message_at.isoformat() if discussion.last_message_at else None,
        'recent_messages': recent_payload,
        'preview_limit': preview_limit,
    })





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_checkout(request):
    """
    Create Stripe checkout session for store purchase.

    POST /api/store/checkout/
    {
        "shipping_address": {...},  // Required for physical items
        "shipping_rate_id": 1,      // Required for physical items
        "success_url": "https://...",
        "cancel_url": "https://..."
    }
    """
    serializer = CheckoutSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cart = StoreCart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    # Import the store stripe service (will be created next)
    from ..store_stripe_service import StoreStripeService

    try:
        checkout_data = StoreStripeService.create_checkout_session(
            cart=cart,
            user=request.user,
            shipping_address=serializer.validated_data.get('shipping_address'),
            shipping_rate_id=serializer.validated_data.get('shipping_rate_id'),
            success_url=serializer.validated_data['success_url'],
            cancel_url=serializer.validated_data['cancel_url']
        )

        return Response(checkout_data)

    except Exception as e:
        logger.error(f"store_checkout error for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'Failed to create checkout session. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([AllowAny])
def store_webhook(request):
    """
    Handle Stripe webhooks for store purchases.

    POST /api/store/webhook/
    """
    import stripe
    import logging
    from django.conf import settings

    logger = logging.getLogger(__name__)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_STORE_WEBHOOK_SECRET', None)

    logger.info(f"Store webhook received. Secret configured: {bool(webhook_secret)}, Sig header: {bool(sig_header)}")

    if not webhook_secret:
        logger.error("STRIPE_STORE_WEBHOOK_SECRET not configured")
        return Response({'error': 'Webhook secret not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Store webhook invalid payload: {str(e)}")
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Store webhook signature verification failed: {str(e)}")
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    # Import the store stripe service
    from ..store_stripe_service import StoreStripeService

    try:
        result = StoreStripeService.process_webhook(event)
        return Response(result)
    except Exception as e:
        logger.error(f"Store webhook error: {str(e)}")
        return Response({'error': 'Webhook processing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

