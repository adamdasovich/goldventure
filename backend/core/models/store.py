from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .users import User




# ============================================================================
# STORE MODULE - E-COMMERCE FOR GOLDVENTURE
# ============================================================================

class StoreCategory(models.Model):
    """Product categories for the store"""

    CATEGORY_SLUGS = [
        ('the_vault', 'The Vault'),
        ('field_gear', 'Field Gear'),
        ('resource_library', 'Resource Library'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'store_categories'
        verbose_name_plural = 'Store Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name




class StoreProduct(models.Model):
    """Products available in the store"""

    PRODUCT_TYPES = [
        ('physical', 'Physical Product'),
        ('digital', 'Digital Download'),
    ]

    BADGE_CHOICES = [
        ('rare', 'Rare'),
        ('limited_edition', 'Limited Edition'),
        ('community_favorite', 'Community Favorite'),
        ('new_arrival', 'New Arrival'),
        ('instant_download', 'Instant Download'),
    ]

    # Basic info
    category = models.ForeignKey(
        StoreCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(help_text="Supports Markdown for rich formatting")
    short_description = models.CharField(max_length=500, blank=True)

    # Pricing
    price_cents = models.IntegerField(help_text="Price in cents (e.g., 5000 = $50.00)")
    compare_at_price_cents = models.IntegerField(
        null=True,
        blank=True,
        help_text="Original price for sale items"
    )

    # Product type and inventory
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='physical')
    sku = models.CharField(max_length=100, blank=True, unique=True, null=True)
    inventory_count = models.IntegerField(default=0, help_text="Available stock")
    weight_grams = models.IntegerField(
        default=0,
        help_text="Weight in grams for shipping calculation"
    )

    # Display settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    badges = models.JSONField(
        default=list,
        blank=True,
        help_text="List of badge slugs: rare, limited_edition, community_favorite, new_arrival"
    )

    # Vault-specific fields (premium items)
    provenance_info = models.TextField(
        blank=True,
        help_text="History and origin for premium/vault items"
    )
    authentication_docs = models.JSONField(
        default=list,
        blank=True,
        help_text="Certificates, lab reports, expert verification URLs"
    )
    min_price_for_inquiry = models.IntegerField(
        default=500000,  # $5,000 in cents
        help_text="Price threshold above which 'Inquire' button shows instead of Add to Cart"
    )

    # Sales tracking
    total_sold = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'store_products'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['product_type', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'is_active'], name='idx_product_featured'),
        ]

    def __str__(self):
        return self.name

    @property
    def price_dollars(self):
        return self.price_cents / 100

    @property
    def is_on_sale(self):
        return self.compare_at_price_cents and self.compare_at_price_cents > self.price_cents

    @property
    def in_stock(self):
        return self.inventory_count > 0 or self.product_type == 'digital'

    @property
    def requires_inquiry(self):
        return self.price_cents >= self.min_price_for_inquiry




class StoreProductImage(models.Model):
    """Product images for gallery"""

    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.URLField(help_text="URL to product image")
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_product_images'
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"




class StoreProductVariant(models.Model):
    """Product variants (sizes, formats, etc.)"""

    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=100, help_text="e.g., 'Large', 'Digital', 'Physical'")
    sku = models.CharField(max_length=100, blank=True)
    price_cents_override = models.IntegerField(
        null=True,
        blank=True,
        help_text="Override price for this variant"
    )
    inventory_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_product_variants'
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def price_cents(self):
        return self.price_cents_override or self.product.price_cents




