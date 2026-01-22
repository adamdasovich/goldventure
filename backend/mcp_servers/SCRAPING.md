# News Scraping Reference

## Overview

The news scraper (`website_crawler.py`) extracts news releases from company websites. It uses multiple strategies to handle different website structures.

## Key Functions

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `crawl_news_releases()` | Extract news from company websites | News scraping tasks |
| `crawl_company_website()` | Extract PDFs and documents | Document discovery |
| `crawl_html_news_pages()` | Internal - HTML news extraction | Called by crawl_news_releases |

**Important:** For news, always use `crawl_news_releases()`, NOT `crawl_company_website()`.

---

## Extraction Strategies

Strategies are applied in order in the `news_page_patterns` loop starting at line ~1640.

### Strategy 1: G2 Goldfields Pattern
- **Selector:** `<strong>` tags containing dates
- **Structure:** Date in strong tag, followed by title/link in next element
- **Example:** `<strong>January 06, 2026</strong><p>Title <a href="globenewswire...">Read More</a></p>`

### Strategy 2: WordPress Block Pattern (WP-BLOCK)
- **Selector:** `.wp-block-post`, `li.wp-block-post`, `.document-card`
- **Structure:** Post with h3 title link and time/date element
- **Used by:** Canada Nickel, many WordPress sites

### Strategy 3: Elementor Pattern
- **Selector:** `h2.elementor-heading-title`, `h3.elementor-heading-title`
- **Structure:** Heading with link, date in nearby elements
- **Used by:** Many Elementor-based sites

### Strategy 4: Elementor Loop (e-loop-item)
- **Selector:** `.e-loop-item`
- **Structure:** Loop item with title in heading, date in `[itemprop="datePublished"]`
- **Used by:** LaFleur Minerals
- **Added:** 2026-01-20

### Strategy 5: UIKit Grid Pattern
- **Selector:** `[uk-grid]`, `.uk-grid`
- **Structure:** Three columns - date, title, VIEW/PDF links
- **Used by:** Scottie Resources
- **Added:** 2026-01-22

### Strategy 6: Structured News Items (ITEM)
- **Selector:** `.news-item`, `.press-release`, `.news-release`, `article.post`
- **Structure:** Container with `.date` element and `.title` link
- **Used by:** Laurion, 1911 Gold, Silverco Mining

### Strategy 7: ASPX Evergreen CMS
- **Selector:** Year tabs in `#Year-{year}` format
- **Structure:** Accordion panels with date and article links
- **Used by:** Harvest Gold, other Evergreen CMS sites
- **Added:** 2026-01-20

### Strategy 8: All Links Fallback (LINK)
- Scans all `<a>` tags for news-like URLs
- Uses `is_news_article_url()` to filter
- Last resort catch-all

---

## Date Parsing

### `parse_date_standalone(text)`
Parses dates from dedicated date elements. Supports:
- `MM.DD.YYYY` (Laurion: 01.07.2026)
- `Month DD, YYYY` (January 15, 2026)
- `Mon DD YYYY` (Nov 17 2025)
- `Mon DD, YYYY` (Jul 7, 2025)
- `MM/DD/YYYY` (01/20/2026)
- `MM/DD/YY` (01/20/26) - Added 2026-01-22
- `Mon DD` (Jan 15) - infers year

### `parse_date_comprehensive(text)`
Extracts dates embedded in longer text (titles, descriptions).

---

## Adding a New Strategy

1. **Identify the HTML structure** using browser dev tools
2. **Find the appropriate location** in `crawl_html_news_pages()` (line ~1640)
3. **Add your strategy** with clear comments:

```python
# ============================================================
# STRATEGY X: Site Name - Description
# Structure: brief HTML structure description
# ============================================================
for item in soup.select('your-selector'):
    try:
        # Extract date
        date_elem = item.select_one('.date-class')
        date_str = parse_date_standalone(date_elem.get_text(strip=True)) if date_elem else None

        # Extract title and link
        title_elem = item.select_one('a.title-class')
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        href = title_elem.get('href', '')

        # Validate
        if not title or len(title) < 15:
            continue

        # Build full URL
        if not href.startswith('http'):
            href = urljoin(news_url, href)

        news = {
            'title': clean_news_title(title, href),
            'url': href,
            'date': date_str,
            'document_type': 'news_release',
            'year': date_str[:4] if date_str else None
        }
        _add_news_item(news_by_url, news, cutoff_date, "YOUR-STRATEGY-NAME")
    except Exception:
        continue
```

4. **Test locally** before deploying
5. **Update CLAUDE.md** with the new strategy

---

## News Page URL Patterns

The scraper tries these URL patterns for each company (line ~1619):

```python
news_page_patterns = [
    f'{url}/news/',
    f'{url}/news/all/',
    f'{url}/news-releases/',
    f'{url}/press-releases/',
    f'{url}/investors/news/',
    f'{url}/investors/news-releases/',
    f'{url}/investor-relations/news-releases/',
    f'{url}/investor-relations/press-releases/',
    f'{url}/news/press-releases/',
    f'{url}/news/{current_year}/',
    f'{url}/news-{current_year}/',
    f'{url}/news-{current_year - 1}/',
    f'{url}/news-releases/{current_year}/',
    f'{url}/news-releases/{current_year - 1}/',
    f'https://wp.{domain}/news-releases/',
    f'https://wp.{domain}/press-releases/',
    url,  # Homepage fallback
]
```

---

## Helper Functions

| Function | Purpose |
|----------|---------|
| `clean_news_title(title, url)` | Remove dates, PDF artifacts from titles |
| `is_valid_news_title(title)` | Check if title looks like real news |
| `is_news_article_url(url)` | Check if URL is likely a news article |
| `_add_news_item(news_by_url, news, cutoff_date, source)` | Add to collection, handles deduplication |
| `_extract_news_from_element(element, source_url, base_url)` | Extract news from container element |

---

## Debugging

### Enable verbose output
The scraper prints `[STRATEGY-NAME] Title... | date` for each item found.

### Test a specific company
```bash
ssh root@137.184.168.166
cd /var/www/goldventure/backend && source venv/bin/activate
python -c "
import asyncio
from mcp_servers.website_crawler import crawl_news_releases

async def test():
    result = await crawl_news_releases('https://company-website.com/', months=6)
    print(f'Found {len(result)} news releases')
    for r in sorted(result, key=lambda x: x.get('date') or '', reverse=True)[:10]:
        print(f'  {r.get(\"date\")} - {r.get(\"title\", \"\")[:55]}')

asyncio.run(test())
"
```

### Check raw HTML
```bash
curl -s "https://company-website.com/news/" | grep -A 20 "pattern-to-find"
```

---

## Common Issues

### News not found
1. Check if URL pattern is in `news_page_patterns`
2. Check if HTML structure matches any strategy
3. Add new strategy if needed

### Wrong dates
1. Check date format in `parse_date_standalone()`
2. Add new format if needed

### Duplicate news
- `_add_news_item()` deduplicates by URL
- Items with dates preferred over items without

### Titles showing PDF filenames
- Strategy is finding PDF links instead of title links
- Fix selector to target title element specifically
