"""
Django Models for Junior Gold Mining Investor Relations Platform
Designed for tracking projects, investors, financings, and market intelligence
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


# ============================================================================
# CORE USER & COMPANY MODELS
# ============================================================================

class User(AbstractUser):
    """Extended user model with role-based access"""
    USER_TYPES = [
        ('admin', 'Platform Admin'),
        ('company', 'Company Representative'),
        ('investor', 'Investor'),
        ('analyst', 'Analyst'),
        ('mining_company', 'Mining Company'),
        ('prospector', 'Prospector'),
        ('student', 'Student'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='investor')
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'


class Company(models.Model):
    """Junior mining companies"""
    COMPANY_STATUS = [
        ('private', 'Private'),
        ('public', 'Public - Listed'),
        ('public_cpc', 'CPC/SPAC'),
        ('subsidiary', 'Subsidiary'),
    ]

    EXCHANGE_CHOICES = [
        ('tsx', 'TSX'),
        ('tsxv', 'TSX Venture'),
        ('cse', 'CSE'),
        ('otc', 'OTC'),
        ('asx', 'ASX'),
        ('aim', 'AIM London'),
        ('other', 'Other'),
    ]

    APPROVAL_STATUS = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]

    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    ticker_symbol = models.CharField(max_length=10, blank=True)
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=COMPANY_STATUS)

    # Corporate info
    incorporation_date = models.DateField(null=True, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    headquarters_city = models.CharField(max_length=100, blank=True)
    headquarters_country = models.CharField(max_length=100, blank=True)

    # Key contacts
    ceo_name = models.CharField(max_length=200, blank=True)
    cfo_name = models.CharField(max_length=200, blank=True)
    ir_contact_name = models.CharField(max_length=200, blank=True)
    ir_contact_email = models.EmailField(blank=True)
    ir_contact_phone = models.CharField(max_length=20, blank=True)

    # Market data
    market_cap_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    shares_outstanding = models.BigIntegerField(null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Meta
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Auto-population fields
    tagline = models.CharField(max_length=500, blank=True, help_text="Company tagline or slogan")
    logo_file = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    source_website_url = models.URLField(blank=True, help_text="Original website URL used for scraping")
    auto_populated = models.BooleanField(default=False, help_text="Was this company auto-populated via scraping?")
    last_scraped_at = models.DateTimeField(null=True, blank=True, help_text="Last time data was scraped")
    data_completeness_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100 score indicating data completeness"
    )
    requires_manual_review = models.BooleanField(default=False, help_text="Flagged for manual review")

    # Additional contact fields
    general_email = models.EmailField(blank=True)
    media_email = models.EmailField(blank=True)
    general_phone = models.CharField(max_length=30, blank=True)

    # Social media
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Address
    street_address = models.CharField(max_length=300, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # User submission fields
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='approved',
        help_text="Approval status for user-submitted companies"
    )
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True, help_text="Main contact email for user-submitted companies")
    brief_description = models.CharField(max_length=500, blank=True, help_text="Brief company description")
    presentation = models.TextField(blank=True, help_text="Company presentation text for user submissions")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if status is rejected")
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_companies',
        help_text="User who submitted this company"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_companies',
        help_text="Admin who reviewed this company"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When the company was reviewed")
    is_user_submitted = models.BooleanField(default=False, help_text="Was this company submitted by a user?")

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.ticker_symbol})" if self.ticker_symbol else self.name

    def calculate_completeness_score(self):
        """Calculate data completeness score based on filled fields"""
        fields_weights = {
            'name': 10,
            'ticker_symbol': 8,
            'exchange': 5,
            'website': 8,
            'description': 10,
            'ceo_name': 5,
            'ir_contact_email': 5,
            'headquarters_city': 3,
            'headquarters_country': 3,
            'logo_url': 5,
            'market_cap_usd': 5,
            'shares_outstanding': 5,
            'linkedin_url': 3,
            'twitter_url': 2,
        }
        # Check projects exist
        has_projects = self.projects.exists() if self.pk else False

        score = 0
        total_weight = sum(fields_weights.values()) + 13  # +13 for projects

        for field, weight in fields_weights.items():
            value = getattr(self, field, None)
            if value:
                score += weight

        if has_projects:
            score += 13

        self.data_completeness_score = int((score / total_weight) * 100)
        return self.data_completeness_score


# ============================================================================
# MINING PROJECT MODELS
# ============================================================================

class Project(models.Model):
    """Mining projects - can be multiple per company"""
    PROJECT_STAGES = [
        ('grassroots', 'Grassroots Exploration'),
        ('early_exploration', 'Early Stage Exploration'),
        ('advanced_exploration', 'Advanced Exploration'),
        ('resource', 'Resource Stage'),
        ('pea', 'PEA Completed'),
        ('pfs', 'PFS Completed'),
        ('fs', 'Feasibility Study'),
        ('permitting', 'Permitting'),
        ('development', 'Development'),
        ('production', 'Production'),
        ('care_maintenance', 'Care & Maintenance'),
        ('closed', 'Closed'),
    ]

    COMMODITY_TYPES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('copper', 'Copper'),
        ('multi_metal', 'Multi-Metal'),
        ('other', 'Other'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    project_stage = models.CharField(max_length=30, choices=PROJECT_STAGES)
    primary_commodity = models.CharField(max_length=20, choices=COMMODITY_TYPES)

    # Location
    country = models.CharField(max_length=100)
    province_state = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Project details
    description = models.TextField(blank=True)
    ownership_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100.00
    )

    # Key dates
    acquisition_date = models.DateField(null=True, blank=True)
    last_drill_program = models.DateField(null=True, blank=True)

    # Meta
    is_flagship = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-is_flagship', 'name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"


class ResourceEstimate(models.Model):
    """NI 43-101 or JORC compliant resource estimates"""
    RESOURCE_CATEGORIES = [
        ('inferred', 'Inferred'),
        ('indicated', 'Indicated'),
        ('measured', 'Measured'),
        ('mni', 'Measured & Indicated'),
        ('proven', 'Proven (Reserve)'),
        ('probable', 'Probable (Reserve)'),
    ]

    STANDARDS = [
        ('ni43101', 'NI 43-101'),
        ('jorc', 'JORC'),
        ('samrec', 'SAMREC'),
        ('other', 'Other'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='resources')
    category = models.CharField(max_length=20, choices=RESOURCE_CATEGORIES)
    standard = models.CharField(max_length=20, choices=STANDARDS, default='ni43101')

    # Resource quantities
    tonnes = models.DecimalField(max_digits=15, decimal_places=2)
    gold_grade_gpt = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    gold_ounces = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    silver_grade_gpt = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    silver_ounces = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    copper_grade_pct = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    # Report details
    report_date = models.DateField()
    cutoff_grade = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    effective_date = models.DateField()
    qualified_person = models.CharField(max_length=200, blank=True)
    report_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resource_estimates'
        ordering = ['-report_date']


class EconomicStudy(models.Model):
    """PEA, PFS, Feasibility Studies"""
    STUDY_TYPES = [
        ('pea', 'Preliminary Economic Assessment'),
        ('pfs', 'Pre-Feasibility Study'),
        ('fs', 'Feasibility Study'),
        ('updated_fs', 'Updated Feasibility Study'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='economic_studies')
    study_type = models.CharField(max_length=20, choices=STUDY_TYPES)
    release_date = models.DateField()

    # Economics
    npv_5_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                     help_text="NPV at 5% discount rate (USD millions)")
    irr_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    payback_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Production
    annual_production_oz = models.IntegerField(null=True, blank=True, help_text="Annual gold production (oz)")
    mine_life_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Costs
    aisc_per_oz = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                       help_text="All-in Sustaining Cost (USD/oz)")
    initial_capex_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                            help_text="Initial CAPEX (USD millions)")

    # Assumptions
    gold_price_assumption = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    exchange_rate_assumption = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # Documents
    report_url = models.URLField(blank=True)
    qualified_person = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'economic_studies'
        ordering = ['-release_date']


# ============================================================================
# FINANCING & INVESTOR RELATIONS
# ============================================================================

class Financing(models.Model):
    """Capital raises, private placements, bought deals"""
    FINANCING_TYPES = [
        ('private_placement', 'Private Placement'),
        ('bought_deal', 'Bought Deal'),
        ('rights_offering', 'Rights Offering'),
        ('flow_through', 'Flow-Through Shares'),
        ('warrant_exercise', 'Warrant Exercise'),
        ('debt', 'Debt Financing'),
        ('royalty_stream', 'Royalty/Stream'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('announced', 'Announced'),
        ('closing', 'Closing'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financings')
    financing_type = models.CharField(max_length=30, choices=FINANCING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Terms
    announced_date = models.DateField()
    closing_date = models.DateField(null=True, blank=True)
    amount_raised_usd = models.DecimalField(max_digits=15, decimal_places=2)
    price_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    shares_issued = models.BigIntegerField(null=True, blank=True)

    # Warrants (if applicable)
    has_warrants = models.BooleanField(default=False)
    warrant_strike_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    warrant_expiry_date = models.DateField(null=True, blank=True)

    # Use of proceeds
    use_of_proceeds = models.TextField(blank=True)

    # Lead agents/brokers
    lead_agent = models.CharField(max_length=200, blank=True)

    # Documents
    press_release_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financings'
        ordering = ['-announced_date']


class Investor(models.Model):
    """Individual and institutional investors"""
    INVESTOR_TYPES = [
        ('individual_retail', 'Retail Investor'),
        ('individual_hnw', 'High Net Worth Individual'),
        ('family_office', 'Family Office'),
        ('fund_pe', 'Private Equity Fund'),
        ('fund_hedge', 'Hedge Fund'),
        ('fund_mutual', 'Mutual Fund'),
        ('institution', 'Institution'),
        ('strategic', 'Strategic Investor'),
        ('insider', 'Insider/Management'),
    ]

    investor_type = models.CharField(max_length=30, choices=INVESTOR_TYPES)

    # Individual info
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    # Company/Fund info
    company_name = models.CharField(max_length=200, blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)

    # Location
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Investment profile
    focus_regions = models.JSONField(default=list, blank=True)
    focus_commodities = models.JSONField(default=list, blank=True)
    preferred_project_stages = models.JSONField(default=list, blank=True)
    typical_check_size_min_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    typical_check_size_max_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Relationship
    relationship_strength = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text="1=Cold, 5=Strong relationship"
    )
    notes = models.TextField(blank=True)

    # Tags for segmentation
    tags = models.JSONField(default=list, blank=True)

    # User account (if registered on platform)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investors'
        ordering = ['company_name', 'last_name']

    def __str__(self):
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}"


class InvestorPosition(models.Model):
    """Track investor positions in companies"""
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='positions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='investor_positions')

    shares_held = models.BigIntegerField()
    percentage_ownership = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    # Position details
    average_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    position_date = models.DateField(help_text="Date of last update")

    # Source
    source = models.CharField(max_length=100, blank=True, help_text="e.g., SEDI, self-reported")
    is_insider = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investor_positions'
        unique_together = ['investor', 'company']


# ============================================================================
# MARKET DATA & INTELLIGENCE
# ============================================================================

class MarketData(models.Model):
    """Daily market data for companies"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='market_data')
    date = models.DateField()

    # Price data
    open_price = models.DecimalField(max_digits=10, decimal_places=4)
    high_price = models.DecimalField(max_digits=10, decimal_places=4)
    low_price = models.DecimalField(max_digits=10, decimal_places=4)
    close_price = models.DecimalField(max_digits=10, decimal_places=4)
    volume = models.BigIntegerField()

    # Calculated
    market_cap_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data'
        unique_together = ['company', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', '-date']),
        ]


