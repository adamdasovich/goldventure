"""
Centralized constants for the GoldVenture Platform.

This file consolidates magic numbers and configuration values used throughout
the codebase to improve maintainability and consistency.
"""

# =============================================================================
# HTTP REQUEST TIMEOUTS (in seconds)
# =============================================================================

class Timeouts:
    """HTTP request timeout values in seconds."""

    # Standard API calls
    DEFAULT = 10
    SHORT = 5
    MEDIUM = 15
    LONG = 30
    EXTENDED = 60

    # Specific service timeouts
    ALPHA_VANTAGE = 10
    KITCO_SCRAPER = 30
    STOCK_PRICE = 15
    NEWS_CONTENT = 15
    DOCUMENT_DOWNLOAD = 60
    GPU_WORKER_DOWNLOAD = 300

    # Playwright/browser timeouts (in milliseconds)
    PAGE_DEFAULT_MS = 15000
    PAGE_EXTENDED_MS = 30000
    PAGE_VALIDATION_MS = 60000
    PAGE_VALIDATION_EXTENDED_MS = 120000


# =============================================================================
# STRING TRUNCATION LIMITS (in characters)
# =============================================================================

class TruncationLimits:
    """Maximum character lengths for various string fields."""

    # Short text fields
    TITLE_SHORT = 100
    TITLE_MEDIUM = 200
    TITLE_LONG = 500

    # Description fields
    DESCRIPTION_SHORT = 200
    DESCRIPTION_MEDIUM = 500
    DESCRIPTION_LONG = 1000
    DESCRIPTION_FULL = 2000

    # Content fields
    CONTENT_PREVIEW = 500
    CONTENT_MEDIUM = 1000
    CONTENT_LONG = 2000
    CONTENT_EXTENDED = 3000
    CONTENT_FULL = 5000

    # URL and email fields
    URL_STANDARD = 200
    URL_LONG = 500
    EMAIL = 254

    # Address fields
    ADDRESS = 300
    COUNTRY = 100

    # Summary fields
    SUMMARY_SHORT = 500
    SUMMARY_LONG = 1000

    # User agent and metadata
    USER_AGENT = 500

    # Claude prompt fields
    CLAUDE_DESCRIPTION = 1500


# =============================================================================
# CACHE TTL VALUES (in seconds)
# =============================================================================

class CacheTTL:
    """Cache time-to-live values in seconds."""

    # Short-lived caches (for frequently changing data)
    VERY_SHORT = 60       # 1 minute
    SHORT = 120           # 2 minutes

    # Standard caches
    DEFAULT = 300         # 5 minutes (metals prices, etc.)
    MEDIUM = 600          # 10 minutes

    # Long-lived caches
    LONG = 3600           # 1 hour (stock data, etc.)
    EXTENDED = 7200       # 2 hours
    VERY_LONG = 86400     # 24 hours


# =============================================================================
# PAGINATION AND QUERY LIMITS
# =============================================================================

class QueryLimits:
    """Pagination and query limit values."""

    # Standard pagination
    PAGE_SIZE_SMALL = 10
    PAGE_SIZE_DEFAULT = 20
    PAGE_SIZE_MEDIUM = 50
    PAGE_SIZE_LARGE = 100

    # Maximum records
    MAX_RESULTS = 1000
    MAX_BATCH_SIZE = 500


# =============================================================================
# CELERY TASK CONFIGURATION
# =============================================================================

class CeleryConfig:
    """Celery task configuration constants."""

    # Time limits in seconds
    TASK_SOFT_LIMIT_DEFAULT = 600      # 10 minutes
    TASK_HARD_LIMIT_DEFAULT = 900      # 15 minutes
    TASK_SOFT_LIMIT_LONG = 3600        # 1 hour
    TASK_HARD_LIMIT_LONG = 3900        # 1 hour 5 minutes

    # Result expiration
    RESULT_EXPIRES = 86400             # 24 hours


# =============================================================================
# FILE SIZE LIMITS
# =============================================================================

class FileSizeLimits:
    """File size limits in bytes."""

    MAX_UPLOAD_MB = 50
    MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

    MAX_DOCUMENT_MB = 100
    MAX_DOCUMENT_BYTES = MAX_DOCUMENT_MB * 1024 * 1024


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimits:
    """Rate limiting configuration."""

    # Requests per minute
    API_STANDARD = 60
    API_PREMIUM = 300
    SCRAPING = 10


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

class Validation:
    """Validation-related constants."""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8

    # Company/entity limits
    MAX_TICKER_LENGTH = 10
    MAX_EXCHANGE_LENGTH = 50

    # Content validation
    MAX_TAGS = 20
    MAX_TAG_LENGTH = 50
