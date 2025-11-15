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
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
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

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.ticker_symbol})" if self.ticker_symbol else self.name


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