class CommodityPrice(models.Model):
    """Gold, silver, copper prices"""
    COMMODITIES = [
        ('gold', 'Gold (USD/oz)'),
        ('silver', 'Silver (USD/oz)'),
        ('copper', 'Copper (USD/lb)'),
    ]

    commodity = models.CharField(max_length=20, choices=COMMODITIES)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'commodity_prices'
        unique_together = ['commodity', 'date']
        ordering = ['-date']


# ============================================================================
# COMMUNICATIONS & DOCUMENTS
# ============================================================================

class NewsRelease(models.Model):
    """Press releases and news"""
    RELEASE_TYPES = [
        ('drill_results', 'Drill Results'),
        ('financing', 'Financing Announcement'),
        ('resource_update', 'Resource Update'),
        ('study_results', 'Study Results'),
        ('corporate', 'Corporate Update'),
        ('acquisition', 'Acquisition/Disposition'),
        ('management', 'Management Change'),
        ('other', 'Other'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='news_releases')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=500)
    release_type = models.CharField(max_length=30, choices=RELEASE_TYPES)
    release_date = models.DateField()

    summary = models.TextField(blank=True)
    full_text = models.TextField(blank=True)
    url = models.URLField(blank=True)

    # Impact tracking
    is_material = models.BooleanField(default=False, help_text="Material news event")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'news_releases'
        ordering = ['-release_date']


