# GoldVenture Platform - Claude Context Guide

> This file is automatically read by Claude Code at the start of each session.
> Keep it updated with critical information to maintain context across conversations.

## Project Overview

**GoldVenture Platform** (aka Junior Mining Intelligence) is a comprehensive mining investment platform that:
- Aggregates junior mining company data (profiles, news, financials)
- Provides AI-powered research tools via Claude
- Tracks financing announcements and investment opportunities
- Offers educational content and a property exchange marketplace

**Live URL:** https://juniorminingintelligence.com

### Servers (DigitalOcean)
| Server | IP | Specs | Purpose |
|--------|-----|-------|---------|
| **Main (CPU)** | 137.184.168.166 | 8 GB RAM / 80 GB Disk | Django, Celery, PostgreSQL, ChromaDB, GPU Orchestrator |
| **GPU Worker** | Dynamic (on-demand) | 48 GB VRAM / RTX 6000 Ada | Docling PDF processing (GPU-accelerated) |

> **Note:** GPU worker droplets are created dynamically by the GPU Orchestrator when document processing jobs are pending. They are auto-destroyed after 5 minutes idle to minimize costs (~$1.57/hr).

---

## Deployment Workflow

> **CRITICAL:** After making code changes locally, you MUST deploy to the server!

### Standard Deployment
```bash
# 1. Commit and push locally
git add -A && git commit -m "Description" && git push

# 2. SSH to main server and pull
ssh root@137.184.168.166
cd /var/www/goldventure && git pull

# 3. Restart Celery (if backend changes)
pkill -f 'celery -A config'
cd /var/www/goldventure/backend && source venv/bin/activate
celery -A config beat --detach --logfile=/var/log/celery-beat.log --pidfile=/var/run/celery-beat.pid
celery -A config worker --detach --concurrency=2 --logfile=/var/log/celery-worker.log --pidfile=/var/run/celery-worker.pid

# 4. Restart Gunicorn (if needed)
pkill -f gunicorn
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 300 --daemon
```

### GPU Worker Deployment
```bash
ssh root@134.122.36.137
cd /var/www/goldventure && git pull
# Restart GPU worker service as needed
```

---

## Architecture Overview

```
goldventure-platform/
├── backend/                    # Django REST API + Celery
│   ├── config/                 # Django settings, celery config
│   ├── core/                   # Main app (models, views, tasks, urls)
│   │   ├── models.py          # 85 models (~4,700 lines)
│   │   ├── views.py           # ViewSets & endpoints (~8,000 lines)
│   │   ├── tasks.py           # Celery background tasks (~1,400 lines)
│   │   ├── serializers.py     # DRF serializers (~2,100 lines)
│   │   └── urls.py            # API routing (145+ endpoints)
│   ├── mcp_servers/           # Scrapers & data processors
│   │   ├── website_crawler.py # Company news scraping (109KB)
│   │   ├── company_scraper.py # Company profile scraping (140KB)
│   │   ├── news_scraper.py    # Industry news (Mining.com, Northern Miner)
│   │   └── rag_utils.py       # ChromaDB vector search
│   ├── gpu_orchestrator.py    # On-demand GPU droplet management
│   ├── gpu_worker.py          # GPU-accelerated document processing
│   └── templates/             # Email templates
└── frontend/                   # Next.js React application
```

---

## GPU Document Processing Architecture

### How It Works
1. **GPU Orchestrator** (`gpu_orchestrator.py`) runs on main server, polls every 60 seconds
2. When `DocumentProcessingJob` records with status='pending' exist, it creates a GPU droplet
3. **GPU Worker** (`gpu_worker.py`) runs on the GPU droplet, processes documents with Docling + GPU
4. Worker stores chunks in PostgreSQL and embeddings in ChromaDB
5. When queue is empty for 5 minutes, orchestrator destroys the GPU droplet

### Key Files
| File | Location | Purpose |
|------|----------|---------|
| `gpu_orchestrator.py` | `/var/www/goldventure/backend/` | Manages GPU droplet lifecycle |
| `gpu_worker.py` | `/var/www/goldventure/backend/` | Processes documents on GPU |
| Orchestrator log | `/var/log/gpu_orchestrator.log` | GPU creation/destruction events |
| State file | `/var/run/gpu_orchestrator_state.json` | Current GPU droplet tracking |

### Environment Variables (Main Server)
- `DO_API_TOKEN` - DigitalOcean API token for droplet management
- `DO_SSH_KEY_ID` - SSH key ID for GPU droplet access
- `DB_PASSWORD` - Transferred securely to GPU worker via SCP

### CRITICAL: CPU vs GPU Processing
> **IMPORTANT:** Document processing should ONLY happen on the GPU worker!

The CPU cannot handle Docling processing efficiently (causes 100% CPU, very slow).

- ❌ **DO NOT** call `process_document_queue()` from views or admin
- ❌ **DO NOT** use threading to process documents on CPU
- ✅ **DO** let the GPU orchestrator handle all `DocumentProcessingJob` records
- ✅ Jobs stay in 'pending' status until GPU worker picks them up

