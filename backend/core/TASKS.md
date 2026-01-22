# Celery Tasks Reference

## Overview

Background tasks are defined in `core/tasks.py` and executed by Celery workers. Celery Beat handles scheduling.

---

## Scheduled Tasks

### News Scraping

#### `scrape_all_companies_news_task`
- **Schedule:** Daily at 7 AM ET (12:00 UTC)
- **Purpose:** Scrape news releases from ALL company websites
- **Duration:** 30-60 minutes depending on company count
- **Calls:** `scrape_single_company_news_task` for each company

#### `scrape_mining_news_task`
- **Schedule:** 8 AM, 1 PM, 6 PM ET (13:00, 18:00, 23:00 UTC)
- **Purpose:** Scrape industry news from Mining.com, Northern Miner
- **Duration:** 1-2 minutes
- **Populates:** `NewsArticle` model (homepage "Latest Mining News")

### Market Data

#### `scrape_metals_prices_task`
- **Schedule:** 9 AM, 4 PM ET (14:00, 21:00 UTC)
- **Purpose:** Fetch gold, silver, copper prices from Kitco
- **Populates:** `MetalPrice` model

#### `fetch_stock_prices_task`
- **Schedule:** 4:30 PM ET weekdays (21:30 UTC Mon-Fri)
- **Purpose:** Fetch stock prices via Alpha Vantage/Yahoo Finance
- **Populates:** `StockPrice` model

### Document Processing

#### `auto_discover_and_process_documents_task`
- **Schedule:** Weekly, Monday 2 AM
- **Purpose:** Process documents for 10 companies
- **Document types:** NI 43-101, news releases, presentations

### Maintenance

#### `cleanup_stuck_jobs_task`
- **Schedule:** Every 15 minutes
- **Purpose:** Mark stuck jobs (running > 30 min) as failed
- **Cleans:** `ScrapingJob`, `DocumentProcessingJob`

---

## On-Demand Tasks

### `scrape_company_news_task(company_id)`
- **Purpose:** Scrape news for a single company
- **Trigger:** Manual API call or scheduled task
- **Location:** Line ~240
- **Financing Detection:** Lines ~384-465

### `scrape_single_company_news_task(company_id)`
- **Purpose:** Lightweight single company scrape (used by batch task)
- **Location:** Line ~720
- **Financing Detection:** Lines ~810-850

### `scrape_company_website_task(job_id, sections=None)`
- **Purpose:** Full website scrape for company onboarding
- **Location:** Line ~975
- **Timeout:** 10 minutes
- **Used by:** Admin onboarding flow

### `process_document_task(job_id)`
- **Purpose:** Process a single document (PDF extraction, RAG)
- **Location:** Line ~170

---

## Financing Detection

Both news scraping tasks include financing detection:

```python
financing_keywords = [
    'private placement', 'financing', 'funding round',
    'capital raise', 'bought deal', 'equity financing',
    'debt financing', 'flow-through', 'warrant',
    'subscription', 'offering'
]

strategic_keywords = [
    'strategic investment', 'strategic partner',
    'equity stake', 'strategic alliance'
]
```

### Key Logic (as of 2026-01-22)
1. Only flag news **within 7 days** of current date
2. Check against `DismissedNewsURL` for similar titles (0.85 threshold)
3. Create `NewsReleaseFlag` with `status='pending'`
4. Send email notification for new flags

**Location:** `scrape_company_news_task` lines ~432-465, `scrape_single_company_news_task` lines ~821-846

---

## Task Configuration

### Celery Beat Schedule (config/settings.py)

```python
CELERY_BEAT_SCHEDULE = {
    'scrape-metals-prices-morning': {
        'task': 'core.tasks.scrape_metals_prices_task',
        'schedule': crontab(hour=14, minute=0),  # 9 AM ET
    },
    'scrape-metals-prices-afternoon': {
        'task': 'core.tasks.scrape_metals_prices_task',
        'schedule': crontab(hour=21, minute=0),  # 4 PM ET
    },
    'fetch-stock-prices-daily': {
        'task': 'core.tasks.fetch_stock_prices_task',
        'schedule': crontab(hour=21, minute=30, day_of_week='mon-fri'),
    },
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
    'scrape-all-companies-news-daily': {
        'task': 'core.tasks.scrape_all_companies_news_task',
        'schedule': crontab(hour=12, minute=0),  # 7 AM ET
    },
    'cleanup-stuck-jobs': {
        'task': 'core.tasks.cleanup_stuck_jobs_task',
        'schedule': crontab(minute='*/15'),
    },
    'auto-discover-documents-weekly': {
        'task': 'core.tasks.auto_discover_and_process_documents_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),
        'kwargs': {'limit': 10, 'document_types': ['ni43101', 'news_release', 'presentation']}
    },
}
```

---

## Managing Celery

### Check Status
```bash
# Check processes
ps aux | grep celery | grep -v grep

# Check active tasks
celery -A config inspect active

# Check queued tasks
celery -A config inspect reserved

# View logs
tail -f /var/log/celery-worker.log
tail -f /var/log/celery-beat.log
```

### Restart Services
```bash
# Kill existing
pkill -f 'celery -A config'

# Remove stale PID files
rm -f /var/run/celery-beat.pid /var/run/celery-worker.pid

# Start beat (scheduler)
cd /var/www/goldventure/backend && source venv/bin/activate
celery -A config beat --detach \
  --logfile=/var/log/celery-beat.log \
  --pidfile=/var/run/celery-beat.pid

# Start worker
celery -A config worker --detach --concurrency=2 \
  --logfile=/var/log/celery-worker.log \
  --pidfile=/var/run/celery-worker.pid
```

### Trigger Task Manually
```bash
cd /var/www/goldventure/backend && source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python -c "
from core.tasks import scrape_all_companies_news_task
result = scrape_all_companies_news_task.delay()
print(f'Task ID: {result.id}')
"
```

### Purge Queue
```bash
celery -A config purge -f
```

---

## Troubleshooting

### Tasks not running
1. Check worker is alive: `ps aux | grep 'celery.*worker'`
2. Check beat is alive: `ps aux | grep 'celery.*beat'`
3. Check Redis is running: `redis-cli ping`
4. Check logs for errors

### Tasks stuck in pending
1. Worker may have died mid-task
2. Restart worker
3. Task will be retried (if acks_late=True)

### Worker keeps dying
1. Check memory usage: `free -h`
2. Check for OOM kills: `dmesg | grep -i kill`
3. Reduce concurrency: `--concurrency=1`

### Beat not scheduling
1. Check beat log for errors
2. Verify schedule in settings.py
3. Restart beat process
