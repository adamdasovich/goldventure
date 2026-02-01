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

### User Timezone
**The user works on Eastern Standard Time (EST / UTC-5)**. All scheduled tasks and time references should account for this.

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

## Company Onboarding & Verification

### Single-Step Onboarding
The onboarding process is a single button click that:
1. Scrapes the company website (via `scrape_and_save_company_task`)
2. Saves to database
3. Triggers comprehensive news scraping (via `scrape_company_news_task`)
4. **Runs Claude-powered verification** (automatic quality check)

### Automatic Verification System (NEW)
After every company is onboarded, a Claude-powered verification runs automatically:

**Location:** `backend/core/claude_validator.py` - `verify_onboarded_company()`

**What it checks:**
- Description is present and meaningful
- Projects were captured (if the company has projects)
- Ticker/exchange information is complete
- News items were captured

**Auto-fixes:**
- If description is missing, Claude extracts it from the website and adds it
- If projects are mentioned on website but not captured, they're auto-added
- All fixes are logged in `CompanyVerificationLog` table

**Verification scores:**
- `complete` (90-100): All data captured correctly
- `incomplete` (50-89): Some data missing but functional
- `needs_review` (<50): Critical issues, needs manual review

### Checking Verification Results
```bash
# View recent verification logs
ssh root@137.184.168.166
cd /var/www/goldventure/backend && source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python -c "
import django
django.setup()
from core.models import CompanyVerificationLog
for log in CompanyVerificationLog.objects.order_by('-created_at')[:10]:
    print(f'{log.company.name}: {log.status} (score: {log.overall_score})')
    if log.fixes_applied:
        print(f'  Fixes: {log.fixes_applied}')
"
```

### Manual Verification/Fix
If auto-verification misses something:
1. Check the company page: `https://juniorminingintelligence.com/companies/{id}`
2. Compare against the source website
3. Manually update via Django admin or database query

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

### Press Releases vs Media Coverage (CRITICAL)

> **THIS IS ESSENTIAL:** Company news should ONLY be official press releases, NOT third-party media coverage!

**Press Releases (✅ CORRECT for company news):**
- Official company announcements from the company's own website
- News distributed via wire services (GlobeNewswire, Newsfile, Business Wire, etc.)
- These are what investors want to see on company profile pages

**Media Coverage (❌ WRONG for company news):**
- Third-party articles ABOUT the company (Mining.com, Northern Miner, Kitco, etc.)
- These are written by journalists, not the company itself
- These should ONLY appear on the homepage "Latest Mining News" section

**Where each type belongs:**
| Type | Source | Where it goes | Scraped by |
|------|--------|---------------|------------|
| Press Releases | Company website, News wires | CompanyNews table (company profiles) | `scrape_company_news_task` |
| Media Coverage | Mining.com, Northern Miner, etc. | NewsArticle table (homepage) | `scrape_mining_news_task` |

**Blocklist in `website_crawler.py` `is_news_article_url()`:**
The function filters OUT these media coverage sites:
- mining.com, northernminer.com, kitco.com, proactiveinvestors.com
- smallcappower.com, resourceworld.com, miningweekly.com, stockwatch.com
- seekingalpha.com, fool.com, investingnews.com, juniorminingnetwork.com, ceo.ca
- Social media: youtube.com, twitter.com, linkedin.com, facebook.com, instagram.com

**If media coverage appears in company news:**
1. It means the company has an "In the News" section linking to media articles
2. The `is_news_article_url()` blocklist should filter these out
3. If a new media site appears, add it to the blocklist in `website_crawler.py`
4. Clean up bad articles: `DELETE FROM core_companynews WHERE source_url LIKE '%mining.com%'`

### Financing Flags
- Only flag news within **7 days** of current date
- Check added 2026-01-22 in `tasks.py` lines ~432 and ~821
- Similarity threshold for dismissed news: 0.85

### Celery (Systemd Services)
- Now managed by systemd with auto-restart on failure
- Beat schedules tasks, Worker executes them - BOTH must be running
- Check status: `systemctl status celery-worker celery-beat`
- Restart commands:
  ```bash
  systemctl restart celery-worker
  systemctl restart celery-beat
  ```
