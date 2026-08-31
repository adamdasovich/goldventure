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
./deploy.sh                 # ~2-4 min
./deploy.sh --install       # same, but npm install first (package.json changed)

# Useful:
pm2 list                            # status / restart count
pm2 logs goldventure-frontend       # tail logs (check after a deploy)
```

`deploy.sh` builds into `.next-build`, and only once that succeeds does it move
the directory into place and restart pm2. It then checks every `/_next/static/`
asset on five pages and, if any is not a 200, **puts the previous build back and
restarts**. A failed deploy costs a restart rather than an outage.

> **Do not go back to `npm run build` in place.** `next start` serves out of
> `.next`, and building into that same directory rewrites it underneath the
> running server: for the whole 2-4 minutes, live requests get chunk URLs the
> server is about to delete and then `MODULE_NOT_FOUND` when it tries to load
> them — a 500 for every visitor, on every deploy. On 2026-08-31 that put
> ~15,000 lines into the pm2 error log across six deploys before anyone looked.
> `next.config.ts` reads `NEXT_DIST_DIR` for exactly this; unset — which is how
> `next start` and `next dev` run — it is `.next`.

> **NOTE (historical, now handled):** this stale-chunk trap is why
> `rm -rf .next/cache` used to be mandatory. `deploy.sh` builds into a fresh
> `.next-build` every time, so there is no cache left to go stale — but the
> failure mode is worth keeping, because it returns the moment anyone builds
> in place again. Next reuses
> prerendered HTML from that directory across builds, and it can serve pages
> referencing CSS/JS chunk hashes from an **earlier** build. Those chunks no
> longer exist, so the browser gets a 404 with an HTML body and reports
> `Refused to apply style ... because its MIME type` — the page returns **200
> with broken styling and dead client JS**. It happened on 2026-08-28: the
> homepage served a missing stylesheet and a missing script, `MetalsTicker`
> rendered nothing, and the only outward symptom was that a component silently
> disappeared. Deleting `.next/cache` (NOT `.next` itself, which the running
> `next start` is serving) and rebuilding fixes it.
>
> Because a broken page still returns 200, `curl -o /dev/null -w '%{http_code}'`
> on `/` proves nothing. Run the asset loop above, or load the page in a real
> browser and check for console errors.

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

> **NOTE:** `npm run test:mobile` (Playwright, `frontend/tests/mobile/`) guards
> the mobile layout at 320/375/390 and 667x375 landscape — viewport overflow,
> the nav trigger, the auth dialogs, and touch-target sizes.
> Against a deploy: `BASE_URL=https://juniorminingintelligence.com npm run test:mobile`.
> It uses the locally installed Chrome, so there is no browser download.
> Read `frontend/tests/mobile/README.md` before changing it — in particular,
> `scrollWidth` does **not** detect overflow on this site, because the
> `overflow-x: clip` guard on `body` in `globals.css` suppresses it. That is how
> a 660px-wide row on `/metals` survived a full static review and three deploys.

> **CRITICAL:** NEVER pass `--omit=optional` (or `--no-optional`) to npm here.
> Tailwind 4 compiles CSS through `lightningcss`, whose platform binary
> (`node_modules/lightningcss/lightningcss.linux-x64-gnu.node`) ships as an
> **optional** dependency. Omitting it deletes the binary and every build then
> dies with `Cannot find module '../lightningcss.linux-x64-gnu.node'` while
> pointing at `app/globals.css`, which reads like a CSS problem and is not.
> Recovery is a plain `npm install` on the server, then rebuild. This took the
> site down for ~5 minutes on 2026-08-24. Use plain `npm install`; if you want a
> clean tree use `npm ci` with no flags.
>
> **CRITICAL:** Gate the pm2 restart on the build's exit code. Chain them with
> `&&` — never two separate lines, never `;`. `next start` serves `.next/`, so
> restarting after a failed build swaps a working process for one with no valid
> build, and every route returns **502**. Watch for the subtler version of this:
> in `npm run build ...; echo "done" && pm2 restart` the restart is gated on the
> `echo`, not on the build. That is what caused the 2026-08-24 outage.
>
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
| `scrape`      | `celery-scrape.service`      | 2           | 2400M     | Bulk crawling. Browser-heavy, runs all day.       |
| `interactive` | `celery-interactive.service` | 2           | 900M      | User-triggered onboarding/manual scrapes.         |
| `default`     | `celery-worker.service`      | 2           | 850M      | Health checks, cleanups, prices, emails, reports. |

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
>
> **NOTE:** `/var/log/celery-worker.log` is misnamed — `settings.py` LOGGING
> defines a `celery_file` FileHandler there, and Django builds its dictConfig in
> every process, so gunicorn and daphne hold write descriptors on it too. It hit
> 2.7 GB unrotated before `/etc/logrotate.d/goldventure` was added
> (`backend/deploy/logrotate-goldventure`). That config MUST keep
> `copytruncate` — a rename-and-create rotation would leave those long-lived
> processes writing to the orphaned inode and never reclaim the space.
> Day-to-day worker output goes to journald, not these files:
> `journalctl -u celery-scrape -n 50 --no-pager`.

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
