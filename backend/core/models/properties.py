from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .users import User, Company
from .mining import Project




# ============================================================================
# PROSPECTOR PROPERTY EXCHANGE MODELS
# ============================================================================

class ProspectorProfile(models.Model):
    """Extended profile for prospectors listing properties"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='prospector_profile')
    display_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, help_text="Optional company/business name")
    bio = models.TextField(blank=True)
    years_experience = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    specializations = models.JSONField(default=list, blank=True, help_text="List of mineral specializations")
    regions_active = models.JSONField(default=list, blank=True, help_text="List of active regions")
    certifications = models.JSONField(default=list, blank=True, help_text="List of certifications [{name, issuer, year}]")
    website_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    # Profile media
    profile_image_url = models.URLField(blank=True)

    # Denormalized stats
    total_listings = models.IntegerField(default=0)
    active_listings = models.IntegerField(default=0)
    successful_transactions = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))

    # Commission Agreement - 5% on successful transactions
    commission_agreement_accepted = models.BooleanField(default=False)
    commission_agreement_date = models.DateTimeField(null=True, blank=True)
    commission_agreement_ip = models.GenericIPAddressField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prospector_profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.display_name} ({self.user.username})"

    @property
    def can_list_properties(self):
        """Check if prospector has accepted commission agreement"""
        return self.commission_agreement_accepted




class ProspectorCommissionAgreement(models.Model):
    """
    Legal record of prospector commission agreement.
    GoldVenture receives 5% commission on any successful transaction
    resulting from property listings on the platform.
    """
    AGREEMENT_VERSION = '1.0'
    COMMISSION_RATE = Decimal('5.00')  # 5%

    prospector = models.ForeignKey(ProspectorProfile, on_delete=models.CASCADE, related_name='commission_agreements')

    # Agreement details
    version = models.CharField(max_length=10, default=AGREEMENT_VERSION)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=COMMISSION_RATE)

    # Legal acceptance
    full_legal_name = models.CharField(max_length=300, help_text="Full legal name as signature")
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Agreement text at time of signing (for legal record)
    agreement_text = models.TextField()

    # Status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'prospector_commission_agreements'
        ordering = ['-accepted_at']

    def __str__(self):
        return f"Commission Agreement - {self.prospector.display_name} ({self.accepted_at.strftime('%Y-%m-%d')})"

    @classmethod
    def get_agreement_text(cls):
        """Return the current commission agreement text"""
        return """
GOLDVENTURE PROSPECTOR COMMISSION AGREEMENT

Version: 1.0
Effective Date: Upon Acceptance

1. PARTIES
This Commission Agreement ("Agreement") is entered into between:
- GoldVenture Platform ("GoldVenture", "we", "us")
- The undersigned Prospector ("You", "Prospector")

2. FREE LISTING SERVICE
GoldVenture provides a FREE property listing service that allows Prospectors to:
- List unlimited mining properties at no upfront cost
- Access our network of investors and mining companies
- Receive inquiries and negotiate directly with interested parties

3. COMMISSION STRUCTURE
In consideration for the free listing service, You agree to pay GoldVenture a commission of:

    FIVE PERCENT (5%) of the total transaction value

This commission applies to any successful transaction resulting from contacts made through the GoldVenture platform, including but not limited to:
- Property sales
- Option agreements
- Joint venture partnerships
- Lease agreements
- Any other transfer of rights or interests

4. PAYMENT TERMS
- Commission is due within 30 days of transaction closing
- Payment shall be made via wire transfer or certified check
- Failure to pay may result in legal action and platform suspension

5. REPORTING OBLIGATIONS
You agree to:
- Notify GoldVenture within 5 business days of any transaction closing
- Provide documentation of transaction value upon request
- Maintain accurate records for a minimum of 7 years

6. TERM AND TERMINATION
- This Agreement remains in effect for 24 months after your last active listing
- Commission obligations survive termination for any transactions initiated during the active period
- GoldVenture may terminate this Agreement for violation of platform terms

7. GOVERNING LAW
This Agreement shall be governed by the laws of British Columbia, Canada.

8. ELECTRONIC SIGNATURE
By accepting this Agreement electronically, You acknowledge that:
- Your electronic signature is legally binding
- You have read and understood all terms
- You have the authority to enter into this Agreement