- View logs: `journalctl -u celery-worker -f` or `tail -f /var/log/celery-worker.log`

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

### 2026-01-27 - Fifth Comprehensive Audit (Code Quality)
**Full codebase audit with code quality improvements.**

#### Fixes Applied
| File | Issue Fixed |
|------|-------------|
| `ProductDetail.tsx` | Added `sanitizeHtml()` to prevent XSS in product descriptions |
| `force_news_update.py` | Fixed bare `except:` → `except ValueError` for date parsing |
| `gpu_orchestrator.py` | Fixed 2 bare `except:` clauses with specific exceptions |
| `tasks.py` | Added `import logging` and converted 103 print statements to logger calls |

#### Codebase Statistics
- **Backend**: 119 Python files, ~75,000 lines of code
- **Frontend**: 142 TypeScript files
- **Largest files**: views.py (8,120 lines), models.py (4,833 lines), company_scraper.py (3,505 lines)

#### Remaining Technical Debt (Lower Priority)
- 121 print statements in MCP servers (should convert to logging)
- 43 console.log statements in frontend (should remove for production)
- Large monolithic files should be split:
  - views.py (8,120 lines) → multiple view modules
  - models.py (4,833 lines) → separate model files by domain
- 5 unimplemented TODO comments in consumers.py and views.py

### 2026-01-27 - Four Comprehensive Security Audits
**Four full code audits performed. Critical issues fixed across multiple rounds.**

#### Security Hardening (settings.py)
- Changed DEBUG default from 'True' to 'False' for safety
- Reduced JWT access token lifetime from 24h to 1h
- Added `BLACKLIST_AFTER_ROTATION` for JWT refresh tokens
- Added rate limiting (100/hr anon, 1000/hr user)
- Added `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY`
- Added `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SAMESITE = 'Lax'`
- Added `SECURE_REFERRER_POLICY` for production

#### Fixed Security Issues (Audits 1-3)
| File | Issue Fixed |
|------|-------------|
| `middleware.py` | Added `is_active` check for JWT users (prevent disabled user access) |
| `admin.py` | Added URL validation in batch_add_view (prevent invalid URLs) |
| `serializers.py` | Fixed bare except → `except (AttributeError, TypeError)` |
| `tasks.py` | Fixed TOCTOU race conditions with `get_or_create` |
| `views.py` | Fixed ViewSets (ResourceEstimate, SpeakerEvent, Financing) to require auth for writes |
| `document_processor_hybrid.py` | Fixed bare except clauses (JSON, date parsing) |
| `rag_utils.py` | Fixed bare except in ChromaDB deletion |
| `company_scraper.py` | Added SSRF protection for iframe URLs (validate http/https) |
| `onboard_company.py` | Fixed bare except clauses (Decimal, datetime parsing) |
| `kitco_scraper.py` | Fixed 4 bare except → `except (ValueError, TypeError, decimal.InvalidOperation)` |
| `news_scraper.py` | Fixed bare except in date parsing |
| `stock_price_scraper.py` | Fixed 2 bare except clauses |
| `news_content_processor.py` | Fixed bare except in ChromaDB deletion |

#### Frontend Security Fixes
| File | Issue Fixed |
|------|-------------|
| `AuthContext.tsx` | Added try-catch for JSON.parse (prevent crashes from corrupted data) |
| `RegisterModal.tsx` | Strengthened password validation (10+ chars, uppercase, lowercase, number) |

#### Fourth Audit Findings - FIXED

**Config Fixes (settings.py, asgi.py, celery.py):**
| Issue | Fix Applied |
|-------|-------------|
| SECRET_KEY with insecure prefix | Removed 'django-insecure-' prefix, added warning if not set in production |
| Personal email hardcoded | Changed defaults to 'admin@example.com' / 'notifications@example.com' |
| DB password defaults to empty | Removed default - now requires explicit env var |
| WebSocket origins hardcoded | Made configurable via WEBSOCKET_ALLOWED_ORIGINS env var |
| Celery debug_task | Removed debug task from production code |