### Checking GPU Status
```bash
# Is orchestrator running?
ps aux | grep gpu_orchestrator | grep -v grep

# Check orchestrator logs
tail -100 /var/log/gpu_orchestrator.log

# Check current state
cat /var/run/gpu_orchestrator_state.json

# List active GPU droplets
curl -s -H "Authorization: Bearer $DO_API_TOKEN" \
  "https://api.digitalocean.com/v2/droplets?tag_name=gpu-worker"
```

---

## Critical Patterns & Gotchas

### News Scraping - TWO DIFFERENT FUNCTIONS (CRITICAL)

> **STOP AND READ THIS:** There are TWO completely different news scraping systems. Using the wrong one will result in missing news!

| Function | File | Purpose | Strategies |
|----------|------|---------|------------|
| `crawl_news_releases()` | `website_crawler.py` | **Company news releases** | NEWS-ENTRY, G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX (comprehensive) |
| `scrape_company_website()` | `company_scraper.py` | **General website scraping** (documents, people, basic news) | Basic article selectors only (limited) |

**Rules:**
- ✅ For company news: Use `crawl_news_releases()` via `scrape_company_news_task`
- ✅ For general onboarding: Use `scrape_company_website()` via `scrape_company_website_task`
- ❌ NEVER rely on `scrape_company_website()` for comprehensive news - it has limited strategies
- ❌ The onboarding process (`approve_company`) uses `scrape_company_website()` which may NOT capture all news

**Why onboarding may miss news:**
The `approve_company` endpoint in `views.py` calls `scrape_company_website()` which has basic news extraction. It does NOT call `scrape_company_news_task` which uses the comprehensive `crawl_news_releases()` function with all the specialized strategies (NEWS-ENTRY, G2, etc.).

**Fix for missing news after onboarding:**
Manually trigger news scrape: `POST /api/companies/{id}/scrape-news/`

### Financing Flags
- Only flag news within **7 days** of current date
- Check added 2026-01-22 in `tasks.py` lines ~432 and ~821
- Similarity threshold for dismissed news: 0.85

### Celery
- Worker dies silently - always check: `ps aux | grep celery`
- Beat schedules tasks, Worker executes them - BOTH must be running
- Restart command:
  ```bash
  pkill -f 'celery -A config'
  cd /var/www/goldventure/backend && source venv/bin/activate
  celery -A config beat --detach --logfile=/var/log/celery-beat.log --pidfile=/var/run/celery-beat.pid
  celery -A config worker --detach --concurrency=2 --logfile=/var/log/celery-worker.log --pidfile=/var/run/celery-worker.pid
  ```

### Server Paths
- **Correct:** `/var/www/goldventure`
- **Wrong:** `/var/www/goldventure-platform`

---

## Celery Beat Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `scrape_all_companies_news_task` | 7 AM ET (12:00 UTC) | Scrape news from all company websites |
| `scrape_mining_news_task` | 8 AM, 1 PM, 6 PM ET | Scrape Mining.com, Northern Miner |
| `scrape_metals_prices_task` | 9 AM, 4 PM ET | Kitco metals prices |
| `fetch_stock_prices_task` | 4:30 PM ET (weekdays) | Stock prices via Alpha Vantage |
| `cleanup_stuck_jobs_task` | Every 15 min | Mark stuck jobs as failed |
| `auto_discover_and_process_documents_task` | Monday 2 AM | Process 10 companies' documents |

---

## Key Models

| Model | Purpose |
|-------|---------|
| `Company` | Mining company profiles |
| `NewsRelease` | Company news releases |
| `CompanyNews` | News with classification (used by frontend) |
| `NewsReleaseFlag` | Financing news pending review |
| `DismissedNewsURL` | False positive financing flags |
| `Financing` | Investment rounds |
| `ScrapingJob` | Track company onboarding scrapes |
| `DocumentProcessingJob` | Track document processing |
| `NewsArticle` | Industry news (homepage) |
| `NewsScrapeJob` | Track industry news scrapes |

---

## Common Operations

### SSH to Server
```bash
ssh root@137.184.168.166
cd /var/www/goldventure/backend
source venv/bin/activate
```

### Run Django Commands
```bash
DJANGO_SETTINGS_MODULE=config.settings python -c "
import django
django.setup()
from core.models import Company
# ... your code
"
```

### Check Celery Status
```bash
ps aux | grep celery | grep -v grep
tail -50 /var/log/celery-worker.log
tail -50 /var/log/celery-beat.log
```

### Trigger Manual Scrape
```bash
# Single company news
curl -X POST "https://juniorminingintelligence.com/api/companies/{id}/scrape-news/" \
  -H "Authorization: Token {token}"

# All companies
python -c "from core.tasks import scrape_all_companies_news_task; scrape_all_companies_news_task.delay()"
```

---

## Recent Changes (Keep Updated)

### 2026-01-22
- Added RLM (Recursive Language Model) processor for long NI 43-101 documents
  - New file: `backend/mcp_servers/rlm_processor.py`
  - New command: `python manage.py process_document_rlm`
  - Auto-switches to RLM for documents >50 pages