class StoreDigitalAsset(models.Model):
    """Digital files for downloadable products"""

    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='digital_assets'
    )
    file_url = models.URLField(help_text="S3 URL to the file")
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField(default=0)
    download_limit = models.IntegerField(
        default=5,
        help_text="Maximum number of downloads allowed"
    )
    expiry_hours = models.IntegerField(
        default=72,
        help_text="Hours until download link expires"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_digital_assets'

    def __str__(self):
        return f"{self.product.name} - {self.file_name}"




class StoreCart(models.Model):
    """Shopping cart for users"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='store_carts'
    )
    session_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="For anonymous/guest carts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    abandoned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp for cart abandonment tracking"
    )

    class Meta:
        db_table = 'store_carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Guest Cart ({self.session_key[:8]}...)"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal_cents(self):
        return sum(item.line_total_cents for item in self.items.all())

    @property
    def has_physical_items(self):
        return self.items.filter(product__product_type='physical').exists()

    @property
    def has_digital_items(self):
        return self.items.filter(product__product_type='digital').exists()




class StoreCartItem(models.Model):
    """Individual items in a shopping cart"""

    cart = models.ForeignKey(
        StoreCart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        StoreProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_cart_items'
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def unit_price_cents(self):
        if self.variant and self.variant.price_cents_override:
            return self.variant.price_cents_override
        return self.product.price_cents

    @property
    def line_total_cents(self):
        return self.unit_price_cents * self.quantity




class StoreOrder(models.Model):
    """Completed orders"""

    ORDER_STATUS = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='store_orders'
    )

    # Stripe identifiers
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    # Order details
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    subtotal_cents = models.IntegerField(default=0)
    shipping_cents = models.IntegerField(default=0)
    tax_cents = models.IntegerField(default=0)
    total_cents = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='usd')

    # Shipping info
    shipping_address = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full shipping address"
    )
    shipping_rate_name = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Customer email (for guests)
    customer_email = models.EmailField(blank=True)

    class Meta:
        db_table = 'store_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['stripe_checkout_session_id']),
        ]

    def __str__(self):
        return f"Order #{self.id} - ${self.total_cents/100:.2f}"

    @property
    def total_dollars(self):
        return self.total_cents / 100




class StoreOrderItem(models.Model):
    """Individual items in an order"""

    order = models.ForeignKey(
        StoreOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        StoreProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )

    # Snapshot of product at time of purchase
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_cents = models.IntegerField()

    # Digital fulfillment
    digital_download_url = models.URLField(blank=True)
    download_count = models.IntegerField(default=0)
    download_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_order_items'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def line_total_cents(self):
        return self.price_cents * self.quantity




class StoreShippingRate(models.Model):
    """Shipping rate tiers"""

    name = models.CharField(max_length=100)  # Standard, Expedited, Express
    description = models.CharField(max_length=255, blank=True)

    # Weight-based pricing
    min_weight_grams = models.IntegerField(default=0)
    max_weight_grams = models.IntegerField(default=99999999)

    # Pricing
    price_cents = models.IntegerField()

    # Delivery estimates
    estimated_days_min = models.IntegerField(default=3)
    estimated_days_max = models.IntegerField(default=7)

    # Region restrictions (North America only per config)
    countries = models.JSONField(
        default=list,
        help_text="List of country codes: ['US', 'CA']"
    )

    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_shipping_rates'
        ordering = ['display_order', 'price_cents']

    def __str__(self):
        return f"{self.name} - ${self.price_cents/100:.2f}"




class StoreProductShare(models.Model):
    """Track product shares to chat (analytics)"""

    SHARE_DESTINATIONS = [
        ('forum', 'Forum Discussion'),
        ('inquiry', 'Property Inquiry'),
        ('direct_message', 'Direct Message'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_shares'
    )
    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    shared_to = models.CharField(max_length=20, choices=SHARE_DESTINATIONS)
    destination_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of forum thread, inquiry, or chat room"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_product_shares'
        indexes = [
            models.Index(fields=['product', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} shared {self.product.name}"




class StoreRecentPurchase(models.Model):
    """Recent purchases for The Ticker social proof feed"""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recent_purchases'
    )
    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='recent_purchases'
    )
    order = models.ForeignKey(
        StoreOrder,
        on_delete=models.CASCADE,
        related_name='recent_purchases'
    )

    # Anonymized location
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_anonymous = models.BooleanField(default=True)

    # Only show purchases above threshold
    amount_cents = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_recent_purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        location = f"{self.city}, {self.country}" if self.city else self.country
        return f"Purchase in {location}: {self.product.name}"




class StoreProductInquiry(models.Model):
    """Inquiries for high-value vault items"""

    INQUIRY_STATUS = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('sold', 'Sold'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_inquiries'
    )
    product = models.ForeignKey(
        StoreProduct,
        on_delete=models.CASCADE,
        related_name='inquiries'
    )

    status = models.CharField(max_length=20, choices=INQUIRY_STATUS, default='new')
    message = models.TextField(help_text="User's inquiry message")

    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    preferred_contact = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('phone', 'Phone')],
        default='email'
    )

    # Admin notes
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'store_product_inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry: {self.product.name} by {self.user.username}"




class UserStoreBadge(models.Model):
    """Gamification badges earned through store purchases"""

    BADGE_TYPES = [
        ('founder', 'Founder'),  # First purchase
        ('bronze_collector', 'Bronze Collector'),  # $100+ spent
        ('silver_prospector', 'Silver Prospector'),  # $500+ spent
        ('gold_miner', 'Gold Miner'),  # $1000+ spent
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='store_badges'
    )
    badge_type = models.CharField(max_length=30, choices=BADGE_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)

    # Stats at time of earning
    total_spent_cents = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_store_badges'
        unique_together = ['user', 'badge_type']

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"


# ============================================================================
# COMPANY AUTO-POPULATION & SCRAPING MODELS
# ============================================================================