**Backend Fixes:**
| Issue | Fix Applied |
|-------|-------------|
| Unprotected AI chat endpoints | Changed `@permission_classes([AllowAny])` → `@permission_classes([IsAuthenticated])` |
| Unsafe JSON parsing (document processors) | Added direct JSON parse attempt before extraction fallback, added structure validation |
| SSRF via allow_redirects=True | Added `is_safe_url()` validation for URLs and redirect destinations |

**MCP Server Fixes:**
| Issue | Fix Applied |
|-------|-------------|
| 25 bare except clauses in website_crawler.py | Added explanatory comments documenting intentional broad exception handling |
| SSRF in company_scraper.py | Added `is_safe_url()` validation function, checks for internal IPs and cloud metadata |

**Frontend Fixes:**
| Issue | Fix Applied |
|-------|-------------|
| Console.log exposing user data | Removed debug console.log from AuthContext.tsx (lines 101, 149) |
| Console.log exposing user roles | Removed debug useEffect from EventBanner.tsx |
| dangerouslySetInnerHTML XSS risk | Added `sanitizeHtml()` function to education module page |

#### Remaining Lower Priority Issues (Design Changes Required)
- WebSocket tokens in query string (needs server-side auth redesign)
- JWT tokens in localStorage (needs httpOnly cookie implementation)
- SESSION_COOKIE_SAMESITE='Lax' instead of 'Strict' (may break frontend)
- Missing Content-Security-Policy header (needs django-csp package)
- Missing Permissions-Policy header
- Unimplemented access control TODOs in consumers.py (lines 395, 904)
- Print statements for debugging (40+ in company_scraper.py, 30+ in website_crawler.py)

### 2026-01-25
- Added media coverage site blocklist to `website_crawler.py` `is_news_article_url()` function
  - Blocks Mining.com, Northern Miner, Kitco, Proactive Investors, and 15+ other media sites
  - Company news should ONLY be official press releases, not third-party media coverage
- Cleaned up 28 bad articles from CompanyNews table (Mining.com and Northern Miner articles)
- Updated CLAUDE.md with Press Releases vs Media Coverage distinction
- Added automatic company verification system with Claude-powered auto-fixes

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

### Press Releases vs Media Coverage (NEW - CRITICAL)
- ❌ Do NOT save media coverage (Mining.com, Northern Miner articles) in CompanyNews
- ❌ Do NOT ignore "In the News" sections on company websites - they link to media coverage, not press releases
- ✅ Company profiles should ONLY have official press releases (from the company or news wires)
- ✅ Media coverage belongs ONLY on the homepage "Latest Mining News" section
- ✅ If a new media site appears in company news, add it to the blocklist in `website_crawler.py` `is_news_article_url()`