- Fixed financing flags to only flag news within 7 days
- Added UIKit grid strategy for Scottie Resources
- Fixed MM/DD/YY date parsing for Silverco Mining
- Fixed geological term "contact" being filtered incorrectly
- Restarted Celery after worker died

### 2026-01-20
- Added Elementor Loop strategy for LaFleur Minerals
- Fixed ASPX Evergreen CMS strategy for Harvest Gold

---

## API Authentication

**Admin Token:** `REDACTED_TOKEN`

```bash
curl -H "Authorization: Token REDACTED_TOKEN" \
  https://juniorminingintelligence.com/api/endpoint/
```

---

## Troubleshooting

### News not appearing on homepage
1. Check if Celery worker is running
2. Check `NewsScrapeJob` table for recent completions
3. Check `NewsArticle` table for recent entries

### Company news not scraping
1. Verify company has `website` field set
2. Check if news URL pattern is supported in `website_crawler.py`
3. Add new strategy if needed (see SCRAPING.md)

### Onboarding stuck
1. Check `ScrapingJob` table for stuck jobs
2. Verify Celery worker is processing tasks
3. Check worker logs for errors

### Financing flags showing old news
1. Verify 7-day cutoff is in place in `tasks.py`
2. Clean up old flags manually if needed

---

## File Quick Reference

| Need to... | Look at... |
|------------|------------|
| Add news scraping strategy | `backend/mcp_servers/website_crawler.py` line ~1640 |
| Modify Celery schedule | `backend/config/settings.py` CELERY_BEAT_SCHEDULE |
| Add API endpoint | `backend/core/urls.py` and `backend/core/views.py` |
| Add database model | `backend/core/models.py` |
| Modify background task | `backend/core/tasks.py` |
| Fix financing detection | `backend/core/tasks.py` lines ~384 and ~810 |

---

## Common Mistakes (Do NOT)

> **IMPORTANT:** When the user corrects a mistake, UPDATE THIS SECTION immediately.

### Server & Paths
- ❌ Server path is NOT `/var/www/goldventure-platform`
- ✅ Server path IS `/var/www/goldventure`

### Scraping Functions (TWO DIFFERENT SYSTEMS - MEMORIZE THIS)
- ❌ Do NOT use `scrape_company_website()` (company_scraper.py) for comprehensive news - it has LIMITED strategies
- ❌ Do NOT assume onboarding captures all news - it uses the LIMITED scraper
- ✅ Use `crawl_news_releases()` (website_crawler.py) for company news - it has ALL strategies (NEWS-ENTRY, G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX)
- ✅ Use `scrape_company_news_task` which calls `crawl_news_releases()` for proper news scraping
- ✅ After onboarding, manually trigger `/api/companies/{id}/scrape-news/` if news is missing

### Scrapers Confusion
- ❌ Do NOT confuse homepage "Latest Mining News" with company news
- ✅ Homepage news = `scrape_mining_news_task` (Mining.com, Northern Miner)
- ✅ Company news = `scrape_all_companies_news_task` (individual company websites)

### Investigation Before Action
- ❌ Do NOT assume something is working without checking
- ❌ Do NOT claim a bug is "legitimate behavior" without thorough investigation
- ✅ Always investigate thoroughly before drawing conclusions
- ✅ Read the actual code, check the database, verify assumptions

### Code Quality
- ❌ Do NOT be sloppy or rush through fixes
- ✅ Take time to understand the problem before writing code
- ✅ Test changes properly before claiming they work

### Git Workflow
- ❌ Do NOT commit without pushing - local and remote must stay in sync
- ✅ Always push to origin immediately after committing
- ✅ After pushing, deploy to server if changes affect production

---

## Lessons Learned (Add mistakes here)

When Claude makes a mistake and gets corrected, add it here:

| Date | Mistake | Correction |
|------|---------|------------|
| 2026-01-22 | Claimed Pacifica flag was legitimate without checking dismissed news | Always check `DismissedNewsURL` table and similarity matching |
| 2026-01-22 | Confused homepage news scraper with company news scraper | They are separate tasks with different sources |
| 2026-01-22 | Forgot server path repeatedly | Path is `/var/www/goldventure` (not goldventure-platform) |
| 2026-01-22 | Created code locally but didn't deploy to server | Always push to GitHub and pull on DO server after changes |
| 2026-01-22 | Documents processing on CPU instead of GPU | Found race condition - views.py was starting CPU processing immediately; GPU orchestrator needs time to spin up. Fixed by removing CPU processing calls. |
| 2026-01-24 | Pushed changes but didn't deploy to server | After git push, ALWAYS deploy immediately: SSH, git pull, restart services. Don't wait for user to report "changes not appearing" |
| 2026-01-24 | Confused `scrape_company_website()` with `crawl_news_releases()` - AGAIN | These are TWO DIFFERENT FUNCTIONS. `crawl_news_releases()` (website_crawler.py) has comprehensive news strategies. `scrape_company_website()` (company_scraper.py) has limited news extraction. Onboarding uses the limited one - news may be missing! |