By typing your full legal name below, you agree to all terms of this Commission Agreement.
"""




class PropertyListing(models.Model):
    """Mining property listings for sale/option/JV/lease"""

    # Property Types
    PROPERTY_TYPES = [
        ('claim', 'Mineral Claim'),
        ('lease', 'Mining Lease'),
        ('fee_simple', 'Fee Simple'),
        ('option', 'Option Agreement'),
        ('permit', 'Exploration Permit'),
    ]

    # Mineral Types
    MINERAL_TYPES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('copper', 'Copper'),
        ('zinc', 'Zinc'),
        ('lead', 'Lead'),
        ('nickel', 'Nickel'),
        ('cobalt', 'Cobalt'),
        ('lithium', 'Lithium'),
        ('uranium', 'Uranium'),
        ('rare_earth', 'Rare Earth Elements'),
        ('platinum', 'Platinum Group'),
        ('diamonds', 'Diamonds'),
        ('iron', 'Iron'),
        ('molybdenum', 'Molybdenum'),
        ('tungsten', 'Tungsten'),
        ('tin', 'Tin'),
        ('other', 'Other'),
    ]

    # Mineral Rights Types
    MINERAL_RIGHTS_TYPES = [
        ('placer', 'Placer'),
        ('lode', 'Lode/Hardrock'),
        ('both', 'Both Placer & Lode'),
    ]

    # Deposit Types
    DEPOSIT_TYPES = [
        ('vein', 'Vein/Lode'),
        ('placer', 'Placer'),
        ('porphyry', 'Porphyry'),
        ('vms', 'VMS (Volcanogenic Massive Sulfide)'),
        ('sedex', 'SEDEX'),
        ('skarn', 'Skarn'),
        ('epithermal', 'Epithermal'),
        ('orogenic', 'Orogenic'),
        ('iocg', 'IOCG'),
        ('mvt', 'MVT'),
        ('laterite', 'Laterite'),
        ('bif', 'BIF (Banded Iron Formation)'),
        ('carlin', 'Carlin-type'),
        ('intrusion', 'Intrusion-related'),
        ('other', 'Other'),
    ]

    # Exploration Stages
    EXPLORATION_STAGES = [
        ('grassroots', 'Grassroots'),
        ('early', 'Early Stage'),
        ('advanced', 'Advanced'),
        ('development', 'Development Ready'),
        ('past_producer', 'Past Producer'),
    ]

    # Listing Types
    LISTING_TYPES = [
        ('sale', 'Outright Sale'),
        ('option', 'Option to Purchase'),
        ('joint_venture', 'Joint Venture'),
        ('lease', 'Lease'),
    ]

    # Listing Status
    LISTING_STATUS = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('active', 'Active'),
        ('under_offer', 'Under Offer'),
        ('sold', 'Sold'),
        ('withdrawn', 'Withdrawn'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]

    # Access Types
    ACCESS_TYPES = [
        ('road', 'Road Accessible'),
        ('fly_in', 'Fly-in Only'),
        ('boat', 'Boat Access'),
        ('combination', 'Combination'),
        ('seasonal', 'Seasonal Access'),
    ]

    # Countries with significant mining
    COUNTRIES = [
        ('CA', 'Canada'),
        ('US', 'United States'),
        ('AU', 'Australia'),
        ('MX', 'Mexico'),
        ('PE', 'Peru'),
        ('CL', 'Chile'),
        ('AR', 'Argentina'),
        ('BR', 'Brazil'),
        ('CO', 'Colombia'),
        ('ZA', 'South Africa'),
        ('GH', 'Ghana'),
        ('ML', 'Mali'),
        ('BF', 'Burkina Faso'),
        ('CD', 'DRC'),
        ('ZM', 'Zambia'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('CN', 'China'),
        ('MN', 'Mongolia'),
        ('OTHER', 'Other'),
    ]

    # Canadian Provinces
    CANADIAN_PROVINCES = [
        ('BC', 'British Columbia'),
        ('AB', 'Alberta'),
        ('SK', 'Saskatchewan'),
        ('MB', 'Manitoba'),
        ('ON', 'Ontario'),
        ('QC', 'Quebec'),
        ('NB', 'New Brunswick'),
        ('NS', 'Nova Scotia'),
        ('NL', 'Newfoundland and Labrador'),
        ('PE', 'Prince Edward Island'),
        ('YT', 'Yukon'),
        ('NT', 'Northwest Territories'),
        ('NU', 'Nunavut'),
    ]

    # Ownership & Identification
    prospector = models.ForeignKey(ProspectorProfile, on_delete=models.CASCADE, related_name='listings')
    slug = models.SlugField(max_length=255, unique=True)

    # Basic Information
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500, blank=True, help_text="Brief summary for search results")
    description = models.TextField(blank=True, help_text="Full property description")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)

    # Location
    country = models.CharField(max_length=5, choices=COUNTRIES)
    province_state = models.CharField(max_length=100)
    region_district = models.CharField(max_length=200, blank=True)
    nearest_town = models.CharField(max_length=200, blank=True)
    coordinates_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    coordinates_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    access_description = models.TextField(blank=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES, blank=True)

    # Claim Details
    claim_numbers = models.JSONField(default=list, help_text="List of claim numbers")
    total_claims = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    total_hectares = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_acres = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, editable=False)
    mineral_rights_type = models.CharField(max_length=20, choices=MINERAL_RIGHTS_TYPES, blank=True)
    surface_rights_included = models.BooleanField(default=False)
    claim_status = models.CharField(max_length=50, blank=True, help_text="active, pending renewal, etc")
    claim_expiry_date = models.DateField(null=True, blank=True)
    annual_holding_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Minerals & Geology
    primary_mineral = models.CharField(max_length=30, choices=MINERAL_TYPES)
    secondary_minerals = models.JSONField(default=list, blank=True, help_text="List of secondary minerals")
    deposit_type = models.CharField(max_length=30, choices=DEPOSIT_TYPES, blank=True)
    geological_setting = models.TextField(blank=True)
    mineralization_style = models.TextField(blank=True)  # Changed from CharField to TextField to allow longer descriptions

    # Exploration Status
    exploration_stage = models.CharField(max_length=20, choices=EXPLORATION_STAGES)
    work_completed = models.JSONField(default=list, blank=True, help_text="List of work completed [{type, date, summary}]")
    historical_production = models.TextField(blank=True)
    assay_highlights = models.JSONField(default=list, blank=True, help_text="Best assay results [{sample_id, mineral, grade, unit}]")
    resource_estimate = models.TextField(blank=True)
    has_43_101_report = models.BooleanField(default=False)

    # Transaction Terms
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    asking_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    price_currency = models.CharField(max_length=3, default='CAD')
    price_negotiable = models.BooleanField(default=True)
    minimum_offer = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    option_terms = models.TextField(blank=True)
    joint_venture_terms = models.TextField(blank=True)
    lease_terms = models.TextField(blank=True)
    nsr_royalty = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="NSR royalty percentage to retain")
    includes_equipment = models.BooleanField(default=False)
    equipment_description = models.TextField(blank=True)
    additional_terms = models.TextField(blank=True)

    # Status & Visibility
    status = models.CharField(max_length=20, choices=LISTING_STATUS, default='draft')
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(null=True, blank=True)

    # Engagement Metrics (denormalized)
    views_count = models.IntegerField(default=0)
    inquiries_count = models.IntegerField(default=0)
    watchlist_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'property_listings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['country', 'province_state']),
            models.Index(fields=['primary_mineral', 'status']),
            models.Index(fields=['exploration_stage', 'status']),
            models.Index(fields=['listing_type', 'status']),
            models.Index(fields=['prospector', '-created_at']),
            models.Index(fields=['-views_count']),
            models.Index(fields=['is_featured', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_primary_mineral_display()})"

    def save(self, *args, **kwargs):
        # Auto-calculate acres from hectares
        if self.total_hectares:
            self.total_acres = self.total_hectares * Decimal('2.47105')
        super().save(*args, **kwargs)




class PropertyMedia(models.Model):
    """Media files associated with property listings"""

    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('map', 'Map'),
    ]

    MEDIA_CATEGORIES = [
        ('hero', 'Hero Image'),
        ('gallery', 'Gallery'),
        ('geological_map', 'Geological Map'),
        ('claim_map', 'Claim Map'),
        ('location_map', 'Location Map'),
        ('assay', 'Assay Certificate'),
        ('report', 'Technical Report'),
        ('permit', 'Permit/License'),
        ('other', 'Other'),
    ]

    listing = models.ForeignKey(PropertyListing, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    category = models.CharField(max_length=30, choices=MEDIA_CATEGORIES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    file_format = models.CharField(max_length=20, blank=True)
    sort_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False, help_text="Primary/hero image for the listing")

    # Audit
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'property_media'
        ordering = ['sort_order', '-uploaded_at']
        indexes = [
            models.Index(fields=['listing', 'media_type']),
            models.Index(fields=['listing', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.listing.title} - {self.title}"




class PropertyInquiry(models.Model):
    """Inquiries from potential buyers to property sellers"""

    INQUIRY_TYPES = [
        ('general', 'General Information'),
        ('site_visit', 'Site Visit Request'),
        ('offer', 'Making an Offer'),
        ('documents', 'Document Request'),
        ('technical', 'Technical Questions'),
    ]

    INQUIRY_STATUS = [
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]

    CONTACT_PREFERENCES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('either', 'Either'),
    ]

    listing = models.ForeignKey(PropertyListing, on_delete=models.CASCADE, related_name='inquiries')
    inquirer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_inquiries')
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPES)
    subject = models.CharField(max_length=255, blank=True)  # Optional subject line
    message = models.TextField()
    contact_preference = models.CharField(max_length=10, choices=CONTACT_PREFERENCES, default='email')
    phone_number = models.CharField(max_length=20, blank=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=INQUIRY_STATUS, default='new')
    response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    # NDA tracking
    is_nda_signed = models.BooleanField(default=False)
    nda_signed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'property_inquiries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'status']),
            models.Index(fields=['inquirer', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Inquiry on {self.listing.title} by {self.inquirer.username}"




class InquiryMessage(models.Model):
    """Messages within an inquiry conversation thread"""

    inquiry = models.ForeignKey(PropertyInquiry, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiry_messages_sent')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inquiry_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['inquiry', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} on inquiry {self.inquiry.id}"




class PropertyWatchlist(models.Model):
    """User watchlist for property listings"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_watchlist')
    listing = models.ForeignKey(PropertyListing, on_delete=models.CASCADE, related_name='watchlisted_by')
    notes = models.TextField(blank=True, help_text="Personal notes about this listing")
    price_alert = models.BooleanField(default=False, help_text="Alert on price changes")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_watchlist'
        unique_together = ['user', 'listing']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} watching {self.listing.title}"