### Investigation Before Action
- ❌ Do NOT assume something is working without checking
- ❌ Do NOT claim a bug is "legitimate behavior" without thorough investigation
- ❌ Do NOT state things as facts without verifying them first
- ❌ Do NOT make excuses or blame user data when the bug is in the code
- ✅ Always investigate thoroughly before drawing conclusions
- ✅ Read the actual code, check the database, verify assumptions
- ✅ When a feature doesn't work, FIRST check the actual data state before speculating

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
| 2026-01-25 | Media coverage from Mining.com/Northern Miner appeared in company news | Company profiles should ONLY have press releases. Some companies have "In the News" sections linking to media articles - these must be filtered. Added blocklist in `is_news_article_url()`. |
| 2026-01-26 | Fixed code locally but didn't deploy before user onboarded company | Verification ran with old buggy code (projects not auto-added). CRITICAL: Always deploy fixes IMMEDIATELY after pushing - don't run manual tests that won't help future users. The code must be live on the server BEFORE it can help. |
| 2026-01-26 | Ran verification manually instead of fixing the code | Manual interventions don't help future users. Always fix the root cause in code and deploy it so the system works automatically for all future onboardings. |
| 2026-01-27 | Added slow crawler config (5s delay, networkidle) without testing performance impact | ALWAYS test performance impact before deploying changes to scheduled tasks. The 5s delay per URL × 35 patterns = 175+ seconds per company, breaking the daily scrape. |
| 2026-01-27 | Used sed shortcuts that broke file formatting | NEVER take shortcuts with file editing. Always use proper tools and verify changes. When editing server files, use Python or proper text manipulation, not sed hacks that can corrupt files. |
| 2026-01-27 | Kept saying "now I'll fix it properly" after breaking things | DO IT RIGHT THE FIRST TIME. Don't rush. Think through the full impact. Use reliable methods. Verify each step. There is no excuse for sloppy work. |
| 2026-01-27 | Deployed multiple "fixes" without investigating root cause | TIME-EXIT wasn't working because crawl4ai has a 60s page_timeout default - each URL that doesn't load blocks for 60s before the time check runs. ALWAYS investigate the ACTUAL root cause before coding a fix. The root cause was page_timeout, not just the time check logic. |
| 2026-01-27 | Didn't understand crawl4ai library behavior | CrawlerRunConfig has `page_timeout=60000` by default. With 35+ URL patterns, slow sites cause multiple 60s timeouts = 300+ second scrapes. ALWAYS check library defaults and documentation before assuming code behavior. |
| 2026-01-27 | Daily scrape took 500+ seconds per company | Root cause was NewsContentProcessor._process_company_news() fetching content from each news URL after scraping (15s timeout × N items). Fix: Skip content processing during daily scrapes (only during onboarding). ALWAYS trace the FULL code path - the scraping was fast (13-60s), but post-processing was adding 500+ seconds. |
| 2026-01-28 | Assumed ticker wasn't scraped without checking | The ticker WAS scraped (NIM on TSX Venture). NEVER assume or state anything without investigating first. Read the actual data, check the database, look at the code. Making false claims wastes time and frustrates the user. |
| 2026-01-28 | Manually triggered scrape while scheduled batch was running | Caused 246 tasks (2x123 companies) to run. ALWAYS check if a batch is already running before triggering a test. Fix: Added distributed lock using Django cache to prevent duplicate concurrent batches. |
| 2026-01-28 | Northern Dynasty only had 1 news item instead of 52 | Website uses year-based URL pattern `/news/news-releases/YYYY/` that wasn't in scraper. ALWAYS investigate actual website structure when news is missing - many sites organize by year. Fix: Added year-based URL patterns. |
| 2026-01-28 | Northisle only had 3 news items instead of 10 | Two issues: (1) `?post_year=` URLs need trailing slash BEFORE query params (`/news-releases/?post_year=` not `/news-releases?post_year=`), (2) URL patterns far down the list never get reached due to 60s timeout. Fix: Add trailing slash and move year-filtered patterns right after base URL. |
| 2026-01-28 | Orosur Mining had 0 news items | Website uses BrighterIR - a third-party IR platform that loads news via iframe widgets (common for UK/AIM-listed companies). Standard HTML scraping doesn't work. Fix: Added BrighterIR detection (look for `polaris.brighterir.com` iframe) and API extraction with `X-Requested-With: XMLHttpRequest` header. |
| 2026-01-28 | Osisko Development had 0 news items despite finding 80 in scraper | Website uses `.list-item` structure with SEPARATE month/day/year divs for dates, plus both news links AND PDF links side-by-side. Scraper was extracting PDF links (no date metadata) instead of actual news page URLs. Fix: Added LIST-ITEM extraction pattern that parses month/day/year divs and skips links with class="pdf" or *.pdf URLs. |
| 2026-01-28 | Panoro Minerals had 0 news items captured | Website uses multilingual URL structure `/en/news/YYYY/` instead of standard `/news/YYYY/`. The `/en/news/` patterns were either missing or placed at the END of the pattern list, so they were never reached before the 60-second timeout. Fix: Added `/en/news/`, `/en/news/{year}/` patterns EARLY in the list (right after base `/news/` patterns). Pattern ORDER matters - put specific/important patterns early. |
| 2026-01-28 | Puma Exploration had 0 news (custom URL) | Website uses completely custom news URL `/en/puma-news/` that doesn't match ANY standard patterns. Fix: Added `news_url` field to Company model so custom URLs can be specified per-company. Crawler now checks `custom_news_url` parameter first before trying standard patterns. For companies with non-standard news pages, set their `news_url` field in the database. |
| 2026-01-28 | Regulus onboarding failed with NOT NULL violation | Added `news_url` field with `blank=True` but forgot `default=''`. Django's `blank=True` ONLY affects form validation, NOT database constraints. Without `default=''`, Django passes nothing to PostgreSQL for unspecified fields, which treats it as NULL. For optional string fields: ALWAYS use `blank=True, default=''`. Use `null=True` only for fields where NULL is semantically different from empty string (dates, numbers, FKs). |
| 2026-01-28 | Silver Tiger had 0 news from 2025 | Pattern `/news/{current_year}/` only adds current year (2026), missing `/news/2025/`. Also: `git pull` updates files but Celery worker keeps running OLD code in memory. Fix: Added `/news/{current_year - 1}/` and `/news/{current_year - 2}/` patterns. ALWAYS restart `celery-worker` after deploying code changes. |
| 2026-01-29 | Silvercorp Metals had 0 news items | Website uses Beaver Builder (JavaScript page builder) to render news content dynamically. Standard HTML scraping returns only CSS/JS infrastructure, not actual news. Fix: Added WordPress REST API support - check `/wp-json/wp/v2/posts` endpoint which returns news as JSON. Many WordPress sites have this API enabled by default. Result: 103 news items scraped. |
| 2026-01-29 | Sitka Gold onboarding was slow (30s timeouts) | `company_scraper.py` line 290-291 added `s` suffix to pluralize keywords like `release` -> `releases`, but `news` is already plural, creating invalid `/newss/` URLs that each caused 30-second timeouts. Fix: Only add `s` suffix if keyword doesn't already end in `s`. |
| 2026-01-29 | Skyharbour: wrong ticker (FCU instead of SYH), 0 news | TWO bugs: (1) Ticker extraction searched full page text BEFORE checking reverse pattern in ticker elements - found "TSX: FCU" (Fission Uranium mentioned in body text) instead of "SYH: TSX.V" in header. Fix: Check ALL patterns (including reverse SYH: TSX.V format) in targeted ticker elements FIRST. (2) News dates were None because site uses tab-based structure with month/day divs and year from parent tab container (tab-2026). Standard date extraction expects year in same element. Fix: Added TAB-DATE extraction strategy. |
| 2026-01-29 | Surge Copper had 0 news with dates (92 found but none saved) | TWO issues: (1) `company_scraper.py` Strategy 4 (flex-wrap) only checked for `/news/` in URLs, but Surge uses `/news-releases/`. (2) Strategy only ran if fewer than 3 items already found - but generic link scan found 278 items without dates first. Fix: Always run flex-wrap strategy (it extracts dates), and check for `/news-releases/`, `/press-releases/`, `/announcement/` in URLs. IMPORTANT: `company_scraper.py` has its OWN news extraction separate from `website_crawler.py` - fixes must be applied to the correct file! |
| 2026-01-31 | Q-Gold had 0 news items | Website uses Strapi CMS (headless CMS) with React frontend. Standard HTML scraping returns "You need to enable JavaScript to run this app." The site has `/api/news` endpoint returning JSON. Fix: Added Strapi CMS API detection in `website_crawler.py` - checks for `/api/news` endpoint with Strapi v4 structure (`{data: [...], Title, Date}`). Result: 25 news items scraped. |
| 2026-02-01 | Red Canyon had 0 news items | Website is Wix-based but doesn't use Wix Blog RSS feed. Uses `/news/slug` URL pattern with "Read More" links and dates in "Jan 26, 2026" format. TWO issues: (1) Old Wix RSS check returned 404, no HTML fallback. (2) Link text was "Read More" (9 chars) which failed `len(text) > 10` check. Fix: Added WIX-HTML extraction strategy that extracts slug from URL as title when link text is generic, matches dates from span elements. Result: 20 news items scraped. |
| 2026-02-01 | Rio Silver ScrapingJob 377 was orphaned (company_id=None) | In `scrape_and_save_company_task` exception handler: (1) Job saved as 'failed' at line 1377 WITHOUT company_id, (2) Fallback company created at line 1400, (3) BUT job was never updated with `job.company = fallback_company`. Fix: Added `job.company = fallback_company; job.save(update_fields=['company'])` after fallback company creation. LESSON: When creating records in sequence (Job → Company), ensure the FK relationship is established even in error/fallback paths. |
| 2026-02-01 | Celery tasks getting lost - jobs stuck in 'pending' forever | MULTIPLE issues: (1) Missing `CELERY_TASK_REJECT_ON_WORKER_LOST` setting - tasks lost on worker crash. (2) No error handling around `.delay()` calls - if Redis down, task never queued but user gets success. (3) Time limits too short (10min) for complex websites (15-20min). (4) `cleanup_stuck_jobs_task` had dead code - `stuck_scraping_pending` query was created but NEVER USED. Fix: Added critical Celery settings (`CELERY_TASK_ACKS_LATE`, `CELERY_TASK_REJECT_ON_WORKER_LOST`, `CELERY_WORKER_PREFETCH_MULTIPLIER=1`), increased time limits to 20min, added try-except around `.delay()` in views, fixed cleanup task to actually retry stuck pending jobs. |

