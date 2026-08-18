# GoldVenture Platform - Claude Context Guide

## Project Overview

**GoldVenture Platform** (aka Junior Mining Intelligence) - mining investment platform aggregating junior mining company data, AI research tools, financing tracking, and a property exchange marketplace.

**Live URL:** https://juniorminingintelligence.com

### Servers (DigitalOcean)

| Server         | IP                  | Purpose                                                            |
| -------------- | ------------------- | ------------------------------------------------------------------ |
| **Main (CPU)** | 137.184.168.166     | Django, Celery, PostgreSQL, ChromaDB, GPU Orchestrator             |
| **GPU Worker** | Dynamic (on-demand) | Docling PDF processing (~$1.57/hr, auto-destroyed after 5min idle) |

**User Timezone:** EST (UTC-5)

---

## Deployment

### Backend (Django / Celery / Gunicorn)

```bash
# 1. Push locally
git add -A && git commit -m "Description" && git push

# 2. Deploy to server
ssh root@137.184.168.166
cd /var/www/goldventure && git pull

# 3. Restart services (if backend changes) — THREE workers, not one
systemctl restart celery-worker celery-scrape celery-interactive celery-beat

# 4. Reload Gunicorn (zero-downtime, picks up new code)
systemctl reload gunicorn
```

### Frontend (Next.js — pm2)

The Next.js app runs under **pm2** as process `goldventure-frontend` (`next start`).
A rebuild is required for any frontend change — `next start` serves the built
output, so editing source without `npm run build` has no effect.

```bash
# After git pull on the server:
cd /var/www/goldventure/frontend
set -o pipefail                     # so a failed build is NOT masked by the pipe
npm run build 2>&1 | grep -v baseline-browser-mapping   # ~2-4 min; serves from .next/
pm2 restart goldventure-frontend    # picks up the new build

# Useful:
pm2 list                            # status / restart count
pm2 logs goldventure-frontend       # tail logs (check after a deploy)
```

> **NOTE:** The `grep -v` filters an unsuppressable build warning
> (`[baseline-browser-mapping] The data in this module is over two months old`).
> It comes from `next/dist/compiled/browserslist/index.js` — Next 16.0.10's
> **vendored** copy, which does a bare `timestamp < twoMonthsAgo && console.warn()`
> with no env-var guard. `BROWSERSLIST_IGNORE_OLD_DATA` exists only in the
> standalone `baseline-browser-mapping` package and has no effect here, and no
> dependency bump silences it. Cosmetic only, no runtime impact; it should go away
> on a future Next upgrade (currently on 16.0.10). Drop the pipe once it does.
> Keep `set -o pipefail` — without it the pipeline reports grep's exit status and
> a broken build would look like it succeeded.

> **CRITICAL:** Server path is `/var/www/goldventure` (NOT `/var/www/goldventure-platform`). Always deploy immediately after pushing — don't wait for the user to notice.
>
> **CRITICAL:** Gunicorn is managed by systemd (`/etc/systemd/system/gunicorn.service`). NEVER use `pkill -f gunicorn` + `gunicorn --daemon` — this creates duplicate processes because systemd auto-restarts the killed process (`Restart=always`). Use `systemctl reload gunicorn` for normal deploys: the unit defines `ExecReload=/bin/kill -s HUP $MAINPID`, so the master survives and gracefully cycles workers (zero downtime), and each worker re-imports the new code. Use `systemctl restart gunicorn` only when the master itself must restart (e.g. changed `ExecStart` args or env vars).
>
> **NOTE:** Zero-downtime reload works because `ExecStart` does NOT use `--preload`. If `--preload` is ever added, HUP no longer picks up code changes — a full `restart` would be required again.

---

## Architecture

