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
**Server:** DigitalOcean droplet at 137.184.168.166

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
│   └── templates/             # Email templates
└── frontend/                   # Next.js React application
```

---

## Critical Patterns & Gotchas

### News Scraping
- **Company news:** Use `crawl_news_releases()` NOT `crawl_company_website()`
- `crawl_company_website()` is for PDFs/documents, not news
- News strategies are in `website_crawler.py` starting around line 1640
- Strategies: G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX

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

### Scraping Functions
- ❌ Do NOT use `crawl_company_website()` for news
- ✅ Use `crawl_news_releases()` for company news

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

---

## Lessons Learned (Add mistakes here)

When Claude makes a mistake and gets corrected, add it here:

| Date | Mistake | Correction |
|------|---------|------------|
| 2026-01-22 | Claimed Pacifica flag was legitimate without checking dismissed news | Always check `DismissedNewsURL` table and similarity matching |
| 2026-01-22 | Confused homepage news scraper with company news scraper | They are separate tasks with different sources |
| 2026-01-22 | Forgot server path repeatedly | Path is `/var/www/goldventure` (not goldventure-platform) |