---

## Security Considerations

### Authentication & Authorization
- JWT tokens expire in 1 hour (access) and 7 days (refresh)
- Rate limiting: 100 req/hr anonymous, 1000 req/hr authenticated
- ViewSets use `get_permissions()` pattern: read=AllowAny, write=IsAuthenticated
- WebSocket auth checks `is_active` on user after token decode

### Known Security Patterns
| Pattern | Location | Purpose |
|---------|----------|---------|
| `get_or_create` | tasks.py | Prevent TOCTOU race conditions |
| URL validation | admin.py, company_scraper.py | Prevent SSRF attacks |
| Specific exceptions | All files | Prevent silent error swallowing |
| Rate limiting | settings.py | Prevent brute force/DoS |

### Security Audit Checklist
When making changes, check for:

**Backend:**
- [ ] Bare `except:` or `except Exception:` clauses (should use specific exceptions)
- [ ] `exists()` followed by `create()` (use `get_or_create` instead)
- [ ] User-supplied URLs being fetched (validate scheme is http/https)
- [ ] Missing authentication on write endpoints (`@permission_classes([IsAuthenticated])`)
- [ ] `int()` conversions without try-except on user input
- [ ] `allow_redirects=True` without validating redirect destination
- [ ] Unsafe JSON parsing (finding { to } without validation)
- [ ] Print statements with sensitive/debug data
- [ ] Personal email addresses or secrets in defaults
- [ ] User input in HTML templates without escaping

**Frontend:**
- [ ] JSON.parse without try-catch
- [ ] dangerouslySetInnerHTML with user-controlled content (sanitize with DOMPurify)
- [ ] console.log with user data or auth info
- [ ] Tokens in localStorage (should be httpOnly cookies)
- [ ] URL inputs without server-side validation
- [ ] Missing Content-Security-Policy header
| 2026-02-01 | Silver X Mining had only 1 news item instead of 100 | `company_scraper.py` had 6+ HTML-based news extraction strategies but NO WordPress REST API support - even though `website_crawler.py` had it. Many WordPress sites (Silver X Mining, Silvercorp) have REST API at `/wp-json/wp/v2/posts` returning news as JSON. Fix: Added Strategy 0 (WordPress REST API) to `_scrape_news_page()` in `company_scraper.py` - checks API BEFORE HTML scraping. LESSON: Two scrapers (`company_scraper.py` for onboarding, `website_crawler.py` for daily scrapes) - ensure both have same detection capabilities! |
