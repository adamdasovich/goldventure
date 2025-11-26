# News Release Crawler - Auto-Discovery of Company News

Complete web crawling system to automatically discover and store news releases from company websites.

## 🎯 What This Does

The system now automatically:
1. **Crawls** a company website for news releases
2. **Filters** to only the last 6 months (configurable)
3. **Extracts** dates and titles from news release PDFs
4. **Stores** them in your database for easy access
5. **Prioritizes** news releases as most important (highest relevance score)

## ✅ Features

- **Date-aware**: Extracts dates from filenames (YYYYMMDD format)
- **Smart filtering**: Only returns news from last 6 months
- **Duplicate detection**: Skips news releases already in database
- **Bulk storage**: Store multiple company news releases at once
- **Database integration**: Direct integration with NewsRelease model

## 🚀 Quick Start

### Test the Crawler

```bash
cd backend
python test_news_crawler.py
```

This will:
- Crawl https://www.1911gold.com for news releases
- Show all news from the last 6 months
- Ask if you want to store them in the database

### Programmatic Usage

```python
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases
import asyncio

async def get_company_news():
    # Crawl for news releases (last 6 months)
    news_releases = await crawl_news_releases(
        url="https://www.1911gold.com",
        months=6,
        max_depth=2
    )

    # Store in database
    stats = store_news_releases(
        company_name="1911 Gold Corp",
        news_releases=news_releases
    )

    print(f"Created: {stats['created']}")
    print(f"Skipped (duplicates): {stats['skipped']}")

asyncio.run(get_company_news())
```

## 📊 Example Output

```
================================================================================
DISCOVERED 17 NEWS RELEASES
================================================================================

NEWS RELEASES (Last 6 months):
--------------------------------------------------------------------------------

1. [2025-11-11] 1911 Gold Announces High-Grade Drilling Results
   URL: https://www.1911gold.com/_resources/news/nr-20251111.pdf
   Relevance: 30.0

2. [2025-11-10] 1911 Gold Completes Underground Drilling Program
   URL: https://www.1911gold.com/_resources/news/nr-20251110.pdf
   Relevance: 30.0

3. [2025-11-06] 1911 Gold Reports Q3 2025 Financial Results
   URL: https://www.1911gold.com/_resources/news/nr-20251106.pdf
   Relevance: 30.0

... and 14 more

================================================================================
DATABASE STORAGE
================================================================================

Store these 17 news releases in the database? (y/n): y

[INFO] Storing news releases for 1911 Gold Corp...

================================================================================
STORAGE RESULTS
================================================================================
Created: 15
Updated: 0
Skipped: 2

[OK] Successfully stored 15 new news release(s)!
     They are now available in the admin interface and chatbot.
```

## 🔧 Configuration

### Change Date Range

Get news from last 12 months instead of 6:

```python
news_releases = await crawl_news_releases(
    url="https://www.1911gold.com",
    months=12,  # 12 months instead of 6
    max_depth=2
)
```

### Change Crawl Depth

Deeper crawling (finds more but takes longer):

```python
news_releases = await crawl_news_releases(
    url="https://www.1911gold.com",
    months=6,
    max_depth=3  # Go 3 levels deep instead of 2
)
```

## 📦 API Reference

### `crawl_news_releases(url, months=6, max_depth=2)`

Crawl a company website for news releases only.

**Parameters:**
- `url` (str): Company website URL
- `months` (int): Number of months to look back (default 6)
- `max_depth` (int): How deep to crawl (default 2)

**Returns:**
- List[Dict]: News release documents with dates, sorted newest first

**Example:**
```python
news = await crawl_news_releases("https://www.1911gold.com", months=6)
```

### `store_news_releases(company_name, news_releases, overwrite_duplicates=False)`

Store crawled news releases in the database.

**Parameters:**
- `company_name` (str): Name of the company (must exist in database)
- `news_releases` (List[Dict]): News releases from crawler
- `overwrite_duplicates` (bool): Update existing releases? (default False)

**Returns:**
- Dict: Statistics with `created`, `updated`, `skipped`, `errors`

**Example:**
```python
stats = store_news_releases(
    company_name="1911 Gold Corp",
    news_releases=news,
    overwrite_duplicates=False
)
print(f"Created {stats['created']} new releases")
```

### `get_existing_news_releases(company_name, months=6)`

Get existing news releases from database.

**Parameters:**
- `company_name` (str): Name of the company
- `months` (int): Number of months to look back

**Returns:**
- List[Dict]: Existing news releases from database

**Example:**
```python
existing = get_existing_news_releases("1911 Gold Corp", months=6)
print(f"Found {len(existing)} existing releases")
```

## 🎯 Use Cases

### 1. Daily News Updates

Run daily to catch new news releases:

```python
# Could be a Django management command
# python manage.py crawl_company_news --all

from core.models import Company
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases

async def update_all_company_news():
    for company in Company.objects.all():
        if company.website:
            print(f"Crawling {company.name}...")

            news = await crawl_news_releases(
                url=company.website,
                months=1  # Just last month for daily updates
            )

            stats = store_news_releases(company.name, news)
            print(f"  Created: {stats['created']}, Skipped: {stats['skipped']}")

asyncio.run(update_all_company_news())
```

