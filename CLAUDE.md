# GoldVenture Platform - Claude Context Guide

## Project Overview

**GoldVenture Platform** (aka Junior Mining Intelligence) - mining investment platform aggregating junior mining company data, AI research tools, financing tracking, and a property exchange marketplace.

**Live URL:** https://juniorminingintelligence.com

### Servers (DigitalOcean)
| Server | IP | Purpose |
|--------|-----|---------|
| **Main (CPU)** | 137.184.168.166 | Django, Celery, PostgreSQL, ChromaDB, GPU Orchestrator |
| **GPU Worker** | Dynamic (on-demand) | Docling PDF processing (~$1.57/hr, auto-destroyed after 5min idle) |

**User Timezone:** EST (UTC-5)

---

## Deployment

```bash
# 1. Push locally
git add -A && git commit -m "Description" && git push

# 2. Deploy to server
ssh root@137.184.168.166
cd /var/www/goldventure && git pull

# 3. Restart services (if backend changes)
systemctl restart celery-worker celery-beat

# 4. Restart Gunicorn (if needed)
pkill -f gunicorn
cd backend && source venv/bin/activate
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 300 --daemon
```

> **CRITICAL:** Server path is `/var/www/goldventure` (NOT `/var/www/goldventure-platform`). Always deploy immediately after pushing — don't wait for the user to notice.

---

## Architecture

```
goldventure-platform/
├── backend/                    # Django REST API + Celery
│   ├── config/                 # Settings, celery config
│   ├── core/                   # Main app
│   │   ├── models.py          # 85 models (~4,700 lines)
│   │   ├── views.py           # ViewSets (~8,000 lines)
│   │   ├── tasks.py           # Celery tasks (~1,400 lines)
│   │   ├── serializers.py     # DRF serializers (~2,100 lines)
│   │   └── urls.py            # 145+ endpoints
│   ├── mcp_servers/           # Scrapers & processors
│   │   ├── website_crawler.py # Company news scraping (109KB)
│   │   ├── company_scraper.py # Company profile scraping (140KB)
│   │   ├── news_scraper.py    # Industry news
│   │   └── rag_utils.py       # ChromaDB vector search
│   ├── gpu_orchestrator.py    # On-demand GPU management
│   └── gpu_worker.py          # GPU document processing
└── frontend/                   # Next.js React application
```

---

## CRITICAL: Two Scraping Systems

| Function | File | Purpose | Strategies |
|----------|------|---------|------------|
| `crawl_news_releases()` | `website_crawler.py` | **Company news** (comprehensive) | NEWS-ENTRY, G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX, WIX-*, JOOMLA, STRAPI, etc. |
| `scrape_company_website()` | `company_scraper.py` | **Profile scraping** (limited news) | Basic article selectors only |

**Rules:**
- For company news: use `scrape_company_news_task` → `crawl_news_releases()`
- Onboarding uses the LIMITED scraper — manually trigger `/api/companies/{id}/scrape-news/` if news is missing
- Company news = press releases ONLY. Media coverage (Mining.com, Northern Miner, etc.) belongs in `NewsArticle` table (homepage). Blocked by `is_news_article_url()` in website_crawler.py
- Homepage news = `scrape_mining_news_task` (separate system)

---

## GPU Document Processing

- GPU Orchestrator polls every 60s, creates GPU droplet when `DocumentProcessingJob` records are pending
- GPU Worker processes with Docling + GPU, stores chunks in PostgreSQL + ChromaDB
- Auto-destroyed after 5min idle
- **NEVER process documents on CPU** — causes 100% CPU, very slow
- Let GPU orchestrator handle all `DocumentProcessingJob` records

```bash
# Check status
ps aux | grep gpu_orchestrator | grep -v grep
tail -100 /var/log/gpu_orchestrator.log
cat /var/run/gpu_orchestrator_state.json
```

---

## Company Onboarding & Verification

Single button click: scrape website → save to DB → scrape news → Claude-powered verification.

**Verification** (`claude_validator.py`): Checks description, projects, ticker, news. Auto-fixes missing data. Scores: `complete` (90-100), `incomplete` (50-89), `needs_review` (<50).

---

## Celery Beat Schedule

| Task | Schedule |
|------|----------|
| `scrape_all_companies_news_task` | 7 AM ET |
| `scrape_mining_news_task` | 8 AM, 1 PM, 6 PM ET |
| `scrape_metals_prices_task` | 9 AM, 4 PM ET |
| `fetch_stock_prices_task` | 4:30 PM ET (weekdays) |
| `cleanup_stuck_jobs_task` | Every 15 min |
| `auto_discover_and_process_documents_task` | Monday 2 AM |

