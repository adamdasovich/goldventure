import re
from urllib.parse import urlparse

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .users import User, Company
from .mining import Project, Financing


# Filenames and path segments that name the template or the section, not the
# release. A URL whose identity comes down to one of these identifies nothing,
# so it must never be used to match two rows together.
#
# website_crawler.py keeps its own copies (GENERIC_PAGE_FILENAMES,
# LISTING_PATH_SEGMENTS) for a different job — deciding whether a URL is an
# article at all. These are deliberately separate: importing the crawler here
# would pull crawl4ai into every model import.
GENERIC_URL_FILENAMES = frozenset({
    'default.aspx', 'default.asp', 'default.htm', 'default.html',
    'index.aspx', 'index.php', 'index.htm', 'index.html',
    'news.aspx', 'news.php', 'news.htm', 'news.html',
})

GENERIC_URL_SEGMENTS = frozenset({
    'news', 'news-releases', 'newsreleases', 'press-releases', 'press-release',
    'press', 'media', 'releases', 'announcements', 'updates', 'latest-news',
    'company-news', 'investors', 'investor-relations', 'en', 'fr', 'index',
    'default', 'home',
})

# `v` is here for YouTube: /watch?v=<id>. Without it every embedded video
# collapses to the identity "watch" — 30 of them across the live tables — and
# two videos posted by one company on one day would match each other.
_URL_ID_PARAM = re.compile(
    r'\b(?:id|content_id|news_id|article|post|release|p|v)=([\w-]+)', re.I
)


def news_url_identity(url):
    """
    The part of a news URL that identifies the release rather than the host
    serving it: the last meaningful path segment, plus any identifying query
    parameter.

    Returns '' when the URL comes down to nothing but a section or template
    name — never a value that could match two unrelated releases. Callers must
    treat '' as "cannot match on this".
    """
    if not url:
        return ''

    parsed = urlparse(url.strip().lower())
    segments = [s for s in parsed.path.split('/') if s]

    # Q4-style platforms end real article URLs with default.aspx.
    while segments and segments[-1] in GENERIC_URL_FILENAMES:
        segments.pop()

    id_match = _URL_ID_PARAM.search(parsed.query or '')
    id_part = id_match.group(1) if id_match else ''

    if not segments:
        # Nothing but a template name; only a query id can identify it.
        return f'?{id_part}' if id_part else ''

    last = segments[-1]
    # A section name, or a bare year archive index, identifies nothing.
    if last in GENERIC_URL_SEGMENTS or re.fullmatch(r'(19|20)\d{2}', last):
        return f'?{id_part}' if id_part else ''

    # A purely numeric last segment is too weak on its own — /news/page/2 and
    # /2026/02/19126 both appear in the live data — so it carries its parent
    # for context: "page/2", "02/19126", "english/2903". Strictly more
    # specific, which can only ever cost a merge, never cause a wrong one.
    if last.isdigit() and len(segments) >= 2:
        last = f'{segments[-2]}/{last}'

    return f'{last}?{id_part}' if id_part else last