```
goldventure-platform/
├── backend/                    # Django REST API + Celery
│   ├── config/                 # Settings, celery config
│   ├── core/                   # Main app
│   │   ├── models/            # 89 models split into 8 domain files
│   │   ├── views/             # ViewSets split into 23 domain files
│   │   ├── serializers/       # DRF serializers split into 10 domain files
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

| Function                   | File                 | Purpose                             | Strategies                                                                                 |
| -------------------------- | -------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------ |
| `crawl_news_releases()`    | `website_crawler.py` | **Company news** (comprehensive)    | NEWS-ENTRY, G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX, WIX-\*, JOOMLA, STRAPI, etc. |
| `scrape_company_website()` | `company_scraper.py` | **Profile scraping** (limited news) | Basic article selectors only                                                               |

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

| Task                                       | Schedule              |
| ------------------------------------------ | --------------------- |
| `scrape_all_companies_news_task`           | 7 AM ET               |
| `scrape_mining_news_task`                  | 8 AM, 1 PM, 6 PM ET   |
| `scrape_metals_prices_task`                | 9 AM, 4 PM ET         |
| `fetch_stock_prices_task`                  | 4:30 PM ET (weekdays) |
| `cleanup_stuck_jobs_task`                  | Every 15 min          |
| `auto_discover_and_process_documents_task` | Monday 2 AM           |

### Celery Workers — three queues, one worker each

Everything used to share a single queue, so the 7 AM batch (~400 scrape tasks,
concurrency 2) starved everything behind it — health checks and onboarding sat
for hours. `CELERY_TASK_ROUTES` in `config/settings.py` splits the work:

| Queue         | Unit                         | Concurrency | MemoryMax | Carries                                           |
| ------------- | ---------------------------- | ----------- | --------- | ------------------------------------------------- |
| `scrape`      | `celery-scrape.service`      | 2           | 1800M     | Bulk crawling. Browser-heavy, runs all day.       |
| `interactive` | `celery-interactive.service` | 2           | 900M      | User-triggered onboarding/manual scrapes.         |
| `default`     | `celery-worker.service`      | 2           | 500M      | Health checks, cleanups, prices, emails, reports. |

```bash
systemctl status celery-worker celery-scrape celery-interactive celery-beat
journalctl -u celery-scrape -n 50 --no-pager     # output goes to journald
```

> **CRITICAL:** A task routed to a queue with no consumer is silently swallowed
> — no error, it just never runs. If you add a queue to `CELERY_TASK_ROUTES`,
> create its worker FIRST. Re-provision all three with
> `bash backend/deploy/setup-celery-queues.sh` (idempotent; it writes the unit
> files, reloads systemd, and prints which queues have live consumers).
>
> **CRITICAL:** Each worker needs a DISTINCT `-n` node name. Two sharing one
> produces `DuplicateNodenameWarning` and silently breaks `celery inspect`
> (that bug cost a day on 2026-08-14).
>
> **NOTE:** `celery-scrape` also consumes the legacy `celery` queue to drain
> pre-split tasks. Drop `,celery` from its `-Q` once `redis-cli llen celery`
> reaches 0.
>
> **NOTE:** `CELERY_TASK_ACKS_LATE = True`, so a task killed by a restart is
> redelivered rather than lost. Restarting mid-batch is safe.

---

## Key Models

| Model                                   | Purpose                                     |
| --------------------------------------- | ------------------------------------------- |
| `Company`                               | Mining company profiles                     |
| `CompanyNews` / `NewsRelease`           | Company news/press releases                 |
| `NewsReleaseFlag` / `DismissedNewsURL`  | Financing flags & dismissed false positives |
| `Financing`                             | Investment rounds                           |
| `ScrapingJob` / `DocumentProcessingJob` | Job tracking                                |
| `NewsArticle` / `NewsScrapeJob`         | Industry news (homepage)                    |

---

## Common Operations

```bash
# SSH to server
ssh root@137.184.168.166
cd /var/www/goldventure/backend && source venv/bin/activate

# Django shell
DJANGO_SETTINGS_MODULE=config.settings python -c "import django; django.setup(); from core.models import *; ..."

# Check Celery (three workers — see the Celery Workers section)
systemctl status celery-worker celery-scrape celery-interactive celery-beat
journalctl -u celery-scrape -n 50 --no-pager

# Confirm every queue has a live consumer (a queue without one eats tasks)
cd /var/www/goldventure/backend && source venv/bin/activate
celery -A config inspect active_queues --timeout 45
for q in celery default scrape interactive; do echo "$q $(redis-cli llen $q)"; done

# Manual news scrape
curl -X POST "https://juniorminingintelligence.com/api/companies/{id}/scrape-news/" -H "Authorization: Token $ADMIN_API_TOKEN"
```

---

## File Quick Reference

| Need to...                 | Look at...                                                                  |
| -------------------------- | --------------------------------------------------------------------------- |
| Add news scraping strategy | `mcp_servers/website_crawler.py` ~line 1640                                 |
| Modify Celery schedule     | `config/settings.py` CELERY_BEAT_SCHEDULE                                   |
| Add API endpoint           | `core/urls.py` + `core/views/<domain>.py`                                   |
| Add database model         | `core/models/<domain>.py` + `core/models/__init__.py` (re-export)           |
| Add serializer             | `core/serializers/<domain>.py` + `core/serializers/__init__.py` (re-export) |
| Fix financing detection    | `core/tasks.py` ~lines 384, 810                                             |

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
- **Gunicorn is managed by systemd** — NEVER `pkill -f gunicorn` + `gunicorn --daemon`. This creates duplicate processes (systemd has `Restart=always`). Use `systemctl reload gunicorn` for code deploys (zero-downtime HUP via `ExecReload`, workers re-import new code); use `systemctl restart gunicorn` only when the master must restart (changed `ExecStart`/env). Reload depends on no `--preload` in `ExecStart`
- When splitting/refactoring Python files, verify ALL runtime imports are present — `import` at module level in the original file may not carry to split files, causing 500s only on code paths that hit the missing name
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
