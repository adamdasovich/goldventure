"""
Website Crawler for Mining Company Documents
Uses Crawl4AI to discover PDFs and technical reports on company websites
"""

import asyncio
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import re
import sys
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


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

            # Strategy 3: Look in parent/grandparent element (handle grid layouts like Silver Spruce)
            parent = pdf_link.find_parent(['div', 'li', 'article', 'section', 'tr'])
            if parent:
                grandparent = parent.find_parent(['div', 'li', 'article', 'section', 'tr'])
                search_element = grandparent if grandparent else parent

                # Get all text from the parent/grandparent for date extraction
                parent_text = search_element.get_text()

                # Extract date from parent text - look for patterns like "December 3, 2025"
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

            # Try to extract FULL DATE - first check if we extracted it from HTML
            full_date = pdf.get('extracted_date')
            year = None

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
                            # Pattern 4: "Month Day YY" in title (e.g., "March 31 25" = March 31, 2025)
                            date_match = re.search(
                                r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[\s,]+(\d{1,2})[\s,]+(\d{2})(?!\d)',
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
                                    # Fall back to just year
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
    Convenience function to crawl a company website for NEWS RELEASES ONLY
    Filters to only news releases from the last N months (default 6)

    Args:
        url: Company website URL
        months: Number of months to look back (default 6)
        max_depth: How deep to crawl (default 2)

    Returns:
        List of news release documents with dates, sorted by newest first
    """
    crawler = MiningDocumentCrawler()
    all_documents = await crawler.discover_documents(
        start_url=url,
        max_depth=max_depth,
        max_pages=50
    )

    # Filter to only news releases
    news_releases = [d for d in all_documents if d['document_type'] == 'news_release']

    # Filter by date range
    news_releases = crawler._filter_by_date_range(news_releases, months=months)

    # ALSO crawl HTML news pages (not just PDFs)
    html_news = await crawl_html_news_pages(url, months=months)

    # Combine PDF and HTML news releases
    all_news = news_releases + html_news

    # Sort by date (newest first)
    all_news.sort(key=lambda x: x.get('date') or '', reverse=True)

    return all_news


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


async def crawl_html_news_pages(url: str, months: int = 6) -> List[Dict]:
    """
    Crawl HTML news pages (not PDFs) from a company website.
    Many companies have news as HTML pages, not PDF downloads.

    Args:
        url: Company website URL
        months: Number of months to look back

    Returns:
        List of news release dictionaries with title, url, date
    """
    import re
    from datetime import datetime, timedelta

    news_releases = []
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    crawler_config = CrawlerRunConfig(
        cache_mode="bypass",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Common news page patterns - including year-specific pages
        current_year = datetime.now().year
        years_to_check = [current_year, current_year - 1]  # Check current year and last year

        news_page_patterns = [
            f'{url}/news',
            f'{url}/news-releases',
            f'{url}/press-releases',
            f'{url}/investors/news',
            f'{url}/investors/news-releases',
        ]

        # Add year-specific patterns
        for year in years_to_check:
            news_page_patterns.extend([
                f'{url}/news/{year}',
                f'{url}/news-releases/{year}',
                f'{url}/press-releases/{year}',
            ])

        for news_url in news_page_patterns:
            try:
                # Try to fetch the news listing page
                result = await crawler.arun(url=news_url, config=crawler_config)

                if not result.success:
                    continue

                soup = BeautifulSoup(result.html, 'html.parser')

                # Find all links on the page that look like news articles
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)

                    # Skip if link text is empty or too short
                    if not link_text or len(link_text) < 15:
                        continue

                    # Build full URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = urljoin(url, href)
                    else:
                        full_url = urljoin(news_url, href)

                    # Check if this looks like a news article URL
                    if not any(pattern in full_url.lower() for pattern in ['/news/', '/press-release', 'news-release']):
                        continue

                    # Try to extract date from the URL or nearby text
                    date_str = None
                    year = None

                    # Pattern 1: /news/2024/article-name or /news/2024-12-01/
                    date_match = re.search(r'/(\d{4})[/-](\d{1,2})[/-](\d{1,2})', full_url)
                    if date_match:
                        year = date_match.group(1)
                        month = date_match.group(2).zfill(2)
                        day = date_match.group(3).zfill(2)
                        date_str = f"{year}-{month}-{day}"

                    # Pattern 2: Just year in URL /news/2024/
                    if not date_str:
                        year_match = re.search(r'/(\d{4})/', full_url)
                        if year_match:
                            year = year_match.group(1)

                    # Try to find date in nearby text (parent or sibling elements)
                    if not date_str:
                        # Look for date in parent element
                        parent = link.find_parent(['div', 'li', 'article'])
                        if parent:
                            parent_text = parent.get_text()
                            # Look for common date patterns
                            date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\\s,]+(\d{1,2})[\\s,]+(\d{4})'
                            date_match = re.search(date_pattern, parent_text, re.IGNORECASE)
                            if date_match:
                                month_name = date_match.group(1)
                                day = date_match.group(2).zfill(2)
                                year = date_match.group(3)

                                # Convert month name to number
                                month_map = {
                                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                                    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                                    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                                }
                                month_num = month_map.get(month_name[:3].lower(), '01')
                                date_str = f"{year}-{month_num}-{day}"

                    # If still no date found, fetch the actual article page and extract date
                    if not date_str:
                        date_str = await _extract_date_from_article_page(crawler, full_url, crawler_config)
                        if date_str:
                            # Extract year from the date string
                            year_match = re.search(r'^(\d{4})', date_str)
                            if year_match:
                                year = year_match.group(1)

                    # If we have a date, check if it's within our time range
                    if date_str:
                        try:
                            article_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if article_date < cutoff_date:
                                continue  # Too old
                        except:
                            pass  # Keep the article if we can't parse the date
                    elif year:
                        # If we only have year, check if it's recent enough
                        try:
                            if int(year) < cutoff_date.year:
                                continue  # Too old
                        except:
                            pass

                    # Add this news release
                    news_releases.append({
                        'title': link_text,
                        'url': full_url,
                        'date': date_str,
                        'document_type': 'news_release',
                        'year': year
                    })

                    print(f"[HTML NEWS] Found: {link_text[:60]}... | {date_str or year or 'unknown date'}")

            except Exception as e:
                # Silently continue if this news URL doesn't exist
                continue

    return news_releases
