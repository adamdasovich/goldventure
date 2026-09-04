"""
Django settings for GoldVenture Platform
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production, SECRET_KEY MUST be set via environment variable
_default_key = 'dev-only-key-do-not-use-in-production-' + 'x' * 20
SECRET_KEY = os.getenv('SECRET_KEY', _default_key)
if not os.getenv('SECRET_KEY') and not os.getenv('DEBUG', 'False') == 'True':
    import warnings
    warnings.warn("SECRET_KEY environment variable not set! Using insecure default.", RuntimeWarning)

# SECURITY WARNING: don't run with debug turned on in production!
# Default to False for safety - must be explicitly set to True for development
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',

    # Local apps
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS - must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.security_middleware.SecurityHeadersMiddleware',  # CSP + Permissions-Policy
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'goldventure_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Required - no default for security
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        # Connection pooling - reuse connections for 10 minutes to reduce overhead
        'CONN_MAX_AGE': 600,
        # SECURITY: Validate connections before use to prevent stale connection errors
        'CONN_HEALTH_CHECKS': True,
    }
}

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Password validation
# Length is the ONLY rule we ask users to satisfy up front — no uppercase/number/
# symbol requirements (NIST 800-63B advises against composition rules). The
# remaining validators below only reject genuinely weak passwords, so they rarely
# fire. Keep min_length in sync with MIN_PASSWORD_LENGTH in
# frontend/components/auth/RegisterModal.tsx.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # SECURITY: Require minimum 12 characters (NIST 800-63B recommendation)
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Toronto'  # Your timezone (Canada)
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Rate limiting to prevent brute force and DoS attacks
    'DEFAULT_THROTTLE_CLASSES': [
        'core.throttling.InternalAwareAnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5000/hour',
        'user': '10000/hour',
    },
    # Count one proxy in front. Without this, DRF identifies an anonymous caller
    # by the WHOLE X-Forwarded-For header, and nginx appends to that header
    # rather than replacing it — so sending `X-Forwarded-For: <anything>` yields
    # the throttle key `<anything>,<real ip>`, and varying it per request gives
    # a fresh 5000/hour bucket every time. The limit was optional for anyone who
    # knew. With one proxy declared, the key is the entry nginx appended, which
    # is the real peer address and cannot be set from outside.
    'NUM_PROXIES': 1,
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Reduced from 24h for security
    # SECURITY: Reduced from 7 days to 3 days to limit window if token is stolen
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # Invalidate old refresh tokens
    # Additional security settings
    'UPDATE_LAST_LOGIN': True,  # Track login times
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# Allow cache control headers for frontend
CORS_ALLOW_HEADERS = list(default_headers) + [
    'cache-control',
    'pragma',
    'expires',
]

# Anthropic API Key
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Voyage AI API Key (for fast embeddings)
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY', '')

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')

# Twelve Data API Key (for metals pricing)
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', '')

# AWS Settings (for S3 document storage - Phase 2)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Stripe Settings (for Company Portal Subscriptions)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Stripe Store Webhook (separate webhook for e-commerce store)
STRIPE_STORE_WEBHOOK_SECRET = os.getenv('STRIPE_STORE_WEBHOOK_SECRET', '')

# Stripe Platform Subscription Webhook (user-level subscriptions)
STRIPE_PLATFORM_WEBHOOK_SECRET = os.getenv('STRIPE_PLATFORM_WEBHOOK_SECRET', '')

# Pin the Stripe Product for each platform tier. Optional, but without a pin
# _get_or_create_product() falls back to an eventually-consistent metadata
# search that has previously created duplicate products.
#
# One product per tier is required, not a matter of taste: Stripe's Customer
# Portal will not offer two prices of the same product/interval/currency as
# switchable, so a single shared product makes plan switching impossible.
STRIPE_PLATFORM_PRODUCT_ID_PROSPECTOR = os.getenv('STRIPE_PLATFORM_PRODUCT_ID_PROSPECTOR', '')
STRIPE_PLATFORM_PRODUCT_ID_MINER = os.getenv('STRIPE_PLATFORM_PRODUCT_ID_MINER', '')

# Legacy: the single shared product every tier used to hang off. Kept only so
# the id stays recorded; nothing reads it since the per-tier split.
STRIPE_PLATFORM_PRODUCT_ID = os.getenv('STRIPE_PLATFORM_PRODUCT_ID', '')

# The company plan (mining companies editing their own page). Its own product,
# its own webhook endpoint, its own signing secret — sharing a secret between
# endpoints means rotating one silently breaks the others.
STRIPE_COMPANY_PRODUCT_ID = os.getenv('STRIPE_COMPANY_PRODUCT_ID', '')
STRIPE_COMPANY_WEBHOOK_SECRET = os.getenv('STRIPE_COMPANY_WEBHOOK_SECRET', '')

# Promotion code offered to early-access users when their comp grant lapses.
# Empty disables the offer; the expiry email simply omits it.
STRIPE_LAUNCH_PROMO_CODE = os.getenv('STRIPE_LAUNCH_PROMO_CODE', '')

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

# Email backend - use SMTP for production
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Junior Mining Intelligence <noreply@juniorminingintelligence.com>')
# Socket timeout for the SMTP conversation. Unset, Python's smtplib blocks
# forever, so a stalled send holds a Celery slot until the task's soft time
# limit kills it — on 2026-08-27 two Ask the Editor alerts each burned 110s
# that way on a memory-starved box. A healthy send here takes ~0.7s, so 20s
# is generous; failing fast lets the task retry instead of being killed.
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))

# Early-access promo: grant new registrations a 1-month comp Prospector
# subscription along with the welcome email. Flip to 'False' via env once the
# launch promo ends — the welcome email still sends, just without the free month.
WELCOME_FREE_MONTH_ENABLED = os.getenv('WELCOME_FREE_MONTH_ENABLED', 'True') == 'True'

# Notification Recipients - MUST be set via environment variables in production
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
NI43101_NOTIFICATION_EMAIL = os.getenv('NI43101_NOTIFICATION_EMAIL', 'notifications@example.com')
FINANCING_NOTIFICATION_EMAIL = os.getenv('FINANCING_NOTIFICATION_EMAIL', 'notifications@example.com')
# Where "Ask the Editor" questions are emailed. Falls back to ADMIN_EMAIL so a
# question is never silently dropped just because the specific var is unset.
EDITOR_NOTIFICATION_EMAIL = os.getenv('EDITOR_NOTIFICATION_EMAIL', ADMIN_EMAIL)
# Where credential-liveness failures are emailed (core/credential_checks.py).
# NOTE: ADMIN_EMAIL still defaults to the placeholder admin@example.com and has
# never been set in production, so alert_recipient() deliberately skips
# @example.com addresses rather than posting failures into a black hole.
CREDENTIAL_ALERT_EMAIL = os.getenv('CREDENTIAL_ALERT_EMAIL', EDITOR_NOTIFICATION_EMAIL)

# ============================================================================
# DJANGO CHANNELS & WEBSOCKET CONFIGURATION
# ============================================================================

# ASGI Application
ASGI_APPLICATION = 'config.asgi.application'

# Channels (for WebSocket support)
INSTALLED_APPS += ['channels']

# Cache & Channel Layers Configuration
REDIS_URL = os.getenv('REDIS_URL', None)

if not DEBUG:
    # PRODUCTION: Redis is REQUIRED for WebSocket support and caching
    if not REDIS_URL:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            "REDIS_URL environment variable is required in production for WebSocket "
            "and caching support. Set REDIS_URL=redis://localhost:6379/0"
        )
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            }
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }
elif REDIS_URL:
    # Development with Redis available
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 20,
                },
            }
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    # Development without Redis: Use in-memory backends
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ============================================================================
# PRODUCTION SECURITY SETTINGS
# ============================================================================

# Cookie security settings (always set for both dev and prod)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    # HTTPS/SSL
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

    # Proxy Headers
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Referrer Policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'


# ============================================================================
# CELERY SETTINGS
# ============================================================================

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max
CELERY_RESULT_EXPIRES = 3600  # 1 hour - most task results are consumed immediately

# CRITICAL: Task reliability settings to prevent task loss
CELERY_TASK_ACKS_LATE = True  # Acknowledge only after successful completion (prevents loss on worker crash)
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Requeue task if worker crashes/loses connection
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Don't prefetch more than 1 task (prevents task hoarding)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True  # Retry Redis connection on startup
CELERY_BROKER_CONNECTION_RETRY = True  # Keep retrying broker connection
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10  # Max retries before giving up

# ----------------------------------------------------------------------------
# Task routing — three queues, one dedicated worker each.
#
# Everything used to share a single queue, so the 7 AM daily batch (~400
# scrape_single_company_news_task, ~9 hours at concurrency 2) starved every
# other task behind it: on 2026-08-18 there were 26 health checks and 9 browser
# cleanups queued for hours, and onboarding a company meant waiting behind the
# whole batch.
#
#   scrape       bulk background crawling. Slow, browser-heavy, can run all day.
#   interactive  user-triggered onboarding/manual scrapes. Also browser-heavy,
#                but a person is waiting, so it must never queue behind `scrape`.
#   default      everything light: health checks, cleanups, price fetches,
#                emails, the Friday report. Must never be starved.
#
# Tasks NOT listed here fall through to CELERY_TASK_DEFAULT_QUEUE.
# Each queue needs its own worker with a DISTINCT -n node name; two workers
# sharing a node name produces DuplicateNodenameWarning and silently breaks
# `celery inspect` (that bug cost a day on 2026-08-14).
# ----------------------------------------------------------------------------
CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_TASK_ROUTES = {
    # --- bulk crawling -------------------------------------------------------
    'core.tasks.scrape_all_companies_news_task':        {'queue': 'scrape'},
    'core.tasks.scrape_single_company_news_task':       {'queue': 'scrape'},
    'core.tasks.scrape_mining_news_task':               {'queue': 'scrape'},
    'core.tasks.auto_discover_and_process_documents_task': {'queue': 'scrape'},
    'core.tasks.hunt_technical_reports_task':           {'queue': 'scrape'},
    'core.tasks.reconcile_chroma_index_task':           {'queue': 'scrape'},
    'core.tasks.backfill_document_dates_task':          {'queue': 'scrape'},
    'core.tasks.process_company_news_for_rag_task':     {'queue': 'scrape'},
    'core.tasks.embed_recent_news_for_rag_task':        {'queue': 'scrape'},
    'core.tasks.store_company_profile_in_rag_task':     {'queue': 'scrape'},

    # --- user-triggered, someone is watching a spinner ------------------------
    # scrape_company_news_task is dispatched from the onboarding views AND from
    # inside scrape_and_save_company_task, so both paths stay interactive.
    'core.tasks.scrape_and_save_company_task':          {'queue': 'interactive'},
    'core.tasks.scrape_company_website_task':           {'queue': 'interactive'},
    'core.tasks.scrape_company_news_task':              {'queue': 'interactive'},
}

# Celery Beat Schedule - Periodic Tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Verify every external credential still works, and email if one does not.
    # These all fail SILENTLY: an expired DigitalOcean token stops GPU document
    # processing with nothing but 401s in a log, a dead Anthropic key drops paid
    # subscribers to the templated briefing because _generate_ai_briefing()
    # swallows every exception, and a revoked SendGrid key still satisfies
    # is_configured(), which only inspects the 'SG.' prefix. It also confirms
    # every configured Stripe webhook secret still has an enabled endpoint --
    # the store endpoint was found unregistered on 2026-09-01, which meant a
    # customer could be charged and no order was ever created.
    # Mondays at 12:15 UTC. Stated in UTC deliberately: crontab() here is UTC,
    # so the wall-clock ET time shifts with daylight saving -- 08:15 EDT in
    # summer, 07:15 EST in winter. (The older entries below label fixed UTC
    # hours with fixed ET times, which is why two of them disagree about what
    # 13:00 UTC is.)
    'check-credentials-weekly': {
        'task': 'core.tasks.check_credentials_task',
        'schedule': crontab(day_of_week=1, hour=12, minute=15),
    },

    # Warn early-access comp-grant holders before their access lapses. Comp
    # grants have no Stripe subscription, so nothing else would tell them.
    # 13:00 UTC = 9 AM ET.
    'notify-expiring-comp-grants': {
        'task': 'core.tasks.notify_expiring_comp_grants_task',
        'schedule': crontab(hour=13, minute=30),
    },

    # Scrape Kitco metals prices twice daily (9 AM and 4 PM ET / 14:00 and 21:00 UTC)
    'scrape-metals-prices-morning': {
        'task': 'core.tasks.scrape_metals_prices_task',
        'schedule': crontab(hour=14, minute=0),  # 9 AM ET
    },
    'scrape-metals-prices-afternoon': {
        'task': 'core.tasks.scrape_metals_prices_task',
        'schedule': crontab(hour=21, minute=0),  # 4 PM ET
    },
    # Fetch stock prices daily after market close (4:30 PM ET / 21:30 UTC) on weekdays
    'fetch-stock-prices-daily': {
        'task': 'core.tasks.fetch_stock_prices_task',
        'schedule': crontab(hour=21, minute=30, day_of_week='mon-fri'),  # 4:30 PM ET, Mon-Fri
    },

    # Fetch base / critical metals prices (copper from Yahoo Finance) after the
    # COMEX copper close — 5:30 PM ET / 22:30 UTC, weekdays.
    'fetch-base-metals-prices-daily': {
        'task': 'core.tasks.fetch_base_metals_prices_task',
        'schedule': crontab(hour=22, minute=30, day_of_week='mon-fri'),  # 5:30 PM ET, Mon-Fri
    },

    # Auto-discover and process documents.
    #
    # No document_types kwarg. It used to read
    # ['ni43101', 'news_release', 'presentation'] and was applied ahead of the
    # task's own priority filter, so the two contradicted each other: this list
    # dropped 'pea' outright, while the priority filter dropped 'news_release'
    # anyway. The priority filter is the more specific of the two — it keeps the
    # most recent of each technical-report subtype and the most recent
    # presentation, and skips news releases (handled by the news scrapers) and
    # financial statements — so it is left to do the filtering alone.
    #
    # limit is deliberately modest. This entry is for ongoing maintenance, not
    # for catching up: each company is a depth-2 browser crawl plus a technical-
    # documents sweep on the `scrape` queue at concurrency 2, and everything it
    # discovers becomes a DocumentProcessingJob that boots a GPU droplet at
    # ~$1.57/hr. Bulk backfill over the whole company list is a supervised batch
    # run, not something to let a weekly cron drift into.
    # STILL DISABLED — but its three blocking flaws are fixed as of 2026-09-04:
    # rotation (least-recently-visited via Company.last_discovered_at, stamped
    # even on failed crawls), the CPU tail-call (process_document_queue() no
    # longer runs Docling on this worker; jobs wait for the GPU orchestrator),
    # and the missing gate (check_discovered_document(): announcement-shaped
    # documents refused, confirmed Content-Length >= the report floor required).
    # A dry_run kwarg exists for a supervised pass. Re-enabling is a product
    # decision, not a code one.
    #
    # Original note, kept for history:
    # DISABLED 2026-09-03, to be revisited the week of 2026-09-07.
    #
    # The document-type fixes earlier today mean this task can queue technical
    # reports for the first time, and nobody has ever seen its discovery volume:
    # the old filters discarded the output before it was logged, and the log
    # line claimed nothing was dropped. An unattended 2 AM run would have been
    # the first measurement, with each discovered document booting a GPU droplet
    # at ~$1.57/hr. It also shares the `scrape` queue with the report hunter,
    # which is now clearing its own backlog — two unmeasured GPU producers in
    # the same window. Re-enable after a supervised dry run establishes the
    # per-company document count.
    # 'auto-discover-documents-weekly': {
    #     'task': 'core.tasks.auto_discover_and_process_documents_task',
    #     'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Every Monday at 2 AM
    #     'kwargs': {
    #         'limit': 25,  # Companies per week. 2 AM leaves 5h before the 7 AM news batch.
    #     }
    # },

    # Hunt for the technical report each pending NewsReportFlag refers to.
    # A flag marks a news release whose title mentions a report; the report is a
    # separate document on the company's site, so this searches for it and either
    # auto-queues a high-confidence match or leaves a ranked shortlist to review.
    #
    # Daily rather than weekly because NI 43-101 s.4.2 gives issuers 45 days from
    # announcing results to file, so a report can appear on any given day. The
    # per-flag backoff in the task (1, 3, 7, 14, 21, 30 days) stops a daily
    # schedule from re-crawling the same site every night. 4 AM ET is clear of
    # both the 2 AM Monday discovery run and the 7 AM news batch on this queue.
    # Re-enabled 2026-09-04 after three supervised batches. The last one — ten
    # companies, six auto-queues — produced zero wrong documents with the full
    # gate set live: score, project match, report-type match, negative-document
    # disqualifier, rejected-URL and failed-job guards, and a confirmed
    # Content-Length of at least MIN_AUTO_QUEUE_SIZE_MB. The earlier batches'
    # failure mode was never "found nothing"; it was announcement PDFs wearing
    # report-shaped names, and the size gate closes that structurally.
    # Everything below the auto-queue bar lands in /admin/news-flags-reports as
    # ranked candidates; everything queued shows its score and reasoning in
    # /admin/document-queue and is cancellable while pending.
    'hunt-technical-reports-daily': {
        'task': 'core.tasks.hunt_technical_reports_task',
        'schedule': crontab(hour=9, minute=0),  # 4 AM ET
        'kwargs': {
            'max_companies': 40,  # Ceiling on sites crawled per run
        }
    },

    # Scrape mining industry news 3 times daily (8 AM, 1 PM, 6 PM ET / 13:00, 18:00, 23:00 UTC)
    'scrape-mining-news-morning': {
        'task': 'core.tasks.scrape_mining_news_task',
        'schedule': crontab(hour=13, minute=0),  # 8 AM ET
    },
    'scrape-mining-news-afternoon': {
        'task': 'core.tasks.scrape_mining_news_task',
        'schedule': crontab(hour=18, minute=0),  # 1 PM ET
    },
    'scrape-mining-news-evening': {
        'task': 'core.tasks.scrape_mining_news_task',
        'schedule': crontab(hour=23, minute=0),  # 6 PM ET
    },

    # Scrape news releases from ALL company websites daily (7 AM ET / 12:00 UTC)
    # Runs Monday-Saturday only (no Sunday - markets closed, no news)
    'scrape-all-companies-news-daily': {
        'task': 'core.tasks.scrape_all_companies_news_task',
        'schedule': crontab(hour=12, minute=0, day_of_week='1-6'),  # 7 AM ET, Mon-Sat
    },

    # Cleanup stuck jobs every 30 minutes (was 15 - reduced to cut unnecessary DB polls)
    'cleanup-stuck-jobs': {
        'task': 'core.tasks.cleanup_stuck_jobs_task',
        'schedule': crontab(minute='*/30'),
    },

    # Cleanup orphaned browser processes every 15 minutes (was 10 - already checks age >10min)
    'cleanup-browser-processes': {
        'task': 'core.tasks.cleanup_browser_processes_task',
        'schedule': crontab(minute='*/15'),
    },

    # Reconcile PostgreSQL chunk rows against the ChromaDB index, hourly.
    # The document/news write path commits Postgres rows before embedding them,
    # with no shared transaction, so an embedding failure silently orphans them.
    #
    # This runs hourly rather than nightly because it is now the ONLY thing that
    # indexes GPU-processed documents: the GPU worker writes chunks to Postgres
    # and no longer embeds at all (it produced 384-dim vectors for a 1024-dim
    # Voyage collection, so every write failed). On the old nightly schedule a
    # document stayed unsearchable for up to a day, and a single GPU batch can
    # produce several thousand chunks — well past the old 2,000 cap, which
    # would have left a permanent backlog.
    'reconcile-chroma-index-hourly': {
        'task': 'core.tasks.reconcile_chroma_index_task',
        'schedule': crontab(minute=20),
        'kwargs': {'repair_limit': 5000},
    },

    # Date documents the GPU worker ingested with document_date NULL. Runs ten
    # minutes before the Chroma reconcile so a document is dated before its
    # chunks are indexed, and is a no-op when nothing is undated.
    # Embed news published in the last week that has no vectors yet. Runs
    # at 3 AM ET, clear of the 7 AM scrape, because embedding an item means
    # fetching its article - neither scraper stores the body. Bounded to 40
    # companies a run: process_company_news_isolated allows each 180s, so 15
    # is the most that fits inside this task's own 3540s soft limit. A
    # normal day brings ~20 new releases across ~15 companies, so that is
    # also roughly steady state; a backlog drains over several nights.
    'embed-recent-news-daily': {
        'task': 'core.tasks.embed_recent_news_for_rag_task',
        'schedule': crontab(hour=8, minute=0),  # 3 AM ET
        'kwargs': {'days': 7, 'max_companies': 15, 'limit_per_company': 10},
    },

    'backfill-document-dates-hourly': {
        'task': 'core.tasks.backfill_document_dates_task',
        'schedule': crontab(minute=10),
    },

    # Worker health check every 5 minutes
    'celery-worker-health-check': {
        'task': 'core.tasks.celery_worker_health_check_task',
        'schedule': crontab(minute='*/5'),
    },

    # Weekly watchlist briefing email to opted-in users (Monday 7 AM ET)
    'send-weekly-briefings': {
        'task': 'core.tasks.send_weekly_briefings_task',
        'schedule': crontab(hour=12, minute=0, day_of_week=1),  # Mon 7 AM ET
    },

    # Weekly industry report — Friday 5:30 PM ET / 22:30 UTC
    # Runs after fetch_stock_prices_task (21:30 UTC) so Friday's stock closes
    # exist. Co-runs with fetch_base_metals_prices_daily at 22:30 — if that
    # race causes Friday's base-metal row to be missed, the report falls back
    # to Thursday's close for those metals.
    'generate-weekly-industry-report': {
        'task': 'core.tasks.generate_weekly_industry_report_task',
        'schedule': crontab(hour=22, minute=30, day_of_week=5),  # Fri 5:30 PM ET
    },
}

# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'json': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'celery_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/celery-worker.log' if not DEBUG else 'celery-worker.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'mcp_servers': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

