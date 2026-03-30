"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from rest_framework import serializers
from ..models import (
    User, Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, MarketData, NewsRelease, Document,
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    # Financial Hub models
    EducationalModule, ModuleCompletion, AccreditedInvestorQualification,
    SubscriptionAgreement, InvestmentTransaction, FinancingAggregate,
    PaymentInstruction, DRSDocument,
    # Property Exchange models
    ProspectorProfile, PropertyListing, PropertyMedia, PropertyInquiry,
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement,
    InquiryMessage,
    # Company Portal models
    CompanyResource, SpeakingEvent, CompanySubscription, SubscriptionInvoice,
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





# ============================================================================
# STORE MODULE SERIALIZERS
# ============================================================================

class StoreCategorySerializer(serializers.ModelSerializer):
    """Serializer for store categories"""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'slug', 'description', 'display_order',
                  'icon', 'is_active', 'product_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()




class StoreProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""

    class Meta:
        model = StoreProductImage
        fields = ['id', 'image_url', 'alt_text', 'display_order', 'is_primary']
        read_only_fields = ['id']




class StoreProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants"""
    effective_price_cents = serializers.SerializerMethodField()
    effective_price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreProductVariant
        fields = ['id', 'name', 'sku', 'price_cents_override', 'inventory_count',
                  'is_active', 'display_order', 'effective_price_cents',
                  'effective_price_dollars']
        read_only_fields = ['id']

    def get_effective_price_cents(self, obj):
        return obj.price_cents

    def get_effective_price_dollars(self, obj):
        return obj.price_cents / 100




class StoreDigitalAssetSerializer(serializers.ModelSerializer):
    """Serializer for digital assets (admin view)"""
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = StoreDigitalAsset
        fields = ['id', 'file_name', 'file_size_bytes', 'file_size_mb',
                  'download_limit', 'expiry_hours']
        read_only_fields = ['id']

    def get_file_size_mb(self, obj):
        return round(obj.file_size_bytes / (1024 * 1024), 2) if obj.file_size_bytes else 0




class StoreProductListSerializer(serializers.ModelSerializer):
    """Compact serializer for product list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'short_description', 'price_cents',
                  'price_dollars', 'compare_at_price_cents', 'compare_at_price_dollars',
                  'product_type', 'inventory_count', 'is_featured', 'badges',
                  'total_sold', 'is_on_sale', 'in_stock', 'category_name',
                  'category_slug', 'primary_image', 'created_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        if primary:
            return StoreProductImageSerializer(primary).data
        return None

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None




class StoreProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail views"""
    category = StoreCategorySerializer(read_only=True)
    images = StoreProductImageSerializer(many=True, read_only=True)
    variants = StoreProductVariantSerializer(many=True, read_only=True)
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    requires_inquiry = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'price_cents', 'price_dollars', 'compare_at_price_cents',
                  'compare_at_price_dollars', 'product_type', 'sku',
                  'inventory_count', 'weight_grams', 'is_active', 'is_featured',
                  'badges', 'provenance_info', 'authentication_docs',
                  'total_sold', 'is_on_sale', 'in_stock', 'requires_inquiry',
                  'category', 'images', 'variants', 'created_at', 'updated_at']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None




class StoreCartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = StoreProductListSerializer(read_only=True)
    variant = StoreProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    unit_price_cents = serializers.IntegerField(read_only=True)
    line_total_cents = serializers.IntegerField(read_only=True)
    line_total_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreCartItem
        fields = ['id', 'product', 'variant', 'product_id', 'variant_id',
                  'quantity', 'unit_price_cents', 'line_total_cents',
                  'line_total_dollars', 'added_at']
        read_only_fields = ['id', 'added_at']

    def get_line_total_dollars(self, obj):
        return obj.line_total_cents / 100




class StoreCartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = StoreCartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    subtotal_cents = serializers.IntegerField(read_only=True)
    subtotal_dollars = serializers.SerializerMethodField()
    has_physical_items = serializers.BooleanField(read_only=True)
    has_digital_items = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreCart
        fields = ['id', 'user', 'items', 'item_count', 'subtotal_cents',
                  'subtotal_dollars', 'has_physical_items', 'has_digital_items',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100




class StoreOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    line_total_cents = serializers.IntegerField(read_only=True)
    line_total_dollars = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrderItem
        fields = ['id', 'product_name', 'variant_name', 'quantity',
                  'price_cents', 'price_dollars', 'line_total_cents',
                  'line_total_dollars', 'digital_download_url',
                  'download_count', 'download_expires_at']

    def get_line_total_dollars(self, obj):
        return obj.line_total_cents / 100

    def get_price_dollars(self, obj):
        return obj.price_cents / 100




class StoreOrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    items = StoreOrderItemSerializer(many=True, read_only=True)
    total_dollars = serializers.SerializerMethodField()
    subtotal_dollars = serializers.SerializerMethodField()
    shipping_dollars = serializers.SerializerMethodField()
    tax_dollars = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StoreOrder
        fields = ['id', 'status', 'status_display', 'subtotal_cents',
                  'subtotal_dollars', 'shipping_cents', 'shipping_dollars',
                  'tax_cents', 'tax_dollars', 'total_cents', 'total_dollars',
                  'currency', 'shipping_address', 'shipping_rate_name',
                  'tracking_number', 'items', 'created_at', 'paid_at',
                  'shipped_at', 'delivered_at']
        read_only_fields = ['id', 'created_at']

    def get_total_dollars(self, obj):
        return obj.total_cents / 100

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100

    def get_shipping_dollars(self, obj):
        return obj.shipping_cents / 100

    def get_tax_dollars(self, obj):
        return obj.tax_cents / 100




class StoreShippingRateSerializer(serializers.ModelSerializer):
    """Serializer for shipping rates"""
    price_dollars = serializers.SerializerMethodField()
    delivery_estimate = serializers.SerializerMethodField()

    class Meta:
        model = StoreShippingRate
        fields = ['id', 'name', 'description', 'price_cents', 'price_dollars',
                  'estimated_days_min', 'estimated_days_max', 'delivery_estimate',
                  'countries']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_delivery_estimate(self, obj):
        if obj.estimated_days_min == obj.estimated_days_max:
            return f"{obj.estimated_days_min} business days"
        return f"{obj.estimated_days_min}-{obj.estimated_days_max} business days"




class StoreRecentPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for The Ticker recent purchases"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    amount_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreRecentPurchase
        fields = ['id', 'product_name', 'product_slug', 'product_image',
                  'location', 'amount_dollars', 'is_anonymous', 'created_at']

    def get_product_image(self, obj):
        primary = obj.product.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.product.images.first()
        return primary.image_url if primary else None

    def get_location(self, obj):
        if obj.city and obj.country:
            return f"{obj.city}, {obj.country}"
        return obj.country or "Unknown"

    def get_amount_dollars(self, obj):
        return obj.amount_cents / 100




class StoreProductShareSerializer(serializers.ModelSerializer):
    """Serializer for product shares"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StoreProductShare
        fields = ['id', 'user', 'username', 'product', 'product_name',
                  'shared_to', 'destination_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']




class StoreProductInquirySerializer(serializers.ModelSerializer):
    """Serializer for product inquiries (high-value items)"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StoreProductInquiry
        fields = ['id', 'user', 'user_email', 'product', 'product_name',
                  'status', 'status_display', 'message', 'phone',
                  'preferred_contact', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']




class StoreProductInquiryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product inquiries"""

    class Meta:
        model = StoreProductInquiry
        fields = ['product', 'message', 'phone', 'preferred_contact']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)




class UserStoreBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user store badges"""
    badge_display = serializers.CharField(source='get_badge_type_display', read_only=True)
    total_spent_dollars = serializers.SerializerMethodField()

    class Meta:
        model = UserStoreBadge
        fields = ['id', 'badge_type', 'badge_display', 'earned_at',
                  'total_spent_cents', 'total_spent_dollars', 'order_count']

    def get_total_spent_dollars(self, obj):
        return obj.total_spent_cents / 100




class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        try:
            product = StoreProduct.objects.get(id=value, is_active=True)
            if not product.in_stock:
                raise serializers.ValidationError("This product is out of stock")
            if product.requires_inquiry:
                raise serializers.ValidationError(
                    "This item requires an inquiry. Please use the inquiry form."
                )
        except StoreProduct.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        return value

    def validate(self, data):
        product = StoreProduct.objects.get(id=data['product_id'])
        variant_id = data.get('variant_id')

        if variant_id:
            try:
                variant = product.variants.get(id=variant_id, is_active=True)
                if variant.inventory_count < data['quantity']:
                    raise serializers.ValidationError(
                        {"quantity": f"Only {variant.inventory_count} available"}
                    )
            except StoreProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"variant_id": "Variant not found for this product"}
                )
        else:
            if product.product_type == 'physical' and product.inventory_count < data['quantity']:
                raise serializers.ValidationError(
                    {"quantity": f"Only {product.inventory_count} available"}
                )

        return data




class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=0)




class CheckoutSerializer(serializers.Serializer):
    """Serializer for initiating checkout"""
    shipping_address = serializers.JSONField(required=False)
    shipping_rate_id = serializers.IntegerField(required=False, allow_null=True)
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()

    def validate_shipping_address(self, value):
        if value:
            required_fields = ['name', 'line1', 'city', 'state', 'postal_code', 'country']
            missing = [f for f in required_fields if not value.get(f)]
            if missing:
                raise serializers.ValidationError(
                    f"Missing required fields: {', '.join(missing)}"
                )
            # Validate North America only
            if value.get('country') not in ['US', 'CA']:
                raise serializers.ValidationError(
                    "Shipping is only available to the United States and Canada"
                )
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Get or create cart for user
            cart = StoreCart.objects.filter(user=request.user).first()
            if not cart or not cart.items.exists():
                raise serializers.ValidationError("Your cart is empty")

            # Check if shipping info needed
            if cart.has_physical_items and not data.get('shipping_address'):
                raise serializers.ValidationError(
                    {"shipping_address": "Shipping address required for physical items"}
                )

            if cart.has_physical_items and not data.get('shipping_rate_id'):
                raise serializers.ValidationError(
                    {"shipping_rate_id": "Please select a shipping option"}
                )

        return data




# ============================================================================
# Store Admin Serializers
# ============================================================================

class StoreProductImageAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for product images - allows full CRUD"""

    class Meta:
        model = StoreProductImage
        fields = ['id', 'image_url', 'alt_text', 'display_order', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']




class StoreProductVariantAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for product variants - allows full CRUD"""
    effective_price_cents = serializers.SerializerMethodField()

    class Meta:
        model = StoreProductVariant
        fields = ['id', 'name', 'sku', 'price_cents_override', 'inventory_count',
                  'is_active', 'display_order', 'effective_price_cents', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_effective_price_cents(self, obj):
        return obj.price_cents




class StoreDigitalAssetAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for digital assets"""
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = StoreDigitalAsset
        fields = ['id', 'file_url', 'file_name', 'file_size_bytes', 'file_size_mb',
                  'download_limit', 'expiry_hours', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_file_size_mb(self, obj):
        return round(obj.file_size_bytes / (1024 * 1024), 2) if obj.file_size_bytes else 0




class StoreCategoryAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for categories - allows full CRUD"""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'slug', 'description', 'display_order',
                  'icon', 'is_active', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_product_count(self, obj):
        return obj.products.count()




class StoreProductAdminListSerializer(serializers.ModelSerializer):
    """Admin serializer for product list view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()
    variant_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'price_cents',
                  'price_dollars', 'product_type', 'inventory_count', 'is_active',
                  'is_featured', 'badges', 'total_sold', 'primary_image',
                  'variant_count', 'image_count', 'created_at', 'updated_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        return primary.image_url if primary else None

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_variant_count(self, obj):
        return obj.variants.count()

    def get_image_count(self, obj):
        return obj.images.count()




class StoreProductAdminDetailSerializer(serializers.ModelSerializer):
    """Admin serializer for product detail/edit view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = StoreProductImageAdminSerializer(many=True, read_only=True)
    variants = StoreProductVariantAdminSerializer(many=True, read_only=True)
    digital_assets = StoreDigitalAssetAdminSerializer(many=True, read_only=True)
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'category', 'category_name', 'price_cents', 'price_dollars',
                  'compare_at_price_cents', 'compare_at_price_dollars',
                  'product_type', 'sku', 'inventory_count', 'weight_grams',
                  'is_active', 'is_featured', 'badges', 'provenance_info',
                  'authentication_docs', 'min_price_for_inquiry', 'total_sold',
                  'images', 'variants', 'digital_assets', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_sold', 'created_at', 'updated_at']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None




class StoreProductAdminCreateSerializer(serializers.ModelSerializer):
    """Admin serializer for creating/updating products"""
    images = StoreProductImageAdminSerializer(many=True, required=False)
    variants = StoreProductVariantAdminSerializer(many=True, required=False)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'category', 'price_cents', 'compare_at_price_cents',
                  'product_type', 'sku', 'inventory_count', 'weight_grams',
                  'is_active', 'is_featured', 'badges', 'provenance_info',
                  'authentication_docs', 'min_price_for_inquiry',
                  'images', 'variants']
        read_only_fields = ['id']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])

        product = StoreProduct.objects.create(**validated_data)

        # Create images
        for idx, image_data in enumerate(images_data):
            StoreProductImage.objects.create(
                product=product,
                display_order=idx,
                **image_data
            )

        # Create variants
        for idx, variant_data in enumerate(variants_data):
            StoreProductVariant.objects.create(
                product=product,
                display_order=idx,
                **variant_data
            )

        return product

    def update(self, instance, validated_data):
        # Remove nested data - these are handled separately
        validated_data.pop('images', None)
        validated_data.pop('variants', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance




class StoreOrderAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for viewing orders"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    items = serializers.SerializerMethodField()
    subtotal_dollars = serializers.SerializerMethodField()
    shipping_dollars = serializers.SerializerMethodField()
    tax_dollars = serializers.SerializerMethodField()
    total_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrder
        fields = ['id', 'user', 'user_email', 'user_name', 'status',
                  'subtotal_cents', 'subtotal_dollars', 'shipping_cents',
                  'shipping_dollars', 'tax_cents', 'tax_dollars',
                  'total_cents', 'total_dollars', 'shipping_address',
                  'customer_email', 'tracking_number', 'shipped_at',
                  'delivered_at', 'paid_at', 'items', 'created_at']

    def get_items(self, obj):
        return [{
            'id': item.id,
            'product_name': item.product_name,
            'variant_name': item.variant_name,
            'quantity': item.quantity,
            'price_cents': item.price_cents,
            'price_dollars': item.price_cents / 100,
        } for item in obj.items.all()]

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100

    def get_shipping_dollars(self, obj):
        return obj.shipping_cents / 100

    def get_tax_dollars(self, obj):
        return obj.tax_cents / 100

    def get_total_dollars(self, obj):
        return obj.total_cents / 100

