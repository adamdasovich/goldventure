"""
Website Crawler for Mining Company Documents
Uses Crawl4AI to discover PDFs and technical reports on company websites

Updated: Comprehensive date parsing, external news wire support, title cleaning
"""

import asyncio
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional, Tuple
import re
import sys
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup

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

    # Pattern 1: MM.DD.YYYY or MM.DD.YY (Laurion style: 01.07.2026 or 12.22.25)
    match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(20\d{2}|\d{2})\s*[-–]?\s*(.*)$', text)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year = match.group(3)
        if len(year) == 2:
            year = f"20{year}" if int(year) <= 50 else f"19{year}"
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            date_str = f"{year}-{month}-{day}"
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

    # Pattern 4: MM/DD/YY at start (01/06/26)
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})\s+(.*)$', text)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year_short = match.group(3)
        year = f"20{year_short}" if int(year_short) <= 50 else f"19{year_short}"
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            date_str = f"{year}-{month}-{day}"
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

    # Pattern 9: MM/DD/YYYY anywhere
    match = re.search(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year = match.group(3)
        if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
            date_str = f"{year}-{month}-{day}"
            return date_str, original_text

    return None, original_text


def parse_date_standalone(text: str) -> Optional[str]:
    """Parse date from a string that contains ONLY a date (for dedicated date elements)."""
    if not text:
        return None
    text = text.strip()

    # MM.DD.YYYY (Laurion: 01.07.2026)
    match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(20\d{2}|\d{2})$', text)
    if match:
        month, day, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

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

    # MM/DD/YYYY
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(20\d{2})$', text)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

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
    """Check if a URL looks like a news article (internal or external)."""
    if not url:
        return False
    url_lower = url.lower()

    # Skip base news listing pages
    if url_lower.rstrip('/').endswith(('/news', '/press-releases', '/news-releases', '/media')):
        return False
    if re.search(r'/news/\d{4}$', url_lower):
        return False

    # Internal news patterns
    internal = ['/news/', '/press-release', '/news-release', '/nr-', '/nr_', '/announcement']
    if any(p in url_lower for p in internal):
        return True

    # External news wire services
    external = [
        'globenewswire.com', 'newswire.ca', 'prnewswire.com',
        'businesswire.com', 'accesswire.com', 'newsfilecorp.com',
        'cision.com', 'marketwatch.com/press-release'
    ]
    if any(p in url_lower for p in external):
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


async def crawl_company_website(url: str, max_depth: int = 2) -> List[Dict]:
    """
    Convenience function to crawl a company website
    Returns list of discovered documents
    """
    crawler = MiningDocumentCrawler()
    documents = await crawler.discover_documents(
        start_url=url,
        max_depth=max_depth,
        max_pages=50
    )
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

    # Deduplicate by URL
    seen_urls = set()
    unique_news = []
    for news in html_news:
        url_normalized = news['url'].split('?')[0].rstrip('/')
        if url_normalized not in seen_urls:
            seen_urls.add(url_normalized)
            unique_news.append(news)

    # Sort: items with dates first (newest first), then items without dates
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

        # Strategy 2: Look for dedicated title element (div.title a, a.title, h2, h3)
        title_elem = element.find('div', class_='title')
        if title_elem:
            title_link = title_elem.find('a', href=True)
            if title_link:
                title = title_link.get_text(strip=True)
                link_url = title_link.get('href', '')

        # Try a.title directly
        if not title:
            title_link = element.find('a', class_='title')
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

        # Build full URL
        if link_url and not link_url.startswith('http'):
            link_url = urljoin(base_url, link_url)

        return {
            'title': title,
            'url': link_url or source_url,
            'date': date_str,
            'document_type': 'news_release',
            'year': date_str[:4] if date_str else None
        }
    except Exception:
        return None


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
    news_releases = []
    seen_urls = set()
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    crawler_config = CrawlerRunConfig(
        cache_mode="bypass",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        current_year = datetime.now().year

        # Normalize URL - remove trailing slashes to avoid double slashes
        url = url.rstrip('/')

        # Extract domain for WordPress subdomain check (Angkor pattern)
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')

        # Streamlined news page patterns
        news_page_patterns = [
            f'{url}/news/',
            f'{url}/news/all/',  # Aston Bay
            f'{url}/news-releases/',
            f'{url}/press-releases/',
            f'{url}/investors/news/',
            f'{url}/investors/news-releases/',  # Canada Nickel
            f'{url}/news/press-releases/',
            f'{url}/news/{current_year}/',  # Garibaldi (year-based)
            f'{url}/news-{current_year}/',  # ATEX Resources (year-suffix pattern)
            f'{url}/news-{current_year - 1}/',  # ATEX Resources (previous year)
            f'https://wp.{domain}/news-releases/',  # Angkor Resources (WP subdomain)
            f'https://wp.{domain}/press-releases/',  # Angkor Resources (WP subdomain)
            url,  # Homepage fallback for 55 North Mining style sites
        ]

        for news_url in news_page_patterns:
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

                    url_normalized = href.split('?')[0].rstrip('/')
                    if url_normalized in seen_urls:
                        continue

                    # Check date range
                    try:
                        if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                            continue
                    except:
                        pass

                    seen_urls.add(url_normalized)
                    news_releases.append({
                        'title': title,
                        'url': href,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    })
                    print(f"[G2] {title[:50]}... | {date_str}")

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

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            continue

                        # Check date range
                        if date_str:
                            try:
                                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                    continue
                            except:
                                pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        })
                        print(f"[WP-BLOCK] {title[:50]}... | {date_str or 'no date'}")
                    except Exception:
                        continue

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

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            continue

                        # Check date range
                        try:
                            if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                continue
                        except:
                            pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': year_str
                        })
                        print(f"[ASTON] {title[:50]}... | {date_str}")
                    except Exception:
                        continue

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

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            continue

                        # Check date range
                        try:
                            if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                continue
                        except:
                            pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        })
                        print(f"[UK-GRID] {title[:50]}... | {date_str}")
                    except Exception:
                        continue

                # ============================================================
                # STRATEGY 5a: 55 North Mining - Homepage PDF news pattern
                # News links to PDFs with date in span, title as text
                # ============================================================
                pdf_divs = soup.select('div.news')
                if pdf_divs:
                    print(f"[DEBUG-PDF] Found {len(pdf_divs)} div.news elements on {news_url}")
                for news_div in pdf_divs:
                    try:
                        # Find PDF link - try multiple approaches
                        link = news_div.select_one('a[href$=".pdf"]')  # ends with .pdf
                        if not link:
                            link = news_div.select_one('a[href*=".pdf"]')  # contains .pdf
                        if not link:
                            # Fallback: any link with pdf in href
                            for a in news_div.select('a'):
                                if '.pdf' in a.get('href', '').lower():
                                    link = a
                                    break
                        if not link:
                            continue

                        href = link.get('href', '')
                        if not href:
                            continue

                        # Build full URL for PDF
                        if not href.startswith('http'):
                            href = urljoin(news_url, href)

                        # Extract date from span inside link
                        date_str = None
                        date_span = link.select_one('span')
                        if date_span:
                            date_text = date_span.get_text(strip=True).lstrip('\xa0').strip()
                            date_str = parse_date_standalone(date_text)

                        # Extract title - get text after the icon/date
                        full_text = link.get_text(separator=' ', strip=True)
                        # Remove date portion and clean up
                        title = full_text
                        if date_span:
                            date_text = date_span.get_text(strip=True)
                            title = full_text.replace(date_text, '').strip()

                        # Clean up title
                        title = re.sub(r'^\s*[\-–—]\s*', '', title).strip()

                        if not title or len(title) < 15:
                            print(f"[DEBUG-PDF] Title too short: {len(title) if title else 0}")
                            continue

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            print(f"[DEBUG-PDF] Already seen: {url_normalized}")
                            continue

                        # Check date range
                        if date_str:
                            try:
                                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                    print(f"[DEBUG-PDF] Date too old: {date_str}")
                                    continue
                            except:
                                pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        })
                        print(f"[PDF-NEWS] {title[:50]}... | {date_str or 'no date'}")
                    except Exception as e:
                        print(f"[DEBUG-PDF] Exception: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

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

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            continue

                        # Check date range
                        if date_str:
                            try:
                                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                    continue
                            except:
                                pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        })
                        print(f"[ARTICLE] {title[:50]}... | {date_str or 'no date'}")
                    except Exception:
                        continue

                # ============================================================
                # STRATEGY 5c: WordPress archive lists (Angkor WP subdomain)
                # Standard WP article/entry list with h2.entry-title
                # ============================================================
                for entry in soup.select('article.post, .post, .hentry, .type-post'):
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
                            date_elem = entry.select_one('.entry-date, .post-date, .date, .posted-on')
                            if date_elem:
                                date_str = parse_date_standalone(date_elem.get_text(strip=True))

                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(news_url, href)

                        url_normalized = href.split('?')[0].rstrip('/')
                        if url_normalized in seen_urls:
                            continue

                        # Check date range
                        if date_str:
                            try:
                                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                    continue
                            except:
                                pass

                        seen_urls.add(url_normalized)
                        news_releases.append({
                            'title': clean_news_title(title, href),
                            'url': href,
                            'date': date_str,
                            'document_type': 'news_release',
                            'year': date_str[:4] if date_str else None
                        })
                        print(f"[WP-ENTRY] {title[:50]}... | {date_str or 'no date'}")
                    except Exception:
                        continue

                # ============================================================
                # STRATEGY 5: Structured news-item elements with date/title divs
                # Handles: Laurion (.news-item .date), 1911 Gold, etc.
                # ============================================================
                for selector in ['.news-item', '.press-release', '.news-release', 'article.post', 'article']:
                    for item in soup.select(selector)[:50]:
                        news = _extract_news_from_element(item, news_url, url)
                        if news:
                            url_normalized = news['url'].split('?')[0].rstrip('/')
                            if url_normalized not in seen_urls:
                                # Check date range
                                if news.get('date'):
                                    try:
                                        if datetime.strptime(news['date'], '%Y-%m-%d') < cutoff_date:
                                            continue
                                    except:
                                        pass
                                seen_urls.add(url_normalized)
                                news_releases.append(news)
                                print(f"[ITEM] {news['title'][:50]}... | {news.get('date', 'no date')}")

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

                    url_normalized = full_url.split('?')[0].rstrip('/')
                    if url_normalized in seen_urls:
                        continue

                    # Check if it's a news article URL (internal or external)
                    if not is_news_article_url(full_url):
                        continue

                    # Extract date and clean title using comprehensive parser
                    date_str, cleaned_title = parse_date_comprehensive(text)

                    # If no date in link text, check parent element
                    if not date_str:
                        parent = link.find_parent(['div', 'li', 'article', 'tr', 'td', 'p'])
                        if parent:
                            # Look for dedicated date element first
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

                    # Check date range
                    if date_str:
                        try:
                            if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                continue
                        except:
                            pass

                    seen_urls.add(url_normalized)
                    news_releases.append({
                        'title': title,
                        'url': full_url,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    })
                    print(f"[LINK] {title[:50]}... | {date_str or 'no date'}")

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
                    url_normalized = full_url.split('?')[0].rstrip('/')

                    if url_normalized in seen_urls:
                        continue

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

                    # Check date range
                    if date_str:
                        try:
                            if datetime.strptime(date_str, '%Y-%m-%d') < cutoff_date:
                                continue
                        except:
                            pass

                    # Clean and validate
                    title = clean_news_title(cleaned_title if cleaned_title else title, full_url)
                    if not is_valid_news_title(title):
                        continue

                    seen_urls.add(url_normalized)
                    news_releases.append({
                        'title': title,
                        'url': full_url,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': date_str[:4] if date_str else None
                    })
                    print(f"[ELEMENTOR] {title[:50]}... | {date_str or 'no date'}")

            except Exception as e:
                # Silently continue if this news URL doesn't exist
                continue

    return news_releases