class Document(models.Model):
    """Technical reports, presentations, financial statements"""
    DOCUMENT_TYPES = [
        ('ni43101', 'NI 43-101 Technical Report'),
        ('presentation', 'Corporate Presentation'),
        ('financial_stmt', 'Financial Statements'),
        ('mda', 'MD&A'),
        ('annual_report', 'Annual Report'),
        ('factsheet', 'Fact Sheet'),
        ('map', 'Project Map'),
        ('other', 'Other'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='documents')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=300)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_date = models.DateField()

    file_url = models.URLField()
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    description = models.TextField(blank=True)

    # Access control
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-document_date']


class DocumentChunk(models.Model):
    """Chunks of document text for RAG/semantic search. Embeddings stored in ChromaDB."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')

    # Chunk metadata
    chunk_index = models.IntegerField()  # Order within document
    page_number = models.IntegerField(null=True, blank=True)
    section_title = models.CharField(max_length=500, blank=True)

    # Content
    text = models.TextField()  # The actual chunk text
    token_count = models.IntegerField()

    # ChromaDB reference (embeddings stored in ChromaDB, not in PostgreSQL)
    chroma_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]


class NewsChunk(models.Model):
    """
    Chunks of news release/article content for RAG/semantic search.
    Embeddings stored in ChromaDB for semantic similarity search.
    """
    CONTENT_TYPES = [
        ('news_release', 'Company News Release'),
        ('news_article', 'External News Article'),
        ('company_news', 'Scraped Company News'),
    ]

    # Link to source (one of these will be set)
    news_release = models.ForeignKey(
        'NewsRelease',
        on_delete=models.CASCADE,
        related_name='chunks',
        null=True,
        blank=True
    )
    news_article = models.ForeignKey(
        'NewsArticle',
        on_delete=models.CASCADE,
        related_name='chunks',
        null=True,
        blank=True
    )
    company_news = models.ForeignKey(
        'CompanyNews',
        on_delete=models.CASCADE,
        related_name='chunks',
        null=True,
        blank=True
    )

    # Company reference for filtering
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='news_chunks',
        null=True,
        blank=True
    )

    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)

    # Chunk metadata
    chunk_index = models.IntegerField()  # Order within the news item
    section_title = models.CharField(max_length=500, blank=True)

    # Content
    text = models.TextField()
    token_count = models.IntegerField()

    # ChromaDB reference
    chroma_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    # Source metadata for search results
    source_title = models.CharField(max_length=500)
    source_url = models.URLField(blank=True)
    source_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_chunks'
        ordering = ['company', 'source_date', 'chunk_index']
        indexes = [
            models.Index(fields=['company', 'content_type']),
            models.Index(fields=['source_date']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.source_title[:50]}"


class InvestorCommunication(models.Model):
    """Track communications with investors"""
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'In-Person Meeting'),
        ('video_call', 'Video Call'),
        ('conference', 'Conference Meeting'),
        ('site_visit', 'Site Visit'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='investor_comms')
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='communications')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text="Company user who logged this")

    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    communication_date = models.DateTimeField()

    subject = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    followup_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investor_communications'
        ordering = ['-communication_date']


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

class CompanyMetrics(models.Model):
    """Quarterly/Annual metrics snapshot"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='metrics')
    period_end_date = models.DateField()

    # Financial
    cash_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    working_capital_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    burn_rate_monthly_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    runway_months = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # Operations
    meters_drilled_period = models.IntegerField(null=True, blank=True)

    # Valuation metrics
    ev_per_resource_oz = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_metrics'
        ordering = ['-period_end_date']
        unique_together = ['company', 'period_end_date']


# ============================================================================
# WATCHLISTS & ALERTS
# ============================================================================

class Watchlist(models.Model):
    """User watchlists for tracking companies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    companies = models.ManyToManyField(Company, related_name='in_watchlists')

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'watchlists'
        ordering = ['name']


class Alert(models.Model):
    """Price alerts, news alerts, etc."""
    ALERT_TYPES = [
        ('price_above', 'Price Above'),
        ('price_below', 'Price Below'),
        ('volume_spike', 'Volume Spike'),
        ('news_release', 'News Release'),
        ('financing', 'New Financing'),
        ('resource_update', 'Resource Update'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='alerts')

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    threshold_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'


class DocumentProcessingJob(models.Model):
    """Track document processing jobs for admin interface"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('ni43101', 'NI 43-101 Technical Report'),
        ('pea', 'Preliminary Economic Assessment'),
        ('news_release', 'News Release'),
        ('financial_statement', 'Financial Statement'),
        ('presentation', 'Presentation'),
        ('fact_sheet', 'Fact Sheet'),
        ('other', 'Other'),
    ]

    # Job details
    url = models.URLField(max_length=500)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, default='ni43101')
    company_name = models.CharField(max_length=200, blank=True, help_text="Leave blank for auto-detection")
    project_name = models.CharField(max_length=200, blank=True, help_text="Leave blank for auto-detection")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_message = models.TextField(blank=True, help_text="Current processing step")
    error_message = models.TextField(blank=True)

    # Results
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='processing_jobs')
    resources_created = models.IntegerField(default=0)
    chunks_created = models.IntegerField(default=0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time_seconds = models.IntegerField(null=True, blank=True)

    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'document_processing_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_status_display()}: {self.url[:50]}..."

    @property
    def duration_display(self):
        """Human-readable processing duration"""
        if self.processing_time_seconds:
            minutes = self.processing_time_seconds // 60
            seconds = self.processing_time_seconds % 60
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return "-"


# ============================================================================
# REAL-TIME FORUM MODELS
# ============================================================================

class ForumDiscussion(models.Model):
    """Discussion thread for a company"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='forum_discussions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_discussions')

    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    # Stats
    message_count = models.IntegerField(default=0)
    participant_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'forum_discussions'
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['company', 'is_active', '-updated_at']),
            models.Index(fields=['company', 'is_archived']),
            models.Index(fields=['-is_pinned', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.company.name}: {self.title}"


class ForumMessage(models.Model):
    """Individual message in a discussion"""
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_messages')
    content = models.TextField()

    # Threading support
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')

    # Moderation
    is_pinned = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'forum_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['discussion', 'created_at']),
            models.Index(fields=['discussion', 'is_pinned', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['discussion', 'is_deleted', 'created_at']),
        ]

    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.user.username}: {content_preview}"


class GuestSpeakerSession(models.Model):
    """Scheduled Q&A session with guest speakers"""
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='guest_sessions')
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='guest_sessions')
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')

    # Settings
    is_moderated = models.BooleanField(default=True)
    allow_anonymous_questions = models.BooleanField(default=False)
    max_participants = models.IntegerField(null=True, blank=True)

    # Stats
    total_questions = models.IntegerField(default=0)
    total_participants = models.IntegerField(default=0)

    # Archive
    is_archived = models.BooleanField(default=False)
    archive_url = models.URLField(blank=True)
    transcript_url = models.URLField(blank=True)
    transcript_content = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'guest_speaker_sessions'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['company', 'scheduled_start']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['company', 'status', '-scheduled_start']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class SessionSpeaker(models.Model):
    """Guest speakers for a session"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='speakers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='speaker_sessions')

    # Speaker details
    role = models.CharField(max_length=100, blank=True)  # e.g., "CEO", "CFO", "Geologist"
    bio = models.TextField(blank=True)

    # Status
    is_primary = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)

    # Stats
    questions_answered = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_speakers'
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"