class ScrapedNewsMixin:
    """
    Match scraped news on what identifies the release, not on the URL alone.

    Keying on URL breaks the day a company moves domains: every release in the
    archive reappears under a new host and is stored a second time. Portofino
    Resources renaming to LatAm Lithium duplicated 44 of its 57 releases that
    way, and nothing about it looked like an error — the scrape reported
    "43 created" and the count simply doubled.

    Subclasses declare which fields carry the URL and the publication date.
    """

    URL_FIELD = 'url'
    DATE_FIELD = 'release_date'

    @classmethod
    def match_scraped(cls, company, url, published_on):
        """
        Find the stored row for a scraped item, or None.

        Exact URL first — the overwhelmingly common case, and unchanged from
        the behaviour this replaces. Only if that misses do we look for the
        same company's item on the same date with the same URL identity.
        Requiring company, date and identity together keeps this from ever
        merging two distinct releases: annual repeats like "AGM Results" share
        a title, but never a date.
        """
        existing = cls.objects.filter(
            company=company, **{cls.URL_FIELD: url}
        ).first()
        if existing is not None:
            return existing

        identity = news_url_identity(url)
        if not identity or not published_on:
            return None

        candidates = cls.objects.filter(
            company=company, **{cls.DATE_FIELD: published_on}
        )
        for candidate in candidates:
            if news_url_identity(getattr(candidate, cls.URL_FIELD)) == identity:
                return candidate
        return None

    @classmethod
    def upsert_from_scrape(cls, company, url, defaults, update_existing=True):
        """
        Create or update the row for one scraped item. Returns (obj, created),
        like update_or_create.

        The stored URL is always moved onto the one just scraped, even when
        `update_existing` is False: a row still pointing at the old host is a
        link that dies when the redirect does. Everything else is left alone in
        that case, so callers wanting get_or_create semantics keep them.
        """
        existing = cls.match_scraped(company, url, defaults.get(cls.DATE_FIELD))

        if existing is not None:
            changed = []
            if update_existing:
                for field, value in defaults.items():
                    setattr(existing, field, value)
                changed = list(defaults)
            if getattr(existing, cls.URL_FIELD) != url:
                setattr(existing, cls.URL_FIELD, url)
                changed.append(cls.URL_FIELD)
            if changed:
                existing.save(update_fields=changed + ['updated_at'])
            return existing, False

        # Nothing matched. update_or_create rather than create, so two workers
        # racing on the same URL cannot both insert.
        return cls.objects.update_or_create(
            company=company, **{cls.URL_FIELD: url}, defaults=defaults
        )


# ============================================================================
# COMMUNICATIONS & DOCUMENTS
# ============================================================================

class NewsRelease(ScrapedNewsMixin, models.Model):
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
    url = models.URLField(max_length=500, blank=True)

    # Impact tracking
    is_material = models.BooleanField(default=False, help_text="Material news event")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'news_releases'
        ordering = ['-release_date']
        indexes = [
            models.Index(fields=['company', '-release_date']),
        ]




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
    # Nullable: the GPU worker has no publication date to work from and used to
    # default this to today, which then propagated into ResourceEstimate.report_date
    # and made three Ixtaca reports from 2015, 2017 and 2019 look simultaneous.
    # Unknown is recorded as unknown; backfill_document_dates recovers it from
    # the title afterwards.
    document_date = models.DateField(null=True, blank=True)

    # 500, not Django's 200 default: 25 GPU jobs failed outright on
    # "value too long for type character varying(200)" because SEDAR and
    # investor-relations PDF links routinely run past 200 characters.
    file_url = models.URLField(max_length=500)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    description = models.TextField(blank=True)

    # Access control
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-document_date']

    def save(self, *args, **kwargs):
        # Normalize the title on every save: scrapers sometimes derive a title
        # from a source URL and leave its query string attached
        # (e.g. 'corporate presentation?v=020506'). Titles never legitimately
        # contain a '?', so trim everything from the first one. This is the
        # single chokepoint that keeps URL cruft out of titles regardless of
        # which code path creates the Document.
        if self.title and '?' in self.title:
            self.title = self.title.split('?', 1)[0].strip()
        super().save(*args, **kwargs)




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




