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
# PROSPECTOR PROPERTY EXCHANGE SERIALIZERS
# ============================================================================

class ProspectorProfileSerializer(serializers.ModelSerializer):
    """Serializer for prospector profiles"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    listings_count = serializers.SerializerMethodField()
    can_list_properties = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProspectorProfile
        fields = [
            'id', 'user', 'username', 'email', 'display_name', 'company_name',
            'bio', 'years_experience', 'specializations', 'regions_active',
            'certifications', 'website_url', 'phone', 'is_verified',
            'verification_date', 'profile_image_url', 'total_listings',
            'active_listings', 'successful_transactions', 'average_rating',
            'listings_count', 'commission_agreement_accepted', 'commission_agreement_date',
            'can_list_properties', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'verification_date',
                          'total_listings', 'active_listings', 'successful_transactions',
                          'average_rating', 'commission_agreement_accepted',
                          'commission_agreement_date', 'can_list_properties',
                          'created_at', 'updated_at']

    def get_listings_count(self, obj):
        if hasattr(obj, '_listings_count'):
            return obj._listings_count
        return obj.listings.filter(status='active').count()




class ProspectorCommissionAgreementSerializer(serializers.ModelSerializer):
    """Serializer for commission agreement acceptance"""
    agreement_text = serializers.SerializerMethodField()
    prospector_name = serializers.CharField(source='prospector.display_name', read_only=True)

    class Meta:
        model = ProspectorCommissionAgreement
        fields = [
            'id', 'prospector', 'prospector_name', 'version', 'commission_rate',
            'full_legal_name', 'accepted_at', 'ip_address', 'user_agent',
            'agreement_text', 'is_active'
        ]
        read_only_fields = ['id', 'prospector', 'version', 'commission_rate',
                          'accepted_at', 'ip_address', 'user_agent', 'is_active']

    def get_agreement_text(self, obj):
        return obj.agreement_text if obj.pk else ProspectorCommissionAgreement.get_agreement_text()




class ProspectorCommissionAgreementCreateSerializer(serializers.Serializer):
    """Serializer for accepting the commission agreement"""
    full_legal_name = serializers.CharField(max_length=300, help_text="Your full legal name as electronic signature")

    def validate_full_legal_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Please enter your full legal name")
        return value.strip()




class ProspectorProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prospector profiles during registration"""

    class Meta:
        model = ProspectorProfile
        fields = [
            'display_name', 'company_name', 'bio', 'years_experience',
            'specializations', 'regions_active', 'website_url', 'phone'
        ]




