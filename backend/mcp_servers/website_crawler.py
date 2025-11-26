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
        Extract news release titles from news listing pages.
        Finds PDF links and then looks for associated title text.
        """
        from urllib.parse import urljoin

        # Strategy: Find all PDF links first, then find their associated titles
        # by looking at the link text itself or nearby elements

        pdf_links = soup.find_all('a', href=lambda href: href and '.pdf' in href.lower())

        for pdf_link in pdf_links:
            href = pdf_link.get('href', '')
            full_url = urljoin(source_url, href)

            # Try multiple strategies to find the title
            title = None

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

            # Strategy 3: Look in parent element
            if not title:
                parent = pdf_link.find_parent(['div', 'li', 'article', 'section'])
                if parent:
                    # Find the first substantial text in parent (excluding the PDF link itself)
                    for child in parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'span']):
                        child_text = child.get_text(strip=True)
                        if child_text and len(child_text) > 20 and len(child_text) < 200:
                            if not child_text.replace('-', '').replace('/', '').isdigit():
                                title = child_text
                                break

            # If we found a good title, update or add the PDF
            if title:
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
                        if not current_text or is_filename:
                            pdf_info['link_text'] = title
                            try:
                                print(f"[TITLE] Updated: {current_text} -> {title[:60]}...")
                            except UnicodeEncodeError:
                                print(f"[TITLE] Updated title")
                        found = True
                        break

                # If not found, add it
                if not found:
                    self.pdf_urls.append({
                        'url': full_url,
                        'link_text': title,
                        'source_page': source_url
                    })
                    try:
                        print(f"[TITLE] Found: {title[:60]}...")
                    except UnicodeEncodeError:
                        print(f"[TITLE] Found title")

    def _process_discovered_pdfs(self, keywords: List[str]) -> List[Dict]:
        """
        Process discovered PDFs and categorize them
        Returns structured list with document type classification
        """
        # Deduplicate PDFs - keep best title for each URL
        seen_urls = {}
        for pdf in self.pdf_urls:
            url_normalized = pdf['url'].split('?')[0].rstrip('/')
            link_text = pdf.get('link_text', '')

            # If URL not seen yet, add it
            if url_normalized not in seen_urls:
                seen_urls[url_normalized] = pdf
            else:
                # URL exists - keep the one with better title
                existing_text = seen_urls[url_normalized].get('link_text', '')
                existing_is_filename = existing_text.endswith('.pdf') or len(existing_text) < 30
                current_is_filename = link_text.endswith('.pdf') or len(link_text) < 30

                # Replace if current has better title than existing
                if existing_is_filename and not current_is_filename:
                    seen_urls[url_normalized] = pdf
                elif not current_is_filename and len(link_text) > len(existing_text):
                    # Both are good titles, keep longer one
                    seen_urls[url_normalized] = pdf

        # Use deduplicated list
        deduped_pdfs = list(seen_urls.values())
        print(f"\n[DEDUP] Reduced {len(self.pdf_urls)} PDFs to {len(deduped_pdfs)} unique URLs\n")

        documents = []

        for pdf in deduped_pdfs:
            url = pdf['url']
            link_text = pdf['link_text']
            combined_text = (link_text + ' ' + url).lower()

            # Determine document type (check in priority order)
            # NEWS RELEASES NOW HAVE HIGHEST PRIORITY (most current company info)
            doc_type = 'other'

            # News releases - HIGHEST PRIORITY for current company information
            if any(kw in combined_text for kw in ['/news/', 'nr-', 'press-release', 'press_release', '/press-releases/', '/news-releases/']):
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

            # Try to extract FULL DATE from filename/text (YYYYMMDD or YYYY-MM-DD format)
            # First try YYYYMMDD format (e.g., nr-20251111.pdf)
            date_match = re.search(r'(20\d{2})(\d{2})(\d{2})', combined_text)
            if date_match:
                year = date_match.group(1)
                month = date_match.group(2)
                day = date_match.group(3)
                full_date = f"{year}-{month}-{day}"
            else:
                # Try YYYY-MM-DD format
                date_match = re.search(r'(20\d{2})-(\d{2})-(\d{2})', combined_text)
                if date_match:
                    full_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    year = date_match.group(1)
                else:
                    # Fall back to just year
                    date_match = re.search(r'(20\d{2})', combined_text)
                    year = date_match.group(1) if date_match else None
                    full_date = None

            documents.append({
                'url': url,
                'title': link_text or url.split('/')[-1],
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

    return news_releases
