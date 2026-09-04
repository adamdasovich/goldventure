from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
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
    # Opt-in (default off) for the Friday weekly industry report email.
    email_weekly_industry_report_enabled = models.BooleanField(default=False)
    # When the one-time welcome email was sent — guards against double-sends
    # and makes the existing-user backfill batch safe to re-run.
    welcome_email_sent_at = models.DateTimeField(null=True, blank=True)
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
    slug = models.SlugField(
        max_length=220,
        blank=True,
        default='',
        help_text="URL-friendly slug derived from name; used in /companies/{id}-{slug}",
    )
    legal_name = models.CharField(max_length=200, blank=True)
    former_names = models.TextField(
        blank=True,
        default='',
        help_text=(
            "Previous names, one per line, most recent first. Appended "
            "automatically by save() whenever `name` changes. Plain text "
            "rather than a JSON list so it substring-matches the same way "
            "`name` does — see Company.name_q()."
        ),
    )
    ticker_symbol = models.CharField(max_length=10, blank=True)
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=COMPANY_STATUS)

    # Corporate info
    incorporation_date = models.DateField(null=True, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    news_url = models.URLField(blank=True, default='', help_text="Custom news page URL if different from standard patterns")
    last_working_news_url = models.URLField(blank=True, default='', help_text="Auto-cached: URL pattern that last successfully found news")
    # When the weekly document-discovery crawl last visited this company's
    # site. The discovery task orders by this (nulls first) and stamps it after
    # every visit — including failed crawls, so a broken site cannot pin itself
    # to the head of the rotation and starve everyone behind it. Without this
    # the task sliced [:limit] off default ordering and crawled the same 25
    # companies every week, forever.
    last_discovered_at = models.DateTimeField(
        null=True, blank=True, db_index=True,
        help_text="Last visit by the weekly document-discovery crawl",
    )
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
            # Added by migration 0056 but never declared here, so makemigrations
            # kept proposing to drop it. Slug is the lookup key for company
            # URLs, so the index stays and the model now matches the database.
            models.Index(fields=['slug'], name='idx_company_slug'),
        ]

    def __str__(self):
        return f"{self.name} ({self.ticker_symbol})" if self.ticker_symbol else self.name

    @classmethod
    def from_db(cls, db, field_names, values):
        # Stash the name as loaded so save() can tell a rename from a no-op.
        # Skipped when name was deferred (.only()/.defer()) — reading it here
        # would fire a second query per row.
        instance = super().from_db(db, field_names, values)
        if 'name' in field_names:
            instance._loaded_name = instance.name
        return instance

    @property
    def former_names_list(self):
        """`former_names` as a list, most recent first, blanks dropped."""
        return [n.strip() for n in self.former_names.splitlines() if n.strip()]

    def add_former_name(self, old_name):
        """
        Record a previous name. Most recent first, case-insensitively deduped,
        and never the company's current name.

        Also prunes the current name out of the existing list: renaming A -> B
        and later back to A must not leave the company listed as formerly
        itself. Returns True if `former_names` changed at all, which includes
        a prune with no addition.
        """
        old_name = (old_name or '').strip()
        current = (self.name or '').strip().casefold()

        existing = [n for n in self.former_names_list if n.casefold() != current]

        if (old_name and old_name.casefold() != current
                and not any(n.casefold() == old_name.casefold() for n in existing)):
            existing.insert(0, old_name)

        new_value = '\n'.join(existing)
        changed = new_value != self.former_names
        self.former_names = new_value
        return changed

    @staticmethod
    def name_q(term, prefix=''):
        """
        Match a company by name, including names it used to trade under.

        Renames are routine in this sector — a TSXV name change arrives with a
        new ticker and usually a consolidation — and articles, filings and
        documents keep using the old name long afterwards. Matching `name`
        alone silently drops all of them on the floor the day we rename.

        `prefix` walks a relation, e.g. name_q(term, 'company__') to filter a
        queryset of something that points at Company.

        A blank term matches nothing. `icontains=''` matches every row, and
        several callers — the AI assistant's company tools among them — pass a
        caller-supplied string straight through without checking it, so an
        empty one would quietly return an arbitrary company as the answer.
        """
        term = (term or '').strip()
        if not term:
            return models.Q(pk__in=[])
        return (
            models.Q(**{f'{prefix}name__icontains': term})
            | models.Q(**{f'{prefix}former_names__icontains': term})
        )

    @staticmethod
    def identity_q(term, prefix=''):
        """`name_q` plus an exact ticker match — the usual 'find this company
        from a free-text identifier' filter. Blank matches nothing: an empty
        ticker would otherwise match every company that has no ticker."""
        term = (term or '').strip()
        if not term:
            return models.Q(pk__in=[])
        return (
            Company.name_q(term, prefix)
            | models.Q(**{f'{prefix}ticker_symbol__iexact': term})
        )

    @classmethod
    def find_by_exact_name(cls, name, queryset=None):
        """
        Find the company that goes, or used to go, by exactly this name.

        For duplicate detection on create — where `name_q`'s substring match
        is far too loose ("Gold Corp." would collide with half the table).
        A company re-encountered under its pre-rename name is the same
        company, not a new one.

        Two steps because `former_names` is newline-separated text: the
        `icontains` narrows to a handful of candidates in the database, then
        the exact per-line comparison happens in Python. That avoids building
        a regex out of a company name, where a stray '.' or '(' would either
        match too much or blow up.
        """
        name = (name or '').strip()
        if not name:
            return None

        qs = cls.objects if queryset is None else queryset
        match = qs.filter(name__iexact=name).first()
        if match:
            return match

        folded = name.casefold()
        for candidate in qs.filter(former_names__icontains=name):
            if any(n.casefold() == folded for n in candidate.former_names_list):
                return candidate
        return None

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        # A caller saving only current_price is not renaming anything, so leave
        # slug and former_names alone. Fields derived from name are only
        # touched when name itself is being written.
        touching_name = update_fields is None or 'name' in update_fields
        also_write = []

        # Keep slug in sync with name. Truncated to 220 to leave room in the URL.
        if self.name and touching_name:
            expected = slugify(self.name)[:220]
            if self.slug != expected:
                self.slug = expected
                also_write.append('slug')

        # Record the outgoing name on a rename. Compared stripped, so that
        # re-saving a name that picked up stray whitespace is not filed as a
        # rename to itself.
        loaded_name = getattr(self, '_loaded_name', None)
        renamed = (
            loaded_name is not None
            and loaded_name.strip() != (self.name or '').strip()
        )
        if self.pk and touching_name and renamed:
            if self.add_former_name(loaded_name):
                also_write.append('former_names')

        # An explicit update_fields would otherwise drop the derived columns —
        # that is how a slug ends up stranded against a name it no longer
        # matches.
        if update_fields is not None and also_write:
            kwargs['update_fields'] = list(update_fields) + also_write

        super().save(*args, **kwargs)
        self._loaded_name = self.name

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