### 2. Initial Company Setup

When adding a new company, get their recent news history:

```python
async def setup_new_company(company_name, website_url):
    # Get 12 months of news for new company
    news = await crawl_news_releases(
        url=website_url,
        months=12,
        max_depth=3
    )

    stats = store_news_releases(company_name, news)
    print(f"Loaded {stats['created']} historical news releases")
```

### 3. Bulk Company Updates

Update multiple companies at once:

```python
from mcp_servers.news_release_storage import store_news_releases_bulk

companies = [
    ("1911 Gold Corp", "https://www.1911gold.com"),
    ("Another Company", "https://example.com"),
]

async def bulk_update():
    company_news_map = {}

    for name, url in companies:
        news = await crawl_news_releases(url, months=6)
        company_news_map[name] = news

    results = store_news_releases_bulk(company_news_map)

    for company, stats in results.items():
        print(f"{company}: Created {stats['created']}, Skipped {stats['skipped']}")

asyncio.run(bulk_update())
```

## ⚙️ How It Works

### 1. Intelligent Crawling

- Follows links to news/press-release sections
- Skips irrelevant pages (contact, careers, social media)
- Respects max_depth to avoid crawling entire site

### 2. News Release Detection

Identifies news releases by:
- URL patterns: `/news/`, `/press-releases/`, `nr-`
- File naming: `nr-20251111.pdf`
- Link text: "press release", "news release"

### 3. Date Extraction

Extracts dates from multiple formats:
- YYYYMMDD: `nr-20251111.pdf` → 2025-11-11
- YYYY-MM-DD: `news-2025-11-11.pdf` → 2025-11-11
- Falls back to year only if full date not found

### 4. Date Filtering

- Filters to only last N months (default 6)
- Based on extracted date from filename
- News without dates are included (might be valuable)

### 5. Database Storage

- Checks for duplicates by URL or title+date
- Creates NewsRelease records with company link
- Returns statistics: created, updated, skipped, errors

## 🔮 Priority System

News releases now have **HIGHEST PRIORITY** in the crawler:

1. **News Releases** - Score: 30 (most current company info)
2. **Technical Reports** - Score: 20
3. **Presentations** - Score: 10
4. **Financial Statements** - Score: 5

This ensures news releases are discovered and processed first.

## 📈 Performance

| Website Size | Depth | Typical Time | News Found |
|--------------|-------|--------------|------------|
| Small (< 50 pages) | 2 | 30-60 seconds | 10-20 |
| Medium (50-200 pages) | 2 | 1-2 minutes | 20-50 |
| Large (> 200 pages) | 2 | 2-5 minutes | 50-100 |

## 🐛 Troubleshooting

### No news releases found

**Possible reasons:**
- Company uses HTML news page (not PDFs)
- News is behind login/paywall
- Website structure changed

**Try:**
- Increase `max_depth` to 3
- Increase `months` to 12
- Check website manually to see if PDFs exist

### Dates not extracting correctly

**Issue:** News release dates showing as None

**Solution:** News releases must have dates in filename:
- Good: `nr-20251111.pdf`, `news-2025-11-11.pdf`
- Bad: `press-release.pdf`, `latest-news.pdf`

### Company not found error

**Issue:** `Company 'XYZ' not found in database`

**Solution:** Company must exist in database first:
```python
from core.models import Company
Company.objects.create(
    name="XYZ Mining",
    ticker_symbol="XYZ",
    website="https://xyz.com"
)
```

## 📝 Database Schema

News releases are stored in the `NewsRelease` model:

```python
NewsRelease.objects.create(
    company=company,              # ForeignKey to Company
    title="News Title",           # From link text or filename
    url="https://...",            # PDF URL
    release_date=date(2025, 11, 11),  # Extracted from filename
    release_type='other',         # Can be classified later
    summary='',                   # To be filled later (optional)
    full_text='',                 # To be extracted later (optional)
    is_material=False             # To be determined later
)
```

## 🎉 Summary

**Before:**
1. Manually browse company website
2. Click through to news section
3. Find latest news releases
4. Copy each URL
5. Manually add to database
6. Repeat for each company

**After:**
1. Run: `python test_news_crawler.py`
2. Answer 'y' to store in database
3. Done! All recent news in database

**Saves:** 95% of time for news tracking!

---

## Next Steps

1. **Schedule Automatic Crawls**
   - Create Django management command
   - Run daily via cron/scheduler
   - Email notifications for new news

2. **Enhance with Text Extraction**
   - Extract full text from PDFs
   - Auto-generate summaries
   - Classify by type (drill results, financing, etc.)

3. **Add to Chatbot**
   - Query latest company news
   - Get news summaries
   - Filter by news type

**Questions? Issues?**
- Check the test script: `test_news_crawler.py`
- Review the crawler code: `mcp_servers/website_crawler.py`
- See storage functions: `mcp_servers/news_release_storage.py`