Celery managed by systemd: `systemctl status celery-worker celery-beat`

---

## Key Models

| Model | Purpose |
|-------|---------|
| `Company` | Mining company profiles |
| `CompanyNews` / `NewsRelease` | Company news/press releases |
| `NewsReleaseFlag` / `DismissedNewsURL` | Financing flags & dismissed false positives |
| `Financing` | Investment rounds |
| `ScrapingJob` / `DocumentProcessingJob` | Job tracking |
| `NewsArticle` / `NewsScrapeJob` | Industry news (homepage) |

---

## Common Operations

```bash
# SSH to server
ssh root@137.184.168.166
cd /var/www/goldventure/backend && source venv/bin/activate

# Django shell
DJANGO_SETTINGS_MODULE=config.settings python -c "import django; django.setup(); from core.models import *; ..."

# Check Celery
systemctl status celery-worker celery-beat
tail -50 /var/log/celery-worker.log

# Manual news scrape
curl -X POST "https://juniorminingintelligence.com/api/companies/{id}/scrape-news/" -H "Authorization: Token $ADMIN_API_TOKEN"
```

---

## File Quick Reference

| Need to... | Look at... |
|------------|------------|
| Add news scraping strategy | `website_crawler.py` ~line 1640 |
| Modify Celery schedule | `config/settings.py` CELERY_BEAT_SCHEDULE |
| Add API endpoint | `core/urls.py` + `core/views.py` |
| Add database model | `core/models.py` |
| Fix financing detection | `core/tasks.py` ~lines 384, 810 |

---

## Troubleshooting

- **News not on homepage**: Check Celery running → `NewsScrapeJob` table → `NewsArticle` table
- **Company news missing**: Check `website` field set → check URL patterns in `website_crawler.py` → add strategy if needed
- **Onboarding stuck**: Check `ScrapingJob` table → Celery worker running → worker logs
- **Financing flags old**: Verify 7-day cutoff in `tasks.py`

---

## API Authentication

> **NEVER** hardcode tokens — use `$ADMIN_API_TOKEN` env var on server.

---

## Security Summary

- JWT: 1hr access, 3-day refresh, blacklist after rotation
- Rate limiting: 100/hr anon, 1000/hr auth
- SSRF protection via `security_utils.py` (`is_safe_url()`, `validate_redirect_url()`)
- ViewSets: read=AllowAny, write=IsAuthenticated
- Password minimum: 12 chars (NIST 800-63B)
- WebSocket auth checks `is_active`; origins: production only

---

## Key Lessons (Patterns to Remember)

### Scraping Patterns
- Many sites organize news by year (`/news/YYYY/`). Always add year-based URL patterns including current and previous 2 years
- Multilingual sites combine prefixes: `/en/investors/news/YYYY/`
- Companies with custom news URLs: use `news_url` field on Company model
- WordPress sites often have REST API at `/wp-json/wp/v2/posts` — check before HTML scraping
- Wix has 3+ layout patterns (WIX-HTML, WIX-BUTTON, WIX-RICHTEXT)
- JS-rendered sites (Strapi, BrighterIR, Beaver Builder): check for API endpoints
- When slug deduplication fails: exclude generic filenames (default.aspx, index.html)

### Date Parsing
- Strip ordinal suffixes (st/nd/rd/th) early in `parse_date_standalone()`
- For ambiguous DD.MM vs MM.DD: check sibling dates on same page for context
- Regex with single-letter groups like `(M)?` need negative lookahead `(?![a-zA-Z])`

### Deployment & Operations
- Always restart Celery after deploying — worker keeps OLD code in memory
- Check if batch is already running before triggering manual scrapes (distributed lock exists)
- `company_scraper.py` has its OWN news extraction separate from `website_crawler.py` — fixes must go to the correct file
- `crawl4ai` has `page_timeout=60000` default — slow sites cause 60s blocks per URL pattern
- Skip content processing during daily scrapes (only during onboarding) to avoid 500s+ per company

### Code Quality Rules
- Investigate root cause before coding fixes
- Read actual code/data/database before making claims
- Test performance impact before deploying scheduled task changes
- Never use sed hacks on server files — use proper tools
- For optional string fields: use `blank=True, default=''` (NOT `null=True`)
- When `parse_date_standalone()` returns None for valid-looking dates: check for ordinal suffixes, unusual formats