class SessionModerator(models.Model):
    """Moderators for a guest speaker session"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='moderators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderated_sessions')

    # Permissions
    can_approve_questions = models.BooleanField(default=True)
    can_reject_questions = models.BooleanField(default=True)
    can_delete_messages = models.BooleanField(default=True)
    can_control_session = models.BooleanField(default=False)  # Start/end session

    # Stats
    questions_approved = models.IntegerField(default=0)
    questions_rejected = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_moderators'
        unique_together = [['session', 'user']]

    def __str__(self):
        return f"{self.user.username} - Moderator for {self.session.title}"


class SessionQuestion(models.Model):
    """Questions asked during guest speaker sessions"""
    QUESTION_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
    ]

    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='questions')
    message = models.ForeignKey(ForumMessage, on_delete=models.CASCADE, related_name='session_question')
    asked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')

    # Status
    status = models.CharField(max_length=20, choices=QUESTION_STATUS, default='pending')
    priority = models.IntegerField(default=0)  # Higher = more important

    # Moderation
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_questions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Engagement
    upvote_count = models.IntegerField(default=0)

    # Answer tracking
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )
    answered_at = models.DateTimeField(null=True, blank=True)
    answer_message = models.ForeignKey(
        ForumMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answer_to_question'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_questions'
        ordering = ['-priority', '-upvote_count', 'created_at']
        indexes = [
            models.Index(fields=['session', 'status', '-priority']),
            models.Index(fields=['session', '-upvote_count']),
            models.Index(fields=['asked_by', '-created_at']),
        ]

    def __str__(self):
        content = self.message.content[:50] + '...' if len(self.message.content) > 50 else self.message.content
        return f"Q: {content} ({self.get_status_display()})"


class QuestionUpvote(models.Model):
    """Track which users upvoted which questions"""
    question = models.ForeignKey(SessionQuestion, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_upvotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'question_upvotes'
        unique_together = [['question', 'user']]
        indexes = [
            models.Index(fields=['question', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} upvoted question {self.question.id}"


class UserPresence(models.Model):
    """Track user online/offline status in discussions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presences')
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='user_presences')

    # Status
    is_online = models.BooleanField(default=False)
    is_typing = models.BooleanField(default=False)

    # Connection tracking
    connection_id = models.CharField(max_length=255, blank=True)  # WebSocket connection ID

    # Timestamps
    last_seen = models.DateTimeField(auto_now=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_presence'
        unique_together = [['user', 'discussion']]
        indexes = [
            models.Index(fields=['discussion', 'is_online']),
            models.Index(fields=['user', 'discussion']),
            models.Index(fields=['discussion', 'is_typing']),
        ]

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        typing = " (typing)" if self.is_typing else ""
        return f"{self.user.username} - {status}{typing}"


class SessionNotification(models.Model):
    """User notifications for guest speaker sessions"""
    NOTIFICATION_TYPE = [
        ('session_reminder_24h', '24 Hour Reminder'),
        ('session_reminder_1h', '1 Hour Reminder'),
        ('session_starting', 'Session Starting'),
        ('session_live', 'Session Live Now'),
        ('session_ended', 'Session Ended'),
        ('question_approved', 'Question Approved'),
        ('question_answered', 'Question Answered'),
        ('speaker_response', 'Speaker Responded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_notifications')
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE)

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.URLField(blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # Related objects
    related_question = models.ForeignKey(
        SessionQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Timestamps
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['session', 'notification_type']),
            models.Index(fields=['is_sent', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class SessionParticipant(models.Model):
    """Track participants in guest speaker sessions"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attended_sessions')

    # Participation tracking
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_currently_active = models.BooleanField(default=True)

    # Engagement stats
    messages_sent = models.IntegerField(default=0)
    questions_asked = models.IntegerField(default=0)
    questions_upvoted = models.IntegerField(default=0)

    class Meta:
        db_table = 'session_participants'
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session', 'is_currently_active']),
            models.Index(fields=['user', '-joined_at']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.session.title}"


# ============================================================================
# GUEST SPEAKER EVENT MODELS
# ============================================================================

class SpeakerEvent(models.Model):
    """Scheduled guest speaker event for companies"""
    EVENT_FORMAT = [
        ('video', 'Video Stream'),
        ('text', 'Text Chat'),
    ]
    EVENT_STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='speaker_events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')

    # Event Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    topic = models.CharField(max_length=255)
    agenda = models.TextField(blank=True)

    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    duration_minutes = models.IntegerField()

    # Format & Capacity
    format = models.CharField(max_length=10, choices=EVENT_FORMAT, default='text')
    max_participants = models.IntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='draft')
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Streaming & Recording
    stream_url = models.URLField(blank=True, help_text="Live stream embed URL (YouTube, Twitch, etc.)")
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    transcript_url = models.URLField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats (denormalized for performance)
    registered_count = models.IntegerField(default=0)
    attended_count = models.IntegerField(default=0)
    questions_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['-scheduled_start']),
        ]

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class EventSpeaker(models.Model):
    """Speaker assigned to an event"""
    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='speakers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='speaking_events')
    title = models.CharField(max_length=255)  # CEO, CFO, Lead Geologist, etc.
    bio = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"


class EventRegistration(models.Model):
    """User registration for an event"""
    REGISTRATION_STATUS = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='registered')

    # Notifications
    reminder_sent = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', '-registered_at']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"


class EventQuestion(models.Model):
    """Question submitted during event"""
    QUESTION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_questions')

    content = models.TextField()
    status = models.CharField(max_length=20, choices=QUESTION_STATUS, default='pending')
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='answered_event_questions')

    upvotes = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-upvotes', '-created_at']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['-upvotes', '-created_at']),
        ]

    def __str__(self):
        return f"Q: {self.content[:50]}..."


class EventReaction(models.Model):
    """Participant engagement reactions"""
    REACTION_TYPE = [
        ('applause', 'Applause'),
        ('thumbs_up', 'Thumbs Up'),
        ('fire', 'Fire'),
        ('heart', 'Heart'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event', 'reaction_type']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.reaction_type}"


# ============================================================================
# FINANCIAL HUB - INVESTOR EDUCATION & QUALIFICATION
# ============================================================================

class EducationalModule(models.Model):
    """Educational content modules for investor education"""
    MODULE_TYPES = [
        ('basics', 'Mining Financing Basics'),
        ('regulations', 'Canadian Securities Regulations'),
        ('investor_rights', 'Investor Rights & Obligations'),
        ('risk_disclosure', 'Risk Disclosures'),
        ('subscription_agreement', 'Subscription Agreement Guide'),
        ('drs', 'Direct Registration System (DRS)'),
    ]

    module_type = models.CharField(max_length=30, choices=MODULE_TYPES, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Content
    content = models.TextField(help_text="HTML/Markdown content")
    estimated_read_time_minutes = models.IntegerField(default=5)

    # Ordering
    sort_order = models.IntegerField(default=0)

    # Status
    is_published = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False, help_text="Required for accreditation process")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'educational_modules'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title


class ModuleCompletion(models.Model):
    """Track user completion of educational modules"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_completions')
    module = models.ForeignKey(EducationalModule, on_delete=models.CASCADE, related_name='completions')

    # Tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)

    # Quiz/Assessment (optional)
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        db_table = 'module_completions'
        unique_together = ['user', 'module']
        indexes = [
            models.Index(fields=['user', 'completed_at']),
            models.Index(fields=['module', '-completed_at']),
        ]

    def __str__(self):
        status = "Completed" if self.completed_at else "In Progress"
        return f"{self.user.username} - {self.module.title} ({status})"


class AccreditedInvestorQualification(models.Model):
    """Store accredited investor qualification results"""
    QUALIFICATION_STATUS = [
        ('pending', 'Pending Review'),
        ('qualified', 'Qualified'),
        ('not_qualified', 'Not Qualified'),
        ('expired', 'Expired'),
    ]

    QUALIFICATION_CRITERIA = [
        ('income_individual', 'Individual Income >$200k'),
        ('income_combined', 'Combined Income >$300k'),
        ('financial_assets', 'Financial Assets ≥$1M'),
        ('net_assets', 'Net Assets ≥$5M'),
        ('entity_assets', 'Entity with Assets ≥$5M'),
        ('professional', 'Registered Dealer/Adviser'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accreditation_qualifications')

    # Qualification Details
    status = models.CharField(max_length=20, choices=QUALIFICATION_STATUS, default='pending')
    criteria_met = models.CharField(max_length=30, choices=QUALIFICATION_CRITERIA, null=True, blank=True)

    # Questionnaire Responses (JSON)
    questionnaire_responses = models.JSONField(default=dict, help_text="Stores all questionnaire answers")

    # Supporting Documentation
    documents_submitted = models.BooleanField(default=False)
    documents_verified = models.BooleanField(default=False)

    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_qualifications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Validity
    qualified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accredited_investor_qualifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


# ============================================================================
# FINANCIAL HUB - SUBSCRIPTION AGREEMENTS & INVESTMENTS
# ============================================================================

class SubscriptionAgreement(models.Model):
    """Subscription agreement for financing participation"""
    AGREEMENT_STATUS = [
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('accepted', 'Accepted by Company'),
        ('funded', 'Funded'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    # Parties
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_agreements')
    financing = models.ForeignKey(Financing, on_delete=models.CASCADE, related_name='subscription_agreements')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscription_agreements')

    # Investment Details
    num_shares = models.BigIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=4)
    total_investment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Warrants (if applicable)
    includes_warrants = models.BooleanField(default=False)
    warrant_shares = models.BigIntegerField(null=True, blank=True)
    warrant_strike_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    warrant_expiry_date = models.DateField(null=True, blank=True)

    # Agreement Status
    status = models.CharField(max_length=30, choices=AGREEMENT_STATUS, default='draft')

    # Document Management
    agreement_pdf_url = models.URLField(blank=True)
    docusign_envelope_id = models.CharField(max_length=255, blank=True)

    # Signature Tracking
    investor_signed_at = models.DateTimeField(null=True, blank=True)
    investor_ip_address = models.GenericIPAddressField(null=True, blank=True)
    company_accepted_at = models.DateTimeField(null=True, blank=True)
    company_accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_agreements'
    )

    # Payment Tracking
    payment_instructions_sent_at = models.DateTimeField(null=True, blank=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)

    # DRS & Share Issuance
    shares_issued = models.BooleanField(default=False)
    shares_issued_at = models.DateTimeField(null=True, blank=True)
    drs_statement_sent_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)

    # Legal & Compliance
    accreditation_verified = models.BooleanField(default=False)
    kyc_completed = models.BooleanField(default=False)
    aml_check_completed = models.BooleanField(default=False)

    # Notes
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_agreements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['docusign_envelope_id']),
        ]

    def __str__(self):
        return f"{self.investor.username} - {self.company.name} - ${self.total_investment_amount:,.2f}"


class InvestmentTransaction(models.Model):
    """Track individual investment transactions and their lifecycle"""
    TRANSACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('payment_pending', 'Payment Pending'),
        ('payment_received', 'Payment Received'),
        ('shares_issued', 'Shares Issued'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_transactions')
    financing = models.ForeignKey(Financing, on_delete=models.CASCADE, related_name='investment_transactions')

    # Transaction Details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')

    # Payment Details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    # Share Allocation
    shares_allocated = models.BigIntegerField(null=True, blank=True)
    price_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'investment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.financing.company.name} - ${self.amount:,.2f}"


class FinancingAggregate(models.Model):
    """Aggregate investment data for financing rounds"""
    financing = models.OneToOneField(Financing, on_delete=models.CASCADE, related_name='aggregate_data')

    # Subscription Metrics
    total_subscriptions = models.IntegerField(default=0)
    total_subscribers = models.IntegerField(default=0)

    # Amount Metrics
    total_committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_funded_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_shares_allocated = models.BigIntegerField(default=0)

    # Status Breakdown (JSON)
    status_breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown by agreement status: {draft: 2, signed: 5, funded: 10}"
    )

    # Investor Type Breakdown (JSON)
    investor_type_breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown by investor type: {individual: 8, institutional: 2}"
    )

    # Last Updated
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financing_aggregates'

    def __str__(self):
        return f"{self.financing.company.name} - {self.financing.financing_type} Aggregate"


class PaymentInstruction(models.Model):
    """Payment instructions for financing participations"""
    PAYMENT_METHOD = [
        ('wire', 'Wire Transfer'),
        ('ach', 'ACH Transfer'),
        ('check', 'Check'),
        ('crypto', 'Cryptocurrency'),
    ]

    subscription_agreement = models.OneToOneField(
        SubscriptionAgreement,
        on_delete=models.CASCADE,
        related_name='payment_instruction'
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_instructions')

    # Payment Method
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)

    # Banking Details (encrypted in production)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=255, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)

    # Additional Instructions
    reference_code = models.CharField(max_length=100, help_text="Unique reference for payment tracking")
    special_instructions = models.TextField(blank=True)

    # Tracking
    sent_to_investor_at = models.DateTimeField(null=True, blank=True)
    viewed_by_investor_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_instructions'

    def __str__(self):
        return f"{self.subscription_agreement.investor.username} - {self.get_payment_method_display()}"


class DRSDocument(models.Model):
    """DRS (Direct Registration System) documents and delivery tracking"""
    DOCUMENT_TYPE = [
        ('statement', 'DRS Statement'),
        ('certificate', 'Share Certificate'),
        ('confirmation', 'Issuance Confirmation'),
        ('educational', 'DRS Educational Material'),
    ]

    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.CASCADE,
        related_name='drs_documents',
        null=True,
        blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drs_documents')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='drs_documents')

    # Document Details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE)
    document_url = models.URLField(blank=True)
    document_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash for verification")

    # Share Details (for statements/certificates)
    num_shares = models.BigIntegerField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(null=True, blank=True)

    # Delivery Tracking
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=50, blank=True, help_text="email, postal, etc")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drs_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['subscription_agreement', '-created_at']),
            models.Index(fields=['delivery_status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()} - {self.company.name}"


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

class NewsSource(models.Model):
    """Configuration for news scraping sources"""
    name = models.CharField(max_length=200, help_text="Display name for the source")
    url = models.URLField(unique=True, help_text="Base URL of the news source")
    is_active = models.BooleanField(default=True, help_text="Whether to include in scraping")

    # Scraping configuration
    scrape_selector = models.CharField(
        max_length=500,
        blank=True,
        help_text="CSS selector for article links (optional, for advanced configuration)"
    )

    # Tracking
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    last_scrape_status = models.CharField(max_length=50, blank=True)
    articles_found_last_scrape = models.IntegerField(default=0)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_news_sources'
    )

    class Meta:
        db_table = 'news_sources'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class NewsArticle(models.Model):
    """Scraped news articles from mining news sources"""
    title = models.CharField(max_length=500)
    url = models.URLField(unique=True, help_text="URL to the full article")
    source = models.ForeignKey(
        NewsSource,
        on_delete=models.CASCADE,
        related_name='articles'
    )

    # Article metadata
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication date from the source"
    )
    author = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True, help_text="Article excerpt or summary if available")
    image_url = models.URLField(blank=True, help_text="Featured image URL if available")

    # Categorization (optional)
    tags = models.JSONField(default=list, blank=True, help_text="Tags or categories from source")

    # Tracking
    scraped_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True, help_text="Whether to show in the feed")

    class Meta:
        db_table = 'news_articles'
        ordering = ['-published_at', '-scraped_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['source', '-published_at']),
            models.Index(fields=['is_visible', '-published_at']),
        ]

    def __str__(self):
        return self.title[:100]

    @property
    def source_name(self):
        return self.source.name if self.source else "Unknown"


