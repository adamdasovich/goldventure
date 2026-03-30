from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .users import User, Company




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
        # Precious Metals
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('platinum', 'Platinum Group Metals'),
        ('palladium', 'Palladium'),
        # Critical/Battery Minerals
        ('lithium', 'Lithium'),
        ('cobalt', 'Cobalt'),
        ('nickel', 'Nickel'),
        ('graphite', 'Graphite'),
        ('manganese', 'Manganese'),
        ('rare_earths', 'Rare Earth Elements'),
        # Base Metals
        ('copper', 'Copper'),
        ('zinc', 'Zinc'),
        ('lead', 'Lead'),
        ('iron_ore', 'Iron Ore'),
        ('tin', 'Tin'),
        # Energy/Specialty Minerals
        ('uranium', 'Uranium'),
        ('vanadium', 'Vanadium'),
        ('tungsten', 'Tungsten'),
        ('molybdenum', 'Molybdenum'),
        ('antimony', 'Antimony'),
        ('niobium', 'Niobium'),
        ('tantalum', 'Tantalum'),
        # Other
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
        indexes = [
            models.Index(fields=['is_active'], name='idx_project_is_active'),
            models.Index(fields=['company', 'is_active'], name='idx_project_company_active'),
        ]

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
    press_release_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    # Closed financing tracking (for /closed-financings page)
    is_closed = models.BooleanField(default=False, help_text="Whether this financing has been marked as closed for display")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the financing was marked as closed")
    closed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_financings',
        help_text="User who marked this financing as closed"
    )
    source_news_flag = models.ForeignKey(
        'NewsReleaseFlag',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_financings',
        help_text="The news flag that originated this financing"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_financings'
    )

    class Meta:
        db_table = 'financings'
        ordering = ['-announced_date']

    def soft_delete(self, user=None):
        """Soft delete this financing record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted financing record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def mark_as_closed(self, user=None):
        """Mark this financing as closed for display on the closed financings page."""
        from django.utils import timezone
        self.is_closed = True
        self.closed_at = timezone.now()
        self.closed_by = user
        if self.status != 'closed':
            self.status = 'closed'
        self.save()




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