class SavedPropertySearch(models.Model):
    """Saved search criteria for property alerts"""

    ALERT_FREQUENCIES = [
        ('instant', 'Instant'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_property_searches')
    name = models.CharField(max_length=200)
    search_criteria = models.JSONField(help_text="Search filter parameters")
    email_alerts = models.BooleanField(default=True)
    alert_frequency = models.CharField(max_length=10, choices=ALERT_FREQUENCIES, default='daily')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_alerted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'saved_property_searches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"




class FeaturedPropertyConfig(models.Model):
    """
    Configuration for featured property on the homepage.
    Only one active record should exist at a time.
    """
    listing = models.ForeignKey(
        PropertyListing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_config'
    )
    is_manual_selection = models.BooleanField(
        default=False,
        help_text="True if manually selected by admin, False for auto-rotation"
    )
    selected_at = models.DateTimeField(auto_now=True)
    selected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_property_selections'
    )
    next_auto_rotation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the next automatic rotation will occur"
    )

    class Meta:
        db_table = 'featured_property_config'
        verbose_name = 'Featured Property Configuration'
        verbose_name_plural = 'Featured Property Configuration'

    def __str__(self):
        if self.listing:
            return f"Featured: {self.listing.title}"
        return "No featured property"

    @classmethod
    def get_current_featured(cls):
        """Get the current featured property configuration"""
        config = cls.objects.first()
        if not config:
            config = cls.objects.create()
        return config

    @classmethod
    def rotate_featured_property(cls):
        """Automatically rotate to a new random property"""
        from django.utils import timezone
        from random import choice

        config = cls.get_current_featured()

        # Get all active listings except current one
        active_listings = PropertyListing.objects.filter(status='active')
        if config.listing:
            active_listings = active_listings.exclude(id=config.listing.id)

        if active_listings.exists():
            new_listing = choice(list(active_listings))
            config.listing = new_listing
            config.is_manual_selection = False
            config.selected_by = None
            # Next rotation is next Monday at midnight
            now = timezone.now()
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = (now + timezone.timedelta(days=days_until_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            config.next_auto_rotation = next_monday
            config.save()

        return config


# ============================================================================
# NEWS ARTICLES MODELS
# ============================================================================




# ============================================================================
# COMPANY PORTAL MODELS (Resources, Events, Subscriptions)
# ============================================================================

class CompanyResource(models.Model):
    """Resources and documents uploaded by companies (similar to PropertyMedia)"""

    RESOURCE_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
        ('map', 'Map'),
    ]

    RESOURCE_CATEGORIES = [
        ('hero', 'Hero Image'),
        ('gallery', 'Gallery'),
        ('logo', 'Company Logo'),
        ('factsheet', 'Fact Sheet'),
        ('investor_presentation', 'Investor Presentation'),
        ('technical_report', 'Technical Report (NI 43-101)'),
        ('financial_report', 'Financial Report'),
        ('annual_report', 'Annual Report'),
        ('news_release', 'News Release'),
        ('map_geological', 'Geological Map'),
        ('map_location', 'Location Map'),
        ('map_claims', 'Claims Map'),
        ('drilling_results', 'Drilling Results'),
        ('assay_certificate', 'Assay Certificate'),
        ('permit', 'Permit/License'),
        ('corporate', 'Corporate Document'),
        ('video_corporate', 'Corporate Video'),
        ('video_site', 'Site Video'),
        ('other', 'Other'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    category = models.CharField(max_length=30, choices=RESOURCE_CATEGORIES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True, help_text="External link to resource")
    thumbnail_url = models.URLField(blank=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    file_format = models.CharField(max_length=20, blank=True)
    sort_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False, help_text="Primary/hero image for the company")
    is_public = models.BooleanField(default=True, help_text="Visible to all users or only subscribers")
    is_featured = models.BooleanField(default=False, help_text="Featured resource shown prominently")

    # Related project (optional - resource can be company-wide or project-specific)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='company_resources',
        help_text="If set, this resource is specific to this project"
    )

    # Audit
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_company_resources')

    class Meta:
        db_table = 'company_resources'
        ordering = ['sort_order', '-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'resource_type']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'is_primary']),
            models.Index(fields=['project', 'category']),
            models.Index(fields=['company', 'is_featured']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.title}"




class SpeakingEvent(models.Model):
    """Speaking events and conferences for companies"""

    EVENT_TYPES = [
        ('conference', 'Conference'),
        ('webinar', 'Webinar'),
        ('investor_day', 'Investor Day'),
        ('roadshow', 'Roadshow'),
        ('agm', 'Annual General Meeting'),
        ('site_visit', 'Site Visit'),
        ('panel', 'Panel Discussion'),
        ('presentation', 'Presentation'),
        ('interview', 'Interview'),
        ('podcast', 'Podcast'),
        ('other', 'Other'),
    ]

    EVENT_STATUS = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live Now'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='speaking_events')
    title = models.CharField(max_length=300)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField(blank=True)

    # Event details
    event_name = models.CharField(max_length=300, blank=True, help_text="Conference/event name if applicable")
    location = models.CharField(max_length=300, blank=True, help_text="Physical location or 'Virtual'")
    is_virtual = models.BooleanField(default=False)

    # Timing
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='America/Toronto')

    # Links
    registration_url = models.URLField(blank=True, help_text="Link to register for the event")
    livestream_url = models.URLField(blank=True, help_text="Link to watch live")
    recording_url = models.URLField(blank=True, help_text="Link to recording after event")
    presentation_url = models.URLField(blank=True, help_text="Link to presentation slides")

    # Speakers
    speakers = models.TextField(blank=True, help_text="Names and titles of company speakers")

    # Status
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='upcoming')
    is_featured = models.BooleanField(default=False)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_speaking_events')

    class Meta:
        db_table = 'speaking_events'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', '-start_datetime']),
            models.Index(fields=['status', '-start_datetime']),
            models.Index(fields=['is_featured', '-start_datetime']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.title}"




class CompanySubscription(models.Model):
    """Stripe subscription for company premium features"""

    SUBSCRIPTION_STATUS = [
        ('trialing', 'Trial Period'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('paused', 'Paused'),
    ]

    # Priced in core/company_stripe_service.py (COMPANY_PRICING), which is the
    # authority. These labels are for the Django admin dropdown only.
    PLAN_TYPES = [
        ('monthly', 'Monthly (CA$50/month)'),
        ('annual', 'Annual (CA$500/year)'),
    ]

    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')

    # Stripe identifiers
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(max_length=255, blank=True)

    # Subscription details
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='monthly')
    status = models.CharField(max_length=30, choices=SUBSCRIPTION_STATUS, default='trialing')
    price_cents = models.IntegerField(default=5000, help_text="Price in cents (5000 = CA$50)")

    # Trial period
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    # Billing period
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    # Cancellation
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)

    # Features enabled (can be extended for tiered plans)
    features = models.JSONField(default=dict, blank=True, help_text="Enabled features for this subscription")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_subscriptions'
        indexes = [
            models.Index(fields=['stripe_customer_id']),
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.get_status_display()}"

    @property
    def is_active(self):
        """Check if subscription is active (includes trial)"""
        return self.status in ['trialing', 'active']

    @property
    def can_access_premium(self):
        """Check if company can access premium features"""
        return self.is_active