class NewsScrapeJob(models.Model):
    """Track scraping job execution"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered manual scrape, null for scheduled"
    )
    is_scheduled = models.BooleanField(default=False, help_text="Whether this was a scheduled job")

    # Results
    sources_processed = models.IntegerField(default=0)
    articles_found = models.IntegerField(default=0)
    articles_new = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'news_scrape_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Scrape Job {self.id} - {self.status}"


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

    PLAN_TYPES = [
        ('monthly', 'Monthly ($20/month)'),
        ('annual', 'Annual ($200/year)'),
    ]

    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')

    # Stripe identifiers
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(max_length=255, blank=True)

    # Subscription details
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='monthly')
    status = models.CharField(max_length=30, choices=SUBSCRIPTION_STATUS, default='trialing')
    price_cents = models.IntegerField(default=2000, help_text="Price in cents (2000 = $20)")

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

class InvestmentInterest(models.Model):
    """
    Tracks investor interest in financing rounds.
    This is the initial registration step before formal subscription agreements.
    Used for lead generation and investor qualification.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('qualified', 'Qualified'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted to Subscription'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    # Core relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_interests')
    financing = models.ForeignKey(Financing, on_delete=models.CASCADE, related_name='investment_interests')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='investment_interests')

    # Accreditation
    is_accredited_investor = models.BooleanField(
        help_text="User confirmed they are an accredited investor"
    )
    accreditation_confirmed_at = models.DateTimeField(auto_now_add=True)

    # Investment details
    shares_requested = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares the investor is interested in"
    )
    price_per_share = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Price per share at time of interest registration"
    )
    investment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total investment amount (shares * price)"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Document confirmations
    term_sheet_confirmed = models.BooleanField(default=False)
    term_sheet_confirmed_at = models.DateTimeField(null=True, blank=True)
    subscription_agreement_confirmed = models.BooleanField(default=False)
    subscription_agreement_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Contact information
    contact_email = models.EmailField(
        help_text="Email for follow-up communications"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for follow-up"
    )

    # Risk acknowledgment
    risk_acknowledged = models.BooleanField(
        default=False,
        help_text="User acknowledged investment risks"
    )
    risk_acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    status_notes = models.TextField(blank=True)

    # Linked subscription agreement (if converted)
    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interest_registrations'
    )

    # Tracking/audit fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investment_interests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'financing']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_accredited_investor']),
        ]
        # Prevent duplicate interests from same user for same financing
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'financing'],
                name='unique_user_financing_interest'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.company.name} - ${self.investment_amount:,.2f}"

    def save(self, *args, **kwargs):
        # Auto-calculate investment amount
        if self.shares_requested and self.price_per_share:
            self.investment_amount = self.shares_requested * self.price_per_share
        super().save(*args, **kwargs)


