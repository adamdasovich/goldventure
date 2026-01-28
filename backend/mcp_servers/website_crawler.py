"""
Website Crawler for Mining Company Documents
Uses Crawl4AI to discover PDFs and technical reports on company websites

Updated: Comprehensive date parsing, external news wire support, title cleaning
"""

import asyncio
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional, Tuple
import re
import sys
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# DATE PARSING - Comprehensive date extraction from multiple formats
# ============================================================================

MONTH_MAP = {
    'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
    'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
    'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
    'aug': '08', 'august': '08', 'sep': '09', 'sept': '09', 'september': '09',
    'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
    'dec': '12', 'december': '12'
}


def parse_date_comprehensive(text: str) -> Tuple[Optional[str], str]:
    """
    Extract date from text using all known patterns.
    Returns (date_str in YYYY-MM-DD, cleaned_text with date removed from start).
    Handles: MM.DD.YYYY, Month DD YYYY, DDMonTitle, YYYYMMDD, etc.
    """
    if not text:
        return None, text

    text = text.strip()
    original_text = text
    date_str = None

    # Pattern 1: XX.XX.YYYY or XX.XX.YY - Could be MM.DD or DD.MM format
    # Determine format by checking which interpretation is valid
    match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(20\d{2}|\d{2})\s*[-–]?\s*(.*)$', text)
    if match:
        first = match.group(1).zfill(2)
        second = match.group(2).zfill(2)
        year = match.group(3)
        if len(year) == 2:
            year = f"20{year}" if int(year) <= 50 else f"19{year}"
        first_int, second_int = int(first), int(second)

        # Try MM.DD.YYYY first (US format)
        if 1 <= first_int <= 12 and 1 <= second_int <= 31:
            date_str = f"{year}-{first}-{second}"
            text = match.group(4).strip() if match.group(4) else ''
            return date_str, text
        # If first > 12, it must be DD.MM.YYYY (European format)
        elif 1 <= second_int <= 12 and 1 <= first_int <= 31:
            date_str = f"{year}-{second}-{first}"
            text = match.group(4).strip() if match.group(4) else ''
            return date_str, text

    # Pattern 2: Month DD, YYYY at start (January 5, 2026Lavras Gold...)
    match = re.match(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(20\d{2})\s*[-–]?\s*(.*)$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower(), '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        date_str = f"{year}-{month}-{day}"
        text = match.group(4).strip() if match.group(4) else ''
        return date_str, text

    # Pattern 3: DDMonTitle - embedded date in title (Kuya Silver: "22DecKuya Silver...")
    match = re.match(r'^(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)([A-Z].*)', text)
    if match:
        day = match.group(1).zfill(2)
        month = MONTH_MAP.get(match.group(2).lower(), '01')
        remaining_title = match.group(3)
        # Determine year - if month is in future, use last year
        current_year = datetime.now().year
        current_month = datetime.now().month
        year = current_year if int(month) <= current_month else current_year - 1
        date_str = f"{year}-{month}-{day}"
        return date_str, remaining_title

    # Pattern 4: XX/XX/YY at start - could be MM/DD/YY or DD/MM/YY
    # Detect format by checking if first or second number > 12
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})\s+(.*)$', text)
    if match:
        first = match.group(1).zfill(2)
        second = match.group(2).zfill(2)
        year_short = match.group(3)
        year = f"20{year_short}" if int(year_short) <= 50 else f"19{year_short}"
        first_int, second_int = int(first), int(second)

        # If first > 12, it MUST be DD/MM/YY (e.g., 13/11/25 = Nov 13)
        if first_int > 12 and 1 <= second_int <= 12:
            date_str = f"{year}-{second}-{first}"  # DD/MM -> YYYY-MM-DD
            text = match.group(4).strip()
            return date_str, text
        # If second > 12, it MUST be MM/DD/YY (e.g., 01/25/26 = Jan 25)
        elif second_int > 12 and 1 <= first_int <= 12:
            date_str = f"{year}-{first}-{second}"  # MM/DD -> YYYY-MM-DD
            text = match.group(4).strip()
            return date_str, text
        # Both <= 12: ambiguous - try DD/MM first (more common internationally)
        # If that would be in the future, fall back to MM/DD
        elif 1 <= first_int <= 12 and 1 <= second_int <= 12:
            # Try DD/MM interpretation first
            dd_mm_date = f"{year}-{second}-{first}"  # DD/MM -> YYYY-MM-DD
            mm_dd_date = f"{year}-{first}-{second}"  # MM/DD -> YYYY-MM-DD

            # Check if DD/MM interpretation is in the future
            try:
                dd_mm_parsed = datetime.strptime(dd_mm_date, '%Y-%m-%d')
                mm_dd_parsed = datetime.strptime(mm_dd_date, '%Y-%m-%d')
                today = datetime.now()

                # If DD/MM is more than 7 days in future but MM/DD is not, use MM/DD
                if dd_mm_parsed > today + timedelta(days=7) and mm_dd_parsed <= today + timedelta(days=7):
                    date_str = mm_dd_date
                else:
                    # Default to DD/MM (European format, more common internationally)
                    date_str = dd_mm_date
            except ValueError:
                # If parsing fails, default to DD/MM
                date_str = dd_mm_date

            text = match.group(4).strip()
            return date_str, text

    # Pattern 5: Abbreviated month (Jan 26 2023 or Jan262023)
    match = re.match(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})\s*,?\s*(20\d{2})\s*[-–]?\s*(.*)$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower(), '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        date_str = f"{year}-{month}-{day}"
        text = match.group(4).strip() if match.group(4) else ''
        return date_str, text

    # Now try to find dates anywhere in text (don't modify text for these)

    # Pattern 6: YYYYMMDD (20261128)
    match = re.search(r'(20\d{2})(\d{2})(\d{2})', text)
    if match:
        year, month, day = match.group(1), match.group(2), match.group(3)
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            date_str = f"{year}-{month}-{day}"
            return date_str, original_text

    # Pattern 7: YYYY-MM-DD or YYYY_MM_DD
    match = re.search(r'(20\d{2})[_-](\d{2})[_-](\d{2})', text)
    if match:
        year, month, day = match.group(1), match.group(2), match.group(3)
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            date_str = f"{year}-{month}-{day}"
            return date_str, original_text

    # Pattern 8: Month DD, YYYY anywhere
    match = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s*(20\d{2})',
        text, re.IGNORECASE
    )
    if match:
        month_name = match.group(1).lower()[:3]
        month = MONTH_MAP.get(month_name, '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        date_str = f"{year}-{month}-{day}"
        return date_str, original_text

    # Pattern 9: XX/XX/YYYY anywhere - could be MM/DD or DD/MM format
    match = re.search(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text)
    if match:
        first = match.group(1).zfill(2)
        second = match.group(2).zfill(2)
        year = match.group(3)
        first_int, second_int = int(first), int(second)

        # If first > 12, it MUST be DD/MM format
        if first_int > 12 and 1 <= second_int <= 12:
            date_str = f"{year}-{second}-{first}"  # DD/MM -> YYYY-MM-DD
            return date_str, original_text
        # If second > 12, it MUST be MM/DD format
        elif second_int > 12 and 1 <= first_int <= 12:
            date_str = f"{year}-{first}-{second}"  # MM/DD -> YYYY-MM-DD
            return date_str, original_text
        # Both <= 12: ambiguous - default to DD/MM (international standard)
        # Use future date check as sanity validation
        elif 1 <= first_int <= 12 and 1 <= second_int <= 12:
            dd_mm_date = f"{year}-{second}-{first}"  # DD/MM interpretation
            mm_dd_date = f"{year}-{first}-{second}"  # MM/DD interpretation
            try:
                dd_mm_parsed = datetime.strptime(dd_mm_date, "%Y-%m-%d")
                mm_dd_parsed = datetime.strptime(mm_dd_date, "%Y-%m-%d")
                now = datetime.now()
                future_threshold = now + timedelta(days=7)
                # If DD/MM is far in future but MM/DD is not, use MM/DD
                if dd_mm_parsed > future_threshold and mm_dd_parsed <= future_threshold:
                    return mm_dd_date, original_text
                return dd_mm_date, original_text
            except (ValueError, TypeError):
                return dd_mm_date, original_text

    return None, original_text


def parse_date_standalone(text: str) -> Optional[str]:
    """Parse date from a string that contains ONLY a date (for dedicated date elements)."""
    if not text:
        return None
    text = text.strip()

    # XX.XX.YYYY - Could be MM.DD.YYYY or DD.MM.YYYY depending on the site
    # Try to determine format by checking which interpretation is valid
    match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(20\d{2}|\d{2})$', text)
    if match:
        first, second, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"
        first_int, second_int = int(first), int(second)

        # Try MM.DD.YYYY first (US format)
        if 1 <= first_int <= 12 and 1 <= second_int <= 31:
            return f"{year}-{first.zfill(2)}-{second.zfill(2)}"
        # If first > 12, it must be DD.MM.YYYY (European format)
        elif 1 <= second_int <= 12 and 1 <= first_int <= 31:
            return f"{year}-{second.zfill(2)}-{first.zfill(2)}"
        # Fallback to MM.DD.YYYY even if potentially invalid
        return f"{year}-{first.zfill(2)}-{second.zfill(2)}"

    # Month DD, YYYY (1911 Gold: December 17, 2025)
    match = re.match(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(20\d{2})$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower()[:3], '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # Month DD / YYYY (GoldMining: January 22 / 2026)
    match = re.match(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*/\s*(20\d{2})$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower()[:3], '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # Mon DD YYYY - no comma (Aston Bay: Nov 17 2025)
    match = re.match(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(20\d{2})$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower(), '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # Mon DD, YYYY - with comma (55 North Mining: Jul 7, 2025)
    match = re.match(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s*(20\d{2})$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower(), '01')
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # XX/XX/YYYY or XX/XX/YY - could be MM/DD or DD/MM format
    # Detect format by checking if first or second number > 12
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(20\d{2}|\d{2})$', text)
    if match:
        first, second, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"
        first_int, second_int = int(first), int(second)

        # If first > 12, it MUST be DD/MM format (e.g., 13/11/25 = Nov 13)
        if first_int > 12 and 1 <= second_int <= 12:
            return f"{year}-{second.zfill(2)}-{first.zfill(2)}"  # DD/MM -> YYYY-MM-DD
        # If second > 12, it MUST be MM/DD format (e.g., 01/25/26 = Jan 25)
        elif second_int > 12 and 1 <= first_int <= 12:
            return f"{year}-{first.zfill(2)}-{second.zfill(2)}"  # MM/DD -> YYYY-MM-DD
        # Both <= 12: ambiguous - default to DD/MM (more common internationally)
        # But use future date check as sanity validation
        elif 1 <= first_int <= 12 and 1 <= second_int <= 12:
            dd_mm_date = f"{year}-{second.zfill(2)}-{first.zfill(2)}"  # DD/MM interpretation
            mm_dd_date = f"{year}-{first.zfill(2)}-{second.zfill(2)}"  # MM/DD interpretation
            # Check if DD/MM interpretation is far in the future (>7 days)
            try:
                from datetime import datetime, timedelta
                dd_mm_parsed = datetime.strptime(dd_mm_date, "%Y-%m-%d")
                mm_dd_parsed = datetime.strptime(mm_dd_date, "%Y-%m-%d")
                now = datetime.now()
                future_threshold = now + timedelta(days=7)

                # If DD/MM is far in future but MM/DD is not, use MM/DD
                if dd_mm_parsed > future_threshold and mm_dd_parsed <= future_threshold:
                    return mm_dd_date
                # Otherwise default to DD/MM (international standard)
                return dd_mm_date
            except (ValueError, TypeError):
                return dd_mm_date  # Default to DD/MM on any error
        else:
            return f"{year}-{second.zfill(2)}-{first.zfill(2)}"  # Default DD/MM

    # Mon DD - NO YEAR (Freegold Ventures: "Jan 15", "Dec 19")
    # Infer year based on whether the date is in the future
    match = re.match(
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$',
        text, re.IGNORECASE
    )
    if match:
        month = MONTH_MAP.get(match.group(1).lower(), '01')
        day = match.group(2).zfill(2)
        # Determine year - if month/day is in the future, use last year
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        month_int = int(month)
        day_int = int(day)
        # If the date appears to be in the future, assume it's from last year
        if month_int > current_month or (month_int == current_month and day_int > current_day):
            year = current_year - 1
        else:
            year = current_year
        return f"{year}-{month}-{day}"

    return None


def clean_news_title(title: str, url: str = '') -> str:
    """Clean up news title - remove dates, PDF artifacts, URL fragments."""
    if not title:
        return ''

    title = title.strip()

    # Decode URL-encoded characters
    title = title.replace('%20', ' ').replace('%2F', '/').replace('%27', "'").replace('%26', '&')

    # Remove DDMon prefix (Kuya Silver: "22DecKuya Silver...")
    match = re.match(r"^(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(.+)$", title, re.IGNORECASE)
    if match:
        title = match.group(3).strip()

    # Remove leading date (parse_date_comprehensive handles most)
    _, title = parse_date_comprehensive(title)

    # Remove "DownloadPDF," prefix
    title = re.sub(r'^Download\s*PDF\s*,?\s*', '', title, flags=re.IGNORECASE)

    # If title starts with YYYYMMDD pattern, extract the meaningful part
    match = re.match(r'^20\d{6}\s+(.+)$', title)
    if match:
        remaining = match.group(1).replace('_', ' ').replace('  ', ' ').strip()
        if len(remaining) > 15:
            title = remaining

    # Remove trailing .pdf
    title = re.sub(r'\.pdf$', '', title, flags=re.IGNORECASE)

    # Remove nr_ or nr- prefixes
    title = re.sub(r'^nr[_-]\s*', '', title, flags=re.IGNORECASE)

    # Clean up underscores in title (often from filenames)
    if '_' in title and ' ' not in title:
        title = title.replace('_', ' ')

    # Clean whitespace
    title = re.sub(r'\s+', ' ', title).strip()

    # If title looks like a URL, extract filename
    if title.startswith('http') or (title.count('/') > 2):
        if url:
            filename = url.split('/')[-1].split('?')[0]
            if filename.endswith('.pdf'):
                filename = filename[:-4]
            filename = filename.replace('_', ' ').replace('-', ' ')
            filename = re.sub(r'^20\d{6}\s*', '', filename)
            filename = re.sub(r'\s+', ' ', filename).strip()
            if len(filename) > 15:
                title = filename.title()

    return title


# ============================================================================
# NEWS TITLE/URL VALIDATION
# ============================================================================

JUNK_TITLE_PATTERNS = [
    'skip to content', 'subscribe for updates', 'subscribe', 'menu',
    'navigation', 'search', 'close', 'home', 'contact', 'about us',
    'privacy policy', 'terms', 'cookie', 'accept', 'decline',
    'read more', 'learn more', 'click here', 'download', 'load more',
    'next page', 'previous', 'back', 'forward', 'share', 'print',
    'email', 'twitter', 'facebook', 'linkedin', 'instagram',
    'older entries', 'newer entries', 'corporate presentation',
    'investor presentation', 'fact sheet', 'news release +',
    'view all', 'see all', 'load more news', 'more news', 'all news',
    'pdf', 'view pdf', 'download pdf', 'view', 'more'
]


def is_valid_news_title(title):
    if not title:
        return False
    title_clean = title.strip()
    title_lower = title_clean.lower()
    if len(title_clean) < 20:  # Reduced from 25 for better coverage
        return False
    for pattern in JUNK_TITLE_PATTERNS:
        if title_lower == pattern or title_lower.startswith(pattern):
            return False
        if pattern in title_lower and len(title_clean) < 35:
            return False
    if re.match(r'^(january|february|march|april|may|june|july|august|september|october|november|december)[\s,]+\d{1,2}[\s,]+\d{4}$', title_lower, re.IGNORECASE):
        return False
    if title_lower.startswith('day:'):
        return False
    if re.match(r'^\d{4}$', title_clean):
        return False
    if title_clean.startswith('http'):
        return False
    return True


def is_valid_news_url(url):
    if not url:
        return False
    url_lower = url.lower().rstrip('/')
    if url_lower.endswith('/news') or url_lower.endswith('/press-releases') or url_lower.endswith('/news-releases') or url_lower.endswith('/media'):
        return False
    if re.search(r'/news/\d{4}$', url_lower) or re.search(r'/\d{4}/news$', url_lower):
        return False
    return True


def is_news_article_url(url: str) -> bool:
    """Check if a URL looks like a news article (internal or external).

    IMPORTANT: This function filters for COMPANY PRESS RELEASES only.
    It EXCLUDES third-party media coverage sites (Mining.com, Northern Miner, etc.)
    which write ABOUT companies but are NOT official press releases.
    """
    if not url:
        return False
    url_lower = url.lower()

    # BLOCKLIST: Third-party media/news sites that write ABOUT companies
    # These are NOT official press releases - they're media coverage
    # Companies sometimes link to these in "In the News" sections, but we don't want them
    media_coverage_sites = [
        'mining.com', 'northernminer.com', 'kitco.com', 'proactiveinvestors.com',
        'smallcappower.com', 'resourceworld.com', 'miningweekly.com',
        'stockwatch.com', 'youtube.com', 'twitter.com', 'linkedin.com',
        'facebook.com', 'instagram.com', 'seekingalpha.com', 'fool.com',
        'investingnews.com', 'juniorminingnetwork.com', 'ceo.ca',
    ]
    if any(site in url_lower for site in media_coverage_sites):
        return False

    # Skip base news listing pages (these are navigation pages, not articles)
    # Strip trailing slash for consistent matching
    url_stripped = url_lower.rstrip('/')
    if url_stripped.endswith(('/news', '/press-releases', '/news-releases', '/media')):
        return False
    # Skip year-based news listing pages like /news/2026 or /news/2026/
    if re.search(r'/news/\d{4}$', url_stripped):
        return False
    # Skip inverted year-news patterns like /2026/news or /2026/news/
    if re.search(r'/\d{4}/news$', url_stripped):
        return False

    # Internal news patterns (company's own news page)
    internal = ['/news/', '/press-release', '/news-release', '/nr-', '/nr_', '/announcement']
    if any(p in url_lower for p in internal):
        return True

    # External news wire services (these distribute OFFICIAL company press releases)
    # These are legitimate because companies use them to distribute their own news
    news_wires = [
        'globenewswire.com', 'newswire.ca', 'prnewswire.com',
        'businesswire.com', 'accesswire.com', 'newsfilecorp.com',
        'cision.com', 'marketwatch.com/press-release'
    ]
    if any(p in url_lower for p in news_wires):
        return True

    # PDF news releases
    if '.pdf' in url_lower and any(p in url_lower for p in ['news', 'nr', 'release', 'press']):
        return True

    return False


class MiningDocumentCrawler:
    """
    Crawler specialized for discovering mining company documents
    Focuses on NI 43-101 reports, presentations, and technical documents
    """

    def __init__(self):
        """Initialize the crawler"""
        self.discovered_urls = set()
        self.pdf_urls = []

    async def discover_documents(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        keywords: List[str] = None
    ) -> List[Dict]:
        """
        Discover documents on a website

        Args:
            start_url: Starting URL (company website)
            max_depth: How deep to crawl (1 = just start page, 2 = one link deep, etc.)
            max_pages: Maximum pages to visit
            keywords: Keywords to filter documents (e.g., ['ni 43-101', 'technical report'])

        Returns:
            List of discovered document dictionaries with url, title, type, etc.
        """
        if keywords is None:
            keywords = [
                'ni 43-101', 'ni43-101', 'ni43101',
                'technical report', 'resource estimate',
                'pea', 'prefeasibility', 'feasibility',
                'mineral resource', 'mineral reserve'
            ]

        self.discovered_urls = set()
        self.pdf_urls = []

        # Configure browser
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )

        # Configure crawler
        crawler_config = CrawlerRunConfig(
            cache_mode="bypass",  # Don't use cache for fresh results
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Start crawling
            await self._crawl_recursive(
                crawler,
                start_url,
                max_depth=max_depth,
                current_depth=0,
                max_pages=max_pages,
                keywords=keywords,
                crawler_config=crawler_config
            )

        # Process discovered PDFs
        documents = self._process_discovered_pdfs(keywords)

        return documents

    async def _crawl_recursive(
        self,
        crawler,
        url: str,
        max_depth: int,
        current_depth: int,
        max_pages: int,
        keywords: List[str],
        crawler_config
    ):
        """Recursively crawl pages to discover documents"""

        # Stop if we've hit limits
        if current_depth > max_depth or len(self.discovered_urls) >= max_pages:
            return

        # Skip if already visited
        if url in self.discovered_urls:
            return

        self.discovered_urls.add(url)

        try:
            # Crawl the page
            result = await crawler.arun(url=url, config=crawler_config)

            if not result.success:
                print(f"[!] Failed to crawl: {url}")
                return

            # Parse HTML
            soup = BeautifulSoup(result.html, 'html.parser')

            # Special handling for news/press-release pages - extract titles from news listings
            if any(keyword in url.lower() for keyword in ['/news/', '/press-release', '/media']):
                self._extract_news_titles(soup, url)

            # Find all links
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                full_url = urljoin(url, href)

                # Check if it's a PDF (handle URLs with parameters like ?v=111911)
                is_pdf = '.pdf' in href.lower() or '.pdf' in full_url.lower().split('?')[0]

                if is_pdf:
                    link_text = link.get_text(strip=True)
                    pdf_info = {
                        'url': full_url,
                        'link_text': link_text,
                        'source_page': url
                    }
                    self.pdf_urls.append(pdf_info)
                    # Safely print with Unicode handling
                    try:
                        if link_text:
                            print(f"[PDF] Found: {link_text[:60]}...")
                        else:
                            # Show URL filename if no link text
                            filename = full_url.split('/')[-1].split('?')[0]
                            print(f"[PDF] Found: {filename}")
                    except UnicodeEncodeError:
                        print(f"[PDF] Found PDF document")

                # If it's an internal link and we haven't hit depth limit, crawl it
                elif current_depth < max_depth:
                    # Skip if it's a PDF (don't crawl PDFs as pages)
                    # Already handled above
                    pass
                    # Check if it's an internal link
                    if self._is_internal_link(url, full_url):
                        # Check if it's likely to contain documents
                        if self._is_relevant_page(full_url, link.get_text(strip=True), keywords):
                            await self._crawl_recursive(
                                crawler, full_url,
                                max_depth, current_depth + 1,
                                max_pages, keywords, crawler_config
                            )

        except Exception as e:
            print(f"[ERROR] Crawling {url}: {str(e)}")

    def _is_internal_link(self, base_url: str, link_url: str) -> bool:
        """Check if a link is internal (same domain)"""
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(link_url).netloc

        # Empty domain means relative URL (internal)
        if not link_domain:
            return True

        # Same domain
        return base_domain == link_domain

    def _is_relevant_page(self, url: str, link_text: str, keywords: List[str]) -> bool:
        """
        Check if a page is likely to contain relevant documents
        Looks at URL path and link text for keywords
        """
        # Skip certain page types
        skip_patterns = [
            '/contact', '/careers', '/team', '/login', '/signin',
            'facebook.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'instagram.com'
        ]

        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False

        # Look for relevant keywords
        relevant_patterns = [
            '/investor', '/reports', '/technical', '/news',
            '/presentations', '/resources', '/projects',
            '/disclosure', '/documents', '/filings'
        ]

        text_lower = (url + ' ' + link_text).lower()

        for pattern in relevant_patterns:
            if pattern in text_lower:
                return True

        # Check for general keywords
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True

        return False

    def _extract_news_titles(self, soup: BeautifulSoup, source_url: str):
        """
        Extract news release titles and dates from news listing pages.
        Finds PDF links and then looks for associated title text and dates.
        """
        from urllib.parse import urljoin
        import re

        # Strategy: Find all PDF links first, then find their associated titles and dates
        # by looking at the link text itself or nearby elements

        pdf_links = soup.find_all('a', href=lambda href: href and '.pdf' in href.lower())

        for pdf_link in pdf_links:
            href = pdf_link.get('href', '')
            full_url = urljoin(source_url, href)

            # Try multiple strategies to find the title and date
            title = None
            extracted_date = None

            # Strategy 1: Check the link's own text (if it's descriptive)
            link_text = pdf_link.get_text(strip=True)
            if link_text and len(link_text) > 20 and not link_text.lower() in ['download', 'pdf', 'view', 'read more']:
                title = link_text

            # Strategy 2: Look for title in preceding siblings (common pattern: title, then PDF link)
            if not title:
                prev_sibling = pdf_link.find_previous_sibling(['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'p', 'div', 'span'])
                if prev_sibling:
                    sibling_text = prev_sibling.get_text(strip=True)
                    if sibling_text and len(sibling_text) > 20 and len(sibling_text) < 300:
                        # Make sure it's not just numbers or dates
                        if not sibling_text.replace('-', '').replace('/', '').replace(',', '').replace(' ', '').isdigit():
                            title = sibling_text

            # Strategy 3: Handle GRID LAYOUTS (like Silver Spruce's uk-grid)
            # Navigate up to find grid container and look for sibling divs with date/title
            parent = pdf_link
            for _ in range(10):  # Navigate up to 10 levels
                parent = parent.parent
                if parent is None:
                    break
                classes = parent.get('class', [])
                # Check for grid-like containers
                if any(c in classes for c in ['uk-grid', 'uk-grid-small', 'grid', 'row', 'news-item', 'news-row']):
                    # Found grid container - look for date and title in direct children divs
                    divs = parent.find_all('div', recursive=False)
                    for div in divs:
                        div_classes = div.get('class', [])
                        div_text = div.get_text(strip=True)

                        # Check for date column (uk-width-1-4@s is Silver Spruce's date column)
                        if 'uk-width-1-4@s' in div_classes or any('date' in c.lower() for c in div_classes):
                            # Try to parse date from this div
                            date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s,]+(\d{1,2})[\s,]+(\d{4})'
                            date_match = re.search(date_pattern, div_text, re.IGNORECASE)
                            if date_match:
                                month_name = date_match.group(1)
                                day = date_match.group(2).zfill(2)
                                year = date_match.group(3)
                                month_map = {
                                    'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
                                    'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
                                    'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
                                    'aug': '08', 'august': '08', 'sep': '09', 'september': '09',
                                    'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
                                    'dec': '12', 'december': '12'
                                }
                                month_num = month_map.get(month_name.lower(), '01')
                                extracted_date = f"{year}-{month_num}-{day}"

                        # Check for title column (uk-width-expand@s is Silver Spruce's title column)
                        if 'uk-width-expand@s' in div_classes or any('title' in c.lower() or 'expand' in c.lower() for c in div_classes):
                            if div_text and len(div_text) > 20 and len(div_text) < 500:
                                if div_text.lower() not in ['pdf', 'download', 'view', 'read more']:
                                    if not title:
                                        title = div_text

                    # If we found date or title from grid, we're done with this strategy
                    if extracted_date or title:
                        break

            # Strategy 4: Fallback to parent/grandparent text search
            if not extracted_date or not title:
                parent = pdf_link.find_parent(['div', 'li', 'article', 'section', 'tr'])
                if parent:
                    grandparent = parent.find_parent(['div', 'li', 'article', 'section', 'tr'])
                    search_element = grandparent if grandparent else parent

                    # Get all text from the parent/grandparent for date extraction
                    parent_text = search_element.get_text()

                    # Extract date from parent text if not found yet
                    if not extracted_date:
                        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s,]+(\d{1,2})[\s,]+(\d{4})'
                        date_match = re.search(date_pattern, parent_text, re.IGNORECASE)
                        if date_match:
                            month_name = date_match.group(1)
                            day = date_match.group(2).zfill(2)
                            year = date_match.group(3)
                            month_map = {
                                'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
                                'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
                                'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
                                'aug': '08', 'august': '08', 'sep': '09', 'september': '09',
                                'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
                                'dec': '12', 'december': '12'
                            }
                            month_num = month_map.get(month_name.lower(), '01')
                            extracted_date = f"{year}-{month_num}-{day}"

                    # Find title if not found yet
                    if not title:
                        for child in search_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'span', 'div', 'td']):
                            child_text = child.get_text(strip=True)
                            if child_text and len(child_text) > 20 and len(child_text) < 300:
                                # Skip if it's just numbers/dates or common link text
                                text_clean = child_text.lower()
                                if text_clean in ['pdf', 'download', 'view', 'read more']:
                                    continue
                                if not child_text.replace('-', '').replace('/', '').replace(',', '').replace(' ', '').isdigit():
                                    title = child_text
                                    break

            # If we found a good title or date, update or add the PDF
            if title or extracted_date:
                # Normalize URLs for comparison (remove trailing slash, parameters, etc.)
                full_url_normalized = full_url.split('?')[0].rstrip('/')

                # Check if this PDF is already in our list
                found = False
                for pdf_info in self.pdf_urls:
                    pdf_url_normalized = pdf_info['url'].split('?')[0].rstrip('/')
                    if pdf_url_normalized == full_url_normalized:
                        # Update the link_text if current one is poor (filename-like or short)
                        current_text = pdf_info.get('link_text', '')
                        # Check if current text looks like a filename
                        is_filename = current_text.endswith('.pdf') or len(current_text) < 30
                        if title and (not current_text or is_filename):
                            pdf_info['link_text'] = title
                            try:
                                print(f"[TITLE] Updated: {current_text} -> {title[:60]}...")
                            except UnicodeEncodeError:
                                print(f"[TITLE] Updated title")
                        # Store extracted date if found
                        if extracted_date and not pdf_info.get('extracted_date'):
                            pdf_info['extracted_date'] = extracted_date
                            print(f"[DATE] Extracted: {extracted_date}")
                        found = True
                        break

                # If not found, add it
                if not found:
                    pdf_entry = {
                        'url': full_url,
                        'link_text': title or link_text,
                        'source_page': source_url
                    }
                    if extracted_date:
                        pdf_entry['extracted_date'] = extracted_date
                        print(f"[DATE] Extracted: {extracted_date}")
                    self.pdf_urls.append(pdf_entry)
                    try:
                        if title:
                            print(f"[TITLE] Found: {title[:60]}...")
                    except UnicodeEncodeError:
                        print(f"[TITLE] Found title")

    def _process_discovered_pdfs(self, keywords: List[str]) -> List[Dict]:
        """
        Process discovered PDFs and categorize them
        Returns structured list with document type classification
        """
        # Deduplicate PDFs - keep best title and merge extracted_date
        seen_urls = {}
        for pdf in self.pdf_urls:
            url_normalized = pdf['url'].split('?')[0].rstrip('/')
            link_text = pdf.get('link_text', '')

            # If URL not seen yet, add it
            if url_normalized not in seen_urls:
                seen_urls[url_normalized] = pdf
            else:
                # URL exists - merge best data
                existing = seen_urls[url_normalized]
                existing_text = existing.get('link_text', '')
                existing_is_filename = existing_text.endswith('.pdf') or len(existing_text) < 30
                current_is_filename = link_text.endswith('.pdf') or len(link_text) < 30

                # Replace if current has better title than existing
                if existing_is_filename and not current_is_filename:
                    # Keep extracted_date from existing if current doesn't have one
                    if existing.get('extracted_date') and not pdf.get('extracted_date'):
                        pdf['extracted_date'] = existing['extracted_date']
                    seen_urls[url_normalized] = pdf
                elif not current_is_filename and len(link_text) > len(existing_text):
                    # Both are good titles, keep longer one
                    if existing.get('extracted_date') and not pdf.get('extracted_date'):
                        pdf['extracted_date'] = existing['extracted_date']
                    seen_urls[url_normalized] = pdf
                else:
                    # Keep existing but merge extracted_date if current has one
                    if pdf.get('extracted_date') and not existing.get('extracted_date'):
                        existing['extracted_date'] = pdf['extracted_date']

        # Use deduplicated list
        deduped_pdfs = list(seen_urls.values())
        print(f"\n[DEDUP] Reduced {len(self.pdf_urls)} PDFs to {len(deduped_pdfs)} unique URLs\n")

        documents = []

        for pdf in deduped_pdfs:
            url = pdf['url']
            link_text = pdf['link_text']
            source_page = pdf.get('source_page', '').lower()
            combined_text = (link_text + ' ' + url).lower()

            # Determine document type (check in priority order)
            # NEWS RELEASES NOW HAVE HIGHEST PRIORITY (most current company info)
            doc_type = 'other'

            # News releases - HIGHEST PRIORITY for current company information
            # Patterns: nr- (hyphen), _nr_ (underscore), _nr. (end of name), omg_nr, press-release variants
            # Also check source page - if found on /news/ page, it's likely a news release
            is_from_news_page = any(kw in source_page for kw in ['/news/', '/news-releases/', '/press-releases/', '/press/'])
            has_news_pattern = any(kw in combined_text for kw in ['/news/', 'nr-', '_nr_', '_nr.', 'omg_nr', 'press-release', 'press_release', '/press-releases/', '/news-releases/', 'news_release', 'newsrelease', 'drill_results', 'drill-results', 'announces', 'announcement'])
            if is_from_news_page or has_news_pattern:
                doc_type = 'news_release'
            # NI 43-101 reports
            elif any(kw in combined_text for kw in ['ni 43-101', 'ni43-101', 'ni43101', '43-101', 'technical-report']):
                doc_type = 'ni43101'
            # Presentations
            elif any(kw in combined_text for kw in ['presentation', 'corporate-presentation', '/presentations/']):
                doc_type = 'presentation'
            # Financial documents
            elif any(kw in combined_text for kw in ['financial', 'annual-report', 'quarterly', '/financial']):
                doc_type = 'financial_statement'

            # Try to extract FULL DATE - PRIORITIZE URL-based dates over HTML-extracted dates
            # URL dates (like nr-20250815.pdf) are more reliable than HTML page scraping
            full_date = None
            year = None
            
            # First try URL-based patterns (most reliable)

            # Month name to number mapping
            month_map = {
                'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
                'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
                'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
                'aug': '08', 'august': '08', 'sep': '09', 'sept': '09', 'september': '09',
                'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
                'dec': '12', 'december': '12'
            }

            if full_date:
                # Use extracted date from HTML (e.g., "December 3, 2025" -> "2025-12-03")
                year = full_date[:4]
            else:
                # Fall back to extracting from filename/URL - try multiple patterns
                # Pattern 1: YYYY_MM_DD or YYYY-MM-DD (e.g., 2024_11_05_nr_sse.pdf)
                date_match = re.search(r'(20\d{2})[_-](\d{2})[_-](\d{2})', combined_text)
                if date_match:
                    year = date_match.group(1)
                    month = date_match.group(2)
                    day = date_match.group(3)
                    full_date = f"{year}-{month}-{day}"
                else:
                    # Pattern 2: YYYYMMDD (8 consecutive digits)
                    date_match = re.search(r'(20\d{2})(\d{2})(\d{2})', combined_text)
                    if date_match:
                        year = date_match.group(1)
                        month = date_match.group(2)
                        day = date_match.group(3)
                        full_date = f"{year}-{month}-{day}"
                    else:
                        # Pattern 3: month-day-year format (e.g., nr-may-9-2019.pdf)
                        date_match = re.search(
                            r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[_-](\d{1,2})[_-](20\d{2})',
                            combined_text, re.IGNORECASE
                        )
                        if date_match:
                            month_name = date_match.group(1).lower()
                            day = date_match.group(2).zfill(2)
                            year = date_match.group(3)
                            month = month_map.get(month_name, '01')
                            full_date = f"{year}-{month}-{day}"
                        else:
                            # Pattern 4: "Month Day YY" in title or filename (e.g., "March 31 25" or "mar_04_20")
                            # Accept spaces, commas, OR underscores as separators
                            date_match = re.search(
                                r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[\s,_]+(\d{1,2})[\s,_]+(\d{2})(?!\d)',
                                combined_text, re.IGNORECASE
                            )
                            if date_match:
                                month_name = date_match.group(1).lower()
                                day = date_match.group(2).zfill(2)
                                year_short = date_match.group(3)
                                # Convert 2-digit year to 4-digit (assume 20xx for years 00-99)
                                year = f"20{year_short}"
                                month = month_map.get(month_name, '01')
                                full_date = f"{year}-{month}-{day}"
                            else:
                                # Pattern 5: "Month Day, YYYY" in title (e.g., "March 31, 2025")
                                date_match = re.search(
                                    r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[\s,]+(\d{1,2})[\s,]+(20\d{2})',
                                    combined_text, re.IGNORECASE
                                )
                                if date_match:
                                    month_name = date_match.group(1).lower()
                                    day = date_match.group(2).zfill(2)
                                    year = date_match.group(3)
                                    month = month_map.get(month_name, '01')
                                    full_date = f"{year}-{month}-{day}"
                                else:
                                    # Fall back to HTML-extracted date if available (less reliable)
                                    html_date = pdf.get('extracted_date')
                                    if html_date:
                                        full_date = html_date
                                        year = html_date[:4]
                                    else:
                                        # Last resort: just extract year from URL
                                        date_match = re.search(r'(20\d{2})', combined_text)
                                        year = date_match.group(1) if date_match else None
                                        full_date = None

            # Determine best title - prefer descriptive link_text, fallback to cleaned filename
            title = link_text
            # If title is poor (just "PDF", "Download", too short), use filename
            if not title or title.lower() in ['pdf', 'download', 'view', 'read more'] or len(title) < 10:
                # Extract filename and clean it up
                filename = url.split('/')[-1].split('?')[0]
                if filename.endswith('.pdf'):
                    filename = filename[:-4]
                # Replace underscores/dashes with spaces, remove date prefix if present
                cleaned = filename.replace('_', ' ').replace('-', ' ')
                # Remove leading date patterns like "2024 11 05 nr sse" -> "nr sse"
                cleaned = re.sub(r'^20\d{2}\s+\d{2}\s+\d{2}\s*', '', cleaned)
                cleaned = re.sub(r'^nr\s+', '', cleaned, flags=re.IGNORECASE)  # Remove leading "nr"
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize whitespace
                if len(cleaned) > 10:
                    title = cleaned.title()  # Title case
                else:
                    title = filename  # Keep original filename if too short

            documents.append({
                'url': url,
                'title': title,
                'document_type': doc_type,
                'year': year,
                'date': full_date,  # Full date if available
                'source_page': pdf['source_page'],
                'relevance_score': self._calculate_relevance(combined_text, keywords)
            })

        # Sort by date (newest first), then by relevance
        # Documents with dates come first, sorted by date, then by relevance
        documents_with_dates = [d for d in documents if d.get('date')]
        documents_without_dates = [d for d in documents if not d.get('date')]

        documents_with_dates.sort(key=lambda x: x['date'], reverse=True)
        documents_without_dates.sort(key=lambda x: x['relevance_score'], reverse=True)

        return documents_with_dates + documents_without_dates

    def _filter_by_date_range(self, documents: List[Dict], months: int = 6) -> List[Dict]:
        """
        Filter documents to only include those from the last N months
        Only filters documents that have a date field
        """
        if not documents:
            return []

        cutoff_date = datetime.now() - timedelta(days=months * 30)
        filtered = []

        for doc in documents:
            if doc.get('date'):
                try:
                    doc_date = datetime.strptime(doc['date'], '%Y-%m-%d')
                    if doc_date >= cutoff_date:
                        filtered.append(doc)
                except ValueError:
                    # If date parsing fails, include the document
                    filtered.append(doc)
            else:
                # No date, include it (might be valuable)
                filtered.append(doc)

        return filtered

    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """
        Calculate relevance score based on keyword matches
        NEWS RELEASES now have highest priority
        """
        score = 0.0
        text_lower = text.lower()

        # HIGHEST PRIORITY: News releases (most current company info)
        news_keywords = ['/news/', 'nr-', 'press-release', 'press_release', '/press-releases/']
        for kw in news_keywords:
            if kw in text_lower:
                score += 15  # Higher score than technical reports

        # High-value keywords: Technical reports
        high_value = ['ni 43-101', 'ni43-101', 'technical report', 'resource estimate']
        for kw in high_value:
            if kw in text_lower:
                score += 10

        # Medium-value keywords
        medium_value = ['pea', 'feasibility', 'mineral resource', 'updated', 'drill', 'assay']
        for kw in medium_value:
            if kw in text_lower:
                score += 5

        # General keywords
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 1

        return score


async def crawl_technical_documents(url: str) -> List[Dict]:
    """
    Crawl common technical document page patterns to find NI 43-101 reports, PEAs, etc.
    This handles deeply nested technical document pages that recursive crawling might miss.
    """
    from urllib.parse import urljoin

    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(cache_mode="bypass")

    technical_docs = []
    seen_urls = set()

    # Common technical document URL patterns
    tech_doc_patterns = [
        '/technical-documents/',
        '/technical-reports/',
        '/technical/',
        '/reports/',
        '/ni-43-101/',
        '/43-101/',
        '/investors/reports/',
        '/investors/technical-reports/',
        '/investor-relations/reports/',
        '/investor-relations/technical-reports/',
    ]

    # Sub-paths to check under discovered project pages
    tech_subpaths = ['/technical-documents/', '/technical-reports/', '/reports/', '/documents/']

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First, try to find project pages that might have technical documents
        project_pages = []
        try:
            result = await crawler.arun(url=url, config=crawler_config)
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')

                # Find project links that might lead to technical documents
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()

                    # Check if this is a project page or technical page
                    if any(kw in href.lower() or kw in text for kw in ['project', 'technical', 'reports', '43-101']):
                        full_url = urljoin(url, href)
                        if full_url not in seen_urls and url.split('/')[2] in full_url:
                            path = href if href.startswith('/') else '/' + href.split('/', 3)[-1] if '/' in href else ''
                            if path:
                                tech_doc_patterns.append(path)
                                # If it's a project page, also add sub-paths for technical documents
                                if '/project' in path.lower():
                                    project_pages.append(path.rstrip('/'))
        except Exception as e:
            print(f"[TECH-DOCS] Error scanning {url}: {e}")

        # Add technical document sub-paths under each discovered project page
        for project_path in project_pages:
            for subpath in tech_subpaths:
                tech_doc_patterns.append(project_path + subpath)

        # Now check each technical document pattern
        for pattern in tech_doc_patterns:
            if not pattern:
                continue
            tech_url = urljoin(url.rstrip('/'), pattern)

            if tech_url in seen_urls:
                continue
            seen_urls.add(tech_url)

            try:
                result = await crawler.arun(url=tech_url, config=crawler_config)
                if not result.success:
                    continue

                print(f"[TECH-DOCS] Scanning: {tech_url}")
                soup = BeautifulSoup(result.html, 'html.parser')

                # Find all PDF links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if '.pdf' not in href.lower():
                        continue

                    pdf_url = urljoin(tech_url, href)
                    if pdf_url in seen_urls:
                        continue
                    seen_urls.add(pdf_url)

                    # Get title from link text or nearby elements
                    title = link.get_text(strip=True)
                    if not title or len(title) < 10:
                        # Try parent element
                        parent = link.parent
                        if parent:
                            title = parent.get_text(strip=True)

                    # Clean up title
                    title = re.sub(r'\s+', ' ', title).strip()
                    if len(title) > 200:
                        title = title[:200] + '...'

                    # Determine document type
                    combined_lower = (title + ' ' + pdf_url).lower()
                    doc_type = 'technical_report'

                    if any(kw in combined_lower for kw in ['ni 43-101', 'ni43-101', '43-101']):
                        doc_type = 'ni_43_101'
                    elif any(kw in combined_lower for kw in ['pea', 'preliminary economic']):
                        doc_type = 'pea'
                    elif any(kw in combined_lower for kw in ['feasibility', 'prefeasibility', 'pre-feasibility']):
                        doc_type = 'feasibility_study'
                    elif any(kw in combined_lower for kw in ['resource estimate', 'mineral resource']):
                        doc_type = 'resource_estimate'

                    technical_docs.append({
                        'url': pdf_url,
                        'title': title if title else 'Technical Document',
                        'document_type': doc_type,
                        'source': 'technical_documents_page'
                    })
                    print(f"[TECH-DOCS] Found: {title[:60]}... ({doc_type})")

            except Exception as e:
                continue

    return technical_docs


async def crawl_company_website(url: str, max_depth: int = 2) -> List[Dict]:
    """
    Convenience function to crawl a company website
    Returns list of discovered documents including technical reports from deep pages
    """
    crawler = MiningDocumentCrawler()

    # Standard recursive document discovery
    documents = await crawler.discover_documents(
        start_url=url,
        max_depth=max_depth,
        max_pages=50
    )

    # Also crawl technical document pages (catches deeply nested NI 43-101 reports)
    try:
        tech_docs = await crawl_technical_documents(url)
        if tech_docs:
            print(f"[CRAWL] Found {len(tech_docs)} additional technical documents")
            # Merge and deduplicate by URL
            seen_urls = {d['url'].split('?')[0].rstrip('/') for d in documents}
            for doc in tech_docs:
                url_norm = doc['url'].split('?')[0].rstrip('/')
                if url_norm not in seen_urls:
                    documents.append(doc)
                    seen_urls.add(url_norm)
    except Exception as e:
        print(f"[CRAWL] Technical documents crawl error: {e}")

    return documents


async def crawl_news_releases(url: str, months: int = 6, max_depth: int = 2) -> List[Dict]:
    """
    Crawl a company website for NEWS RELEASES.
    OPTIMIZED: Only uses HTML news extraction for speed.
    The slow recursive PDF crawl is skipped - most news is in HTML format.

    Args:
        url: Company website URL
        months: Number of months to look back (default 6)
        max_depth: How deep to crawl (default 2) - unused, kept for API compatibility

    Returns:
        List of news release documents with dates, sorted by newest first
    """
    # Use optimized HTML-only extraction (much faster than recursive PDF crawl)
    html_news = await crawl_html_news_pages(url, months=months)

    # IMPORTANT: Sort by date FIRST (items with dates come before items without)
    # This ensures that when we deduplicate by title, we keep the version WITH the date
    html_news_sorted = sorted(
        html_news,
        key=lambda x: (0 if x.get('date') else 1, x.get('date') or '0000-00-00'),
        reverse=False  # Items with dates first, then sorted by date ascending
    )
    # Re-sort so newest dates come first among dated items
    html_news_sorted = sorted(
        html_news_sorted,
        key=lambda x: (0 if x.get('date') else 1, x.get('date') or ''),
        reverse=False  # 0 (has date) before 1 (no date), then by date descending
    )
    # Actually let's just separate and process
    with_dates_raw = [n for n in html_news if n.get('date')]
    without_dates_raw = [n for n in html_news if not n.get('date')]
    # Sort dated items newest first
    with_dates_raw.sort(key=lambda x: x['date'], reverse=True)
    # Combine: dated items first (so they're kept during dedup), then undated
    html_news_sorted = with_dates_raw + without_dates_raw

    # Deduplicate by URL AND title (same news can have multiple URLs)
    # Process dated items first so they're kept over undated duplicates
    seen_urls = set()
    seen_titles = set()
    unique_news = []
    for news in html_news_sorted:
        url_normalized = news['url'].split('?')[0].rstrip('/')
        # Normalize title for comparison (lowercase, remove extra spaces)
        title_normalized = re.sub(r'\s+', ' ', news.get('title', '').lower().strip())
        # Create title+date key to allow same title with different dates (recurring reports)
        title_date_key = f"{title_normalized}|{news.get('date', '')}"

        # Skip if we've seen this URL
        if url_normalized in seen_urls:
            continue
        # Skip if we've seen this exact title+date combo (but allow same title with different dates)
        if title_normalized and title_date_key in seen_titles:
            continue

        seen_urls.add(url_normalized)
        if title_normalized:
            seen_titles.add(title_date_key)
        unique_news.append(news)

    # Sort final result: items with dates first (newest first), then items without dates
    with_dates = sorted([n for n in unique_news if n.get('date')], key=lambda x: x['date'], reverse=True)
    without_dates = [n for n in unique_news if not n.get('date')]

    return with_dates + without_dates


async def _extract_date_from_article_page(crawler, article_url: str, crawler_config) -> str:
    """
    Fetch an individual news article page and extract the publication date.

    Args:
        crawler: AsyncWebCrawler instance
        article_url: URL of the news article page
        crawler_config: Crawler configuration

    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    try:
        # Fetch the article page
        result = await crawler.arun(url=article_url, config=crawler_config)

        if not result.success:
            return None

        soup = BeautifulSoup(result.html, 'html.parser')

        # Strategy 1: Look for meta tags with publication date
        meta_tags = [
            ('property', 'article:published_time'),
            ('name', 'publish-date'),
            ('name', 'publication_date'),
            ('name', 'date'),
            ('property', 'og:published_time'),
            ('itemprop', 'datePublished'),
        ]

        for attr, value in meta_tags:
            meta = soup.find('meta', {attr: value})
            if meta and meta.get('content'):
                date_content = meta['content']
                # Parse ISO format or other common formats
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_content)
                if date_match:
                    return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        # Strategy 2: Look for time element with datetime attribute
        time_elem = soup.find('time', datetime=True)
        if time_elem:
            datetime_str = time_elem['datetime']
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_str)
            if date_match:
                return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        # Strategy 3: Look for common date patterns in text near the article title
        # Find article header or title area
        article_areas = soup.find_all(['article', 'header', 'div'], class_=re.compile(r'(article|post|entry|news|content)', re.IGNORECASE))

        for area in article_areas[:3]:  # Check first 3 matching areas
            area_text = area.get_text()

            # Look for date patterns like "December 7, 2025" or "Dec 7, 2025"
            date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\\s,]+(\d{1,2})[\\s,]+(\d{4})'
            date_match = re.search(date_pattern, area_text, re.IGNORECASE)

            if date_match:
                month_name = date_match.group(1)
                day = date_match.group(2).zfill(2)
                year = date_match.group(3)

                # Convert month name to number
                month_map = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12',
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                }
                month_num = month_map.get(month_name.lower(), '01')
                return f"{year}-{month_num}-{day}"

        # Strategy 3b: Look in ALL divs near the top of the page (first 50 divs)
        all_divs = soup.find_all('div')[:50]
        for div in all_divs:
            div_text = div.get_text(strip=True)
            # Look for standalone date text (likely the publication date)
            if len(div_text) < 100:  # Short text - likely just a date
                date_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})$'
                date_match = re.search(date_pattern, div_text.strip(), re.IGNORECASE)

                if date_match:
                    month_name = date_match.group(1)
                    day = date_match.group(2).zfill(2)
                    year = date_match.group(3)

                    month_map = {
                        'january': '01', 'february': '02', 'march': '03', 'april': '04',
                        'may': '05', 'june': '06', 'july': '07', 'august': '08',
                        'september': '09', 'october': '10', 'november': '11', 'december': '12',
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                    }
                    month_num = month_map.get(month_name.lower(), '01')
                    return f"{year}-{month_num}-{day}"

        # Strategy 4: Look for numeric date patterns in the first few paragraphs
        text_content = soup.get_text()[:2000]  # First 2000 chars

        # Pattern like "12/07/2025" or "12-07-2025"
        numeric_date = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text_content)
        if numeric_date:
            month = numeric_date.group(1).zfill(2)
            day = numeric_date.group(2).zfill(2)
            year = numeric_date.group(3)
            return f"{year}-{month}-{day}"

        return None

    except Exception as e:
        # Silently fail and return None
        print(f"[DATE EXTRACT ERROR] {article_url}: {str(e)}")
        return None


def _extract_news_from_element(element, source_url: str, base_url: str) -> Optional[Dict]:
    """
    Extract news from article/news-item element with improved handling.
    Handles structures like:
    - Laurion: <div class="news-item"><div class="date">01.07.2026</div><div class="title"><a>...</a></div></div>
    - 1911 Gold: <div class="news-item"><span class="date">December 17, 2025</span><a class="title">...</a></div>
    """
    try:
        date_str = None
        title = None
        link_url = None

        # Strategy 1: Look for dedicated date element (div.date, span.date, time, .news-date)
        date_elem = element.find(['div', 'span', 'time'], class_=lambda c: c and 'date' in str(c).lower())
        if date_elem:
            date_str = parse_date_standalone(date_elem.get_text(strip=True))

        # Strategy 2: Look for dedicated title element (div.title a, div.news-title a, a.title, h2, h3)
        title_elem = element.find('div', class_='title')
        if not title_elem:
            title_elem = element.find('div', class_='news-title')  # GoldMining pattern
        if title_elem:
            title_link = title_elem.find('a', href=True)
            if title_link:
                title = title_link.get_text(strip=True)
                link_url = title_link.get('href', '')

        # Try a.title or a with class containing 'title' (e.g., news-item__title)
        if not title:
            title_link = element.find('a', class_='title')
            if not title_link:
                title_link = element.find('a', class_=lambda c: c and 'title' in str(c).lower())
            if title_link:
                title = title_link.get_text(strip=True)
                link_url = title_link.get('href', '')

        # Try h2/h3/h4 with link
        if not title:
            for heading in element.find_all(['h2', 'h3', 'h4']):
                heading_link = heading.find('a', href=True)
                if heading_link:
                    title = heading_link.get_text(strip=True)
                    link_url = heading_link.get('href', '')
                    break
                else:
                    title = heading.get_text(strip=True)

        # Fallback: first link with substantial text
        if not title:
            for link in element.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                href = link.get('href', '')
                # Skip PDF links that say "View PDF" etc
                if link_text.lower() in ['pdf', 'view', 'view pdf', 'download', 'read more']:
                    continue
                if len(link_text) > 20:
                    title = link_text
                    link_url = href
                    break

        # If no date yet, try comprehensive parsing on element text
        if not date_str:
            elem_text = element.get_text(strip=True)
            date_str, _ = parse_date_comprehensive(elem_text[:100])

        # Get link URL if we don't have one
        if not link_url:
            first_link = element.find('a', href=True)
            if first_link:
                link_url = first_link.get('href', '')

        # Validate
        if not title or len(title) < 10:
            return None

        # Clean title
        title = clean_news_title(title, link_url or '')

        if not is_valid_news_title(title):
            return None

        # Build full URL - use source_url (current page) for proper path resolution
        if link_url and not link_url.startswith('http'):
            link_url = urljoin(source_url, link_url)

        return {
            'title': title,
            'url': link_url or source_url,
            'date': date_str,
            'document_type': 'news_release',
            'year': date_str[:4] if date_str else None
        }
    except Exception as e:
        logger.debug(f"Failed to parse news item from HTML: {e}")
        return None  # Parsing failed - return None to signal no valid news item


def _extract_url_slug(url: str) -> str:
    """
    Extract the meaningful slug from a news URL.
    Examples:
      /news/20260112-max-resource-enters... -> 20260112-max-resource-enters...
      /news/2026/20260112-max-resource... -> 20260112-max-resource...
      /press-releases/2026/01/some-news -> some-news
    """
    # Remove query params and trailing slash
    clean_url = url.split('?')[0].rstrip('/')
    # Get the last path segment
    parts = clean_url.split('/')
    slug = parts[-1] if parts else ''
    # If slug looks like a year (e.g., '2026'), try the second-to-last
    if slug.isdigit() and len(slug) == 4 and len(parts) > 1:
        slug = parts[-2]
    return slug.lower()


# Track seen slugs globally for deduplication across different URL paths
_seen_slugs: Dict[str, str] = {}  # Map slug -> first URL seen


def _add_news_item(news_by_url: Dict[str, Dict], news: Dict, cutoff_date: datetime, source: str) -> bool:
    """
    Add news item to collection, preferring items WITH dates over items WITHOUT dates.
    Uses both URL and SLUG deduplication to catch same news with different URL paths.
    Returns True if item was added/updated, False if skipped.
    """
    global _seen_slugs

    url_norm = news['url'].split('?')[0].rstrip('/')
    slug = _extract_url_slug(news['url'])

    # Check date range first
    if news.get('date'):
        try:
            if datetime.strptime(news['date'], '%Y-%m-%d') < cutoff_date:
                return False
        except (ValueError, TypeError):
            pass

    # SLUG DEDUPLICATION: Check if we've seen this slug before with a different URL
    # This catches cases like:
    #   /news/20260112-article vs /news/2026/20260112-article vs /press-releases/2026/20260112-article
    if slug and len(slug) > 10:  # Only for meaningful slugs (not 'news', '2026', etc.)
        if slug in _seen_slugs and _seen_slugs[slug] != url_norm:
            # Same slug, different URL - skip this duplicate
            return False
        _seen_slugs[slug] = url_norm

    # If URL not seen yet, add it
    if url_norm not in news_by_url:
        news_by_url[url_norm] = news
        print(f"[{source}] {news['title'][:50]}... | {news.get('date', 'no date')}")
        return True

    # URL already exists - update if new item has date and existing doesn't
    existing = news_by_url[url_norm]
    if news.get('date') and not existing.get('date'):
        news_by_url[url_norm] = news
        print(f"[{source}] UPDATED with date: {news['title'][:50]}... | {news.get('date')}")
        return True

    return False


async def crawl_html_news_pages(url: str, months: int = 6) -> List[Dict]:
    """
    Crawl HTML news pages from a company website.
    Supports: external news wires, multiple date formats, various HTML layouts.

    Args:
        url: Company website URL
        months: Number of months to look back

    Returns:
        List of news release dictionaries with title, url, date
    """
    global _seen_slugs
    _seen_slugs = {}  # Reset slug tracker for new crawl session

    news_by_url: Dict[str, Dict] = {}  # Map URL -> news item (prefer items with dates)
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    # Fast config for daily news scraping - no delays, short timeout
    # The slow config (5s delay, networkidle) caused 2+ hour scrapes
    # page_timeout=15000 (15 seconds) prevents slow/unreachable sites from blocking
    # (default was 60000ms which caused 300+ second scrapes when multiple URLs timed out)
    crawler_config = CrawlerRunConfig(
        cache_mode="bypass",
        page_timeout=15000,  # 15 seconds max per URL (was 60s default)
    )

    # Track scrape start time for time-based early exit
    scrape_start_time = datetime.now()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        current_year = datetime.now().year

        # Normalize URL - remove trailing slashes to avoid double slashes
        url = url.rstrip('/')

        # Extract domain for WordPress subdomain check (Angkor pattern)
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')

        # ============================================================
        # SPECIAL CASE: ASP.NET Evergreen CMS (Harvest Gold pattern)
        # These sites use JavaScript year selectors that require interaction
        # Check for /news/default.aspx pattern
        # Use the base domain (scheme + netloc) not the full URL which might include paths
        # ============================================================
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        aspx_news_urls = [
            f'{base_url}/news/default.aspx',
            f'{base_url}/news/news.aspx',
            f'{base_url}/news-releases/default.aspx',
        ]

        for aspx_url in aspx_news_urls:
            try:
                # First check if the page exists and has Evergreen structure
                result = await crawler.arun(url=aspx_url, config=crawler_config)
                if not result.success:
                    continue

                soup = BeautifulSoup(result.html, 'html.parser')

                # Check for Evergreen year selector
                year_select = soup.select_one('select.evergreen-dropdown')
                if not year_select:
                    continue

                print(f"[ASPX] Found Evergreen CMS page: {aspx_url}")

                # Get available years from the dropdown
                years = [opt.get('value') for opt in year_select.select('option') if opt.get('value')]
                # Only process recent years (within the cutoff window)
                cutoff_year = (datetime.now() - timedelta(days=months * 30)).year
                years_to_check = [y for y in years if y and int(y) >= cutoff_year][:3]  # Max 3 years

                for year in years_to_check:
                    try:
                        # Use JavaScript to select the year and get the content
                        js_code = f'''
                        const select = document.querySelector("select.evergreen-dropdown");
                        if (select) {{
                            select.value = "{year}";
                            select.dispatchEvent(new Event("change", {{ bubbles: true }}));
                        }}
                        await new Promise(r => setTimeout(r, 2000));
                        '''

                        year_config = CrawlerRunConfig(
                            cache_mode="bypass",
                            js_code=js_code,
                            wait_until="networkidle",
                            page_timeout=30000
                        )

                        year_result = await crawler.arun(url=aspx_url, config=year_config)
                        if not year_result.success:
                            continue

                        year_soup = BeautifulSoup(year_result.html, 'html.parser')

                        # Extract news items from Evergreen structure
                        for item in year_soup.select('.evergreen-news-item, .evergreen-item'):
                            try:
                                # Get date
                                date_elem = item.select_one('.evergreen-news-date, .evergreen-item-date-time')
                                date_str = None
                                if date_elem:
                                    date_str = parse_date_standalone(date_elem.get_text(strip=True))

                                # Get title and link
                                link = item.select_one('.evergreen-news-headline-link, .evergreen-item-title, a[href*="/news/"]')
                                if not link:
                                    continue

                                title = link.get_text(strip=True)
                                href = link.get('href', '')

                                if not title or len(title) < 15:
                                    continue

                                # Build full URL
                                if href and not href.startswith('http'):
                                    href = urljoin(aspx_url, href)

                                news = {
                                    'title': clean_news_title(title, href),
                                    'url': href,
                                    'date': date_str,
                                    'document_type': 'news_release',
                                    'year': date_str[:4] if date_str else year
                                }
                                _add_news_item(news_by_url, news, cutoff_date, f"ASPX-{year}")
                            except Exception as e:
                                logger.debug(f"Skipping malformed ASPX news item: {e}")
                                continue  # Skip malformed item, continue with next

                        print(f"[ASPX] Processed year {year}")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next
            except Exception as e:
                logger.debug(f"Skipping failed pattern: {e}")
                continue  # Skip failed pattern, try next

        # Streamlined news page patterns
        news_page_patterns = [
            f'{url}/news/',
            f'{url}/news/all/',  # Aston Bay
            f'{url}/news-releases/',
            f'{url}/press-releases/',
            # WordPress category patterns (New Age Metals, many WP sites)
            f'{url}/category/press/',
            f'{url}/category/news/',
            f'{url}/category/press-releases/',
            f'{url}/category/news-releases/',
            f'{url}/investors/news/',
            f'{url}/investors/news-releases/',  # Canada Nickel
            f'{url}/investor-relations/news-releases/',  # NEO Battery Materials
            f'{url}/investor-relations/press-releases/',  # IR press releases pattern
            f'{url}/news/press-releases/',
            f'{url}/news/{current_year}/',  # Garibaldi (year-based)
            f'{url}/news-{current_year}/',  # ATEX Resources (year-suffix pattern)
            f'{url}/news-{current_year - 1}/',  # ATEX Resources (previous year)
            # Year-based archive pages under news-releases (Aftermath Silver pattern)
            f'{url}/news-releases/{current_year}/',
            f'{url}/news-releases/{current_year - 1}/',
            # Northern Dynasty pattern: /news/news-releases/YYYY/
            f'{url}/news/news-releases/{current_year}/',
            f'{url}/news/news-releases/{current_year - 1}/',
            f'{url}/news/news-releases/{current_year - 2}/',
            f'{url}/news/news-releases/{current_year - 3}/',
            # GoGold Resources pattern: /investors/press-releases/YYYY/
            f'{url}/investors/press-releases/{current_year}/',
            f'{url}/investors/press-releases/{current_year - 1}/',
            # Also check year-based under press-releases
            f'{url}/press-releases/{current_year}/',
            f'{url}/press-releases/{current_year - 1}/',
            # Query parameter year filtering (Cassiar Gold pattern)
            f'{url}/news/?current_year={current_year}',
            f'{url}/news/?current_year={current_year - 1}',
            f'{url}/news?current_year={current_year}',
            f'{url}/news?current_year={current_year - 1}',
            # Northisle WordPress pattern: ?post_year= filtering
            f'{url}/news-releases?post_year={current_year}',
            f'{url}/news-releases?post_year={current_year - 1}',
            f'{url}/news-releases?post_year={current_year - 2}',
            f'{url}/news-releases?post_year={current_year - 3}',
            url,  # Homepage fallback for 55 North Mining style sites
        ]

        # Only add wp.* subdomain patterns for known domains that use this structure
        # This avoids DNS resolution failures for sites that don't have wp.* subdomains
        wp_subdomain_domains = ['angkorresources.com', 'angkorgold.ca']
        if any(wp_domain in domain for wp_domain in wp_subdomain_domains):
            news_page_patterns.extend([
                f'https://wp.{domain}/news-releases/',
                f'https://wp.{domain}/press-releases/',
            ])

        for news_url in news_page_patterns:
            # PRE-PATTERN TIME CHECK: Skip remaining patterns if we've exceeded time limits
            # This check runs BEFORE each URL fetch, so we don't waste time on slow URLs
            elapsed_so_far = (datetime.now() - scrape_start_time).total_seconds()
            if elapsed_so_far > 60 and len(news_by_url) > 0:
                print(f"[TIME-EXIT] {elapsed_so_far:.1f}s elapsed with {len(news_by_url)} items, skipping remaining patterns")
                break
            if elapsed_so_far > 90:
                print(f"[TIME-EXIT] {elapsed_so_far:.1f}s elapsed, skipping remaining patterns")
                break

            try:
                result = await crawler.arun(url=news_url, config=crawler_config)
                if not result.success:
                    continue

                soup = BeautifulSoup(result.html, 'html.parser')
                print(f"[SCAN] {news_url}")

                # ============================================================
                # STRATEGY 1: G2 Goldfields pattern - dates in <strong> tags
                # <strong>January 06, 2026</strong> followed by text and globenewswire link
                # ============================================================
                for strong in soup.find_all('strong'):
                    strong_text = strong.get_text(strip=True)
                    date_str = parse_date_standalone(strong_text)
                    if not date_str:
                        continue

                    # Look for the next p or text with the title and link
                    next_elem = strong.find_next(['p', 'div'])
                    if not next_elem:
                        continue

                    next_text = next_elem.get_text(strip=True)
                    link = next_elem.find('a', href=True)
                    if not link:
                        continue

                    href = link.get('href', '')
                    # Check for external news wire
                    if not any(nw in href.lower() for nw in ['globenewswire', 'newswire', 'prnewswire', 'businesswire']):
                        continue

                    # Extract title (text before "– Read More" or similar)
                    title = re.sub(r'\s*[-–—]\s*(Read\s*More|More|View).*$', '', next_text, flags=re.IGNORECASE).strip()

                    if len(title) < 15:
                        continue

                    news = {
                        'title': title,
                        'url': urljoin(news_url, href),
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    }
                    _add_news_item(news_by_url, news, cutoff_date, "G2")

                # ============================================================
                # STRATEGY 2: WordPress/document card news (Canada Nickel)
                # Uses: .wp-block-post-title h3 a, time or p.date
                # ============================================================
                for post in soup.select('.wp-block-post, li.wp-block-post, .document-card'):
                    try:
                        # Get title from h3 with link
                        title_elem = post.select_one('.wp-block-post-title a, .document-card-title a, h3 a')
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Get date from time element or p.date
                        date_str = None

                        # Try time element first
                        time_elem = post.select_one('time.wp-block-post-date, time')
                        if time_elem:
                            # Try datetime attribute first
                            if time_elem.get('datetime'):
                                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', time_elem['datetime'])
                                if date_match:
                                    date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                            # Fallback to text content
                            if not date_str:
                                date_str = parse_date_standalone(time_elem.get_text(strip=True))

                        # Try p.date element (Canada Nickel pattern)
                        if not date_str:
                            date_elem = post.select_one('p.date, .date, span.date')
                            if date_elem:
                                date_str = parse_date_standalone(date_elem.get_text(strip=True))

                        # Build full URL
                        if href and not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "WP-BLOCK")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY: Northisle WordPress theme pattern
                # Structure: <div class="news-releases__post">
                #   <div class="news-ttl"><span>Title</span><div class="date">January 21, 2026</div></div>
                #   <a href="..." class="btn-link">Read More</a>
                # </div>
                # ============================================================
                for post in soup.select('.news-releases__post'):
                    try:
                        # Get title from .news-ttl span
                        title_elem = post.select_one('.news-ttl span')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue

                        # Get date from .date
                        date_elem = post.select_one('.date')
                        date_str = None
                        if date_elem:
                            date_str = parse_date_standalone(date_elem.get_text(strip=True))

                        # Get link from a.btn-link
                        link = post.select_one('a.btn-link')
                        if not link:
                            continue
                        href = link.get('href', '')
                        if not href:
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
                        _add_news_item(news_by_url, news, cutoff_date, "NORTHISLE-WP")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY: DAT-ARTICAL pattern (Mayfair Gold)
                # Structure: <div class="dat-artical">
                #   <div class="date"><h3>December 18, 2025</h3></div>
                #   <div class="articals"><h3><a href="...">Title</a></h3></div>
                # </div>
                # ============================================================
                for artical in soup.select('.dat-artical, div.dat-artical'):
                    try:
                        # Get date from .date h3
                        date_elem = artical.select_one('.date h3, .date')
                        date_str = None
                        if date_elem:
                            date_str = parse_date_standalone(date_elem.get_text(strip=True))

                        # Get title and link from .articals h3 a
                        link = artical.select_one('.articals h3 a, .articals a, h3 a')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        href = link.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Build full URL
                        if href and not href.startswith('http'):
                            href = urljoin(news_url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "DAT-ARTICAL")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 3: Aston Bay pattern - date in stacked divs (Mon/DD/YYYY)
                # Structure: <div class="flex"><div class="uk-width-auto">date</div><div class="uk-width-expand">title</div></div>
                # ============================================================
                for flex_container in soup.select('div.flex.flex-wrap, div[class*="flex"][class*="items-center"]'):
                    try:
                        # Look for date box with stacked month/day/year
                        date_box = flex_container.select_one('div.uk-width-auto, div[class*="shadow"]')
                        if not date_box:
                            continue

                        # Extract month, day, year from separate divs
                        divs = date_box.find_all('div', recursive=True)
                        texts = [d.get_text(strip=True) for d in divs if d.get_text(strip=True)]

                        # Look for pattern: [Mon, DD, YYYY] in text list
                        month_str = day_str = year_str = None
                        for t in texts:
                            t_lower = t.lower()
                            if t_lower in MONTH_MAP:
                                month_str = MONTH_MAP[t_lower]
                            elif t.isdigit() and 1 <= int(t) <= 31 and not year_str:
                                day_str = t.zfill(2)
                            elif t.isdigit() and len(t) == 4 and t.startswith('20'):
                                year_str = t

                        if not (month_str and day_str and year_str):
                            continue

                        date_str = f"{year_str}-{month_str}-{day_str}"

                        # Find the title link in sibling expand div
                        title_div = flex_container.select_one('div.uk-width-expand, div.px-4')
                        if not title_div:
                            continue

                        title_link = title_div.find('a', href=True)
                        if not title_link:
                            continue

                        title = title_link.get_text(strip=True)
                        href = title_link.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Build full URL
                        if href and not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "ASTON")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4: Garibaldi uk-grid pattern - date/title in separate columns
                # Structure: <div uk-grid><div class="uk-width-1-5">DATE</div><div class="uk-width-expand">TITLE</div>...</div>
                # ============================================================
                for grid in soup.select('[uk-grid], .uk-grid'):
                    try:
                        # Look for date column (uk-width-1-5@s or similar)
                        date_col = grid.select_one('[class*="uk-width-1-5"], [class*="uk-width-auto"]')
                        if not date_col:
                            continue

                        date_text = date_col.get_text(strip=True)
                        date_str = parse_date_standalone(date_text)
                        if not date_str:
                            continue

                        # Look for title column (uk-width-expand@s)
                        title_col = grid.select_one('[class*="uk-width-expand"]')
                        if not title_col:
                            continue

                        title = title_col.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue

                        # Find the VIEW or PDF link
                        view_link = grid.select_one('a[href*="/news/"]')
                        pdf_link = grid.select_one('a[href*=".pdf"]')

                        href = None
                        if view_link:
                            href = view_link.get('href', '')
                        elif pdf_link:
                            href = pdf_link.get('href', '')

                        if not href:
                            continue

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "UK-GRID")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4b: Avino news-entry pattern
                # Structure: <div class="news-entry" uk-grid><div class="date">DATE</div><div class="title"><a>TITLE</a></div></div>
                # ============================================================
                for entry in soup.select('.news-entry'):
                    try:
                        # Look for date column
                        date_col = entry.select_one('.date, [class*="uk-width-1-5"]')
                        if not date_col:
                            continue

                        date_text = date_col.get_text(strip=True)
                        date_str = parse_date_standalone(date_text)
                        if not date_str:
                            continue

                        # Look for title column with link
                        title_col = entry.select_one('.title, [class*="uk-width-4-5"], [class*="uk-width-expand"]')
                        if not title_col:
                            continue

                        link = title_col.select_one('a')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        href = link.get('href', '')

                        if not title or not href:
                            continue

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "NEWS-ENTRY")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4c: Blue Lagoon news-archive-list pattern
                # Structure: <ul class="news-archive-list"><li><p class="date">DATE</p><p class="title">TITLE</p><p class="file"><a href="PDF">PDF</a></p></li></ul>
                # ============================================================
                for li in soup.select('ul.news-archive-list li'):
                    try:
                        # Get date from p.date
                        date_el = li.select_one('p.date')
                        if not date_el:
                            continue

                        date_text = date_el.get_text(strip=True)
                        date_str = parse_date_standalone(date_text)
                        if not date_str:
                            continue

                        # Get title from p.title
                        title_el = li.select_one('p.title')
                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        if not title:
                            continue

                        # Get PDF link from p.file a
                        file_el = li.select_one('p.file a')
                        if not file_el:
                            continue

                        href = file_el.get('href', '')
                        if not href:
                            continue

                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "NEWS-ARCHIVE-LIST")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4d: Ultimate Elements Grid pattern (CanAlaska)
                # Structure: <div class="uc_post_title"><a><div class="ue_p_title">TITLE</div></a></div>
                #            <div class="ue-meta-data"><div class="ue-grid-item-meta-data">DATE</div></div>
                # ============================================================
                # Find all title elements
                for title_div in soup.select('.uc_post_title'):
                    try:
                        # Get the link
                        link = title_div.select_one('a')
                        if not link:
                            continue

                        href = link.get('href', '')
                        if not href:
                            continue

                        # Get title from ue_p_title inside link
                        title_el = link.select_one('.ue_p_title') or link
                        title = title_el.get_text(strip=True)
                        if not title or len(title) < 10:
                            continue

                        # Find date - look in next siblings for ue-meta-data or ue-grid-item-meta-data
                        date_str = None
                        # Check siblings after title_div
                        for sibling in title_div.find_next_siblings():
                            date_el = sibling.select_one('.ue-grid-item-meta-data') if sibling.name else None
                            if not date_el and hasattr(sibling, 'get') and 'ue-grid-item-meta-data' in sibling.get('class', []):
                                date_el = sibling
                            if date_el:
                                date_text = date_el.get_text(strip=True)
                                date_str = parse_date_standalone(date_text)
                                break
                            # Stop if we hit another title
                            if sibling.select_one('.uc_post_title'):
                                break

                        # Also try parent container
                        if not date_str:
                            parent = title_div.find_parent(['div', 'article', 'li'])
                            for _ in range(5):
                                if parent is None:
                                    break
                                date_el = parent.select_one('.ue-grid-item-meta-data')
                                if date_el:
                                    date_text = date_el.get_text(strip=True)
                                    date_str = parse_date_standalone(date_text)
                                    break
                                parent = parent.find_parent(['div', 'article', 'li'])

                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "UE-GRID")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4e: Cassiar Gold pattern - news_item with h3 date
                # Structure: <div class="news_item"><h3>23 January 2026</h3><p><a href="...">Title</a></p></div>
                # ============================================================
                for news_item in soup.select('.news_item, .newsItem'):
                    try:
                        # Get date from h3
                        date_el = news_item.select_one('h3')
                        date_str = None
                        if date_el:
                            date_str = parse_date_standalone(date_el.get_text(strip=True))

                        # Get link and title from p > a
                        link = news_item.select_one('p a, a')
                        if not link:
                            continue

                        href = link.get('href', '')
                        title = link.get_text(strip=True)

                        if not href or not title or len(title) < 10:
                            continue

                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "NEWS-ITEM-H3")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4f: Cosa Resources pattern - div.news-link with date in parent
                # Structure: <div class="flex...">Jan 21, 2026<div class="news-link"><a href="...">Title</a></div></div>
                # ============================================================
                for news_link in soup.select('div.news-link, .news-link'):
                    try:
                        link = news_link.select_one('a')
                        if not link:
                            continue

                        href = link.get('href', '')
                        title = link.get_text(strip=True)

                        if not href or not title or len(title) < 10:
                            continue

                        # Skip if not a news release URL
                        if '/news' not in href.lower():
                            continue

                        # Get date from parent element's text
                        date_str = None
                        parent = news_link.parent
                        if parent:
                            parent_text = parent.get_text()
                            # Look for date pattern in parent text
                            date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', parent_text)
                            if date_match:
                                date_str = parse_date_standalone(date_match.group(0))

                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "NEWS-LINK")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4g: Globex Mining pattern - PDF press releases with embedded titles
                # Structure: Text contains "Month DD, YYYY<Title>View English PDF" where link says "View PDF"
                # The actual title is between the date and the generic PDF link text
                # ============================================================
                for pdf_link in soup.select('a[href*=".pdf"]'):
                    try:
                        href = pdf_link.get('href', '')
                        link_text = pdf_link.get_text(strip=True).lower()

                        # Only process generic PDF link text (not actual titles)
                        if not any(x in link_text for x in ['view', 'pdf', 'download', 'english', 'french']):
                            continue

                        # Skip if already found this URL
                        if href in news_by_url:
                            continue

                        # Get parent element that contains both date and title
                        parent = pdf_link.find_parent()
                        while parent and parent.name not in ['tr', 'div', 'li', 'article', 'p', 'td']:
                            parent = parent.find_parent()

                        if not parent:
                            continue

                        parent_text = parent.get_text(strip=True)

                        # Extract date and title using regex
                        # Pattern: MonthName DD, YYYY followed by title text followed by View/Share
                        match = re.match(
                            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})\s*(.+?)(?:View|Share|Download|PDF|English|French)',
                            parent_text, re.IGNORECASE
                        )

                        if not match:
                            continue

                        month_name, day, year, title = match.groups()
                        title = title.strip()

                        # Skip if title is too short or looks like a generic label
                        if len(title) < 15:
                            continue

                        # Build date string
                        month = MONTH_MAP.get(month_name.lower(), '01')
                        date_str = f"{year}-{month}-{day.zfill(2)}"

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': year
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "PDF-EMBEDDED-TITLE")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 4h: GoGold Resources pattern - div.file with p and span
                # Structure: <div class="file"><p>Title<br/><span>Date</span></p><a href="PDF">Download</a></div>
                # ============================================================
                for file_div in soup.select('div.file'):
                    try:
                        # Find the paragraph with title and date
                        p_elem = file_div.select_one('p')
                        if not p_elem:
                            continue

                        # Extract date from span inside p
                        date_span = p_elem.select_one('span')
                        date_str = None
                        if date_span:
                            date_str = parse_date_standalone(date_span.get_text(strip=True))

                        # Extract title - it's the text before the span/br
                        # Get all text and remove the date part
                        full_text = p_elem.get_text(separator=' ', strip=True)
                        title = full_text
                        if date_span:
                            date_text = date_span.get_text(strip=True)
                            title = full_text.replace(date_text, '').strip()

                        if not title or len(title) < 15:
                            continue

                        # Find PDF link
                        link = file_div.select_one('a[href*=".pdf"], a.btn')
                        if not link:
                            continue

                        href = link.get('href', '')
                        if not href:
                            continue

                        if not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "FILE-DIV")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5a: 55 North Mining - Homepage PDF news pattern
                # News links to PDFs with date in span, title as text
                # ============================================================
                for news_div in soup.select('div.news'):
                    try:
                        # Find PDF link
                        link = news_div.select_one('a[href$=".pdf"], a[href*=".pdf"]')
                        if not link:
                            for a in news_div.select('a'):
                                if '.pdf' in a.get('href', '').lower():
                                    link = a
                                    break
                        if not link:
                            continue

                        href = link.get('href', '')
                        if not href:
                            continue

                        if not href.startswith('http'):
                            href = urljoin(news_url, href)

                        # Extract date from span inside link
                        date_str = None
                        date_span = link.select_one('span')
                        if date_span:
                            date_text = date_span.get_text(strip=True).lstrip('\xa0').strip()
                            date_str = parse_date_standalone(date_text)

                        # Extract title
                        full_text = link.get_text(separator=' ', strip=True)
                        title = full_text
                        if date_span:
                            date_text = date_span.get_text(strip=True)
                            title = full_text.replace(date_text, '').strip()
                        title = re.sub(r'^\s*[\-–—]\s*', '', title).strip()

                        if not title or len(title) < 15:
                            continue

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "PDF-NEWS")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b-NEW: WP Posts Pro plugin (Centurion Minerals pattern)
                # Uses: div.wpp_section with span[itemprop="datePublished"] and b[itemprop="name"] a
                # ============================================================
                for wpp_section in soup.select('div.wpp_section, .wpp_group'):
                    try:
                        # Get date from span with itemprop="datePublished"
                        date_elem = wpp_section.select_one('span[itemprop="datePublished"]')
                        if not date_elem:
                            continue

                        date_str = parse_date_standalone(date_elem.get_text(strip=True))
                        if not date_str:
                            continue

                        # Get title from b[itemprop="name"] a or just find the link
                        title_link = wpp_section.select_one('b[itemprop="name"] a, b a, a[href]')
                        if not title_link:
                            continue

                        title = title_link.get_text(strip=True)
                        href = title_link.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Build full URL
                        if href and not href.startswith('http'):
                            href = urljoin(news_url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "WPP")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b-POWERPACK: PowerPack Posts Grid with schema.org metadata
                # (GR Silver Mining pattern)
                # Structure: div.pp-content-post with meta[itemprop="mainEntityOfPage"] for title
                # and meta[itemprop="datePublished"] for date in YYYY-MM-DD format
                # ============================================================
                for post in soup.select('div.pp-content-post'):
                    try:
                        # Get title from meta tag
                        title_meta = post.select_one('meta[itemprop="mainEntityOfPage"]')
                        if not title_meta:
                            continue
                        title = title_meta.get('content', '')

                        # Get date from meta tag (YYYY-MM-DD format)
                        date_meta = post.select_one('meta[itemprop="datePublished"]')
                        if not date_meta:
                            continue
                        date_str = date_meta.get('content', '')

                        if not title or not date_str or len(title) < 15:
                            continue

                        # Validate date format
                        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                            continue

                        # Get post URL if available
                        link = post.select_one('a[href]')
                        href = link.get('href', '') if link else news_url

                        if href and not href.startswith('http'):
                            href = urljoin(url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "POWERPACK")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b-ELEMENTOR: Elementor Loop pattern
                # Handles multiple layouts:
                # - LaFleur: h1.elementor-heading-title + time element + a.elementor-button
                # - Argenta Silver: Wrapped <a> with h2 for date + h2 for title
                # ============================================================
                for loop_item in soup.select('.e-loop-item, [data-elementor-type="loop-item"]'):
                    try:
                        title = None
                        date_str = None
                        href = None

                        # Check if the whole item is wrapped in an <a> tag (Argenta pattern)
                        # Look for a.e-con link or direct child <a> tag
                        wrapper_link = loop_item.select_one('a.e-con[href]')
                        if not wrapper_link:
                            # Check for direct child <a> that wraps content
                            for child in loop_item.children:
                                if hasattr(child, 'name') and child.name == 'a' and child.get('href'):
                                    wrapper_link = child
                                    break
                        if wrapper_link:
                            href = wrapper_link.get('href', '')

                        # Get all headings - some sites use h1, some use h2
                        headings = loop_item.select('h1.elementor-heading-title, h2.elementor-heading-title, .elementor-heading-title')

                        if len(headings) >= 2:
                            # Multiple headings: first is usually date, second is title (Argenta pattern)
                            first_text = headings[0].get_text(strip=True)
                            second_text = headings[1].get_text(strip=True)

                            # Try to parse date from first heading
                            parsed_date = parse_date_standalone(first_text)
                            if parsed_date:
                                date_str = parsed_date
                                title = second_text
                            else:
                                # First heading is title, try date from second
                                parsed_date = parse_date_standalone(second_text)
                                if parsed_date:
                                    date_str = parsed_date
                                    title = first_text
                                else:
                                    # Neither is a pure date, use first as title
                                    title = first_text
                        elif len(headings) == 1:
                            # Single heading - title might have embedded date
                            title = headings[0].get_text(strip=True)

                        if not title or len(title) < 10:
                            continue

                        # Extract date from time element if not found in headings
                        if not date_str:
                            time_elem = loop_item.select_one('li[itemprop="datePublished"] time, time')
                            if time_elem:
                                datetime_attr = time_elem.get('datetime', '')
                                if datetime_attr:
                                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_attr)
                                    if date_match:
                                        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                                if not date_str:
                                    date_str = parse_date_standalone(time_elem.get_text(strip=True))

                        # Extract URL if not from wrapper link
                        if not href:
                            for button in loop_item.select('a.elementor-button[href]'):
                                btn_href = button.get('href', '')
                                if btn_href.startswith('#') or 'action' in btn_href.lower():
                                    continue
                                if btn_href.startswith('http') or btn_href.startswith('/'):
                                    href = btn_href
                                    break

                        # Fallback to date link
                        if not href:
                            date_link = loop_item.select_one('li[itemprop="datePublished"] a[href]')
                            if date_link:
                                href = date_link.get('href', '')

                        # Last resort - any link in the item
                        if not href:
                            any_link = loop_item.select_one('a[href]')
                            if any_link:
                                link_href = any_link.get('href', '')
                                if not link_href.startswith('#'):
                                    href = link_href

                        if not href:
                            continue

                        # Build full URL
                        if href and not href.startswith('http'):
                            href = urljoin(news_url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "ELEMENTOR")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b-NEWSCARD: Liberty Gold news-card pattern
                # Structure: <a class="news-card" href="URL">
                #   <div>...<p class="elementor-heading-title">DATE</p>...</div>
                #   <div>...<h2 class="elementor-heading-title">TITLE</h2>...</div>
                # </a>
                # ============================================================
                for news_card in soup.select('a.news-card[href]'):
                    try:
                        href = news_card.get('href', '')
                        if not href or href.startswith('#'):
                            continue

                        # Find all heading elements inside
                        headings = news_card.select('.elementor-heading-title')
                        if len(headings) < 2:
                            continue

                        # First heading is typically date, second is title
                        date_text = headings[0].get_text(strip=True)
                        title = headings[1].get_text(strip=True)

                        # Parse date
                        date_str = parse_date_standalone(date_text)

                        # If first wasn't date, try swapping
                        if not date_str and len(headings) >= 2:
                            date_str = parse_date_standalone(title)
                            if date_str:
                                title = date_text

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
                        _add_news_item(news_by_url, news, cutoff_date, "NEWSCARD")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b-UIKIT: Scottie Resources UIKit Grid pattern
                # Uses uk-grid with date in first column, title in second, links in third
                # Structure: div[uk-grid] > div.uk-width-1-4@s (date) + div.uk-width-expand@s (title) + div (VIEW/PDF links)
                # ============================================================
                for grid in soup.select('[uk-grid], .uk-grid'):
                    try:
                        # Look for the three-column structure
                        columns = grid.find_all('div', recursive=False)
                        if len(columns) < 2:
                            continue

                        # First column should contain a date
                        date_col = columns[0]
                        date_text = date_col.get_text(strip=True)
                        date_str = parse_date_standalone(date_text)
                        if not date_str:
                            continue

                        # Second column should contain the title
                        title_col = columns[1] if len(columns) > 1 else None
                        if not title_col:
                            continue
                        title = title_col.get_text(strip=True)
                        if not title or len(title) < 15:
                            continue

                        # Skip non-news items (navigation elements, not geological terms)
                        title_lower = title.lower()
                        if any(skip == title_lower or title_lower.startswith(skip + ' ') or ' ' + skip + ' ' not in title_lower and title_lower.endswith(' ' + skip)
                               for skip in ['subscribe', 'menu', 'home']):
                            continue
                        # "contact" as standalone nav item but not geological "contact zone"
                        if title_lower in ['contact', 'contact us'] or title_lower.startswith('contact us'):
                            continue

                        # Find VIEW link in any column (usually the third)
                        href = None
                        for col in columns:
                            view_link = col.find('a', href=True, string=re.compile(r'view', re.I))
                            if view_link:
                                href = view_link.get('href', '')
                                break
                            # Also try any link that's not PDF
                            for link in col.find_all('a', href=True):
                                link_href = link.get('href', '')
                                link_text = link.get_text(strip=True).lower()
                                if link_text != 'pdf' and '.pdf' not in link_href.lower():
                                    if '/news/' in link_href or '/press' in link_href:
                                        href = link_href
                                        break

                        if not href:
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
                        _add_news_item(news_by_url, news, cutoff_date, "UIKIT")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5b: ATEX Resources - Article with time element
                # Uses <article> tags with <time datetime="..."> elements
                # ============================================================
                for article in soup.select('article.post-format-standard, article.post'):
                    try:
                        # Get link from post-content div
                        content_div = article.select_one('.post-content, .entry-content, .article-content')
                        if not content_div:
                            content_div = article

                        link = content_div.select_one('a[href]')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        href = link.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Skip media/video content
                        if any(skip in href.lower() for skip in ['/media/', 'youtube.com', 'vimeo.com']):
                            continue

                        # Get date from time element
                        date_str = None
                        time_elem = article.select_one('time[datetime]')
                        if time_elem:
                            datetime_attr = time_elem.get('datetime', '')
                            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_attr)
                            if date_match:
                                date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

                        # Fallback to time element text
                        if not date_str and time_elem:
                            date_str = parse_date_standalone(time_elem.get_text(strip=True))

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(news_url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "ARTICLE")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5c: WordPress archive lists (Angkor WP subdomain)
                # Standard WP article/entry list with h2.entry-title
                # ============================================================
                for entry in soup.select('article.post, article.hentry, article.type-post'):
                    try:
                        # Get title link
                        title_elem = entry.select_one('h2.entry-title a, h2 a, .entry-title a, h3 a')
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')

                        if not title or len(title) < 15:
                            continue

                        # Get date
                        date_str = None

                        # Try time element
                        time_elem = entry.select_one('time.entry-date, time, .posted-on time')
                        if time_elem:
                            datetime_attr = time_elem.get('datetime', '')
                            if datetime_attr:
                                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_attr)
                                if date_match:
                                    date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                            if not date_str:
                                date_str = parse_date_standalone(time_elem.get_text(strip=True))

                        # Try date class elements
                        if not date_str:
                            date_elem = entry.select_one('.entry-date, .post-date, .date, .posted-on, span.published, .post-meta span')
                            if date_elem:
                                date_str = parse_date_standalone(date_elem.get_text(strip=True))

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(news_url, href)

                        news = {
                            'title': clean_news_title(title, href),
                            'url': urljoin(news_url, href),
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        }
                        _add_news_item(news_by_url, news, cutoff_date, "WP-ENTRY")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5c-GRID: News section grid layout (New Pacific Metals pattern)
                # Structure: <div class="row news-section">
                #   <div class="col-lg-2">Dec 4, 2025</div>
                #   <div class="col-lg-7"><a href="...">Title</a></div>
                # </div>
                # ============================================================
                news_grid_rows = soup.select('.news-section, .news-row')
                if '/news' in news_url and news_grid_rows:
                    print(f"[NEWS-GRID-DEBUG] Found {len(news_grid_rows)} news-section rows on {news_url}")
                for news_row in news_grid_rows:
                    try:
                        # Find all column divs
                        cols = news_row.select('div[class*="col-"]')
                        if len(cols) < 2:
                            continue

                        # First column typically has date
                        date_str = None
                        date_col = cols[0]
                        date_text = date_col.get_text(strip=True)
                        if date_text:
                            date_str = parse_date_standalone(date_text)

                        # Second or third column has the link/title
                        title = None
                        href = None
                        for col in cols[1:]:
                            link = col.select_one('a[href]')
                            if link:
                                title = link.get_text(strip=True)
                                href = link.get('href', '')
                                break

                        if not title or not href or len(title) < 15:
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
                        _add_news_item(news_by_url, news, cutoff_date, "NEWS-GRID")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5d: Freegold Ventures - a.latest with h3 date
                # Links with "latest" class containing h3 date (Mon DD format)
                # <a class="latest" href="..."><h3>Jan 15</h3>Title</a>
                # ============================================================
                for latest_link in soup.select('a.latest[href]'):
                    try:
                        href = latest_link.get('href', '')
                        if not href:
                            continue

                        # Get date from h3 element inside
                        date_str = None
                        h3_elem = latest_link.select_one('h3')
                        if h3_elem:
                            date_str = parse_date_standalone(h3_elem.get_text(strip=True))

                        # Get title - text content excluding the h3
                        # Clone the element and remove h3 to get remaining text
                        title_parts = []
                        for child in latest_link.children:
                            if hasattr(child, 'name') and child.name == 'h3':
                                continue
                            text = child.get_text(strip=True) if hasattr(child, 'get_text') else str(child).strip()
                            if text:
                                title_parts.append(text)
                        title = ' '.join(title_parts)

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
                        _add_news_item(news_by_url, news, cutoff_date, "LATEST")
                    except Exception as e:
                        logger.debug(f"Skipping malformed news item: {e}")
                        continue  # Skip malformed item, continue with next

                # ============================================================
                # STRATEGY 5: Structured news-item elements with date/title divs
                # Handles: Laurion (.news-item .date), 1911 Gold, etc.
                # ============================================================
                for selector in ['.news-item', '.news_item', '.press-release', '.news-release', 'article.post', 'article']:
                    for item in soup.select(selector)[:50]:
                        news = _extract_news_from_element(item, news_url, url)
                        if news:
                            _add_news_item(news_by_url, news, cutoff_date, "ITEM")

                # ============================================================
                # STRATEGY 3: All links - catch external news services and internal
                # ============================================================
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if not text or len(text) < 15 or len(text) > 300:
                        continue

                    # Build full URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(url, href)

                    # Check if it's a news article URL (internal or external)
                    if not is_news_article_url(full_url):
                        continue

                    # Extract date and clean title using comprehensive parser
                    date_str, cleaned_title = parse_date_comprehensive(text)

                    # If no date in link text, check parent element
                    if not date_str:
                        parent = link.find_parent(['div', 'li', 'article', 'tr', 'td', 'p'])
                        if parent:
                            # Look for itemprop="datePublished" (WP Posts Pro pattern)
                            date_elem = parent.find(['span', 'time'], attrs={'itemprop': 'datePublished'})
                            if date_elem:
                                date_str = parse_date_standalone(date_elem.get_text(strip=True))
                            # Look for dedicated date element by class
                            if not date_str:
                                date_elem = parent.find(['div', 'span', 'time'], class_=lambda c: c and 'date' in str(c).lower())
                                if date_elem:
                                    date_str = parse_date_standalone(date_elem.get_text(strip=True))
                            # Fallback to parsing parent text
                            if not date_str:
                                date_str, _ = parse_date_comprehensive(parent.get_text(strip=True))

                    # Use cleaned title or original
                    title = cleaned_title if cleaned_title and len(cleaned_title) > 15 else text
                    title = clean_news_title(title, full_url)

                    if not is_valid_news_title(title):
                        continue

                    news = {
                        'title': title,
                        'url': full_url,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    }
                    _add_news_item(news_by_url, news, cutoff_date, "LINK")

                # ============================================================
                # STRATEGY 4: Elementor-based news layouts
                # ============================================================
                elementor_headings = soup.find_all(['h2', 'h3'], class_=re.compile(r'elementor-heading-title'))
                for heading in elementor_headings[:50]:
                    heading_link = heading.find('a', href=True)
                    if not heading_link:
                        continue

                    title = heading_link.get_text(strip=True)
                    href = heading_link.get('href', '')

                    if not title or len(title) < 15 or re.match(r'^\d{4}$', title):
                        continue

                    if any(p in title.lower() for p in ['skip to content', 'menu', 'contact', 'home', 'about', 'subscribe']):
                        continue

                    full_url = urljoin(url, href) if not href.startswith('http') else href

                    # Extract date using comprehensive parser
                    date_str, cleaned_title = parse_date_comprehensive(title)

                    # Look for date in nearby elements
                    if not date_str:
                        search_container = heading
                        for _ in range(5):
                            if search_container.parent:
                                search_container = search_container.parent
                            else:
                                break

                        date_elements = search_container.find_all(['span', 'h3', 'p', 'div'],
                            class_=re.compile(r'icon-box-title|date|time', re.I))
                        for elem in date_elements:
                            date_str = parse_date_standalone(elem.get_text(strip=True))
                            if date_str:
                                break

                    # Clean and validate
                    title = clean_news_title(cleaned_title if cleaned_title else title, full_url)
                    if not is_valid_news_title(title):
                        continue

                    news = {
                        'title': title,
                        'url': full_url,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    }
                    _add_news_item(news_by_url, news, cutoff_date, "ELEMENTOR")

                # ============================================================
                # EARLY EXIT CHECKS - prevent scrapes from running 2+ hours
                # ============================================================

                # EARLY EXIT 1: For daily scraping, stop if we found enough recent news
                # This dramatically speeds up the scrape by skipping unnecessary URL patterns
                if months <= 6:  # Only for short-term scraping (daily scrape uses months=3)
                    recent_count = sum(1 for n in news_by_url.values()
                                      if n.get('date') and
                                      datetime.strptime(n['date'], '%Y-%m-%d') > datetime.now() - timedelta(days=30))
                    if recent_count >= 3:
                        print(f"[EARLY-EXIT] Found {recent_count} recent news items, stopping URL pattern search")
                        break

                # EARLY EXIT 2: Time-based limits to prevent long-running scrapes
                elapsed_seconds = (datetime.now() - scrape_start_time).total_seconds()
                # If we found news, exit after 60 seconds (we have data, stop searching)
                if elapsed_seconds > 60 and len(news_by_url) > 0:
                    print(f"[TIME-EXIT] Scrape running for {elapsed_seconds:.1f}s with {len(news_by_url)} items, stopping early")
                    break
                # If no news found after 90 seconds, give up (probably won't find anything)
                if elapsed_seconds > 90 and len(news_by_url) == 0:
                    print(f"[TIME-EXIT] Scrape running for {elapsed_seconds:.1f}s with no news found, giving up")
                    break

            except Exception as e:
                # Silently continue if this news URL doesn't exist
                continue

    # Secondary deduplication by title+date (same news can appear on multiple pages with different URLs)
    # Prefer items with article-like URLs over archive/listing page URLs
    seen_titles = {}  # Map "title|date" -> news item
    for news in news_by_url.values():
        title_key = f"{news['title'].lower().strip()}|{news.get('date', '')}"

        if title_key not in seen_titles:
            seen_titles[title_key] = news
        else:
            # If we already have this title+date, keep the one with a more specific URL
            # (longer URL path usually means it's the actual article, not an archive page)
            existing_url = seen_titles[title_key]['url']
            new_url = news['url']

            # Prefer URLs that look like article pages (longer, more specific paths)
            # Avoid archive pages like /news/, /news/2026/, etc.
            existing_is_archive = existing_url.rstrip('/').endswith(('/news', '/press', '/media')) or \
                                  re.search(r'/news/\d{4}/?$', existing_url) or \
                                  re.search(r'/\d{4}/?$', existing_url)
            new_is_archive = new_url.rstrip('/').endswith(('/news', '/press', '/media')) or \
                             re.search(r'/news/\d{4}/?$', new_url) or \
                             re.search(r'/\d{4}/?$', new_url)

            # Prefer non-archive URL over archive URL
            if existing_is_archive and not new_is_archive:
                seen_titles[title_key] = news
            elif not existing_is_archive and not new_is_archive:
                # Both are article URLs - keep the longer one (more specific)
                if len(new_url) > len(existing_url):
                    seen_titles[title_key] = news

    deduped_news = list(seen_titles.values())
    if len(deduped_news) < len(news_by_url):
        print(f"[DEDUP] Removed {len(news_by_url) - len(deduped_news)} duplicate news items by title+date")

    # Tertiary deduplication by URL slug (catch same news with different URL paths)
    # e.g., /news/20260112-article vs /news/2026/20260112-article vs /press-releases/20260112-article
    seen_slugs_final = {}  # Map slug -> news item
    for news in deduped_news:
        slug = _extract_url_slug(news['url'])
        if slug and len(slug) > 10:  # Only for meaningful slugs
            if slug not in seen_slugs_final:
                seen_slugs_final[slug] = news
            else:
                # Keep the one with the simpler/shorter URL path (usually the canonical one)
                existing_url = seen_slugs_final[slug]['url']
                new_url = news['url']
                # Prefer URLs with fewer path segments
                existing_depth = existing_url.count('/')
                new_depth = new_url.count('/')
                if new_depth < existing_depth:
                    seen_slugs_final[slug] = news
        else:
            # Short slugs (like 'news', '2026') - keep all, use URL as key
            seen_slugs_final[news['url']] = news

    final_news = list(seen_slugs_final.values())
    if len(final_news) < len(deduped_news):
        print(f"[DEDUP] Removed {len(deduped_news) - len(final_news)} duplicate news items by URL slug")

    return final_news