class NewsReleaseFlag(models.Model):
    """
    Tracks news releases flagged for potential financing announcements.
    Superusers review these and can create Financing records from them.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed_financing', 'Confirmed Financing - Created'),
        ('reviewed_false_positive', 'False Positive - Dismissed'),
    ]

    news_release = models.OneToOneField(
        NewsRelease,
        on_delete=models.CASCADE,
        related_name='financing_flag'
    )
    
    # Detection metadata
    flagged_at = models.DateTimeField(auto_now_add=True)
    detected_keywords = models.JSONField(
        default=list,
        help_text="List of financing keywords that triggered the flag"
    )
    
    # Review workflow
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_news_flags'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Link to created financing record (if confirmed)
    created_financing = models.ForeignKey(
        Financing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_flag'
    )
    
    # Review notes
    review_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'news_release_flags'
        ordering = ['-flagged_at']
        indexes = [
            models.Index(fields=['status', '-flagged_at']),
        ]
    
    def __str__(self):
        return f"Flag: {self.news_release.company.name} - {self.news_release.title[:50]}"
    
    def mark_as_financing(self, reviewer, financing_record, notes=''):
        """Mark as confirmed financing and link to created Financing record"""
        from django.utils import timezone
        
        self.status = 'reviewed_financing'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.created_financing = financing_record
        self.review_notes = notes
        self.save()
    
    def dismiss_as_false_positive(self, reviewer, notes=''):
        """Dismiss as false positive"""
        from django.utils import timezone

        self.status = 'reviewed_false_positive'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

        # Record URL and title as permanently dismissed to prevent re-flagging
        if self.news_release and self.news_release.url:
            url = self.news_release.url
            title = self.news_release.title or ''

            dismissed, created = DismissedNewsURL.objects.get_or_create(
                url=url,
                reason='false_positive',
                defaults={
                    'company': self.news_release.company,
                    'dismissed_by': reviewer,
                    'title': title,
                    'normalized_url': DismissedNewsURL.normalize_url(url),
                    'normalized_title': DismissedNewsURL.normalize_title(title),
                }
            )
            # Update title if record already existed but didn't have title
            if not created and not dismissed.title and title:
                dismissed.title = title
                dismissed.normalized_title = DismissedNewsURL.normalize_title(title)
                dismissed.save()


class NewsReportFlag(models.Model):
    """
    Tracks news releases flagged for potential technical reports
    (NI 43-101, PEA, PFS, DFS, MRE, etc.).
    Superusers review these, submit the report PDF URL, and the existing
    docling GPU pipeline ingests the document into the vector DB.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed_processed', 'Submitted for Processing'),
        ('reviewed_false_positive', 'False Positive - Dismissed'),
    ]

    REPORT_TYPE_CHOICES = [
        ('ni43101', 'NI 43-101 Technical Report'),
        ('pea', 'Preliminary Economic Assessment'),
        ('pfs', 'Prefeasibility Study'),
        ('dfs', 'Definitive Feasibility Study'),
        ('mre', 'Mineral Resource Estimate'),
        ('other', 'Other Technical Report'),
    ]

    news_release = models.OneToOneField(
        NewsRelease,
        on_delete=models.CASCADE,
        related_name='report_flag'
    )

    flagged_at = models.DateTimeField(auto_now_add=True)
    detected_keywords = models.JSONField(
        default=list,
        help_text="List of technical-report keywords that triggered the flag"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_report_flags'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Set when the superuser submits the report PDF URL for docling processing
    report_url = models.URLField(max_length=2000, blank=True, default='')
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        blank=True,
        default=''
    )
    processing_job = models.ForeignKey(
        'DocumentProcessingJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_report_flags'
    )

    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'news_report_flags'
        ordering = ['-flagged_at']
        indexes = [
            models.Index(fields=['status', '-flagged_at']),
        ]

    def __str__(self):
        return f"ReportFlag: {self.news_release.company.name} - {self.news_release.title[:50]}"

    def mark_as_processed(self, reviewer, job, report_url, report_type, notes=''):
        """Mark as submitted for docling processing and link the job."""
        from django.utils import timezone

        self.status = 'reviewed_processed'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.processing_job = job
        self.report_url = report_url
        self.report_type = report_type
        self.review_notes = notes
        self.save()

    def dismiss_as_false_positive(self, reviewer, notes=''):
        """Dismiss as false positive (separate dismissal scope from financing flags)."""
        from django.utils import timezone

        self.status = 'reviewed_false_positive'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

        # Record URL/title as dismissed under the 'report_false_positive' scope
        # so it does NOT suppress financing flags on the same URL (and vice versa).
        if self.news_release and self.news_release.url:
            url = self.news_release.url
            title = self.news_release.title or ''

            dismissed, created = DismissedNewsURL.objects.get_or_create(
                url=url,
                reason='report_false_positive',
                defaults={
                    'company': self.news_release.company,
                    'dismissed_by': reviewer,
                    'title': title,
                    'normalized_url': DismissedNewsURL.normalize_url(url),
                    'normalized_title': DismissedNewsURL.normalize_title(title),
                }
            )
            if not created and not dismissed.title and title:
                dismissed.title = title
                dismissed.normalized_title = DismissedNewsURL.normalize_title(title)
                dismissed.save()


