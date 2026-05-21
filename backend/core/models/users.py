from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal



# Note: Abstract base models available in base_models.py for future refactoring
# from .base_models import TimestampedModel, SoftDeleteModel, ActivatableModel


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
    # When the user last opened their dashboard daily briefing — powers the
    # "since your last visit" framing.
    last_briefing_seen = models.DateTimeField(null=True, blank=True)
    # Opt-in (default off) for the weekly briefing email.
    email_briefing_enabled = models.BooleanField(default=False)
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
    news_url = models.URLField(blank=True, default='', help_text="Custom news page URL if different from standard patterns")
    last_working_news_url = models.URLField(blank=True, default='', help_text="Auto-cached: URL pattern that last successfully found news")
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

    # Soft delete fields (critical records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_companies'
    )

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
    brief_description = models.CharField(max_length=2000, blank=True, help_text="Brief company description")
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
        indexes = [
            models.Index(fields=['is_active'], name='idx_company_is_active'),
            models.Index(fields=['approval_status'], name='idx_company_approval_status'),
            models.Index(fields=['is_active', 'approval_status'], name='idx_company_active_status'),
            models.Index(fields=['ticker_symbol'], name='idx_company_ticker'),
        ]

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

    def soft_delete(self, user=None):
        """Soft delete this company record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted company record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


# ============================================================================
# MINING PROJECT MODELS
# ============================================================================

