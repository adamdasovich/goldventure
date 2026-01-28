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
    }
}

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
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
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Reduced from 24h for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # Invalidate old refresh tokens
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
STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID', '')  # Optional: Pre-configured price ID from Stripe Dashboard

# Stripe Store Webhook (separate webhook for e-commerce store)
STRIPE_STORE_WEBHOOK_SECRET = os.getenv('STRIPE_STORE_WEBHOOK_SECRET', '')

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

# Notification Recipients - MUST be set via environment variables in production
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
NI43101_NOTIFICATION_EMAIL = os.getenv('NI43101_NOTIFICATION_EMAIL', 'notifications@example.com')
FINANCING_NOTIFICATION_EMAIL = os.getenv('FINANCING_NOTIFICATION_EMAIL', 'notifications@example.com')

# ============================================================================
# DJANGO CHANNELS & WEBSOCKET CONFIGURATION
# ============================================================================

# ASGI Application
ASGI_APPLICATION = 'config.asgi.application'

# Channels (for WebSocket support)
INSTALLED_APPS += ['channels']

# Channel Layers Configuration (In-Memory for development)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Cache Configuration
REDIS_URL = os.getenv('REDIS_URL', None)
if REDIS_URL and not DEBUG:
    # Production: Use Redis for caching and channel layers
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
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
    # Development: Use LocMemCache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
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
CELERY_RESULT_EXPIRES = 86400  # 24 hours - prevent Redis memory bloat from old results

# Celery Beat Schedule - Periodic Tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
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

    # RECOMMENDED SCHEDULE ARCHITECTURE: Auto-discover and process documents
    # Conservative approach: 10 companies per week, focused on high-priority document types
    'auto-discover-documents-weekly': {
        'task': 'core.tasks.auto_discover_and_process_documents_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Every Monday at 2 AM
        'kwargs': {
            'limit': 10,  # Process 10 companies per week
            'document_types': ['ni43101', 'news_release', 'presentation']  # High-priority types
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
    'scrape-all-companies-news-daily': {
        'task': 'core.tasks.scrape_all_companies_news_task',
        'schedule': crontab(hour=12, minute=0),  # 7 AM ET
    },

    # Cleanup stuck jobs every 15 minutes
    # Detects and marks as failed any jobs stuck in 'running' or 'processing' state
    'cleanup-stuck-jobs': {
        'task': 'core.tasks.cleanup_stuck_jobs_task',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}