class DismissedNewsURL(models.Model):
    # Unique per (url, reason) so the same URL can be dismissed independently
    # under the financing-flag scope ('false_positive') and the technical-report
    # scope ('report_false_positive') without one suppressing the other.
    url = models.URLField(max_length=2000, db_index=True)
    normalized_url = models.CharField(max_length=500, blank=True, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    normalized_title = models.CharField(max_length=500, blank=True, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="dismissed_news_urls")
    dismissed_at = models.DateTimeField(auto_now_add=True)
    dismissed_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=100, default="false_positive")

    class Meta:
        db_table = "dismissed_news_urls"
        constraints = [
            models.UniqueConstraint(fields=['url', 'reason'], name='uniq_dismissed_url_reason'),
        ]

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        # Auto-generate normalized fields on save
        if self.url and not self.normalized_url:
            self.normalized_url = self.normalize_url(self.url)
        if self.title and not self.normalized_title:
            self.normalized_title = self.normalize_title(self.title)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_url(url):
        """Normalize URL for comparison - remove trailing slashes, query params, and common suffixes"""
        import re
        from urllib.parse import urlparse, urlunparse

        if not url:
            return ''

        # Parse URL
        parsed = urlparse(url)

        # Remove query string and fragment
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

        # Remove trailing slashes
        normalized = normalized.rstrip('/')

        # Remove common WordPress duplicate suffixes like -2, -3, -2-2, etc.
        normalized = re.sub(r'-\d+(-\d+)*$', '', normalized)

        return normalized.lower()

    @staticmethod
    def normalize_title(title):
        """Normalize title for comparison - lowercase, remove punctuation, extra spaces"""
        import re

        if not title:
            return ''

        # Lowercase
        normalized = title.lower()

        # Remove common prefixes that vary
        normalized = re.sub(r'^(press release[:\s]*|news[:\s]*)', '', normalized)

        # Remove punctuation except spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @classmethod
    def is_similar_to_dismissed(cls, company, url=None, title=None, similarity_threshold=0.85, reason='false_positive'):
        """
        Check if a URL or title is similar to any dismissed news for this company,
        within the given dismissal `reason` scope. Financing-flag dismissals
        (reason='false_positive') and report-flag dismissals
        (reason='report_false_positive') are tracked independently.
        Returns (is_similar, matched_dismissed_record) tuple.
        """
        from difflib import SequenceMatcher

        base_qs = cls.objects.filter(reason=reason)

        # Check exact URL match first
        if url:
            exact = base_qs.filter(url=url).first()
            if exact:
                return True, exact

            # Check normalized URL match
            normalized_url = cls.normalize_url(url)
            if normalized_url:
                match = base_qs.filter(
                    company=company,
                    normalized_url=normalized_url
                ).first()
                if match:
                    return True, match

        # Check title similarity
        if title:
            normalized_title = cls.normalize_title(title)
            if normalized_title:
                # Get all dismissed titles for this company within this reason scope
                dismissed_titles = base_qs.filter(
                    company=company,
                    normalized_title__isnull=False
                ).exclude(normalized_title='').values_list('normalized_title', 'id')

                for dismissed_norm_title, dismissed_id in dismissed_titles:
                    if dismissed_norm_title:
                        # Calculate similarity ratio
                        similarity = SequenceMatcher(None, normalized_title, dismissed_norm_title).ratio()
                        if similarity >= similarity_threshold:
                            return True, cls.objects.get(id=dismissed_id)

        return False, None




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