class PropertyMediaSerializer(serializers.ModelSerializer):
    """Serializer for property media files"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = PropertyMedia
        fields = [
            'id', 'listing', 'media_type', 'category', 'title', 'description',
            'file_url', 'thumbnail_url', 'file_size_mb', 'file_format',
            'sort_order', 'is_primary', 'uploaded_at', 'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']




class PropertyListingListSerializer(serializers.ModelSerializer):
    """Compact serializer for property listing lists/search results"""
    prospector_name = serializers.CharField(source='prospector.display_name', read_only=True)
    prospector_verified = serializers.BooleanField(source='prospector.is_verified', read_only=True)
    primary_mineral_display = serializers.CharField(source='get_primary_mineral_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    exploration_stage_display = serializers.CharField(source='get_exploration_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    country_display = serializers.CharField(source='get_country_display', read_only=True)
    hero_image = serializers.SerializerMethodField()
    is_watchlisted = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = [
            'id', 'slug', 'title', 'summary', 'property_type', 'property_type_display',
            'country', 'country_display', 'province_state', 'region_district',
            'primary_mineral', 'primary_mineral_display', 'exploration_stage',
            'exploration_stage_display', 'listing_type', 'listing_type_display',
            'asking_price', 'price_currency', 'price_negotiable',
            'total_hectares', 'total_acres', 'total_claims',
            'status', 'status_display', 'is_featured',
            'prospector', 'prospector_name', 'prospector_verified',
            'views_count', 'inquiries_count', 'watchlist_count',
            'hero_image', 'is_watchlisted',
            'created_at', 'published_at'
        ]

    def get_hero_image(self, obj):
        hero = obj.media.filter(is_primary=True).first()
        if hero:
            return hero.file_url
        # Fall back to first image
        first_image = obj.media.filter(media_type='image').first()
        return first_image.file_url if first_image else None

    def get_is_watchlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.watchlisted_by.filter(user=request.user).exists()
        return False




class PropertyListingDetailSerializer(serializers.ModelSerializer):
    """Full serializer for property listing detail view"""
    prospector = ProspectorProfileSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)

    # Display values
    primary_mineral_display = serializers.CharField(source='get_primary_mineral_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    exploration_stage_display = serializers.CharField(source='get_exploration_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    country_display = serializers.CharField(source='get_country_display', read_only=True)
    mineral_rights_type_display = serializers.CharField(source='get_mineral_rights_type_display', read_only=True)
    deposit_type_display = serializers.CharField(source='get_deposit_type_display', read_only=True)
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)

    is_watchlisted = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = [
            'id', 'prospector', 'slug',
            # Basic information
            'title', 'summary', 'description', 'property_type', 'property_type_display',
            # Location
            'country', 'country_display', 'province_state', 'region_district', 'nearest_town',
            'coordinates_lat', 'coordinates_lng', 'access_description', 'access_type', 'access_type_display',
            # Claim details
            'claim_numbers', 'total_claims', 'total_hectares', 'total_acres',
            'mineral_rights_type', 'mineral_rights_type_display',
            'surface_rights_included', 'claim_status', 'claim_expiry_date', 'annual_holding_cost',
            # Minerals & geology
            'primary_mineral', 'primary_mineral_display', 'secondary_minerals',
            'deposit_type', 'deposit_type_display', 'geological_setting', 'mineralization_style',
            # Exploration status
            'exploration_stage', 'exploration_stage_display', 'work_completed',
            'historical_production', 'assay_highlights', 'resource_estimate', 'has_43_101_report',
            # Transaction terms
            'listing_type', 'listing_type_display', 'asking_price', 'price_currency',
            'price_negotiable', 'minimum_offer', 'option_terms', 'joint_venture_terms',
            'lease_terms', 'nsr_royalty', 'includes_equipment', 'equipment_description', 'additional_terms',
            # Status & visibility
            'status', 'status_display', 'is_featured', 'featured_until',
            # Engagement metrics
            'views_count', 'inquiries_count', 'watchlist_count',
            # Timestamps
            'created_at', 'updated_at', 'published_at', 'expires_at',
            # Nested serializers
            'media',
            # Method fields
            'is_watchlisted', 'is_owner',
        ]
        read_only_fields = ['id', 'slug', 'prospector', 'views_count', 'inquiries_count',
                          'watchlist_count', 'created_at', 'updated_at', 'published_at']

    def get_is_watchlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.watchlisted_by.filter(user=request.user).exists()
        return False

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.prospector.user == request.user
            except (AttributeError, TypeError):
                return False
        return False




class PropertyListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating property listings"""
    # Allow null for total_claims - will use default value of 1 if not provided
    total_claims = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    # Allow empty description
    description = serializers.CharField(required=False, allow_blank=True)
    # Allow empty summary
    summary = serializers.CharField(required=False, allow_blank=True, max_length=500)

    class Meta:
        model = PropertyListing
        exclude = ['prospector', 'slug', 'views_count', 'inquiries_count',
                  'watchlist_count', 'published_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Generate slug from title
        from django.utils.text import slugify
        import uuid
        base_slug = slugify(validated_data.get('title', 'property'))
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        validated_data['slug'] = unique_slug

        # Set default for total_claims if null or not provided
        if validated_data.get('total_claims') is None:
            validated_data['total_claims'] = 1

        return super().create(validated_data)




class PropertyInquirySerializer(serializers.ModelSerializer):
    """Serializer for property inquiries"""
    inquirer_name = serializers.CharField(source='inquirer.username', read_only=True)
    inquirer_email = serializers.EmailField(source='inquirer.email', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_slug = serializers.SlugField(source='listing.slug', read_only=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PropertyInquiry
        fields = [
            'id', 'listing', 'listing_title', 'listing_slug',
            'inquirer', 'inquirer_name', 'inquirer_email',
            'inquiry_type', 'inquiry_type_display', 'subject', 'message',
            'contact_preference', 'phone_number',
            'status', 'status_display', 'response', 'responded_at',
            'is_nda_signed', 'nda_signed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'inquirer', 'status', 'response', 'responded_at',
                          'created_at', 'updated_at']




class PropertyInquiryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new inquiries"""

    class Meta:
        model = PropertyInquiry
        fields = ['listing', 'inquiry_type', 'subject', 'message', 'contact_preference', 'phone_number']




class PropertyInquiryResponseSerializer(serializers.Serializer):
    """Serializer for responding to inquiries"""
    response = serializers.CharField()




class PropertyWatchlistSerializer(serializers.ModelSerializer):
    """Serializer for watchlist items"""
    listing = PropertyListingListSerializer(read_only=True)

    class Meta:
        model = PropertyWatchlist
        fields = ['id', 'listing', 'notes', 'price_alert', 'added_at']
        read_only_fields = ['id', 'added_at']




class PropertyWatchlistCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding to watchlist"""

    class Meta:
        model = PropertyWatchlist
        fields = ['listing', 'notes', 'price_alert']




class SavedPropertySearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches"""

    class Meta:
        model = SavedPropertySearch
        fields = [
            'id', 'name', 'search_criteria', 'email_alerts',
            'alert_frequency', 'created_at', 'last_alerted_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_alerted_at']




# Choice list serializers for frontend dropdowns
class PropertyChoicesSerializer(serializers.Serializer):
    """Returns all choice options for property forms"""
    property_types = serializers.SerializerMethodField()
    mineral_types = serializers.SerializerMethodField()
    mineral_rights_types = serializers.SerializerMethodField()
    deposit_types = serializers.SerializerMethodField()
    exploration_stages = serializers.SerializerMethodField()
    listing_types = serializers.SerializerMethodField()
    access_types = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    canadian_provinces = serializers.SerializerMethodField()

    def get_property_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.PROPERTY_TYPES]

    def get_mineral_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.MINERAL_TYPES]

    def get_mineral_rights_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.MINERAL_RIGHTS_TYPES]

    def get_deposit_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.DEPOSIT_TYPES]

    def get_exploration_stages(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.EXPLORATION_STAGES]

    def get_listing_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.LISTING_TYPES]

    def get_access_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.ACCESS_TYPES]

    def get_countries(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.COUNTRIES]

    def get_canadian_provinces(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.CANADIAN_PROVINCES]




# ============================================================================
# INQUIRY MESSAGE SERIALIZERS (Conversation Thread)
# ============================================================================

class InquiryMessageSerializer(serializers.ModelSerializer):
    """Serializer for inquiry conversation messages"""
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    is_from_prospector = serializers.SerializerMethodField()

    class Meta:
        model = InquiryMessage
        fields = [
            'id', 'inquiry', 'sender', 'sender_name', 'sender_email',
            'message', 'is_read', 'is_from_prospector', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

    def get_is_from_prospector(self, obj):
        """Check if message is from the property owner (prospector)"""
        return obj.sender == obj.inquiry.listing.prospector.user




class InquiryMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new inquiry messages"""

    class Meta:
        model = InquiryMessage
        fields = ['message']

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()




class PropertyInquiryWithMessagesSerializer(serializers.ModelSerializer):
    """Serializer for inquiry detail with full conversation thread"""
    inquirer_name = serializers.CharField(source='inquirer.username', read_only=True)
    inquirer_email = serializers.EmailField(source='inquirer.email', read_only=True)
    inquirer_full_name = serializers.SerializerMethodField()
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_slug = serializers.SlugField(source='listing.slug', read_only=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    messages = InquiryMessageSerializer(many=True, read_only=True)
    prospector_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = PropertyInquiry
        fields = [
            'id', 'listing', 'listing_title', 'listing_slug',
            'inquirer', 'inquirer_name', 'inquirer_email', 'inquirer_full_name',
            'inquiry_type', 'inquiry_type_display', 'subject', 'message',
            'contact_preference', 'phone_number',
            'status', 'status_display', 'response', 'responded_at',
            'is_nda_signed', 'nda_signed_at',
            'messages', 'prospector_name', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'inquirer', 'status', 'response', 'responded_at',
                          'created_at', 'updated_at']

    def get_inquirer_full_name(self, obj):
        return obj.inquirer.get_full_name() or obj.inquirer.username

    def get_prospector_name(self, obj):
        return obj.listing.prospector.display_name or obj.listing.prospector.user.username

    def get_unread_count(self, obj):
        """Count unread messages for the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