class InvestmentInterestAggregate(models.Model):
    """
    Aggregated public statistics for investment interests.
    This is the PUBLIC-FACING data shown on company pages.
    Contains NO personally identifiable information.
    """
    financing = models.OneToOneField(
        Financing,
        on_delete=models.CASCADE,
        related_name='interest_aggregate'
    )

    # Public metrics (NO PII)
    total_interest_count = models.IntegerField(
        default=0,
        help_text="Number of investors who expressed interest"
    )
    total_shares_requested = models.BigIntegerField(
        default=0,
        help_text="Total shares requested across all interests"
    )
    total_amount_interested = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total investment amount interested"
    )

    # Percentage metrics
    percentage_filled = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Percentage of financing goal filled by interests"
    )

    # Last updated
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investment_interest_aggregates'

    def __str__(self):
        return f"{self.financing.company.name} - Interest Aggregate"

    def recalculate(self):
        """Recalculate aggregate statistics from investment interests"""
        from django.db.models import Sum, Count
        from django.utils import timezone

        # Get aggregated data from active interests (not withdrawn/rejected)
        stats = self.financing.investment_interests.filter(
            status__in=['pending', 'qualified', 'contacted', 'converted']
        ).aggregate(
            count=Count('id'),
            total_shares=Sum('shares_requested'),
            total_amount=Sum('investment_amount')
        )

        self.total_interest_count = stats['count'] or 0
        self.total_shares_requested = stats['total_shares'] or 0
        self.total_amount_interested = stats['total_amount'] or Decimal('0.00')

        # Calculate percentage of financing goal filled (use amount_raised_usd as target)
        if self.financing.amount_raised_usd and self.financing.amount_raised_usd > 0:
            self.percentage_filled = min(
                (self.total_amount_interested / self.financing.amount_raised_usd) * 100,
                Decimal('100.00')
            )
        else:
            self.percentage_filled = Decimal('0.00')

        self.last_calculated_at = timezone.now()
        self.save()

    @classmethod
    def update_for_financing(cls, financing):
        """Get or create aggregate and recalculate"""
        aggregate, created = cls.objects.get_or_create(financing=financing)
        aggregate.recalculate()
        return aggregate


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

