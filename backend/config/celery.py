"""
Celery configuration for GoldVenture Platform
"""
import logging
import os

from celery import Celery
from celery.signals import worker_process_init

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('goldventure')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Secret scrubbing -- see scrub_secrets_from_environ() below for the why.
#
# Three groups, because "is it safe to delete this name" has three different
# answers and a single flat list would hide that.
# --------------------------------------------------------------------------

# Group 1: the value is also on `settings` under the SAME name, and every
# reader goes through settings. Scrubbed only once settings is confirmed to
# hold a non-empty value.
_SCRUB_VIA_SETTINGS = (
    'SECRET_KEY',                     # session + CSRF signing
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'STRIPE_COMPANY_WEBHOOK_SECRET',
    'STRIPE_STORE_WEBHOOK_SECRET',
    'STRIPE_PLATFORM_WEBHOOK_SECRET',
    'ANTHROPIC_API_KEY',              # core/claude_validator.py reads settings first
    'VOYAGE_API_KEY',                 # mcp_servers/embeddings.py._voyage_api_key()
    'EMAIL_HOST_PASSWORD',            # core/email_service.py reads settings first
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'ALPHA_VANTAGE_API_KEY',
    'TWELVE_DATA_API_KEY',
)

# Group 2: the value survives somewhere other than settings.<NAME>. DATABASES
# is built at settings import, so the connection password is already captured
# in the dict and psycopg never re-reads the environment.
_SCRUB_VIA_RESOLVER = (
    ('DB_PASSWORD', lambda s: (s.DATABASES.get('default') or {}).get('PASSWORD') or ''),
)

# Group 3: nothing in a Celery worker reads these at all.
#   DO_API_TOKEN / DO_SSH_KEY_ID / DB_PASSWORD are read by gpu_orchestrator.py
#     and gpu_worker.py, which are standalone processes -- not Celery children,
#     and gpu_orchestrator has its own env file. Removing them here cannot
#     affect them.
#   WS_SECRET_ACCESS_KEY is a typo'd duplicate of AWS_SECRET_ACCESS_KEY in
#     .env, holding the same live credential, read by no code anywhere.
_SCRUB_NO_READER_HERE = (
    'DO_API_TOKEN',
    'DO_SSH_KEY_ID',
    'WS_SECRET_ACCESS_KEY',
)


@worker_process_init.connect
def scrub_secrets_from_environ(**_kwargs):
    """
    Drop secrets from os.environ in every Celery worker child process.

    WHY: these workers spawn Playwright/Chromium to crawl arbitrary
    third-party sites, and a child process inherits its parent's environment.
    settings.py calls load_dotenv(), so all 17 secrets in .env sat in the
    environment of every `chrome` process -- and of `chrome_crashpad`, whose
    entire job is to serialise process memory to disk on a crash. On 2026-09-01
    a dump under /root/.config/google-chrome-for-testing/Crash Reports/pending/
    was found to contain the full live Stripe secret key. That key was rotated
    the same day; this stops its replacement, and everything else, being
    exposed the same way.

    WHY HERE rather than at the launch sites: crawl4ai's BrowserConfig exposes
    no `env` parameter, so the environment cannot be scrubbed per launch, and
    there are seven launch sites across four modules. Doing it once per worker
    child covers all of them, including any added later.

    WHY A SIGNAL rather than module import: config/__init__.py imports this
    module while Django is still importing settings, so calling django.setup()
    here would be re-entrant. worker_process_init fires in each prefork child
    once the app registry is ready -- including children respawned by
    --max-tasks-per-child, which fork from a parent that still holds the values.

    A name in group 1 or 2 is removed ONLY once its value is confirmed to still
    be reachable after removal, so a misconfigured .env degrades to "still
    leaking" rather than to "payments silently broken". Names that are not
    secret (STRIPE_PUBLISHABLE_KEY, the *_PRODUCT_ID values, DB_HOST/USER/NAME)
    are deliberately left alone.
    """
    from django.conf import settings

    scrubbed, skipped = [], []

    for name in _SCRUB_VIA_SETTINGS:
        if name not in os.environ:
            continue
        if getattr(settings, name, ''):
            del os.environ[name]
            scrubbed.append(name)
        else:
            skipped.append(name)

    for name, resolver in _SCRUB_VIA_RESOLVER:
        if name not in os.environ:
            continue
        try:
            survives = resolver(settings)
        except Exception:
            survives = ''
        if survives:
            del os.environ[name]
            scrubbed.append(name)
        else:
            skipped.append(name)

    for name in _SCRUB_NO_READER_HERE:
        if name in os.environ:
            del os.environ[name]
            scrubbed.append(name)

    if scrubbed:
        logger.info(
            'Scrubbed %d secret(s) from the worker environment so browser '
            'subprocesses cannot inherit them: %s',
            len(scrubbed), ', '.join(sorted(scrubbed))
        )
    if skipped:
        logger.warning(
            'Left %s in os.environ: the value would not survive removal, so '
            'scrubbing would break whatever reads it. Check .env.',
            ', '.join(sorted(skipped))
        )