class SubscriptionInvoice(models.Model):
    """Track Stripe invoices for subscriptions"""

    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('uncollectible', 'Uncollectible'),
    ]

    subscription = models.ForeignKey(
        CompanySubscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )

    # Stripe identifiers
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    # Invoice details
    status = models.CharField(max_length=20, choices=INVOICE_STATUS)
    amount_cents = models.IntegerField(help_text="Amount in cents")
    currency = models.CharField(max_length=3, default='usd')

    # Dates
    invoice_date = models.DateTimeField()
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # PDF
    invoice_pdf_url = models.URLField(blank=True)
    hosted_invoice_url = models.URLField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscription_invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['stripe_invoice_id']),
            models.Index(fields=['subscription', '-invoice_date']),
        ]

    def __str__(self):
        return f"{self.subscription.company.name} - ${self.amount_cents/100:.2f} ({self.status})"




class CompanyAccessRequest(models.Model):
    """
    Track requests from users to be associated with a company.
    Used for Company Portal onboarding.
    """

    REQUEST_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    ROLE_CHOICES = [
        ('ir_manager', 'IR Manager'),
        ('ceo', 'CEO'),
        ('cfo', 'CFO'),
        ('marketing', 'Marketing'),
        ('communications', 'Communications'),
        ('other', 'Other'),
    ]

    # The user requesting access
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='company_access_requests'
    )

    # The company they want to be associated with
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='access_requests'
    )

    # Request details
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='other')
    job_title = models.CharField(max_length=200)
    justification = models.TextField(
        help_text="Why the user should be granted access to this company"
    )
    work_email = models.EmailField(
        help_text="Work email for verification (should match company domain)"
    )

    # Admin response
    reviewer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_access_requests'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_access_requests'
        ordering = ['-created_at']
        # Prevent duplicate pending requests
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'company'],
                condition=models.Q(status='pending'),
                name='unique_pending_request_per_user_company'
            )
        ]
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['company', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.company.name} ({self.status})"

    def approve(self, reviewer, notes=''):
        """Approve the request and associate user with company"""
        from django.utils import timezone

        self.status = 'approved'
        self.reviewer = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

        # Associate user with company
        self.user.company = self.company
        self.user.user_type = 'company'
        self.user.save()

    def reject(self, reviewer, notes=''):
        """Reject the request"""
        from django.utils import timezone

        self.status = 'rejected'
        self.reviewer = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()


# ============================================================================
# INVESTMENT INTEREST REGISTRATION
# ============================================================================