class CompanyPerson(models.Model):
    """
    Board members, executives, and technical team members for companies.
    Extracted during auto-population process.
    """
    ROLE_TYPES = [
        ('board_director', 'Board Director'),
        ('executive', 'Executive'),
        ('technical_team', 'Technical Team'),
        ('advisor', 'Advisor'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='people'
    )
    full_name = models.CharField(max_length=200)
    role_type = models.CharField(max_length=30, choices=ROLE_TYPES)
    title = models.CharField(max_length=200, blank=True, help_text="Job title, e.g., 'CEO', 'VP Exploration'")
    biography = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)
    photo_file = models.ImageField(upload_to='company_people/', blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    # Extraction metadata
    source_url = models.URLField(blank=True, help_text="URL where this data was found")
    extraction_confidence = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score of extraction (0.0-1.0)"
    )
    extracted_at = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    # Ordering
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_people'
        ordering = ['company', 'role_type', 'display_order', 'full_name']
        verbose_name_plural = 'Company People'

    def __str__(self):
        return f"{self.full_name} - {self.title} ({self.company.name})"


class CompanyDocument(models.Model):
    """
    Documents discovered and processed for companies.
    Stores PDFs, presentations, reports with processing status.
    """
    DOCUMENT_TYPES = [
        ('presentation', 'Corporate Presentation'),
        ('fact_sheet', 'Fact Sheet'),
        ('ni43101', 'NI 43-101 Technical Report'),
        ('financial_report', 'Financial Report'),
        ('annual_report', 'Annual Report'),
        ('quarterly_report', 'Quarterly Report'),
        ('news_release', 'News Release'),
        ('other', 'Other'),
    ]

    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='scraped_documents'
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # File storage
    source_url = models.URLField(help_text="Original URL where document was found")
    file_path = models.FileField(upload_to='company_documents/', blank=True, null=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_format = models.CharField(max_length=20, blank=True, help_text="e.g., pdf, pptx")

    # Metadata
    publication_date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    is_latest = models.BooleanField(default=True, help_text="Is this the latest version of this document type?")

    # Processing
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    processing_error = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Extracted content (for search/indexing)
    extracted_text = models.TextField(blank=True, help_text="Extracted text content for search")
    thumbnail_url = models.URLField(blank=True)

    # Extraction metadata
    relevance_score = models.FloatField(default=0.0)
    extracted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_documents'
        ordering = ['-publication_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'document_type']),
            models.Index(fields=['company', 'is_latest']),
        ]

    def __str__(self):
        return f"{self.title} ({self.company.name})"


class CompanyNews(models.Model):
    """
    News releases and press releases scraped from company websites.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='scraped_news'
    )
    title = models.CharField(max_length=500)
    content = models.TextField(blank=True, help_text="Full text content of news release")
    summary = models.TextField(blank=True, help_text="AI-generated summary")

    # Source
    source_url = models.URLField(help_text="URL of the news release")
    is_pdf = models.BooleanField(default=False, help_text="Is the source a PDF file?")

    # Dates
    publication_date = models.DateField(null=True, blank=True)
    publication_datetime = models.DateTimeField(null=True, blank=True)

    # Categorization
    categories = models.JSONField(default=list, blank=True, help_text="Auto-detected categories")
    keywords = models.JSONField(default=list, blank=True, help_text="Extracted keywords")

    # Extraction metadata
    extracted_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_news'
        ordering = ['-publication_date', '-created_at']
        verbose_name_plural = 'Company News'
        indexes = [
            models.Index(fields=['company', 'publication_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.company.name})"


class ScrapingJob(models.Model):
    """
    Tracks scraping jobs for company auto-population.
    Provides audit trail and status tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Target
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scraping_jobs'
    )
    company_name_input = models.CharField(max_length=300, help_text="Original company name or URL input")
    website_url = models.URLField(blank=True, help_text="Target website URL")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Progress tracking
    sections_to_process = models.JSONField(default=list, help_text="List of sections to scrape")
    sections_completed = models.JSONField(default=list)
    sections_failed = models.JSONField(default=list)

    # Results
    data_extracted = models.JSONField(default=dict, help_text="Extracted data before saving to models")
    documents_found = models.IntegerField(default=0)
    people_found = models.IntegerField(default=0)
    news_found = models.IntegerField(default=0)

    # Errors
    error_messages = models.JSONField(default=list)
    error_traceback = models.TextField(blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # User tracking
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scraping_jobs'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scraping_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Scraping: {self.company_name_input} ({self.status})"

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class FailedCompanyDiscovery(models.Model):
    """
    Tracks failed attempts to discover/scrape companies.
    Useful for retry logic and manual intervention.
    """
    company_name = models.CharField(max_length=300)
    website_url = models.URLField(blank=True)

    # Failure details
    failure_reason = models.TextField()
    attempts = models.IntegerField(default=1)
    last_attempted_at = models.DateTimeField(auto_now=True)

    # Resolution
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_discoveries'
    )
    resolution_notes = models.TextField(blank=True)

    # Link to successful company if resolved
    resolved_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='failed_discoveries'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'failed_company_discoveries'
        ordering = ['-last_attempted_at']
        verbose_name_plural = 'Failed Company Discoveries'

    def __str__(self):
        return f"Failed: {self.company_name} ({self.attempts} attempts)"