class CompanyNews(ScrapedNewsMixin, models.Model):
    """
    News releases and press releases scraped from company websites.
    """
    # This model names its URL and date columns differently to NewsRelease.
    URL_FIELD = "source_url"
    DATE_FIELD = "publication_date"

    NEWS_TYPE_CHOICES = [
        ('general', 'General News'),
        ('drill_results', 'Drill Results'),
        ('resource_estimate', 'Resource Estimate'),
        ('financing', 'Financing'),
        ('acquisition', 'Acquisition/Merger'),
        ('management', 'Management Change'),
        ('exploration', 'Exploration Update'),
        ('production', 'Production Update'),
        ('regulatory', 'Regulatory/Permitting'),
        ('corporate', 'Corporate Update'),
    ]

    FINANCING_TYPE_CHOICES = [
        ('none', 'No Financing'),
        ('private_placement', 'Private Placement'),
        ('bought_deal', 'Bought Deal'),
        ('flow_through', 'Flow-Through'),
        ('rights_offering', 'Rights Offering'),
        ('debt', 'Debt Financing'),
        ('warrant_exercise', 'Warrant Exercise'),
        ('other', 'Other Financing'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='scraped_news'
    )
    title = models.CharField(max_length=500)
    content = models.TextField(blank=True, help_text="Full text content of news release")
    summary = models.TextField(blank=True, help_text="AI-generated summary")

    # Source
    source_url = models.URLField(max_length=500, help_text="URL of the news release")
    is_pdf = models.BooleanField(default=False, help_text="Is the source a PDF file?")

    # Dates
    publication_date = models.DateField(null=True, blank=True)
    publication_datetime = models.DateTimeField(null=True, blank=True)

    # News classification
    news_type = models.CharField(max_length=30, choices=NEWS_TYPE_CHOICES, default='general')
    is_material = models.BooleanField(default=False, help_text="Material news (drill results, resource estimates, financings)")

    # Financing detection
    financing_type = models.CharField(max_length=30, choices=FINANCING_TYPE_CHOICES, default='none')
    financing_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                           help_text="Financing amount in CAD")
    financing_price_per_unit = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                                   help_text="Price per unit/share")

    # Drill results detection
    has_drill_results = models.BooleanField(default=False)
    best_intercept = models.CharField(max_length=200, blank=True, help_text="Best drill intercept mentioned")

    # Processing status
    is_processed = models.BooleanField(default=False, help_text="Has been processed by document processor")
    processing_job = models.ForeignKey('DocumentProcessingJob', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='news_items')

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
            models.Index(fields=['company', '-publication_date']),
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




class CompanyVerificationLog(models.Model):
    """
    Tracks verification results for onboarded companies.
    Used to identify companies that need manual review.
    """
    STATUS_CHOICES = [
        ('complete', 'Complete'),
        ('incomplete', 'Incomplete'),
        ('needs_review', 'Needs Review'),
        ('error', 'Error'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='verification_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    overall_score = models.IntegerField(default=0)  # 0-100 completeness score

    # Detailed issues (JSON array)
    issues = models.JSONField(default=list, blank=True)

    # Auto-fixes applied (JSON array of strings)
    fixes_applied = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'company_verification_logs'
        ordering = ['-created_at']
        verbose_name = 'Company Verification Log'
        verbose_name_plural = 'Company Verification Logs'

    def __str__(self):
        return f"Verification: {self.company.name} ({self.status}, score: {self.overall_score})"


# ============================================================================
# METALS PRICING
# ============================================================================




# ============================================================================
# FAILED TASK LOG - Dead Letter Queue for Celery
# ============================================================================

class FailedTaskLog(models.Model):
    """
    Stores permanently failed Celery tasks for review and potential reprocessing.
    Acts as a 'dead letter queue' for tasks that failed after all retries.
    """
    task_name = models.CharField(max_length=255, db_index=True)
    task_id = models.CharField(max_length=255, unique=True)
    args = models.TextField(blank=True, default='')
    kwargs = models.TextField(blank=True, default='')
    exception_type = models.CharField(max_length=255)
    exception_message = models.TextField()
    traceback = models.TextField()

    # Status for manual review
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('reprocessed', 'Reprocessed'),
        ('ignored', 'Ignored'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_failed_tasks'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'failed_task_log'
        ordering = ['-created_at']
        verbose_name = 'Failed Task Log'
        verbose_name_plural = 'Failed Task Logs'
        indexes = [
            models.Index(fields=['task_name', '-created_at'], name='failedtask_name_date_idx'),
            models.Index(fields=['status', '-created_at'], name='failedtask_status_date_idx'),
        ]

    def __str__(self):
        return f"{self.task_name} ({self.task_id[:8]}...) - {self.status}"