# ============================================================================
# METALS PRICING
# ============================================================================

class MetalPrice(models.Model):
    """
    Stores historical precious metals prices scraped from Kitco.
    Updated twice daily via scheduled task.
    """
    METAL_CHOICES = [
        ('XAU', 'Gold'),
        ('XAG', 'Silver'),
        ('XPT', 'Platinum'),
        ('XPD', 'Palladium'),
    ]

    metal = models.CharField(max_length=3, choices=METAL_CHOICES)
    bid_price = models.DecimalField(max_digits=12, decimal_places=2)
    ask_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Source tracking
    source = models.CharField(max_length=50, default='Kitco')
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'metal_prices'
        ordering = ['-scraped_at', 'metal']
        indexes = [
            models.Index(fields=['metal', '-scraped_at']),
            models.Index(fields=['-scraped_at']),
        ]

    def __str__(self):
        return f"{self.get_metal_display()}: ${self.bid_price} ({self.scraped_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def mid_price(self):
        """Calculate mid-market price"""
        return (self.bid_price + self.ask_price) / 2

    @classmethod
    def get_latest_prices(cls):
        """Get the most recent price for each metal"""
        from django.db.models import Max

        latest_times = cls.objects.values('metal').annotate(
            latest=Max('scraped_at')
        )

        prices = {}
        for item in latest_times:
            price = cls.objects.filter(
                metal=item['metal'],
                scraped_at=item['latest']
            ).first()
            if price:
                prices[item['metal']] = price

        return prices


class StockPrice(models.Model):
    """
    Stores daily closing stock prices and volume for companies.
    Updated daily after market close (4:30 PM ET weekdays).
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_prices')

    # Price data
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField(default=0)

    # Optional additional data if available
    open_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    # Change calculations
    change_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    # Currency
    currency = models.CharField(max_length=3, default='CAD')  # Most TSX/TSXV stocks are CAD

    # Source tracking
    source = models.CharField(max_length=50, default='Alpha Vantage')
    date = models.DateField()  # The trading date
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_prices'
        ordering = ['-date', 'company__ticker_symbol']
        unique_together = ['company', 'date']  # One record per company per day
        indexes = [
            models.Index(fields=['company', '-date']),
            models.Index(fields=['-date']),
            models.Index(fields=['company', 'date']),
        ]

    def __str__(self):
        return f"{self.company.ticker_symbol}: ${self.close_price} ({self.date})"

    @classmethod
    def get_latest_prices(cls):
        """Get the most recent price for each company"""
        from django.db.models import Max

        latest_dates = cls.objects.values('company').annotate(
            latest=Max('date')
        )

        prices = {}
        for item in latest_dates:
            price = cls.objects.filter(
                company_id=item['company'],
                date=item['latest']
            ).select_related('company').first()
            if price:
                prices[price.company.ticker_symbol] = price

        return prices

    @classmethod
    def get_company_history(cls, company, days=30):
        """Get price history for a company"""
        from datetime import timedelta
        from django.utils import timezone

        start_date = timezone.now().date() - timedelta(days=days)
        return cls.objects.filter(
            company=company,
            date__gte=start_date
        ).order_by('date')

    @classmethod
    def get_price_on_date(cls, company, target_date):
        """Get the price for a specific company on a specific date"""
        return cls.objects.filter(
            company=company,
            date=target_date
        ).first()
