"""
Company Auto-Population Scraper
Uses Crawl4AI to automatically extract comprehensive company information from mining company websites.
"""

import asyncio
import re
import sys
import requests
import ipaddress
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


def is_safe_url(url: str) -> bool:
    """
    Validate URL is safe to fetch (prevent SSRF attacks).
    Blocks internal IPs, localhost, and cloud metadata endpoints.
    """
    try:
        parsed = urlparse(url)

        # Only allow http/https
        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost variants
        if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            return False

        # Block common cloud metadata endpoints
        if hostname in ('169.254.169.254', 'metadata.google.internal'):
            return False

        # Try to parse as IP address and check for private/reserved ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            # Not an IP address, likely a domain name - that's fine
            pass

        return True
    except Exception:
        return False

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class CompanyDataScraper:
    """
    Comprehensive scraper for mining company websites.
    Extracts company info, team members, documents, and news.
    """

    def __init__(self):
        self.base_url = ""
        self.domain = ""
        self.visited_urls = set()
        self.extracted_data = {
            'company': {},
            'people': [],
            'documents': [],
            'news': [],
            'projects': [],
            'contacts': {},
            'social_media': {},
        }
        self.errors = []
        self.scrape_start_time = None
        self.max_scrape_seconds = 480  # 8 minutes default

    def _time_remaining(self) -> float:
        """Returns seconds remaining in time budget, or infinity if not tracking."""
        if not self.scrape_start_time:
            return float('inf')
        elapsed = (datetime.now() - self.scrape_start_time).total_seconds()
        return self.max_scrape_seconds - elapsed

    def _should_continue_scraping(self, section_name: str = "") -> bool:
        """
        Check if we have enough time to continue scraping.
        Logs a message if skipping due to time constraints.
        """
        remaining = self._time_remaining()
        if remaining < 30:  # Less than 30 seconds remaining
            elapsed = (datetime.now() - self.scrape_start_time).total_seconds()
            print(f"[TIME-LIMIT] {elapsed:.0f}s elapsed, skipping {section_name or 'remaining sections'} (need 30s buffer)")
            return False
        return True

    async def scrape_company(
        self,
        website_url: str,
        max_depth: int = 2,
        sections: List[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for scraping a company website.

        Args:
            website_url: Company website URL
            max_depth: How deep to crawl
            sections: Specific sections to scrape (None = all)
                     Options: ['homepage', 'about', 'team', 'investors', 'projects', 'news', 'contact']

        Returns:
            Dictionary with extracted data
        """
        if sections is None:
            sections = ['homepage', 'about', 'team', 'investors', 'projects', 'news', 'contact']

        self.base_url = website_url.rstrip('/')
        self.domain = urlparse(website_url).netloc
        self.visited_urls = set()
        self.extracted_data = {
            'company': {},
            'people': [],
            'documents': [],
            'news': [],
            'projects': [],
            'contacts': {},
            'social_media': {},
        }
        self.errors = []

        # Track time budget - Celery task has 600s hard limit, aim to finish in 480s (8 min)
        # to leave buffer for post-processing and database saves
        self.scrape_start_time = datetime.now()
        self.max_scrape_seconds = 480  # 8 minutes max for scraping

        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )

        # Fast config - reduced delays to fit within time budget
        # With ~50 potential pages, need to keep per-page time low
        crawler_config = CrawlerRunConfig(
            cache_mode="bypass",
            delay_before_return_html=2.0,  # 2 seconds (was 5s - too slow for 50 pages)
            page_timeout=30000,  # 30 second timeout (was 90s - too long for failed pages)
            wait_until="domcontentloaded",
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # 1. Scrape homepage first (gets basic info, nav structure) - ALWAYS do this
            if 'homepage' in sections:
                print(f"[SCRAPE] Scraping homepage: {self.base_url}")
                await self._scrape_homepage(crawler, crawler_config)

            # 2. Find and scrape About/Corporate section
            if ('about' in sections or 'team' in sections) and self._should_continue_scraping('about'):
                about_urls = self._find_section_urls(['about', 'corporate', 'company', 'who-we-are'])
                for url in about_urls[:2]:  # Limit to 2 about pages
                    if not self._should_continue_scraping('about pages'):
                        break
                    print(f"[SCRAPE] Scraping about page: {url}")
                    await self._scrape_about_page(crawler, crawler_config, url)

            # 3. Find and scrape Team/Management section
            if 'team' in sections and self._should_continue_scraping('team'):
                team_urls = self._find_section_urls(['team', 'management', 'leadership', 'board', 'directors', 'executives'])
                for url in team_urls[:3]:  # Limit to 3 team pages
                    if not self._should_continue_scraping('team pages'):
                        break
                    print(f"[SCRAPE] Scraping team page: {url}")
                    await self._scrape_team_page(crawler, crawler_config, url)

            # 4. Find and scrape Investors section
            if 'investors' in sections and self._should_continue_scraping('investors'):
                investor_urls = self._find_section_urls([
                    'investor', 'shareholders', 'financial', 'reports',
                    'presentations', 'presentation',
                    'factsheet', 'fact-sheet', 'fact_sheet',
                ])
                for url in investor_urls[:5]:
                    if not self._should_continue_scraping('investor pages'):
                        break
                    print(f"[SCRAPE] Scraping investor page: {url}")
                    await self._scrape_investor_page(crawler, crawler_config, url)

            # 5. Find and scrape Projects section
            if 'projects' in sections and self._should_continue_scraping('projects'):
                project_urls = self._find_section_urls(['project', 'property', 'properties', 'assets', 'operations', 'exploration'])
                for url in project_urls[:3]:
                    if not self._should_continue_scraping('project pages'):
                        break
                    print(f"[SCRAPE] Scraping projects page: {url}")
                    await self._scrape_projects_page(crawler, crawler_config, url)

                # ENHANCED: Also look for potential project pages in nav_links
                if self._should_continue_scraping('potential projects'):
                    potential_project_urls = self._find_potential_project_urls()
                    for url in potential_project_urls[:5]:
                        if not self._should_continue_scraping('potential project pages'):
                            break
                        if url not in self.visited_urls:
                            print(f"[SCRAPE] Scraping potential project page: {url}")
                            await self._scrape_projects_page(crawler, crawler_config, url)

                # ENHANCED: Scrape project pages found in navigation dropdown menus
                if self._should_continue_scraping('nav dropdown projects'):
                    nav_dropdown_projects = self.extracted_data.get('_nav_dropdown_projects', [])
                    for url in nav_dropdown_projects[:10]:
                        if not self._should_continue_scraping('nav dropdown project pages'):
                            break
                        if url not in self.visited_urls:
                            print(f"[SCRAPE] Scraping nav dropdown project page: {url}")
                            await self._scrape_projects_page(crawler, crawler_config, url)

                # After scraping listing pages, visit individual project detail pages
                if self._should_continue_scraping('project details'):
                    detail_urls_to_visit = []
                    for project in self.extracted_data.get('projects', []):
                        source_url = project.get('source_url', '')
                        if source_url and source_url not in self.visited_urls:
                            path = urlparse(source_url).path.rstrip('/')
                            parts = [p for p in path.split('/') if p]
                            if len(parts) >= 2 and parts[0] in ['projects', 'project', 'properties', 'property']:
                                detail_urls_to_visit.append(source_url)

                    for url in detail_urls_to_visit[:10]:
                        if not self._should_continue_scraping('project detail pages'):
                            break
                        print(f"[SCRAPE] Scraping project detail page: {url}")
                        await self._scrape_projects_page(crawler, crawler_config, url)

            # 6. Find and scrape News section
            if 'news' in sections and self._should_continue_scraping('news'):
                news_urls = self._find_section_urls(['news', 'press', 'media', 'releases'])
                for url in news_urls[:10]:
                    if not self._should_continue_scraping('news pages'):
                        break
                    print(f"[SCRAPE] Scraping news page: {url}")
                    await self._scrape_news_page(crawler, crawler_config, url)

            # 7. Find and scrape Contact section (lowest priority - skip if short on time)
            if 'contact' in sections and self._should_continue_scraping('contact'):
                contact_urls = self._find_section_urls(['contact', 'connect'])
                for url in contact_urls[:1]:
                    print(f"[SCRAPE] Scraping contact page: {url}")
                    await self._scrape_contact_page(crawler, crawler_config, url)

        # Post-process and deduplicate
        self._post_process_data()

        return {
            'data': self.extracted_data,
            'errors': self.errors,
            'urls_visited': list(self.visited_urls),
        }

    def _find_section_urls(self, keywords: List[str]) -> List[str]:
        """Find URLs that match section keywords from discovered links."""
        matching_urls = []

        # Check stored nav links from homepage
        nav_links = self.extracted_data.get('_nav_links', [])

        for link in nav_links:
            url_lower = link.get('url', '').lower()
            text_lower = link.get('text', '').lower()

            for keyword in keywords:
                if keyword in url_lower or keyword in text_lower:
                    full_url = urljoin(self.base_url, link['url'])
                    if full_url not in matching_urls:
                        matching_urls.append(full_url)
                    break

        # Also construct common URL patterns
        current_year = datetime.utcnow().year
        prev_year = current_year - 1

        for keyword in keywords:
            common_patterns = [
                f"{self.base_url}/{keyword}/",
                f"{self.base_url}/{keyword}",
            ]
            # Only add plural 's' suffix if keyword doesn't already end in 's'
            # (e.g., 'news' is already plural - don't create '/newss/')
            if not keyword.endswith('s'):
                common_patterns.extend([
                    f"{self.base_url}/{keyword}s/",
                    f"{self.base_url}/{keyword}s",
                ])

            # For news, add multiple year-based URL patterns that mining company sites commonly use
            if keyword in ['news', 'press', 'releases']:
                # Try current year, previous year, and year before that for better coverage
                years_to_try = [current_year, prev_year, prev_year - 1]

                for year in years_to_try:
                    common_patterns.extend([
                        # Pattern: /news/2025/ or /news/2024/
                        f"{self.base_url}/{keyword}/{year}/",
                        # Pattern: /2025/news/ or /2024/news/
                        f"{self.base_url}/{year}/{keyword}/",
                        # Pattern: /news-2025/ or /news-2024/
                        f"{self.base_url}/{keyword}-{year}/",
                        # Pattern: /news/news-2025/ (ATEX Resources uses this pattern)
                        f"{self.base_url}/{keyword}/{keyword}-{year}/",
                        # Pattern: /press-releases/2025/
                        f"{self.base_url}/press-releases/{year}/",
                        # Pattern: /news-releases/2025/
                        f"{self.base_url}/news-releases/{year}/",
                    ])

                # Also add non-year-specific news URLs
                common_patterns.extend([
                    f"{self.base_url}/press-releases/",
                    f"{self.base_url}/news-releases/",
                    # Additional patterns for sites with nested news structures
                    f"{self.base_url}/news-media/news-releases/",
                    f"{self.base_url}/news-media/press-releases/",
                    f"{self.base_url}/media/news-releases/",
                    f"{self.base_url}/media/press-releases/",
                    f"{self.base_url}/investors/news/",
                    f"{self.base_url}/investors/press-releases/",
                ])

                # Year-based patterns for nested news structures (e.g., Clean Air Metals)
                for year in years_to_try:
                    common_patterns.extend([
                        f"{self.base_url}/news-media/news-releases/{year}/",
                        f"{self.base_url}/news-media/press-releases/{year}/",
                        f"{self.base_url}/media/news-releases/{year}/",
                        f"{self.base_url}/media/press-releases/{year}/",
                        f"{self.base_url}/investors/news/{year}/",
                        f"{self.base_url}/investors/press-releases/{year}/",
                    ])

            for pattern in common_patterns:
                if pattern not in matching_urls:
                    matching_urls.append(pattern)

        return matching_urls

    def _find_potential_project_urls(self) -> List[str]:
        """
        Find nav links that look like project pages even if they don't contain 'project' keyword.
        Many mining company sites use direct URLs like /laird-lake/ or /golden-summit/
        instead of /projects/laird-lake/.

        Uses patterns to identify likely project names:
        - Geographic names (lakes, mountains, rivers, creeks, springs)
        - Mining-related terms in link text
        - Short, clean URL slugs at root level
        """
        potential_urls = []
        nav_links = self.extracted_data.get('_nav_links', [])

        # Skip these common non-project pages
        skip_keywords = {
            'about', 'contact', 'news', 'media', 'investor', 'team', 'leadership',
            'board', 'management', 'corporate', 'governance', 'esg', 'sustainability',
            'careers', 'home', 'privacy', 'terms', 'legal', 'disclaimer',
            'presentation', 'factsheet', 'report', 'financial', 'sedar',
            'subscribe', 'login', 'sign', 'register'
        }

        # Geographic suffixes that often indicate project names
        project_indicators = [
            'lake', 'river', 'creek', 'mountain', 'hill', 'valley', 'springs',
            'ridge', 'peak', 'basin', 'gulch', 'canyon', 'flat', 'mine',
            'deposit', 'project', 'property', 'claim', 'belt', 'district'
        ]

        for link in nav_links:
            url = link.get('url', '')
            text = link.get('text', '').lower().strip()

            # Skip external links
            if not self._is_internal_link(url):
                continue

            # Parse URL path
            path = urlparse(url).path.rstrip('/').lower()
            parts = [p for p in path.split('/') if p]

            # Skip if path has more than 2 levels (likely not a top-level project page)
            if len(parts) > 2:
                continue

            # Skip if any skip keywords in URL or text
            url_lower = url.lower()
            if any(kw in url_lower or kw in text for kw in skip_keywords):
                continue

            # Check if link text or URL contains project indicators
            combined = url_lower + ' ' + text
            has_project_indicator = any(ind in combined for ind in project_indicators)

            # Also check for 2-3 word geographic-sounding names
            # (e.g., "Laird Lake", "Excelsior Springs", "Golden Summit")
            words = text.split()
            is_short_name = 1 <= len(words) <= 4

            # Simple URL slug at root level (e.g., /laird-lake/)
            is_simple_slug = len(parts) == 1 and '-' in parts[0]

            if has_project_indicator or (is_short_name and is_simple_slug):
                full_url = urljoin(self.base_url, url)
                if full_url not in potential_urls:
                    potential_urls.append(full_url)
                    print(f"[DISCOVER] Potential project page: {text} -> {full_url}")

        return potential_urls

    def _extract_nav_dropdown_projects(self, soup) -> List[str]:
        """
        Extract project URLs from navigation dropdown menus.

        Many mining company sites have a structure like:
        <nav>
          <li class="has-dropdown">
            <a href="/projects">Projects</a>
            <ul class="dropdown">
              <li><a href="/projects/minera-don-nicolas">Minera Don Nicolas</a></li>
              <li><a href="/projects/lagoa-salgada">Lagoa Salgada</a></li>
            </ul>
          </li>
        </nav>

        This method finds such structures and extracts the child project URLs.
        """
        project_urls = []
        project_keywords = ['project', 'propert', 'asset', 'operation', 'portfolio', 'mine']

        # Common dropdown indicators in class names
        dropdown_parent_classes = ['has-dropdown', 'has-submenu', 'has-children', 'menu-item-has-children', 'dropdown']
        dropdown_child_classes = ['dropdown', 'sub-menu', 'submenu', 'g-dropdown', 'children', 'dropdown-menu']

        # Find all nav elements and menu containers
        nav_containers = soup.find_all(['nav', 'header', 'div'], class_=lambda x: x and any(
            c in str(x).lower() for c in ['nav', 'menu', 'header']
        ))

        # Also check direct nav tags
        nav_containers.extend(soup.find_all('nav'))

        for container in nav_containers:
            # Find list items that might be dropdown parents
            for li in container.find_all('li'):
                li_classes = ' '.join(li.get('class', [])).lower()

                # Check if this li has dropdown indicators
                has_dropdown = any(cls in li_classes for cls in dropdown_parent_classes)

                # Also check if it contains a nested ul
                nested_ul = li.find('ul')
                if not nested_ul and not has_dropdown:
                    continue

                # Get the parent link text
                parent_link = li.find('a', recursive=False)
                if not parent_link:
                    # Try to find direct child anchor
                    for child in li.children:
                        if hasattr(child, 'name') and child.name == 'a':
                            parent_link = child
                            break

                if not parent_link:
                    continue

                parent_text = parent_link.get_text(strip=True).lower()

                # Check if this is a projects dropdown
                is_project_parent = any(kw in parent_text for kw in project_keywords)

                if not is_project_parent:
                    continue

                print(f"[NAV-DROPDOWN] Found projects dropdown menu: '{parent_link.get_text(strip=True)}'")

                # Extract child links from the dropdown
                if nested_ul:
                    for child_li in nested_ul.find_all('li'):
                        child_link = child_li.find('a', href=True)
                        if child_link:
                            href = child_link.get('href', '')
                            text = child_link.get_text(strip=True)

                            # Skip empty or anchor-only links
                            if not href or href == '#' or href.startswith('javascript:'):
                                continue

                            # Skip if it looks like a section header
                            if not text or len(text) > 100:
                                continue

                            full_url = urljoin(self.base_url, href)

                            if full_url not in project_urls and self._is_internal_link(href):
                                project_urls.append(full_url)
                                print(f"[NAV-DROPDOWN] Found project: '{text}' -> {full_url}")

        return project_urls

    async def _scrape_homepage(self, crawler, config):
        """Scrape homepage for basic company info and navigation."""
        try:
            # Try initial crawl - may fail on Cloudflare-protected sites
            result = None
            cloudflare_indicators = ['one moment', 'just a moment', 'please wait', 'checking your browser',
                                    'cloudflare', 'ddos protection', 'attention required']

            try:
                result = await crawler.arun(url=self.base_url, config=config)
            except Exception as crawl_error:
                error_msg = str(crawl_error).lower()
                # If navigation error, wait and retry with longer delay
                if 'navigating' in error_msg or 'content' in error_msg:
                    print(f"[CLOUDFLARE] Page navigation detected, waiting and retrying...")
                    await asyncio.sleep(8)  # Wait 8 seconds for Cloudflare to complete
                    from crawl4ai import CrawlerRunConfig
                    retry_config = CrawlerRunConfig(
                        cache_mode="bypass",
                        delay_before_return_html=5.0,  # 5 second delay for Cloudflare
                        page_timeout=45000,  # 45 second timeout for Cloudflare retry
                        wait_until="domcontentloaded",
                    )
                    result = await crawler.arun(url=self.base_url, config=retry_config)
                else:
                    raise crawl_error

            if not result or not result.success:
                self.errors.append(f"Failed to load homepage: {self.base_url}")
                return

            self.visited_urls.add(self.base_url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Detect Cloudflare challenge pages and retry with longer wait
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""
            if any(indicator in title_text.lower() for indicator in cloudflare_indicators):
                print(f"[CLOUDFLARE] Detected challenge page in title, retrying with longer wait...")
                # Wait and retry with longer delay
                await asyncio.sleep(8)  # Wait 8 seconds for Cloudflare to complete
                from crawl4ai import CrawlerRunConfig
                retry_config = CrawlerRunConfig(
                    cache_mode="bypass",
                    delay_before_return_html=5.0,  # 5 second delay for Cloudflare
                    page_timeout=45000,  # 45 second timeout for Cloudflare retry
                    wait_until="domcontentloaded",
                )
                result = await crawler.arun(url=self.base_url, config=retry_config)
                if not result.success:
                    self.errors.append(f"Failed to bypass Cloudflare for: {self.base_url}")
                    return
                soup = BeautifulSoup(result.html, 'html.parser')
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else ""
                # If still showing Cloudflare, give up
                if any(indicator in title_text.lower() for indicator in cloudflare_indicators):
                    self.errors.append(f"Could not bypass Cloudflare protection for: {self.base_url}")
                    return

            # Extract company name from title or header
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                # Clean up common suffixes
                for suffix in [' - Home', ' | Home', ' - Official', ' | Official', ' - Mining', ' | Mining']:
                    title_text = title_text.replace(suffix, '')
                # Clean up common prefixes like "Welcome to"
                for prefix in ['Welcome to ', 'Welcome To ', 'Home - ', 'Home | ']:
                    if title_text.startswith(prefix):
                        title_text = title_text[len(prefix):]

                # Handle titles with taglines (e.g., "Company Name | Tagline" or "Company – Tagline")
                # Split on common separators: |, –, -, :
                separators = ['|', ' – ', ' - ', ' — ', ': ']
                parts = None
                for sep in separators:
                    if sep in title_text:
                        parts = [p.strip() for p in title_text.split(sep)]
                        break

                if parts and len(parts) >= 2:
                    # Company identifiers that indicate a proper company name (not just keywords)
                    company_suffixes = ['corp', 'corporation', 'inc', 'incorporated', 'ltd', 'limited',
                                       'llc', 'lp', 'co.', 'company', 'plc', 'resources', 'metals',
                                       'mining', 'exploration', 'minerals', 'gold', 'silver', 'copper',
                                       'nickel', 'energy', 'ventures']
                    # Tagline indicators (words that suggest this is NOT the company name)
                    tagline_indicators = ['unlocking', 'discovering', 'exploring', 'developing',
                                         'focused on', 'leading', 'premier', 'innovative',
                                         'potential', 'opportunity', 'future']

                    # Score each part - higher score = more likely to be company name
                    best_part = None
                    best_score = -1
                    for part in parts:
                        part_lower = part.lower()
                        score = 0
                        # Company suffix is strong indicator (+10)
                        if any(kw in part_lower for kw in company_suffixes):
                            score += 10
                        # Tagline indicator is negative (-5)
                        if any(kw in part_lower for kw in tagline_indicators):
                            score -= 5
                        # Shorter parts more likely to be company names (+2 if < 30 chars)
                        if len(part) < 30:
                            score += 2
                        # First part gets slight preference (+1)
                        if part == parts[0]:
                            score += 1

                        if score > best_score:
                            best_score = score
                            best_part = part

                    if best_part:
                        title_text = best_part

                self.extracted_data['company']['name'] = title_text.strip()

            # Extract tagline/slogan (usually in hero section)
            hero_selectors = [
                'h1', '.hero h1', '.hero-title', '.tagline', '.slogan',
                '[class*="hero"] h1', '[class*="banner"] h1'
            ]
            for selector in hero_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) < 200:
                        self.extracted_data['company']['tagline'] = text
                        break

            # Extract logo
            logo_selectors = [
                'header img[src*="logo"]', '.logo img', 'img.logo',
                'header img', '[class*="logo"] img', 'a.navbar-brand img'
            ]
            for selector in logo_selectors:
                element = soup.select_one(selector)
                if element and element.get('src'):
                    logo_url = urljoin(self.base_url, element['src'])
                    self.extracted_data['company']['logo_url'] = logo_url
                    break

            # Extract description from meta tags - prefer og:description over name="description"
            # og:description often has more detailed content
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            meta_desc = soup.find('meta', attrs={'name': 'description'})

            desc_content = None
            if og_desc and og_desc.get('content'):
                desc_content = og_desc['content']
            elif meta_desc and meta_desc.get('content'):
                desc_content = meta_desc['content']

            # Fallback: Try to extract description from JSON-LD schema (Yoast SEO, etc.)
            # Some sites like Corcel Exploration only have description in JSON-LD
            if not desc_content:
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        import json
                        schema_data = json.loads(script.string)

                        # Handle @graph structure (common in Yoast SEO)
                        if isinstance(schema_data, dict) and '@graph' in schema_data:
                            for item in schema_data['@graph']:
                                if isinstance(item, dict):
                                    # Look for WebSite or Organization description
                                    if item.get('@type') in ['WebSite', 'Organization', 'Corporation']:
                                        if item.get('description'):
                                            desc_content = item['description']
                                            print(f"[DESC] Found description in JSON-LD ({item.get('@type')})")
                                            break
                        # Direct schema object
                        elif isinstance(schema_data, dict) and schema_data.get('description'):
                            desc_content = schema_data['description']
                            print(f"[DESC] Found description in JSON-LD")

                        if desc_content:
                            break
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        continue

            if desc_content:
                # Basic validation - skip if it looks like error page or garbage
                desc_lower = desc_content.lower()
                garbage_keywords = ['page not found', '404', 'apologies', "can't find", 'click here']
                if not any(kw in desc_lower for kw in garbage_keywords):
                    self.extracted_data['company']['description'] = desc_content

            # Also try to extract company description from homepage content
            # Look for "About" sections or first substantial paragraphs
            about_selectors = [
                '[class*="about"]', 'section[id*="about"]', '#about',
                '.company-description', '.overview', '[class*="overview"]',
                '.intro', '[class*="intro"]', 'main section'
            ]
            homepage_desc = None

            # First, try to find "About [Company]" or "Welcome to [Company]" h2 headers and extract following paragraphs
            # This handles sites like Athena Gold where About section is marked by h2 header
            # Also handles sites like Eastfield Resources where description is under "Welcome to" header
            for header in soup.find_all(['h2', 'h3']):
                header_text = header.get_text(strip=True).lower()
                if 'about' in header_text or 'welcome to' in header_text:
                    # Found About header, get next sibling paragraphs
                    parent = header.find_parent(['div', 'section'])
                    if parent:
                        paragraphs = parent.find_all('p')
                        for p in paragraphs[:5]:
                            p_text = p.get_text(strip=True)
                            p_lower = p_text.lower()
                            if len(p_text) > 80:
                                company_indicators = ['company', 'corporation', 'advancing', 'developing',
                                                     'exploring', 'project', 'mine', 'mineral', 'resource',
                                                     'property', 'hectare', 'land package', 'producer',
                                                     'exploration', 'production', 'asset', 'operations',
                                                     'junior', 'hunting', 'gold', 'silver', 'copper']
                                bio_indicators = ['cpa', 'cfo', 'ceo', 'years of experience',
                                                 'previously served', 'his career', 'her career',
                                                 'results oriented', 'accomplished', 'executive']
                                has_company = any(ind in p_lower for ind in company_indicators)
                                has_bio = any(ind in p_lower for ind in bio_indicators)
                                if has_company and not has_bio:
                                    homepage_desc = p_text
                                    break
                        if homepage_desc:
                            break

            # Fallback: try CSS selectors if h2 method didn't work
            if not homepage_desc:
                for selector in about_selectors:
                    section = soup.select_one(selector)
                    if section:
                        paragraphs = section.find_all('p')
                        for p in paragraphs[:5]:
                            p_text = p.get_text(strip=True)
                            # Look for company-related text (not bios)
                            p_lower = p_text.lower()
                            if len(p_text) > 80:
                                # Check if it talks about the company (not a person)
                                company_indicators = ['company', 'corporation', 'advancing', 'developing',
                                                     'exploring', 'project', 'mine', 'mineral', 'resource',
                                                     'property', 'hectare', 'land package', 'producer',
                                                     'exploration', 'production', 'asset', 'operations',
                                                     'junior', 'hunting', 'gold', 'silver', 'copper']
                                bio_indicators = ['cpa', 'cfo', 'ceo', 'years of experience',
                                                 'previously served', 'his career', 'her career',
                                                 'results oriented', 'accomplished', 'executive']
                                has_company = any(ind in p_lower for ind in company_indicators)
                                has_bio = any(ind in p_lower for ind in bio_indicators)
                                if has_company and not has_bio:
                                    homepage_desc = p_text
                                    break
                        if homepage_desc:
                            break

            # Last resort: If still no description, scan main content area for company-related paragraphs
            # This handles sites where description isn't in a labeled section
            if not homepage_desc:
                # Look in main, article, or the largest content div
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in str(x).lower() or 'main' in str(x).lower()))
                if main_content:
                    paragraphs = main_content.find_all('p')
                    for p in paragraphs[:10]:  # Check first 10 paragraphs
                        p_text = p.get_text(strip=True)
                        p_lower = p_text.lower()
                        if len(p_text) > 100:  # Need substantial text
                            company_indicators = ['company', 'corporation', 'ltd', 'inc', 'advancing', 'developing',
                                                 'exploring', 'project', 'mine', 'mineral', 'resource',
                                                 'property', 'hectare', 'land package', 'producer',
                                                 'exploration', 'production', 'asset', 'operations',
                                                 'junior', 'gold', 'silver', 'copper', 'lithium',
                                                 'partners', 'investors', 'venture']
                            bio_indicators = ['cpa', 'cfo', 'ceo', 'president', 'years of experience',
                                             'previously served', 'his career', 'her career',
                                             'results oriented', 'accomplished', 'executive', 'mr.', 'ms.', 'dr.']
                            # Count company indicators vs bio indicators
                            company_count = sum(1 for ind in company_indicators if ind in p_lower)
                            bio_count = sum(1 for ind in bio_indicators if ind in p_lower)
                            # Accept if it has multiple company indicators and few bio indicators
                            if company_count >= 2 and bio_count == 0:
                                homepage_desc = p_text
                                print(f"[DESC] Found description from main content scan")
                                break

            # Use homepage description if it's better than meta description
            current_desc = self.extracted_data['company'].get('description', '')
            if homepage_desc and (not current_desc or len(homepage_desc) > len(current_desc)):
                self.extracted_data['company']['description'] = homepage_desc

            # Extract ticker symbol (often in header or stock ticker bar)
            # Note: Be careful with OTC patterns - "OTCQB" and "OTCQX" are market tiers, not exchanges

            # FIRST: Check for TradingView widgets (common on mining company websites)
            # These contain the ticker in URL-encoded format: "symbol":"TSXV:MFG"
            tradingview_pattern = r'tradingview[^"]*%22symbol%22%3A%22([A-Z]+)%3A([A-Z]+)%22'
            raw_html = str(soup)
            tv_matches = re.findall(tradingview_pattern, raw_html, re.IGNORECASE)
            if tv_matches:
                for exchange_code, ticker_code in tv_matches:
                    exchange_code = exchange_code.upper()
                    ticker_code = ticker_code.upper()
                    # Map TradingView exchange codes to our format
                    exchange_map = {'TSXV': 'TSXV', 'TSX': 'TSX', 'CSE': 'CSE', 'NEO': 'NEO'}
                    if exchange_code in exchange_map and len(ticker_code) >= 2 and len(ticker_code) <= 5:
                        self.extracted_data['company']['ticker_symbol'] = ticker_code
                        self.extracted_data['company']['exchange'] = exchange_map[exchange_code]
                        print(f"[TICKER] Found TradingView widget: {exchange_code}:{ticker_code}")
                        # Don't continue searching - TradingView is authoritative
                        break

            # If TradingView didn't find ticker, use pattern matching
            ticker_patterns = [
                # TSX Venture patterns: "TSX.V: SSE", "TSX-V: AMM", "TSXV: AMM", "TSXV:SGN" (no space)
                r'\b(TSX[.\-\s]?V|TSXV)[:\s]*([A-Z]{2,5})\b',
                # Ticker.V format: "SGN.V" (common format for TSXV)
                r'\b([A-Z]{2,5})\.(V)\b',
                # TSX main patterns: "TSX: AMM" or "TSX:AMM" (only match if NOT followed by V)
                r'\b(TSX)(?![.\-]?V)[:\s]*([A-Z]{2,5})\b',
                # CSE patterns: "CSE: AMM" or "CSE:AMM"
                r'\b(CSE)[:\s]*([A-Z]{2,5})\b',
                # NEO patterns: "NEO: AMM" or "NEO:AMM"
                r'\b(NEO)[:\s]*([A-Z]{2,5})\b',
                # ASX/AIM patterns
                r'\b(ASX|AIM)[:\s]*([A-Z]{2,5})\b',
                # OTC patterns - specifically look for OTCQB/OTCQX followed by ticker
                r'\b(?:OTCQB|OTCQX)[:\s]*([A-Z]{3,5})\b',
                # US OTC pattern: "US: SSEBF" or "OTC: SSEBF"
                r'\b(?:US|OTC)[:\s]*([A-Z]{4,5})\b',
                # Reverse patterns: "AMM: TSX"
                r'\b([A-Z]{2,5})[:\s]+(TSX[.\-\s]?V|TSXV|TSX|CSE|NEO|ASX|AIM)\b',
                # Parenthetical format: "(TSX-V: SGN)" or "(TSXV: SGN)"
                r'\((TSX[.\-\s]?V|TSXV)[:\s]*([A-Z]{2,5})\)',
                r'\((TSX)[:\s]*([A-Z]{2,5})\)',
                r'\((CSE)[:\s]*([A-Z]{2,5})\)',
            ]

            # First, try to find ticker in specific stock ticker elements (often JS-rendered)
            # Look for elements with class names containing 'stock', 'ticker', 'quote'
            ticker_selectors = [
                '[class*="stock"]', '[class*="ticker"]', '[class*="quote"]',
                '[id*="stock"]', '[id*="ticker"]', '[id*="quote"]',
                '.stock-info', '.stock-price', '.stock-ticker',
                'header', '.topbar', '.top-bar', '[class*="topbar"]'
            ]
            ticker_text = ""
            for selector in ticker_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    elem_text = elem.get_text(separator=' ')
                    # Only use if it contains exchange-like text
                    if any(ex in elem_text.upper() for ex in ['TSX', 'CSE', 'NEO', 'ASX', 'OTC', 'NYSE', 'NASDAQ']):
                        ticker_text += " " + elem_text

            # Check for stock quote iframes (common pattern for mining company websites)
            # These load ticker info from external services like quotemedia, adnetcms, brighterir, etc.
            stock_iframes = soup.find_all('iframe', class_=lambda x: x and any(
                kw in ' '.join(x).lower() for kw in ['quote', 'stock', 'ticker', 'bir-']
            ))
            if not stock_iframes:
                # Also check for iframes with stock-related src URLs
                stock_iframes = soup.find_all('iframe', src=lambda x: x and any(
                    kw in x.lower() for kw in ['quote', 'stock', 'feed.adnet', 'brighterir', 'quotemedia']
                ))

            # Fetch iframe content if found
            for iframe in stock_iframes[:2]:  # Limit to first 2 iframes
                iframe_src = iframe.get('src', '')
                # Validate iframe URL to prevent SSRF - only allow http/https
                if iframe_src and iframe_src.startswith(('http://', 'https://')):
                    try:
                        iframe_resp = requests.get(iframe_src, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }, timeout=5)
                        if iframe_resp.status_code == 200:
                            iframe_content = iframe_resp.text
                            # Look for ticker patterns in iframe content
                            ticker_text += " " + iframe_content
                            # Also check for data attributes like data-qmod-params
                            iframe_soup = BeautifulSoup(iframe_content, 'html.parser')
                            for elem in iframe_soup.find_all(attrs={'data-qmod-params': True}):
                                qmod_data = elem.get('data-qmod-params', '')
                                if qmod_data:
                                    ticker_text += " " + qmod_data
                    except Exception as e:
                        print(f"[WARN] Failed to fetch iframe: {iframe_src}: {e}")

            # Helper function to normalize exchange names
            def normalize_exchange(ex):
                ex_clean = ex.upper().replace(' ', '').replace('-', '').replace('.', '')
                # Map variations to standard codes
                if ex_clean in ['TSXV', 'TSXV', 'TSXVENTURE']:
                    return 'TSXV'
                if ex_clean == 'TSX':
                    return 'TSX'
                if ex_clean == 'CSE':
                    return 'CSE'
                if ex_clean == 'NEO':
                    return 'NEO'
                if ex_clean in ['ASX', 'AIM']:
                    return ex_clean
                return ex_clean

            # Helper function to validate ticker symbol
            def is_valid_ticker(ticker):
                """Check if a string looks like a valid stock ticker."""
                if not ticker or len(ticker) < 2 or len(ticker) > 5:
                    return False
                # Must be all letters
                if not ticker.isalpha():
                    return False
                # Should not be a common word or exchange name
                invalid_tickers = ['OTCQX', 'OTCQB', 'TSX', 'TSXV', 'CSE', 'NEO', 'NYSE', 'NASDAQ', 'ASX', 'AIM', 'OTC', 'US', 'GOLD']
                if ticker.upper() in invalid_tickers:
                    return False
                return True

            # Helper function to extract ticker from match
            def extract_ticker_from_match(match, pattern_idx):
                groups = match.groups()
                # Handle OTCQB/OTCQX/US pattern (only has ticker, no exchange group)
                if len(groups) == 1:
                    ticker = groups[0].upper()
                    if not is_valid_ticker(ticker):
                        return None, None
                    return ticker, 'OTC'

                # Determine which group is exchange vs ticker
                exchange_keywords = ['TSX', 'TSXV', 'CSE', 'NEO', 'ASX', 'AIM', 'V']
                g0_upper = groups[0].upper().replace(' ', '').replace('-', '').replace('.', '')
                g1_upper = groups[1].upper().replace(' ', '').replace('-', '').replace('.', '')

                # Check for .V format (ticker.V means TSXV)
                if g1_upper == 'V':
                    ticker = groups[0].upper()
                    if not is_valid_ticker(ticker):
                        return None, None
                    return ticker, 'TSXV'
                elif any(kw in g0_upper for kw in exchange_keywords):
                    ticker = groups[1].upper()
                    if not is_valid_ticker(ticker):
                        return None, None
                    return ticker, normalize_exchange(groups[0])
                else:
                    ticker = groups[0].upper()
                    if not is_valid_ticker(ticker):
                        return None, None
                    return ticker, normalize_exchange(groups[1])

            # Canadian exchange patterns (prioritized - these are primary listings)
            canadian_patterns = ticker_patterns[:6]  # TSX, TSXV, CSE, NEO patterns
            # OTC patterns (secondary - often dual-listed)
            otc_patterns = ticker_patterns[6:8]  # OTCQB/OTCQX patterns
            # Reverse and parenthetical patterns (ticker first, then exchange)
            reverse_patterns = ticker_patterns[8:]

            # Priority 1: Look for ANY Canadian pattern in targeted ticker elements FIRST
            # This includes both "TSX.V: SYH" and "SYH: TSX.V" formats
            # IMPORTANT: Check ticker elements with ALL patterns before searching full page
            # to avoid picking up other companies' tickers mentioned in body text
            ticker_found = False
            all_canadian_with_reverse = canadian_patterns + reverse_patterns
            for idx, pattern in enumerate(all_canadian_with_reverse):
                match = re.search(pattern, ticker_text, re.IGNORECASE)
                if match:
                    # Determine correct pattern index for extract_ticker_from_match
                    actual_idx = idx if idx < 6 else idx - 6 + 8
                    ticker, exchange = extract_ticker_from_match(match, actual_idx)
                    if ticker and exchange:  # Validate extraction succeeded
                        self.extracted_data['company']['ticker_symbol'] = ticker
                        self.extracted_data['company']['exchange'] = exchange
                        ticker_found = True
                        print(f"[TICKER] Found Canadian exchange in ticker elements: {exchange}:{ticker}")
                        break

            # Priority 2: Look for OTC tickers in targeted ticker elements
            if not ticker_found:
                for idx, pattern in enumerate(otc_patterns):
                    match = re.search(pattern, ticker_text, re.IGNORECASE)
                    if match:
                        ticker, exchange = extract_ticker_from_match(match, idx + 6)
                        if ticker and exchange:  # Validate extraction succeeded
                            self.extracted_data['company']['ticker_symbol'] = ticker
                            self.extracted_data['company']['exchange'] = exchange
                            ticker_found = True
                            print(f"[TICKER] Found OTC in ticker elements: {exchange}:{ticker}")
                            break

            # Priority 3: Look for Canadian exchange tickers in full page text
            # WARNING: This can pick up other companies' tickers mentioned in body text
            # Only use this as a fallback when ticker elements don't have the info
            if not ticker_found:
                full_page_text = soup.get_text()
                for idx, pattern in enumerate(canadian_patterns):
                    match = re.search(pattern, full_page_text, re.IGNORECASE)
                    if match:
                        ticker, exchange = extract_ticker_from_match(match, idx)
                        if ticker and exchange:  # Validate extraction succeeded
                            self.extracted_data['company']['ticker_symbol'] = ticker
                            self.extracted_data['company']['exchange'] = exchange
                            ticker_found = True
                            print(f"[TICKER] Found Canadian exchange in page text: {exchange}:{ticker}")
                            break

            # Priority 4: Other patterns (reverse patterns, parenthetical) in full page
            if not ticker_found:
                full_page_text = soup.get_text() if 'full_page_text' not in dir() else full_page_text
                for idx, pattern in enumerate(reverse_patterns):
                    match = re.search(pattern, full_page_text, re.IGNORECASE)
                    if match:
                        ticker, exchange = extract_ticker_from_match(match, idx + 8)
                        if ticker and exchange:  # Validate extraction succeeded
                            self.extracted_data['company']['ticker_symbol'] = ticker
                            self.extracted_data['company']['exchange'] = exchange
                            ticker_found = True
                            print(f"[TICKER] Found via reverse pattern: {exchange}:{ticker}")
                            break

            if not ticker_found:
                print(f"[TICKER] No ticker found on page")

            # Extract navigation links for later use
            nav_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if href and text and len(text) < 50:
                    # Only internal links
                    if self._is_internal_link(href):
                        nav_links.append({'url': href, 'text': text})
            self.extracted_data['_nav_links'] = nav_links

            # Extract project URLs from dropdown navigation menus
            dropdown_project_urls = self._extract_nav_dropdown_projects(soup)
            if dropdown_project_urls:
                self.extracted_data['_nav_dropdown_projects'] = dropdown_project_urls
                print(f"[NAV-DROPDOWN] Found {len(dropdown_project_urls)} project URLs from dropdown menus")

            # Extract social media links
            self._extract_social_media(soup)

            # ENHANCED: Extract direct document links from homepage (presentations, fact sheets)
            # Many mining company homepages have "CORPORATE PRESENTATION" buttons linking directly to PDFs
            await self._extract_homepage_documents(soup)

            # Extract flagship project from homepage (many mining companies feature their main project)
            page_text = soup.get_text()
            project_keywords = ['deposit', 'mine', 'project', 'property']

            # Look for project mentions in headers
            for header in soup.find_all(['h1', 'h2', 'h3']):
                header_text = header.get_text(strip=True)
                header_lower = header_text.lower().strip()

                # Use intelligent validation to skip invalid project names
                if not self._is_valid_project_name(header_text):
                    continue

                # Skip all-caps short headers (likely company name)
                if header_text.isupper() and len(header_text.split()) <= 3:
                    continue

                # Check if header mentions a project
                if any(kw in header_lower for kw in project_keywords):
                    # Get description from following content
                    description = ''
                    for sibling in header.find_next_siblings(['p', 'div'])[:2]:
                        sib_text = sibling.get_text(strip=True)
                        if sib_text and len(sib_text) > 30:
                            description = sib_text[:500]
                            break

                    # Determine location
                    location = None
                    locations = ['Canada', 'USA', 'United States', 'Mexico', 'Peru', 'Chile',
                                'Australia', 'Nevada', 'Ontario', 'Quebec', 'British Columbia',
                                'Puebla', 'Sonora', 'Durango', 'Yukon', 'Alaska']
                    combined = header_text + ' ' + description
                    for loc in locations:
                        if loc.lower() in combined.lower():
                            location = loc
                            break

                    project = {
                        'name': header_text[:200],
                        'description': description,
                        'location': location,
                        'source_url': self.base_url
                    }

                    # Avoid duplicates (case-insensitive)
                    if not any(p.get('name', '').lower() == project['name'].lower() for p in self.extracted_data['projects']):
                        self.extracted_data['projects'].append(project)

            print(f"[OK] Homepage scraped: {self.extracted_data['company'].get('name', 'Unknown')}")

        except Exception as e:
            self.errors.append(f"Homepage scraping error: {str(e)}")
            print(f"[ERROR] Homepage: {str(e)}")

    async def _scrape_about_page(self, crawler, config, url: str):
        """Scrape about/corporate page for company details."""
        if url in self.visited_urls:
            return

        try:
            # First, check if this URL serves a PDF directly (like /corp-presentation/)
            # Some sites serve PDFs from URLs without .pdf extension
            import requests as sync_requests
            try:
                resp = sync_requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=10)
                content_type = resp.headers.get('Content-Type', '').lower()
                is_pdf = 'application/pdf' in content_type
                if not is_pdf and resp.status_code == 200:
                    first_bytes = resp.raw.read(10)
                    is_pdf = first_bytes.startswith(b'%PDF')
                resp.close()

                if is_pdf:
                    # This URL serves a PDF directly - add it as a document
                    self.visited_urls.add(url)
                    url_lower = url.lower()
                    doc_type = 'other'
                    if any(kw in url_lower for kw in ['presentation', 'corp-presentation', 'corporate-presentation']):
                        doc_type = 'presentation'
                    elif any(kw in url_lower for kw in ['fact', '1pager', 'one-pager']):
                        doc_type = 'fact_sheet'

                    path = urlparse(url).path.rstrip('/')
                    slug = path.split('/')[-1] if path else 'document'
                    title = slug.replace('-', ' ').replace('_', ' ').title()

                    doc = {
                        'source_url': url,
                        'title': title,
                        'document_type': doc_type,
                        'extracted_at': datetime.utcnow().isoformat(),
                    }
                    self.extracted_data['documents'].append(doc)
                    print(f"[OK] Direct PDF detected at {url}: {title} ({doc_type})")
                    return
            except Exception as pdf_check_error:
                print(f"[DEBUG] PDF check failed for {url}: {pdf_check_error}")

            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Extract longer description - try multiple strategies
            description = ''

            # Helper function to detect if text is a biography
            def is_biography_text(text):
                """Check if text appears to be a person's biography."""
                if not text or len(text) < 50:
                    return False
                text_lower = text.lower()

                # Bio indicator patterns
                bio_indicators = [
                    'years of experience', 'years experience', 'extensive experience',
                    r'over \d+ years', r'more than \d+ years',
                    'has served as', 'served as', 'previously served',
                    'formerly', 'former', 'prior to', 'prior to that',
                    'currently serves', 'currently the', 'was the',
                    r'joined .* in \d{4}', 'joined the company',
                    'holds a degree', 'received his', 'received her', 'earned his', 'earned her',
                    'graduated from', 'bachelor', 'master', 'mba', r'ph\.?d',
                    'professional geologist', r'p\.geo', r'p\.eng',
                    r'^he has', r'^she has', r'^he is', r'^she is', r'^mr\.', r'^ms\.', r'^mrs\.',
                    'his career', 'her career', 'his expertise', 'her expertise',
                    'brings .* years', 'brings extensive', 'brings over',
                    'responsible for', 'oversees', 'manages', 'leads the',
                    'board of directors', 'advisory board', 'audit committee',
                    r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+(has|is|was|brings|joined|serves)',
                    'successful entrepreneur', 'founded several', 'founded multiple',
                    'worked at', 'worked for', 'employed at', 'employed by',
                    r'spent \d+ years', 'where he', 'where she',
                    'managing director', 'vice president', 'chief financial officer',
                    'chief executive', 'portfolio manager', 'investment banker',
                    # Professional credential patterns (CPAs, engineers, etc.)
                    r'\bcpa\b', r'\bca\b.*finance', 'chartered accountant', 'certified public accountant',
                    'senior finance leadership', 'finance leadership', 'finance executive',
                    # Accomplishment/result patterns for bios
                    'results oriented', 'results-oriented', 'accomplished', 'accomplished mining',
                    'demonstrated history', 'proven track record', 'track record of',
                    # Mining executive bio patterns
                    'mining executive', 'mining professional', 'exploration geologist',
                    'mine development', 'mining industry', 'mining operations',
                ]

                for ind in bio_indicators:
                    if re.search(ind, text_lower):
                        return True

                # Check if text starts with a person's name pattern
                name_start_pattern = r'^[A-Z][a-z]+\s+(?:\([^)]+\)\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(is|has|was|brings|joined|serves|holds)'
                if re.match(name_start_pattern, text):
                    return True

                # Check for multiple executive titles in short text (likely team page content)
                exec_titles = ['ceo', 'cfo', 'coo', 'president', 'chairman', 'director',
                              'vice president', 'vp', 'chief', 'officer', 'executive']
                title_count = sum(1 for t in exec_titles if t in text_lower)
                if title_count >= 2 and len(text) < 300:
                    return True

                return False

            # Strategy 1: Look for specific content areas
            content_selectors = [
                'article', '.content', '.main-content', '#content',
                '[class*="about"]', '[class*="corporate"]', 'main', '.uk-section'
            ]
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Get all paragraphs but filter out biographies
                    paragraphs = element.find_all('p')
                    if paragraphs:
                        valid_paras = []
                        for p in paragraphs[:10]:  # Check up to 10 paragraphs
                            p_text = p.get_text(strip=True)
                            if len(p_text) > 50 and not is_biography_text(p_text):
                                valid_paras.append(p_text)
                            if len(valid_paras) >= 5:
                                break
                        if valid_paras:
                            desc_text = ' '.join(valid_paras)
                            if len(desc_text) > len(description):
                                description = desc_text
                    break

            # Strategy 2: If no specific container, look for first substantial paragraphs on page
            # But SKIP paragraphs that are in team/leadership/management sections
            if not description or len(description) < 100:
                all_paragraphs = soup.find_all('p')
                substantial_paras = []
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    # Look for company-describing paragraphs (not navigation, not person bios)
                    if len(text) > 80:
                        text_lower = text.lower()

                        # Check if this paragraph is inside a team/leadership section
                        # by looking at parent containers
                        in_team_section = False
                        for parent in p.parents:
                            if parent.name in ['section', 'div', 'article']:
                                parent_class = ' '.join(parent.get('class', []))
                                parent_id = parent.get('id', '')
                                parent_text = parent_class + ' ' + parent_id
                                team_indicators = ['team', 'leadership', 'management', 'executive',
                                                  'director', 'officer', 'board', 'people', 'staff']
                                if any(ind in parent_text.lower() for ind in team_indicators):
                                    in_team_section = True
                                    break
                                # Also check for nearby headers that indicate team section
                                prev_header = parent.find_previous(['h1', 'h2', 'h3'])
                                if prev_header:
                                    header_text = prev_header.get_text(strip=True).lower()
                                    if any(ind in header_text for ind in team_indicators):
                                        in_team_section = True
                                        break

                        if in_team_section:
                            continue

                        # Comprehensive bio detection - much more thorough than before
                        bio_indicators = [
                            # Experience patterns
                            'years of experience', 'years experience', 'extensive experience',
                            'over \\d+ years', 'more than \\d+ years',
                            # Role/position history
                            'has served as', 'served as', 'previously served',
                            'formerly', 'former', 'prior to', 'prior to that',
                            'currently serves', 'currently the', 'is the', 'was the',
                            'joined .* in \\d{4}', 'joined the company',
                            # Education/credentials
                            'holds a degree', 'received his', 'received her', 'earned his', 'earned her',
                            'graduated from', 'bachelor', 'master', 'mba', 'ph\\.?d',
                            'professional geologist', 'p\\.geo', 'p\\.eng',
                            # Personal pronouns indicating biography
                            '^he has', '^she has', '^he is', '^she is', '^mr\\.', '^ms\\.', '^mrs\\.',
                            'his career', 'her career', 'his expertise', 'her expertise',
                            'his role', 'her role', 'his responsibilities', 'her responsibilities',
                            # Career narrative
                            'brings .* years', 'brings extensive', 'brings over',
                            'responsible for', 'oversees', 'manages', 'leads the',
                            'board of directors', 'advisory board', 'audit committee',
                            # Name patterns (John Smith has...)
                            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+(has|is|was|brings|joined|serves)',
                            # Entrepreneur/founder bio patterns
                            'successful entrepreneur', 'founded several', 'founded multiple',
                            'led the .* division', 'exploration division', 'mining division',
                            # Work history
                            'worked at', 'worked for', 'employed at', 'employed by',
                            'spent \\d+ years', 'where he', 'where she',
                            # Professional credential patterns (CPAs, engineers, etc.)
                            '\\bcpa\\b', '\\bca\\b.*finance', 'chartered accountant', 'certified public accountant',
                            'senior finance leadership', 'finance leadership', 'finance executive',
                            # Accomplishment/result patterns for bios
                            'results oriented', 'results-oriented', 'accomplished', 'accomplished mining',
                            'demonstrated history', 'proven track record', 'track record of',
                            # Mining executive bio patterns
                            'mining executive', 'mining professional', 'exploration geologist',
                            'mine development', 'mining industry', 'mining operations',
                        ]

                        is_bio = False
                        for ind in bio_indicators:
                            if re.search(ind, text_lower):
                                is_bio = True
                                break

                        # Additional check: if text starts with a person's name pattern
                        # Pattern: "FirstName LastName is/has/was/brings..."
                        name_start_pattern = r'^[A-Z][a-z]+\s+(?:\([^)]+\)\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(is|has|was|brings|joined|serves|holds)'
                        if re.match(name_start_pattern, text):
                            is_bio = True

                        # Check if text mentions too many executive titles (likely team page content)
                        exec_titles = ['ceo', 'cfo', 'coo', 'president', 'chairman', 'director',
                                      'vice president', 'vp', 'chief', 'officer', 'executive']
                        title_count = sum(1 for t in exec_titles if t in text_lower)
                        if title_count >= 2 and len(text) < 300:
                            is_bio = True

                        if not is_bio:
                            substantial_paras.append(text)
                            if len(substantial_paras) >= 3:
                                break

                if substantial_paras:
                    combined = ' '.join(substantial_paras)
                    if len(combined) > len(description):
                        description = combined

            # Validate and update description if we found something better
            def is_valid_description(desc):
                """Check if description is valid content, not garbage."""
                if not desc or len(desc) < 50:
                    return False
                desc_lower = desc.lower()

                # Check if it looks like a person bio (starts with a name)
                # Pattern: "FirstName LastName continues/brings/has/is/serves..."
                import re
                bio_start_patterns = [
                    r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+(continues|brings|has|is|was|serves|served|joined|leads|led|holds|held|spent|worked|oversaw|managed|built|established|founded|pioneered)\b',
                    r'^(mr\.|mrs\.|ms\.|dr\.)\s+[A-Z][a-z]+\s+(continues|brings|has|is|was|serves)\b',
                    r'^[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\s+(continues|brings|has|is|was|serves)\b',  # "John A. Smith brings..."
                ]
                for pattern in bio_start_patterns:
                    if re.search(pattern, desc, re.IGNORECASE):
                        return False

                # Garbage indicators (error pages, role lists, etc.)
                garbage_indicators = [
                    'page not found', '404', 'sorry', 'apologies',
                    "can't find", "cannot find", 'check your spelling',
                    "couldn't find", "could not find", 'the page you were looking for',
                    'use the navigation', 'explore other pages', 'page does not exist',
                    'this page has been moved', 'page has been removed',
                    'chairman ceo cfo', 'ceo cfo', 'director director',
                    'president vice president', 'corporate secretary',
                    'click here to', 'go back to', 'return to homepage',
                    'sign-up to follow', 'subscribe to', 'newsletter sign up',
                    # Bio indicators
                    'years of experience', 'his career', 'her career', 'his expertise', 'her expertise',
                    'previously served as', 'before joining', 'prior to joining', 'background includes',
                    # Technical/geological content (drill results, resource estimates)
                    'block model', 'exploration target', 'drill program', 'drill hole',
                    'g/t ag', 'g/t au', 'g/t zn', 'g/t cu', 'g/t pb',  # grades
                    'mineral resource', 'ore reserves', 'jorc', 'ni 43-101', 'ni43-101',
                    'inferred resource', 'indicated resource', 'measured resource',
                    'tonnes @', 'mt @', 'zneq', 'aueq', 'ageq', 'cueq',  # equiv grades
                    'omnigeo', 'intercept', 'assay', 'mineralization',
                ]
                if any(ind in desc_lower for ind in garbage_indicators):
                    return False
                # Check if it looks like a list of roles (many job titles)
                role_words = ['ceo', 'cfo', 'coo', 'director', 'president', 'chairman', 'secretary', 'officer']
                role_count = sum(1 for word in role_words if word in desc_lower)
                if role_count >= 3 and len(desc) < 200:
                    return False
                return True

            # Check if current description is already good (from homepage)
            # Don't replace a good homepage description with content from about pages
            # (which often have team/bio mixed in)
            current_desc = self.extracted_data['company'].get('description', '')
            current_is_good = is_valid_description(current_desc) and len(current_desc) > 100

            # Only update description if:
            # 1. We found a valid one AND
            # 2. Either we don't have one OR the new one is significantly better
            if description and is_valid_description(description):
                # If we already have a good description, only replace if new one is much longer
                # and doesn't look like it came from a team page
                if current_is_good:
                    # Only replace if new description is at least 50% longer
                    if len(description) > len(current_desc) * 1.5:
                        self.extracted_data['company']['description'] = description[:1000]
                else:
                    # Current description is missing or garbage, use new one
                    self.extracted_data['company']['description'] = description[:1000]

            # Look for incorporation/founding info
            page_text = soup.get_text()

            # Founded/Incorporated year
            year_patterns = [
                r'(?:founded|incorporated|established|formed)\s+(?:in\s+)?(\d{4})',
                r'since\s+(\d{4})',
            ]
            for pattern in year_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    year = int(match.group(1))
                    if 1900 < year < 2030:
                        self.extracted_data['company']['incorporation_year'] = year
                        break

            # Jurisdiction
            jurisdiction_patterns = [
                r'(?:incorporated|registered)\s+(?:in|under)\s+(?:the\s+)?(?:laws\s+of\s+)?([A-Za-z\s]+?)(?:\.|,|\s+and)',
                r'(?:British Columbia|Ontario|Quebec|Alberta|Nevada|Delaware|Colorado)',
            ]
            for pattern in jurisdiction_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    jurisdiction = match.group(1) if match.lastindex else match.group(0)
                    self.extracted_data['company']['jurisdiction'] = jurisdiction.strip()
                    break

            print(f"[OK] About page scraped: {url}")

        except Exception as e:
            self.errors.append(f"About page error ({url}): {str(e)}")

    async def _scrape_team_page(self, crawler, config, url: str):
        """Scrape team/management page for people info."""
        if url in self.visited_urls:
            return

        try:
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Find team member containers
            member_selectors = [
                '.team-member', '.member', '.person', '.executive',
                '.director', '.management-member', '[class*="team-member"]',
                '[class*="executive"]', '[class*="director"]', '.bio-card'
            ]

            members_found = []

            for selector in member_selectors:
                members = soup.select(selector)
                if members:
                    for member in members:
                        person = self._extract_person_from_element(member, url)
                        if person and person.get('full_name'):
                            members_found.append(person)
                    break

            # If no structured members found, try header-based patterns (h3 name, h4 title)
            if not members_found:
                # Strategy 2: Look for h3/h4 pairs (common pattern: h3=name, h4=title, p=bio)
                headers = soup.find_all('h3')
                for h3 in headers:
                    name = h3.get_text(strip=True)
                    # Skip section headers
                    if not name or len(name) > 80 or len(name) < 4:
                        continue
                    # Skip if it looks like a section title (all caps, ends with common section words)
                    name_lower = name.lower()
                    if any(x in name_lower for x in ['management', 'team', 'directors', 'officers', 'advisory', 'corporate']):
                        continue

                    # Look for title in next h4 sibling
                    title = None
                    next_elem = h3.find_next_sibling()
                    if next_elem and next_elem.name == 'h4':
                        title = next_elem.get_text(strip=True)

                    # Look for bio in following paragraph
                    bio = None
                    for sibling in h3.find_next_siblings(['p'])[:2]:
                        text = sibling.get_text(strip=True)
                        if text and len(text) > 50:
                            bio = text[:1500]
                            break

                    if name and (title or bio):
                        members_found.append({
                            'full_name': name,
                            'title': title or '',
                            'biography': bio or '',
                            'source_url': url,
                            'extracted_at': datetime.utcnow().isoformat(),
                        })

            # If still no members, try text pattern extraction
            if not members_found:
                members_found = self._extract_people_from_text(soup, url)

            # Determine role type based on page URL
            url_lower = url.lower()
            role_type = 'executive'
            if 'board' in url_lower or 'director' in url_lower:
                role_type = 'board_director'
            elif 'technical' in url_lower or 'advisor' in url_lower:
                role_type = 'technical_team'

            for person in members_found:
                if not person.get('role_type'):
                    person['role_type'] = role_type
                self.extracted_data['people'].append(person)

            print(f"[OK] Team page scraped: {len(members_found)} people found")

        except Exception as e:
            self.errors.append(f"Team page error ({url}): {str(e)}")

    def _extract_person_from_element(self, element, source_url: str) -> Optional[Dict]:
        """Extract person info from a team member element."""
        person = {
            'source_url': source_url,
            'extracted_at': datetime.utcnow().isoformat(),
        }

        # Name
        name_selectors = ['h2', 'h3', 'h4', '.name', '.title', '[class*="name"]']
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name and len(name) < 100 and not self._is_title(name):
                    person['full_name'] = name
                    break

        # Title/Position
        title_selectors = ['.position', '.title', '.role', '[class*="position"]', '[class*="title"]', 'p']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and self._is_title(title) and len(title) < 100:
                    person['title'] = title
                    break

        # Photo
        img = element.find('img')
        if img and img.get('src'):
            person['photo_url'] = urljoin(source_url, img['src'])

        # Bio (longer text)
        bio_selectors = ['.bio', '.biography', '.description', 'p']
        for selector in bio_selectors:
            bio_elems = element.select(selector)
            for bio_elem in bio_elems:
                bio = bio_elem.get_text(strip=True)
                if bio and len(bio) > 50 and bio != person.get('title'):
                    person['biography'] = bio[:1500]
                    break
            if person.get('biography'):
                break

        # LinkedIn
        linkedin = element.find('a', href=lambda x: x and 'linkedin.com' in x.lower())
        if linkedin:
            person['linkedin_url'] = linkedin['href']

        return person if person.get('full_name') else None

    def _extract_people_from_text(self, soup, source_url: str) -> List[Dict]:
        """Extract people from page text when structured elements aren't available."""
        people = []

        # Common executive titles
        title_patterns = [
            r'((?:Dr\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})[,\s]+(?:the\s+)?(CEO|CFO|COO|President|Chairman|Director|VP|Vice President|Chief [A-Za-z]+ Officer)',
        ]

        page_text = soup.get_text()
        for pattern in title_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                name, title = match
                if len(name) < 60:
                    people.append({
                        'full_name': name.strip(),
                        'title': title.strip(),
                        'source_url': source_url,
                        'extracted_at': datetime.utcnow().isoformat(),
                    })

        return people

    def _is_title(self, text: str) -> bool:
        """Check if text looks like a job title."""
        title_keywords = [
            'ceo', 'cfo', 'coo', 'president', 'chairman', 'director',
            'vp', 'vice', 'chief', 'officer', 'manager', 'head',
            'executive', 'founder', 'partner', 'advisor', 'geologist',
            'engineer', 'counsel', 'secretary'
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in title_keywords)

    def _is_valid_project_name(self, name: str) -> bool:
        """
        Intelligently validate if a string is a valid project name.
        Returns False for narrative text, taglines, section headers, and generic terms.

        Good project names are typically:
        - Short (1-5 words, usually < 40 characters)
        - Proper nouns (place names, geographic features)
        - End with words like "Project", "Mine", "Property", "Deposit" (optional)

        Bad project names are:
        - Long narrative sentences
        - Taglines/slogans ("Picking Up Where Historic Miners Left Off")
        - Section headers ("Our Projects", "Maps & Sections")
        - Generic descriptive text
        """
        if not name or len(name) < 2:
            return False

        name_lower = name.lower().strip()
        name_stripped = name.strip()

        # ===== LENGTH HEURISTICS =====
        # Real project names are short - typically 1-5 words
        word_count = len(name_stripped.split())
        if word_count > 8:  # More than 8 words is almost certainly narrative
            return False

        # Names over 60 chars are suspicious (unless they're project + location)
        if len(name_stripped) > 60 and word_count > 5:
            return False

        # ===== GENERIC/NAVIGATION TERMS =====
        invalid_exact_names = [
            'deposit', 'mine', 'project', 'property', 'claim', 'prospect',
            'the project', 'the deposit', 'the mine', 'our project', 'our projects',
            'projects', 'properties', 'operations', 'assets', 'home', 'about',
            'about us', 'contact', 'news', 'investors', 'team', 'management',
            'overview', 'gallery', 'maps', 'documents', 'introduction',
            'maps & sections', 'maps and sections', 'photo gallery', 'video gallery',
            'downloads', 'resources', 'media', 'highlights', 'location map',
            # Technical/scientific section names (not actual projects)
            'alteration', 'metallurgy', 'mineralization', 'geological setting',
            'geology', 'geochemistry', 'geophysics', 'stratigraphy', 'structure',
            'technical reports', 'image gallery', 'photo gallery', 'maps & figures',
            'resource', 'resource estimate', 'mineral resource', 'reserves',
            'drilling', 'exploration', 'development', 'production', 'processing',
            'infrastructure', 'environment', 'permitting', 'social', 'sustainability',
            'history', 'project history', 'background', 'corporate', 'summary',
            # Regulatory/legal disclosure sections (not projects)
            'national instrument 43-101', 'ni 43-101', '43-101', 'ni43-101',
            'national instrument 43-101 disclosure', 'ni 43-101 disclosure',
            'qualified person', 'qualified persons', 'qp', 'qp statement',
            'cautionary statement', 'forward-looking statements', 'forward looking',
            'disclaimer', 'legal', 'terms of use', 'privacy policy',
            'technical disclosure', 'mineral resource disclosure',
        ]
        if name_lower in invalid_exact_names:
            return False

        # ===== NARRATIVE/TAGLINE DETECTION =====
        # Taglines often have certain patterns
        narrative_patterns = [
            # Starting with action verbs (tagline indicator)
            r'^(picking|unlocking|discovering|exploring|developing|building|creating|leading|driving)',
            # Starting with gerunds
            r'^(advancing|expanding|growing|transforming|delivering|pursuing)',
            # Promotional phrases
            r'where .* left off', r'the future of', r'premier', r'world-?class',
            r'next generation', r'cutting[- ]edge', r'industry[- ]leading',
            # Descriptive narrative
            r'^a\s+', r'^an\s+', r'^the\s+(?![\w]+\s+(?:project|mine|property|deposit))',
            # Question forms
            r'\?$',
            # Sentences (contains punctuation patterns typical of sentences)
            r'\.\s+[A-Z]',  # Period followed by capital letter (multiple sentences)
        ]
        for pattern in narrative_patterns:
            if re.search(pattern, name_lower):
                return False

        # ===== MEDIA/DOCUMENT CONTENT =====
        media_indicators = [
            'video presentation', 'technical presentation', 'corporate presentation',
            'investor presentation', 'press release', 'news release',
            'annual report', 'quarterly report', 'financial statement',
            'webinar', 'interview', 'pdf', 'download', 'view more', 'read more',
            'click here', 'learn more', 'see details',
        ]
        for indicator in media_indicators:
            if indicator in name_lower:
                return False

        # ===== STRUCTURAL INDICATORS OF BAD NAMES =====
        # Names with "unpatented mining claims" are descriptive text, not project names
        if 'unpatented' in name_lower or 'staked claims' in name_lower:
            return False

        # Names that are mostly lowercase words (proper nouns should be capitalized)
        words = name_stripped.split()
        if len(words) >= 3:
            lowercase_words = [w for w in words if w[0].islower() and w.lower() not in ['the', 'of', 'at', 'in', 'and', 'or', 'for', 'to', 'a', 'an']]
            if len(lowercase_words) >= len(words) * 0.6:  # More than 60% lowercase = likely narrative
                return False

        # ===== GEOCHEMISTRY/SAMPLE DATA (from onboard_company.py) =====
        geochemistry_patterns = [
            r'^\d+\s*[-–]\s*\d+',  # Number ranges like "1-50" or "100-200"
            r'^\d+[a-z]*\s*$',  # Just numbers with optional letter suffix
            r'sample\s*(id|no|number|#)',
            r'\b(au|ag|cu|pb|zn|ni|co)\s*[-–]\s*\d+',
            r'\bsed\s+(au|ag|cu|pb|zn)',
            r'\b(lake|stream|soil|rock)\s+sed\b',
        ]
        for pattern in geochemistry_patterns:
            if re.search(pattern, name_lower):
                return False

        # ===== YEAR-BASED PROGRAM NAMES =====
        # e.g., "2024 Drill Program", "2025 Exploration"
        year_program_pattern = r'^20\d{2}\s+(drill|drilling|exploration|sampling|field)\s*(program|campaign|season)?'
        if re.search(year_program_pattern, name_lower):
            return False

        # ===== POSITIVE INDICATORS (boost confidence) =====
        # Names ending with project-related words are more likely valid
        project_suffixes = ['project', 'mine', 'property', 'deposit', 'prospect', 'claims', 'trend', 'belt', 'district']
        has_project_suffix = any(name_lower.endswith(suffix) for suffix in project_suffixes)

        # Names that look like place names (capitalized proper nouns)
        looks_like_place_name = (
            len(words) >= 1 and
            len(words) <= 4 and
            words[0][0].isupper() and
            len(name_stripped) < 50
        )

        # If it has a project suffix or looks like a place name, it's probably valid
        if has_project_suffix or looks_like_place_name:
            return True

        # For names without clear positive indicators, be more conservative
        # Allow if short and doesn't have negative indicators
        if word_count <= 4 and len(name_stripped) < 40:
            return True

        return False

    async def _scrape_investor_page(self, crawler, config, url: str):
        """Scrape investor relations page for documents and financial info."""
        if url in self.visited_urls:
            return

        try:
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Find all PDF links on this page
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    doc = self._classify_document(link, url)
                    if doc:
                        self.extracted_data['documents'].append(doc)

            # Find and follow sub-pages for presentations, fact sheets, and reports
            sub_page_keywords = [
                'presentation', 'corp-presentation', 'corporate-presentation',
                'fact-sheet', 'factsheet', 'fact_sheet', '1pager', 'one-pager',
                'reports', 'documents', 'filings', 'annual-report'
            ]
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                link_text = link.get_text(strip=True).lower()
                combined = href + ' ' + link_text

                # Check if this links to a sub-page with key documents
                if any(kw in combined for kw in sub_page_keywords):
                    full_url = urljoin(url, link.get('href', ''))
                    if full_url not in self.visited_urls and self.base_url in full_url:
                        await self._scrape_document_subpage(crawler, config, full_url)

            # Look for stock info
            page_text = soup.get_text()

            # Market cap
            market_cap_pattern = r'market\s+cap(?:italization)?[:\s]+\$?([\d,\.]+)\s*(million|billion|M|B)?'
            match = re.search(market_cap_pattern, page_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                multiplier = match.group(2)
                if multiplier and multiplier.lower() in ['million', 'm']:
                    value *= 1_000_000
                elif multiplier and multiplier.lower() in ['billion', 'b']:
                    value *= 1_000_000_000
                self.extracted_data['company']['market_cap_usd'] = value

            # Shares outstanding
            shares_pattern = r'shares\s+outstanding[:\s]+([\d,\.]+)\s*(million|M)?'
            match = re.search(shares_pattern, page_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                if match.group(2):
                    value *= 1_000_000
                self.extracted_data['company']['shares_outstanding'] = int(value)

            print(f"[OK] Investor page scraped: {len(self.extracted_data['documents'])} documents found")

        except Exception as e:
            self.errors.append(f"Investor page error ({url}): {str(e)}")

    async def _scrape_document_subpage(self, crawler, config, url: str):
        """Scrape a sub-page (like /presentations/ or /fact-sheet/) for documents."""
        if url in self.visited_urls:
            return

        try:
            # First, check if this URL serves a PDF directly using requests
            # Some sites serve PDFs from URLs like /1pager/ or /corp-presentation/
            import requests as sync_requests
            try:
                # Validate URL is safe before fetching (SSRF protection)
                if not is_safe_url(url):
                    return

                # Use stream=True to avoid downloading the whole file
                # Use allow_redirects=True to follow redirect URLs like /presentation-link/ -> PDF
                resp = sync_requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=10, allow_redirects=True)
                content_type = resp.headers.get('Content-Type', '').lower()
                final_url = resp.url  # Get final URL after redirects

                # Validate final URL after redirects (SSRF protection)
                if not is_safe_url(final_url):
                    resp.close()
                    return

                # Check if it's a PDF by content-type or by reading first bytes
                is_pdf = 'application/pdf' in content_type
                if not is_pdf and resp.status_code == 200:
                    # Read first few bytes to check for PDF signature
                    first_bytes = resp.raw.read(10)
                    is_pdf = first_bytes.startswith(b'%PDF')
                resp.close()

                if is_pdf:
                    # This URL serves a PDF directly - add it as a document
                    # Use original URL for visited tracking, but final_url for the document
                    self.visited_urls.add(url)
                    self.visited_urls.add(final_url)  # Also mark final URL as visited

                    # Classify based on both original URL and final URL
                    combined_lower = (url + ' ' + final_url).lower()

                    # Determine document type from URL
                    doc_type = 'other'
                    if any(kw in combined_lower for kw in ['presentation', 'corp-presentation', 'corporate-presentation']):
                        doc_type = 'presentation'
                    elif any(kw in combined_lower for kw in ['fact', '1pager', 'one-pager']):
                        doc_type = 'fact_sheet'

                    # Extract title from final URL slug (the actual PDF filename)
                    path = urlparse(final_url).path.rstrip('/')
                    slug = path.split('/')[-1] if path else 'document'
                    # Remove .pdf extension if present
                    if slug.lower().endswith('.pdf'):
                        slug = slug[:-4]
                    title = slug.replace('-', ' ').replace('_', ' ').title()

                    doc = {
                        'source_url': final_url,  # Store actual PDF URL, not redirect URL
                        'title': title,
                        'document_type': doc_type,
                        'extracted_at': datetime.utcnow().isoformat(),
                    }
                    self.extracted_data['documents'].append(doc)
                    print(f"[OK] Direct PDF detected at {final_url}: {title} ({doc_type})")
                    return
            except Exception as pdf_check_error:
                # PDF check failed, continue with regular scraping
                print(f"[DEBUG] PDF check failed for {url}: {pdf_check_error}")

            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Determine the page type from the URL to help with classification
            url_lower = url.lower()
            page_hint = None
            if 'presentation' in url_lower:
                page_hint = 'presentation'
            elif 'fact' in url_lower and 'sheet' in url_lower:
                page_hint = 'fact_sheet'
            elif '1pager' in url_lower or 'one-pager' in url_lower:
                page_hint = 'fact_sheet'

            # Find all PDF links
            docs_found = 0
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    doc = self._classify_document(link, url)
                    if doc:
                        # If the page is specifically for presentations/fact sheets,
                        # override the classification if it was 'other'
                        if page_hint and doc.get('document_type') == 'other':
                            doc['document_type'] = page_hint
                        self.extracted_data['documents'].append(doc)
                        docs_found += 1

            if docs_found > 0:
                print(f"[OK] Document sub-page scraped ({url}): {docs_found} documents found")

        except Exception as e:
            self.errors.append(f"Document sub-page error ({url}): {str(e)}")

    def _classify_document(self, link, source_url: str) -> Optional[Dict]:
        """Classify a document link by type."""
        href = link.get('href', '')
        text = link.get_text(strip=True)
        combined = (text + ' ' + href).lower()

        doc = {
            'source_url': urljoin(source_url, href),
            'title': text or href.split('/')[-1],
            'extracted_at': datetime.utcnow().isoformat(),
        }

        # Classify document type
        if any(kw in combined for kw in ['ni 43-101', 'ni43-101', '43-101', 'technical report']):
            doc['document_type'] = 'ni43101'
        elif any(kw in combined for kw in ['preliminary economic assessment', 'pea report', 'pea study', ' pea ']):
            doc['document_type'] = 'pea'
        elif any(kw in combined for kw in ['presentation', 'corporate presentation', 'corpdeck', 'corp_deck', 'investor deck', 'investor_deck', 'company deck', 'company_deck']):
            doc['document_type'] = 'presentation'
        elif any(kw in combined for kw in ['fact sheet', 'factsheet', 'fact_sheet', 'investor fact']):
            doc['document_type'] = 'fact_sheet'
        elif any(kw in combined for kw in ['annual report', 'annual-report', 'annual_report']):
            doc['document_type'] = 'annual_report'
        elif any(kw in combined for kw in ['quarterly', 'q1 ', 'q2 ', 'q3 ', 'q4 ']):
            doc['document_type'] = 'quarterly_report'
        elif any(kw in combined for kw in ['financial', 'statement']):
            doc['document_type'] = 'financial_report'
        else:
            doc['document_type'] = 'other'

        # Extract year
        year_match = re.search(r'(20\d{2})', combined)
        if year_match:
            doc['year'] = int(year_match.group(1))

        return doc

    async def _scrape_projects_page(self, crawler, config, url: str):
        """Scrape projects/properties page."""
        if url in self.visited_urls:
            return

        try:
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')
            projects_found = []

            # Invalid project names to skip (too generic or just keywords)
            invalid_names = [
                'deposit', 'mine', 'project', 'property', 'claim', 'prospect',
                'the project', 'the deposit', 'the mine', 'our project', 'our projects',
                'projects', 'properties', 'operations', 'assets', 'home', 'about',
                'about us', 'contact', 'news', 'investors', 'team', 'management',
                'overview', 'gallery', 'maps', 'documents', 'introduction'
            ]

            # Keywords that indicate media content, not actual projects
            media_keywords = [
                'video presentation', 'technical presentation', 'corporate presentation',
                'investor presentation', 'press release', 'news release', 'presentation',
                'annual report', 'quarterly report', 'financial statement',
                'technical video', 'webinar', 'interview', 'video', 'pdf', 'download'
            ]

            # Check if this is a specific project page (e.g., /projects/pino-de-plata/)
            # by looking at the URL structure and page content
            url_path = urlparse(url).path.rstrip('/')
            path_parts = [p for p in url_path.split('/') if p]

            # Classic structure: /projects/golden-summit/ (depth 2+, starts with projects)
            is_project_detail_page = (
                len(path_parts) >= 2 and
                path_parts[0] in ['projects', 'project', 'properties', 'property'] and
                path_parts[-1] not in ['projects', 'project', 'properties', 'property']
            )

            # Also detect root-level project pages (e.g., /philadelphia/, /silverton/)
            # These are common when navigation links directly to project pages
            # Check by looking for project-related content in h1/h2 headers
            if not is_project_detail_page and len(path_parts) == 1:
                # Single-segment URL - check if it looks like a project page
                slug = path_parts[0].lower()
                # Skip common non-project pages
                non_project_slugs = {
                    'home', 'about', 'about-us', 'contact', 'contact-us', 'news', 'press',
                    'investor', 'investors', 'team', 'management', 'leadership', 'board',
                    'governance', 'esg', 'sustainability', 'careers', 'subscribe', 'login',
                    'gallery', 'media', 'documents', 'reports', 'corporate', 'highlights',
                    'overview', 'history', 'events', 'calendar', 'mandates', 'shareholder',
                    'shareholders', 'presentations', 'factsheet', 'stock', 'stockinformation',
                    'inthemedia', 'faq', 'privacy', 'terms', 'legal', 'disclaimer'
                }
                if slug not in non_project_slugs:
                    # Check if page has project indicators in title, h1, or h2
                    # Some sites use h2 for main title instead of h1
                    project_indicators = ['property', 'project', 'mine', 'deposit', 'claim',
                                        'exploration', 'mineral', 'prospect', 'gold', 'silver',
                                        'copper', 'zinc', 'nickel', 'lithium']

                    # Check page title first (most reliable indicator)
                    title = soup.find('title')
                    if title:
                        title_text = title.get_text(strip=True).lower()
                        if any(ind in title_text for ind in project_indicators):
                            is_project_detail_page = True

                    # Also check h1/h2 headers
                    if not is_project_detail_page:
                        for header in soup.find_all(['h1', 'h2'])[:3]:
                            header_text = header.get_text(strip=True).lower()
                            if any(ind in header_text for ind in project_indicators):
                                is_project_detail_page = True
                                break

            if is_project_detail_page:
                # This is a specific project page - extract project name from header or URL
                project_name = None
                description = None
                location = None

                # Strategy 1: Look for the main header (h1 or h2) that matches the URL slug
                url_slug = path_parts[-1].replace('-', ' ').replace('_', ' ').lower()
                for header in soup.find_all(['h1', 'h2']):
                    header_text = header.get_text(strip=True)
                    header_lower = header_text.lower().strip()

                    # Use intelligent validation
                    if not self._is_valid_project_name(header_text):
                        continue

                    # Check if header matches URL slug or is a reasonable project name
                    header_normalized = header_lower.replace('-', ' ').replace('_', ' ')
                    if url_slug in header_normalized or header_normalized in url_slug:
                        project_name = header_text
                        break
                    # Also accept if it's the first valid h1 or h2 on a project detail page
                    # (some sites use h2 for main content title)
                    if not project_name and header.name in ['h1', 'h2']:
                        project_name = header_text
                        break

                # Strategy 2: Try to extract project name from page title
                # e.g., "Sycamore Canyon Property – Arizona Gold & Silver" -> "Sycamore Canyon Property"
                # Prefer title if it has a more specific project indicator (Property, Project, Mine)
                title = soup.find('title')
                title_candidate = None
                if title:
                    title_text = title.get_text(strip=True)
                    # Split on common separators: |, –, -, :, —
                    separators = ['|', ' – ', ' - ', ' — ', ': ']
                    for sep in separators:
                        if sep in title_text:
                            parts = title_text.split(sep)
                            # First part is usually the project name
                            candidate = parts[0].strip()
                            if self._is_valid_project_name(candidate) and len(candidate) < 60:
                                title_candidate = candidate
                            break

                # Use title candidate if we don't have a name yet
                if not project_name and title_candidate:
                    project_name = title_candidate
                # Also prefer title candidate if it has more specific project indicators
                elif project_name and title_candidate:
                    title_lower = title_candidate.lower()
                    name_lower = project_name.lower()
                    project_terms = ['property', 'project', 'mine', 'deposit']
                    title_has_term = any(term in title_lower for term in project_terms)
                    name_has_term = any(term in name_lower for term in project_terms)
                    # If title has project term but current name doesn't, prefer title
                    if title_has_term and not name_has_term:
                        project_name = title_candidate

                # Strategy 3: If still no name, derive from URL slug
                if not project_name:
                    slug_name = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                    # Validate the slug-derived name too
                    if self._is_valid_project_name(slug_name):
                        project_name = slug_name

                # Extract description from page content
                # Look for introduction/overview section or first substantial paragraph
                intro_headers = soup.find_all(['h3', 'h4'], string=re.compile(r'introduction|overview|about', re.I))
                if intro_headers:
                    for para in intro_headers[0].find_next_siblings(['p'])[:3]:
                        para_text = para.get_text(strip=True)
                        if para_text and len(para_text) > 50:
                            description = para_text[:1000]
                            break

                if not description:
                    # Find first substantial paragraph after headers
                    main_content = soup.find(['article', 'main', '.content', '.main-content', '[class*="content"]'])
                    search_area = main_content if main_content else soup
                    for para in search_area.find_all('p'):
                        para_text = para.get_text(strip=True)
                        if para_text and len(para_text) > 100:
                            description = para_text[:1000]
                            break

                # Extract location from description or page content
                page_text = soup.get_text()
                locations = [
                    'Canada', 'USA', 'United States', 'Mexico', 'Peru', 'Chile', 'Argentina',
                    'Australia', 'Nevada', 'Ontario', 'Quebec', 'British Columbia', 'Alberta',
                    'Saskatchewan', 'Manitoba', 'Yukon', 'Northwest Territories', 'Nunavut',
                    'Chihuahua', 'Sonora', 'Durango', 'Puebla', 'Oaxaca', 'Guerrero',
                    'Alaska', 'Arizona', 'Colorado', 'Idaho', 'Montana', 'Utah', 'Wyoming'
                ]
                for loc in locations:
                    if loc.lower() in page_text.lower():
                        location = loc
                        break

                # Extract commodity from page content
                commodity = None
                commodities = {
                    'gold': ['gold', 'au ', ' au,', 'gold-'],
                    'silver': ['silver', 'ag ', ' ag,', 'silver-'],
                    'copper': ['copper', 'cu ', ' cu,'],
                    'zinc': ['zinc', 'zn ', ' zn,'],
                    'lead': ['lead', 'pb '],
                    'nickel': ['nickel', 'ni '],
                    'lithium': ['lithium', 'li '],
                    'uranium': ['uranium', ' u ']
                }
                page_lower = page_text.lower()
                for comm, patterns in commodities.items():
                    if any(p in page_lower for p in patterns):
                        commodity = comm
                        break

                # Project name has already been validated, just add it
                if project_name:
                    project = {
                        'name': project_name[:200],
                        'description': description,
                        'location': location,
                        'commodity': commodity,
                        'source_url': url
                    }
                    if not any(p.get('name', '').lower() == project['name'].lower() for p in projects_found):
                        projects_found.append(project)

            else:
                # This is a projects listing/index page - look for project links and containers

                # Strategy 1: Find project containers using CSS selectors
                project_selectors = [
                    '.project', '.property', '[class*="project"]',
                    '[class*="property"]', '.asset', 'article'
                ]

                for selector in project_selectors:
                    projects = soup.select(selector)
                    if projects:
                        for proj in projects:
                            project = self._extract_project_from_element(proj, url)
                            if project and project.get('name'):
                                # Use the new intelligent validation method
                                if self._is_valid_project_name(project['name']):
                                    projects_found.append(project)
                        break

                # Strategy 2: Look for links to project subpages
                # This catches navigation menus with project links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    href_lower = href.lower()
                    text = link.get_text(strip=True)

                    # Links that look like project pages
                    if any(kw in href_lower for kw in ['/project', '/property', '/asset', '/deposit', '/mine']):
                        if text and len(text) > 2 and len(text) < 100:
                            # Use the new intelligent validation method
                            if self._is_valid_project_name(text):
                                # Check URL depth - we only want top-level project pages
                                # e.g., /projects/golden-summit/ is good (depth 2)
                                # but /projects/golden-summit/alteration/ is a sub-section (depth 3)
                                full_url = urljoin(url, href)
                                parsed_href = urlparse(full_url)
                                href_path = parsed_href.path.rstrip('/')
                                href_parts = [p for p in href_path.split('/') if p]

                                # Only accept depth 2 (e.g., /projects/golden-summit)
                                # Skip depth 3+ (e.g., /projects/golden-summit/alteration)
                                if len(href_parts) > 2:
                                    # This is likely a sub-section page, skip it
                                    continue

                                # Avoid adding the current page or parent pages
                                if full_url.rstrip('/') != url.rstrip('/') and url.rstrip('/') in full_url:
                                    project = {
                                        'name': text[:200],
                                        'source_url': full_url
                                    }
                                    if not any(p.get('name', '').lower() == project['name'].lower() for p in projects_found):
                                        projects_found.append(project)

                # Strategy 3: If still no projects, look at headers with project keywords
                if not projects_found:
                    project_keywords = ['deposit', 'mine', 'project', 'property', 'claim', 'prospect']
                    for header in soup.find_all(['h1', 'h2', 'h3']):
                        header_text = header.get_text(strip=True)
                        header_lower = header_text.lower().strip()

                        # Use the new intelligent validation
                        if not self._is_valid_project_name(header_text):
                            continue

                        # Skip all-caps short headers (likely company name)
                        if header_text.isupper() and len(header_text.split()) <= 3:
                            continue

                        if any(kw in header_lower for kw in project_keywords):
                            description = ''
                            for sibling in header.find_next_siblings(['p', 'div'])[:3]:
                                sib_text = sibling.get_text(strip=True)
                                if sib_text and len(sib_text) > 20:
                                    description = sib_text[:500]
                                    break

                            location = None
                            locations = ['Canada', 'USA', 'United States', 'Mexico', 'Peru', 'Chile',
                                        'Australia', 'Nevada', 'Ontario', 'Quebec', 'British Columbia',
                                        'Puebla', 'Sonora', 'Durango', 'Yukon', 'Alaska']
                            combined_text = header_text + ' ' + description
                            for loc in locations:
                                if loc.lower() in combined_text.lower():
                                    location = loc
                                    break

                            project = {
                                'name': header_text[:200],
                                'description': description,
                                'location': location,
                                'source_url': url
                            }

                            if not any(p.get('name', '').lower() == project['name'].lower() for p in projects_found):
                                projects_found.append(project)

            # Add found projects
            self.extracted_data['projects'].extend(projects_found)

            print(f"[OK] Projects page scraped: {len(projects_found)} projects found")

        except Exception as e:
            self.errors.append(f"Projects page error ({url}): {str(e)}")

    def _extract_project_from_element(self, element, source_url: str) -> Optional[Dict]:
        """
        Extract project info from element.
        Uses intelligent heuristics to find the actual project name vs taglines/descriptions.
        """
        project = {'source_url': source_url}

        # ===== NAME EXTRACTION (with intelligent validation) =====
        # Try multiple strategies to find the actual project name
        candidate_names = []

        # Strategy 1: Look for headers with project-specific classes first
        for selector in ['.project-name', '.property-name', '[class*="project-title"]',
                        '[class*="property-title"]', 'h2.name', 'h3.name']:
            name_elem = element.select_one(selector)
            if name_elem:
                text = name_elem.get_text(strip=True)
                if text and self._is_valid_project_name(text):
                    candidate_names.append((text, 3))  # High priority

        # Strategy 2: Check for links that might contain the project name
        # (often the actual name is in the link to the detail page)
        for link in element.select('a[href*="project"], a[href*="property"]'):
            text = link.get_text(strip=True)
            if text and self._is_valid_project_name(text):
                candidate_names.append((text, 2))  # Medium priority
                # Also capture the URL for later
                href = link.get('href', '')
                if href:
                    project['source_url'] = urljoin(source_url, href)

        # Strategy 3: Standard header extraction with validation
        for selector in ['h2', 'h3', 'h4', '.title', '.name']:
            name_elem = element.select_one(selector)
            if name_elem:
                text = name_elem.get_text(strip=True)
                if text and self._is_valid_project_name(text):
                    candidate_names.append((text, 1))  # Lower priority

        # Strategy 4: Derive from URL slug if we have a project detail link
        if project.get('source_url') and 'project' in project['source_url'].lower():
            url_path = urlparse(project['source_url']).path
            parts = [p for p in url_path.split('/') if p]
            if len(parts) >= 2:
                slug = parts[-1].replace('-', ' ').replace('_', ' ').title()
                if self._is_valid_project_name(slug):
                    candidate_names.append((slug, 0))  # Fallback priority

        # Select the best candidate (highest priority, then shortest)
        if candidate_names:
            # Sort by priority (desc) then length (asc) - prefer short, high-priority names
            candidate_names.sort(key=lambda x: (-x[1], len(x[0])))
            project['name'] = candidate_names[0][0]

        # ===== DESCRIPTION EXTRACTION =====
        # Find first substantial paragraph that's not just the project name
        desc_elem = element.select_one('p, .description, .excerpt, .summary')
        if desc_elem:
            desc_text = desc_elem.get_text(strip=True)
            # Make sure description is different from name and substantial
            if desc_text and len(desc_text) > 20 and desc_text != project.get('name'):
                project['description'] = desc_text[:500]

        # ===== LOCATION EXTRACTION =====
        text = element.get_text()
        locations = [
            'Canada', 'USA', 'United States', 'Mexico', 'Peru', 'Chile', 'Argentina',
            'Australia', 'Nevada', 'Ontario', 'Quebec', 'British Columbia', 'Alberta',
            'Saskatchewan', 'Manitoba', 'Yukon', 'Northwest Territories', 'Nunavut',
            'Arizona', 'Colorado', 'Idaho', 'Montana', 'Utah', 'Wyoming', 'Alaska',
            'Sonora', 'Chihuahua', 'Durango', 'Puebla', 'Oaxaca', 'Guerrero',
        ]
        for loc in locations:
            if loc.lower() in text.lower():
                project['location'] = loc
                break

        # ===== COMMODITY EXTRACTION =====
        text_lower = text.lower()
        commodities = {
            'gold': ['gold', ' au ', 'au,', 'au-'],
            'silver': ['silver', ' ag ', 'ag,', 'ag-'],
            'copper': ['copper', ' cu ', 'cu,'],
            'zinc': ['zinc', ' zn ', 'zn,'],
            'lead': ['lead', ' pb '],
            'nickel': ['nickel', ' ni '],
            'lithium': ['lithium', ' li '],
            'uranium': ['uranium'],
            'rare_earths': ['rare earth', 'ree'],
        }
        for comm, patterns in commodities.items():
            if any(p in text_lower for p in patterns):
                project['commodity'] = comm
                break

        return project if project.get('name') else None

    async def _scrape_news_page(self, crawler, config, url: str):
        """Scrape news/press releases page."""
        if url in self.visited_urls:
            return

        try:
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')
            news_found = []

            # Strategy 1: Find news items using various selectors
            # Order matters - put specific semantic elements first, wildcards last
            news_selectors = [
                'article.post', 'article', '.post', '.entry', '.news-item', '.press-release',
                '.news-release', '[class*="news-item"]', '[class*="press-release"]'
            ]

            for selector in news_selectors:
                items = soup.select(selector)
                if items:
                    for item in items[:30]:  # Limit to 30 news items
                        news = self._extract_news_from_element(item, url)
                        if news and news.get('title') and len(news['title']) > 10:
                            news_found.append(news)
                    # Only break if we found meaningful news items
                    if len(news_found) >= 3:
                        break

            # Strategy 2: Handle grid-based news layouts (like Silver Spruce's uk-grid)
            # Look for grids containing date + title + VIEW/PDF links
            if not news_found:
                grids = soup.find_all(class_=re.compile(r'uk-grid|news-row|news-grid'))
                for grid in grids[:50]:  # Limit to 50 grids
                    grid_text = grid.get_text(strip=True)

                    # Skip if no date-like pattern - check multiple formats
                    # Format 1: Month Day, Year (January 8, 2025)
                    date_pattern_long = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
                    # Format 2: MM.DD.YY (12.17.25)
                    date_pattern_dot = r'\d{1,2}\.\d{1,2}\.\d{2}(?!\d)'
                    # Format 3: YYYY-MM-DD
                    date_pattern_iso = r'\d{4}-\d{2}-\d{2}'

                    date_match = re.search(date_pattern_long, grid_text, re.IGNORECASE)
                    date_match_dot = re.search(date_pattern_dot, grid_text)
                    date_match_iso = re.search(date_pattern_iso, grid_text)

                    if not date_match and not date_match_dot and not date_match_iso:
                        continue

                    # Skip if it contains navigation text
                    if any(x in grid_text.lower() for x in ['contact', 'subscribe', 'menu', 'navigation']):
                        continue

                    # Find the date using the matched pattern
                    pub_date = None
                    if date_match:
                        date_str = date_match.group(0)
                        try:
                            pub_date = datetime.strptime(date_str.replace(',', ''), '%B %d %Y').strftime('%Y-%m-%d')
                        except (ValueError, TypeError):
                            pass
                    elif date_match_dot:
                        # Parse MM.DD.YY format
                        date_str = date_match_dot.group(0)
                        parts = date_str.split('.')
                        if len(parts) == 3:
                            month, day, year_short = parts
                            year_int = int(year_short)
                            year = f"20{year_short}" if year_int <= 50 else f"19{year_short}"
                            pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif date_match_iso:
                        pub_date = date_match_iso.group(0)

                    # Find title (usually the longest text that's not date/VIEW/PDF)
                    title = None
                    divs = grid.find_all('div', recursive=False)
                    for div in divs:
                        div_text = div.get_text(strip=True)
                        # Skip date divs, VIEW, PDF
                        if div_text.lower() in ['view', 'pdf', 'download'] or len(div_text) < 20:
                            continue
                        # Skip if text is just a date in any format
                        if re.match(date_pattern_long, div_text, re.IGNORECASE):
                            continue
                        if re.match(r'^\d{1,2}\.\d{1,2}\.\d{2,4}$', div_text):  # MM.DD.YY or MM.DD.YYYY
                            continue
                        if re.match(r'^\d{4}-\d{2}-\d{2}$', div_text):  # YYYY-MM-DD
                            continue
                        if len(div_text) > 20 and len(div_text) < 500:
                            title = div_text
                            break

                    # Find source URL (VIEW or PDF link)
                    source_url = None
                    for link in grid.find_all('a', href=True):
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True).lower()
                        if link_text in ['view', 'pdf', 'read more', 'more']:
                            source_url = urljoin(url, href)
                            break

                    if title and (pub_date or source_url):
                        news = {
                            'title': title,
                            'publication_date': pub_date,
                            'source_url': source_url or url,
                        }
                        # Avoid duplicates
                        if not any(n.get('title', '').lower() == title.lower() for n in news_found):
                            news_found.append(news)

            # Strategy 3: Handle list-based news layouts with PDF links (like Silverco)
            # Look for <li> items containing date + title + PDF link
            if not news_found or len(news_found) < 3:
                list_items = soup.find_all('li')
                for li in list_items[:100]:  # Limit to 100 list items
                    li_text = li.get_text(strip=True)

                    # Skip if too short or no link
                    links = li.find_all('a', href=True)
                    if not links or len(li_text) < 20:
                        continue

                    # Look for MM/DD/YY date format at the start (like "01/06/26")
                    date_match_slash = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})\s*', li_text)

                    pub_date = None
                    title = None
                    source_url = None

                    if date_match_slash:
                        month = date_match_slash.group(1).zfill(2)
                        day = date_match_slash.group(2).zfill(2)
                        year_short = date_match_slash.group(3)
                        year_int = int(year_short)
                        year = f"20{year_short}" if year_int <= 50 else f"19{year_short}"
                        pub_date = f"{year}-{month}-{day}"

                        # Get the title - text after the date
                        remaining_text = li_text[date_match_slash.end():].strip()
                        # Title is usually before any PDF/link markers
                        title = remaining_text

                        # Find the PDF or news link
                        for link in links:
                            href = link.get('href', '')
                            link_text = link.get_text(strip=True)
                            # Prefer links to PDFs or resource files
                            if '.pdf' in href.lower() or '/_resources/' in href.lower():
                                source_url = urljoin(url, href)
                                # The link text is often the title
                                if len(link_text) > 20:
                                    title = link_text
                                break
                            # Or news release URLs
                            elif '/news' in href.lower() or '/release' in href.lower():
                                source_url = urljoin(url, href)
                                if len(link_text) > 20:
                                    title = link_text
                                break

                        # If no source URL found but we have a link, use first meaningful link
                        if not source_url and links:
                            for link in links:
                                href = link.get('href', '')
                                link_text = link.get_text(strip=True)
                                if href and not href.startswith('#') and len(link_text) > 10:
                                    source_url = urljoin(url, href)
                                    title = link_text
                                    break

                    if title and pub_date:
                        # Clean up title - remove common suffixes
                        title = title.strip()
                        if title.lower().endswith(('pdf', '.pdf', 'view', 'read more')):
                            title = title[:-4].strip() if title.lower().endswith('.pdf') else title[:-3].strip()

                        news = {
                            'title': title[:500],
                            'publication_date': pub_date,
                            'source_url': source_url or url,
                            'extracted_at': datetime.utcnow().isoformat(),
                        }
                        # Avoid duplicates
                        if not any(n.get('title', '').lower() == title.lower() for n in news_found):
                            news_found.append(news)

            # Strategy 4: Handle flex-wrap div news layouts (Surge Copper, Freegold Ventures)
            # Pattern: div.flex.flex-wrap containing date div + title link
            # ALWAYS run this strategy - it extracts dates which generic link scan doesn't
            flex_rows = soup.find_all('div', class_=lambda c: c and 'flex' in c and 'flex-wrap' in c)
            for row in flex_rows[:100]:
                row_text = row.get_text(strip=True)

                # Look for "Month Day, Year" date format (e.g., "Nov 19, 2025")
                date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})'
                date_match = re.search(date_pattern, row_text, re.IGNORECASE)

                if not date_match:
                    continue

                # Parse the date
                month_map = {
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                }
                month = month_map.get(date_match.group(1).lower()[:3], '01')
                day = date_match.group(2).zfill(2)
                year = date_match.group(3)
                pub_date = f"{year}-{month}-{day}"

                # Find the news link in this row
                news_link = None
                title = None
                source_url = None

                for link in row.find_all('a', href=True):
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    # Look for links to news articles (news, news-releases, press-releases, etc.)
                    if any(p in href.lower() for p in ['/news', '/press', '/release', '/announcement']) and len(link_text) > 20:
                        title = link_text
                        source_url = urljoin(url, href)
                        break

                if title and pub_date:
                    news = {
                        'title': title[:500],
                        'publication_date': pub_date,
                        'source_url': source_url or url,
                        'extracted_at': datetime.utcnow().isoformat(),
                    }
                    # Avoid duplicates
                    if not any(n.get('title', '').lower() == title.lower() for n in news_found):
                        news_found.append(news)

            # Strategy 5: Elementor-based news pages (Tinka Resources)
            # Pattern: <h2 class="elementor-heading-title">January 23, 2026</h2>
            #          <h2 class="elementor-heading-title"><a href="PDF">Title</a></h2>
            # Date and title are in separate h2 elements with elementor-heading-title class
            elementor_headings = soup.find_all(['h2', 'h3'], class_=lambda c: c and 'elementor-heading-title' in c)
            i = 0
            while i < len(elementor_headings) - 1:
                heading = elementor_headings[i]
                heading_text = heading.get_text(strip=True)

                # Check if this heading contains a date (e.g., "January 23, 2026")
                date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
                date_match = re.match(date_pattern, heading_text, re.IGNORECASE)

                if date_match:
                    # Parse the date
                    month_map = {
                        'january': '01', 'february': '02', 'march': '03', 'april': '04',
                        'may': '05', 'june': '06', 'july': '07', 'august': '08',
                        'september': '09', 'october': '10', 'november': '11', 'december': '12'
                    }
                    month = month_map.get(date_match.group(1).lower(), '01')
                    day = date_match.group(2).zfill(2)
                    year = date_match.group(3)
                    pub_date = f"{year}-{month}-{day}"

                    # Look at next heading for title/link
                    next_heading = elementor_headings[i + 1]
                    title_link = next_heading.find('a', href=True)

                    if title_link:
                        title = title_link.get_text(strip=True)
                        href = title_link.get('href', '')

                        if title and len(title) > 15:
                            news = {
                                'title': title[:500],
                                'publication_date': pub_date,
                                'source_url': urljoin(url, href),
                                'extracted_at': datetime.utcnow().isoformat(),
                            }
                            if not any(n.get('title', '').lower() == title.lower() for n in news_found):
                                news_found.append(news)
                            i += 2  # Skip both date and title headings
                            continue

                i += 1

            # Find news links - look for links that appear to be news items
            # Common patterns: links with dates, links in list items, links with news-like URLs
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                href_lower = href.lower()
                text = link.get_text(strip=True)

                # Skip navigation, form elements, and short text
                if not text or len(text) < 15 or len(text) > 300:
                    continue

                # Skip common non-news patterns
                skip_patterns = ['email', 'subscribe', 'sign up', 'contact', 'login',
                                'register', 'search', 'menu', 'home', 'about']
                if any(p in text.lower() for p in skip_patterns):
                    continue

                # Check if this looks like a news link
                is_news_link = False

                # Pattern 1: URL contains news-related paths
                if any(p in href_lower for p in ['/news', '/press', '/release', '/announcement', '/update']):
                    is_news_link = True

                # Pattern 2: Link text contains a date pattern (e.g., "October 3rd, 2025")
                date_text_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}'
                if re.search(date_text_pattern, text, re.IGNORECASE):
                    is_news_link = True

                # Pattern 3: URL contains date pattern
                if re.search(r'20\d{2}[/-]\d{2}[/-]\d{2}', href):
                    is_news_link = True

                # Pattern 4: Parent element suggests news context
                parent = link.parent
                if parent and parent.name in ['li', 'p', 'div']:
                    parent_text = parent.get_text(strip=True)
                    if re.search(date_text_pattern, parent_text, re.IGNORECASE):
                        is_news_link = True

                if is_news_link:
                    # Get title - try parent element if link text is just a date
                    title = text
                    parent = link.parent
                    if parent and re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}', text, re.IGNORECASE):
                        # Link text is just a date, get title from parent or sibling
                        parent_text = parent.get_text(strip=True)
                        # Remove the date portion to get the headline
                        title_match = re.sub(
                            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\w*,?\s*\d{4}\s*[—–-]*\s*',
                            '', parent_text, flags=re.IGNORECASE
                        ).strip()
                        if title_match and len(title_match) > 10:
                            title = title_match
                        else:
                            # Try next sibling
                            next_sib = link.next_sibling
                            if next_sib and hasattr(next_sib, 'strip'):
                                sib_text = next_sib.strip().lstrip('—–- ')
                                if sib_text and len(sib_text) > 10:
                                    title = sib_text

                    news = {
                        'title': title[:500],  # Truncate to max field length
                        'source_url': urljoin(url, href),
                        'extracted_at': datetime.utcnow().isoformat(),
                    }

                    # Extract date from URL or text
                    month_map = {
                        'january': '01', 'february': '02', 'march': '03', 'april': '04',
                        'may': '05', 'june': '06', 'july': '07', 'august': '08',
                        'september': '09', 'october': '10', 'november': '11', 'december': '12',
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                        'oct': '10', 'nov': '11', 'dec': '12'
                    }

                    # Try ISO format first (2025-10-03)
                    date_match = re.search(r'(20\d{2})[/-](\d{2})[/-](\d{2})', href + text)
                    if date_match:
                        news['publication_date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    else:
                        # Try text date format (October 3rd, 2025)
                        month_match = re.search(
                            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\w*,?\s*(20\d{2})',
                            text, re.IGNORECASE
                        )
                        if month_match:
                            month = month_map.get(month_match.group(1).lower(), '01')
                            day = month_match.group(2).zfill(2)
                            year = month_match.group(3)
                            news['publication_date'] = f"{year}-{month}-{day}"
                        else:
                            # Try abbreviated month with concatenated day/year (Jan262023 or Jan 262023)
                            # This pattern is used by Grizzly Discoveries
                            abbrev_match = re.search(
                                r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})(\d{4})',
                                title, re.IGNORECASE
                            )
                            if abbrev_match:
                                month = month_map.get(abbrev_match.group(1).lower(), '01')
                                day = abbrev_match.group(2).zfill(2)
                                year = abbrev_match.group(3)
                                news['publication_date'] = f"{year}-{month}-{day}"
                                # Also clean up the title by removing the date prefix
                                title = title[abbrev_match.end():].strip()
                                news['title'] = title[:500] if title else news['title']

                    # Avoid duplicates
                    if not any(n.get('source_url') == news['source_url'] for n in news_found):
                        news_found.append(news)

            # Add found news to extracted data - allow more items per page since we want comprehensive coverage
            self.extracted_data['news'].extend(news_found[:100])  # Limit to 100 items per page

            print(f"[OK] News page scraped: {len(news_found)} items found")

        except Exception as e:
            self.errors.append(f"News page error ({url}): {str(e)}")

    def _extract_news_from_element(self, element, source_url: str) -> Optional[Dict]:
        """Extract news item from element."""
        news = {'source_url': source_url, 'extracted_at': datetime.utcnow().isoformat()}

        def is_date_only_title(text: str) -> bool:
            """Check if text is just a date (not a real title)."""
            if not text:
                return True
            text = text.strip()
            # Pattern for "Month Day, Year" format
            date_pattern = re.compile(
                r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$',
                re.IGNORECASE
            )
            if date_pattern.match(text):
                return True
            # Pattern for YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}$', text):
                return True
            # Pattern for MM/DD/YYYY
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', text):
                return True
            return False

        # Title - look for link first, then headers
        # Try multiple selectors in order of preference
        title_selectors = [
            'h2 a', 'h3 a', '.title a', '.entry-title a', 'a[class*="title"]',
            'h2', 'h3', 'h4', '.title', '.entry-title',
            '.elementor-heading-title',  # Elementor sites
            'a'
        ]

        title_elem = None
        title_text = None
        title_url = None

        for selector in title_selectors:
            elem = element.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # Skip date-only titles and try next selector
                if text and len(text) > 10 and not is_date_only_title(text):
                    title_elem = elem
                    title_text = text
                    if elem.name == 'a' and elem.get('href'):
                        title_url = urljoin(source_url, elem['href'])
                    break

        # If still no title, try finding the longest non-date text in links
        if not title_text:
            for link in element.select('a'):
                text = link.get_text(strip=True)
                if text and len(text) > 20 and not is_date_only_title(text):
                    # Skip "Continue Reading", "Read More", etc.
                    if text.lower() not in ['continue reading', 'read more', 'view', 'pdf', 'download']:
                        title_text = text
                        if link.get('href'):
                            title_url = urljoin(source_url, link['href'])
                        break

        if title_text:
            news['title'] = title_text
            if title_url:
                news['source_url'] = title_url

        # Date - try multiple strategies
        pub_date = None

        # Strategy 1: Look for time element with datetime attribute
        time_elem = element.select_one('time[datetime]')
        if time_elem and time_elem.get('datetime'):
            datetime_attr = time_elem.get('datetime')
            # Handle ISO format: 2025-12-18T00:00:00 or 2025-12-18
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_attr)
            if date_match:
                pub_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        # Strategy 2: Look for date elements by class
        if not pub_date:
            date_elem = element.select_one('.date, time, [class*="date"], .meta, .entry-date, span[class*="meta"]')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                pub_date = self._parse_date_text(date_text)

        # Strategy 3: Look for date in the entire element text
        if not pub_date:
            element_text = element.get_text(strip=True)
            pub_date = self._parse_date_text(element_text)

        if pub_date:
            news['publication_date'] = pub_date

        # IMPORTANT: Only return news items that have BOTH a title AND a date
        # News without dates are low quality and should be skipped
        if not news.get('title') or not news.get('publication_date'):
            return None

        return news

    def _parse_date_text(self, text: str) -> Optional[str]:
        """Parse date from text using various formats."""
        if not text:
            return None

        # Format 1: ISO format (2025-12-18)
        date_match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', text)
        if date_match:
            return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        # Format 1.5: MM/DD/YY or MM/DD/YYYY format (01/06/26 or 01/06/2026)
        slash_date = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
        if slash_date:
            month = slash_date.group(1).zfill(2)
            day = slash_date.group(2).zfill(2)
            year_str = slash_date.group(3)
            if len(year_str) == 2:
                year_int = int(year_str)
                year = f"20{year_str}" if year_int <= 50 else f"19{year_str}"
            else:
                year = year_str
            return f"{year}-{month}-{day}"

        # Format 2: Month Day, Year (December 18, 2025)
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
            'oct': '10', 'nov': '11', 'dec': '12'
        }

        month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+(\d{1,2})\w*[.,]?\s+(\d{4})'
        month_match = re.search(month_pattern, text, re.IGNORECASE)
        if month_match:
            month = month_map.get(month_match.group(1).lower(), '01')
            day = month_match.group(2).zfill(2)
            year = month_match.group(3)
            return f"{year}-{month}-{day}"

        # Format 3: Day Month Year (18 December 2025)
        day_first_pattern = r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+(\d{4})'
        day_match = re.search(day_first_pattern, text, re.IGNORECASE)
        if day_match:
            day = day_match.group(1).zfill(2)
            month = month_map.get(day_match.group(2).lower(), '01')
            year = day_match.group(3)
            return f"{year}-{month}-{day}"

        # Format 4: Abbreviated month with concatenated day/year (Jan262023 or Jan 262023)
        # This pattern is used by Grizzly Discoveries
        abbrev_concat_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})(\d{4})'
        abbrev_match = re.search(abbrev_concat_pattern, text, re.IGNORECASE)
        if abbrev_match:
            month = month_map.get(abbrev_match.group(1).lower(), '01')
            day = abbrev_match.group(2).zfill(2)
            year = abbrev_match.group(3)
            return f"{year}-{month}-{day}"

        # Format 5: MM / DD / YYYY with spaces around slashes (11 / 19 / 2024)
        spaced_slash_pattern = r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})'
        spaced_match = re.search(spaced_slash_pattern, text)
        if spaced_match:
            month = spaced_match.group(1).zfill(2)
            day = spaced_match.group(2).zfill(2)
            year = spaced_match.group(3)
            return f"{year}-{month}-{day}"

        # Format 6: MM.DD.YY with dots and 2-digit year (12.17.25)
        # Used by Nobel Resources and some other sites
        dot_short_year_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{2})(?!\d)'
        dot_match = re.search(dot_short_year_pattern, text)
        if dot_match:
            month = dot_match.group(1).zfill(2)
            day = dot_match.group(2).zfill(2)
            year_short = dot_match.group(3)
            # Convert 2-digit year to 4-digit (assume 20xx for years 00-50, 19xx for 51-99)
            year_int = int(year_short)
            year = f"20{year_short}" if year_int <= 50 else f"19{year_short}"
            return f"{year}-{month}-{day}"

        # Format 7: MM.DD.YYYY with dots and 4-digit year (12.17.2025)
        dot_full_year_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        dot_full_match = re.search(dot_full_year_pattern, text)
        if dot_full_match:
            month = dot_full_match.group(1).zfill(2)
            day = dot_full_match.group(2).zfill(2)
            year = dot_full_match.group(3)
            return f"{year}-{month}-{day}"

        return None

    async def _scrape_contact_page(self, crawler, config, url: str):
        """Scrape contact page for address and contact info."""
        if url in self.visited_urls:
            return

        try:
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')
            page_text = soup.get_text()

            # Extract emails from mailto links (more reliable)
            mailto_links = soup.find_all('a', href=lambda x: x and 'mailto:' in x.lower())
            for link in mailto_links:
                href = link.get('href', '')
                email = href.replace('mailto:', '').split('?')[0].strip()
                email_lower = email.lower()
                if 'info@' in email_lower or 'contact@' in email_lower:
                    self.extracted_data['contacts']['general_email'] = email
                elif 'ir@' in email_lower or 'investor' in email_lower:
                    self.extracted_data['contacts']['ir_email'] = email
                elif 'media@' in email_lower or 'press@' in email_lower:
                    self.extracted_data['contacts']['media_email'] = email
                elif not self.extracted_data['contacts'].get('general_email'):
                    # Use the first email found as general contact
                    self.extracted_data['contacts']['general_email'] = email

            # Also try regex extraction for emails in text
            if not self.extracted_data['contacts'].get('general_email'):
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', page_text)
                for email in emails:
                    email_lower = email.lower()
                    # Skip generic web emails
                    if any(x in email_lower for x in ['example.com', 'test.com', 'wix.com', 'wordpress']):
                        continue
                    if 'info@' in email_lower or 'contact@' in email_lower:
                        self.extracted_data['contacts']['general_email'] = email
                    elif 'ir@' in email_lower or 'investor' in email_lower:
                        self.extracted_data['contacts']['ir_email'] = email
                    elif not self.extracted_data['contacts'].get('general_email'):
                        self.extracted_data['contacts']['general_email'] = email

            # Extract phone numbers from tel: links first
            tel_links = soup.find_all('a', href=lambda x: x and 'tel:' in x.lower())
            for link in tel_links:
                href = link.get('href', '')
                phone = href.replace('tel:', '').strip()
                if phone:
                    self.extracted_data['contacts']['phone'] = phone
                    break

            # Fallback: regex for phone numbers
            if not self.extracted_data['contacts'].get('phone'):
                # Look for "Tel:" or "Phone:" followed by number
                phone_match = re.search(r'(?:Tel|Phone|Call)[:\s]+([+\d\s\-\(\)]{10,20})', page_text, re.IGNORECASE)
                if phone_match:
                    self.extracted_data['contacts']['phone'] = phone_match.group(1).strip()
                else:
                    phones = re.findall(r'[\+]?[\d\s\-\(\)]{10,20}', page_text)
                    for phone in phones:
                        # Filter out numbers that are too short or have weird patterns
                        clean = re.sub(r'[\s\-\(\)]', '', phone)
                        if len(clean) >= 10 and len(clean) <= 15:
                            self.extracted_data['contacts']['phone'] = phone.strip()
                            break

            # Extract address
            address_selectors = ['.address', '[class*="address"]', 'address']
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    self.extracted_data['contacts']['address'] = addr_elem.get_text(strip=True)
                    break

            # Extract social media
            self._extract_social_media(soup)

            print(f"[OK] Contact page scraped")

        except Exception as e:
            self.errors.append(f"Contact page error ({url}): {str(e)}")

    def _extract_social_media(self, soup):
        """Extract social media links from page."""
        social_patterns = {
            'linkedin': 'linkedin.com',
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'youtube': 'youtube.com',
        }

        for platform, domain in social_patterns.items():
            link = soup.find('a', href=lambda x: x and domain in x.lower())
            if link:
                self.extracted_data['social_media'][platform] = link['href']

    async def _extract_homepage_documents(self, soup):
        """
        Extract direct document links from homepage (presentations, fact sheets).

        Many mining company homepages have prominent "CORPORATE PRESENTATION" or
        "FACT SHEET" buttons that link directly to PDFs. This captures those documents
        that might otherwise be missed if they're not in a dedicated /investors/ section.
        """
        import requests as sync_requests

        # Keywords that indicate document links worth checking
        doc_keywords = [
            'presentation', 'corporate presentation', 'investor presentation',
            'fact sheet', 'factsheet', 'one-pager', '1-pager',
            'corporate deck', 'investor deck', 'company deck'
        ]

        # Find all links that might be documents
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text(strip=True)
            combined = (href + ' ' + text).lower()

            # Skip if already visited
            full_url = urljoin(self.base_url, href)
            if full_url in self.visited_urls:
                continue

            # Check if this looks like a document link
            is_potential_doc = False
            doc_type = 'other'

            # Direct PDF link
            if '.pdf' in href.lower():
                is_potential_doc = True
                if any(kw in combined for kw in ['presentation', 'deck']):
                    doc_type = 'presentation'
                elif any(kw in combined for kw in ['fact', 'sheet', '1pager', 'one-pager']):
                    doc_type = 'fact_sheet'

            # URL or text contains document keywords (might redirect to PDF)
            elif any(kw in combined for kw in doc_keywords):
                is_potential_doc = True
                if any(kw in combined for kw in ['presentation', 'deck']):
                    doc_type = 'presentation'
                elif any(kw in combined for kw in ['fact', 'sheet', '1pager', 'one-pager']):
                    doc_type = 'fact_sheet'

            if not is_potential_doc:
                continue

            # For non-PDF URLs, check if they serve a PDF
            if '.pdf' not in href.lower():
                try:
                    # Validate URL is safe before fetching (SSRF protection)
                    if not is_safe_url(full_url):
                        continue

                    resp = sync_requests.get(
                        full_url,
                        headers={'User-Agent': 'Mozilla/5.0'},
                        stream=True,
                        timeout=10,
                        allow_redirects=True
                    )
                    content_type = resp.headers.get('Content-Type', '').lower()

                    # Check if it's a PDF
                    is_pdf = 'application/pdf' in content_type
                    if not is_pdf and resp.status_code == 200:
                        first_bytes = resp.raw.read(10)
                        is_pdf = first_bytes.startswith(b'%PDF')

                    # Get final URL after redirects
                    if is_pdf:
                        final_url = resp.url
                        # Validate final URL after redirects (SSRF protection)
                        if not is_safe_url(final_url):
                            resp.close()
                            continue
                        full_url = final_url
                    else:
                        resp.close()
                        continue
                    resp.close()
                except Exception as e:
                    continue

            # Add the document
            self.visited_urls.add(full_url)

            # Generate title from link text or URL
            title = text if text and len(text) > 3 else None
            if not title:
                path = urlparse(full_url).path.rstrip('/')
                slug = path.split('/')[-1].replace('.pdf', '').replace('-', ' ').replace('_', ' ')
                title = slug.title() if slug else 'Corporate Document'

            # Extract year from URL or title
            year = None
            year_match = re.search(r'(20\d{2})', full_url + ' ' + (title or ''))
            if year_match:
                year = int(year_match.group(1))

            doc = {
                'source_url': full_url,
                'title': title,
                'document_type': doc_type,
                'extracted_at': datetime.utcnow().isoformat(),
            }
            if year:
                doc['year'] = year

            self.extracted_data['documents'].append(doc)
            print(f"[HOMEPAGE-DOC] Found {doc_type}: {title} -> {full_url}")

    def _is_internal_link(self, href: str) -> bool:
        """Check if link is internal."""
        if not href:
            return False
        if href.startswith('#') or href.startswith('javascript:'):
            return False
        if href.startswith('/') or href.startswith('./'):
            return True
        parsed = urlparse(href)
        return parsed.netloc == '' or parsed.netloc == self.domain

    def _post_process_data(self):
        """Clean up and deduplicate extracted data."""
        # Remove internal nav links and dropdown project URLs
        self.extracted_data.pop('_nav_links', None)
        self.extracted_data.pop('_nav_dropdown_projects', None)

        # Deduplicate people by name
        seen_names = set()
        unique_people = []
        for person in self.extracted_data['people']:
            name = person.get('full_name', '').lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_people.append(person)
        self.extracted_data['people'] = unique_people

        # Deduplicate documents by URL
        seen_urls = set()
        unique_docs = []
        for doc in self.extracted_data['documents']:
            url = doc.get('source_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_docs.append(doc)
        self.extracted_data['documents'] = unique_docs

        # Deduplicate news by normalized URL and clean titles
        seen_urls = set()
        unique_news = []

        # Month abbreviation map for date parsing
        month_abbr_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }

        for news in self.extracted_data['news']:
            url = news.get('source_url', '')

            # Skip year-archive URLs (e.g., /news-2024, /news-2025)
            if re.search(r'/news-20\d{2}/?$', url):
                continue

            # Normalize URL for deduplication (remove www., trailing slash, lowercase)
            normalized_url = url.replace('www.', '').rstrip('/').lower()

            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            # Clean date prefix from title (e.g., "26Nov" -> "")
            title = news.get('title', '')
            prefix_match = re.match(r'^(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', title, re.IGNORECASE)
            if prefix_match:
                day = prefix_match.group(1).zfill(2)
                month_abbr = prefix_match.group(2).lower()
                month = month_abbr_map.get(month_abbr)

                # Remove prefix from title
                title = re.sub(r'^\d{1,2}(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', '', title, flags=re.IGNORECASE).strip()
                news['title'] = title

                # Extract date if not already set
                if not news.get('publication_date') and month:
                    year_match = re.search(r'(20\d{2})', url)
                    year = year_match.group(1) if year_match else str(datetime.utcnow().year)
                    news['publication_date'] = f"{year}-{month}-{day}"

            if title and len(title) > 10:
                unique_news.append(news)

        self.extracted_data['news'] = unique_news

        # Merge and deduplicate projects by name
        # When we have multiple entries for the same project (from listing + detail pages),
        # merge them keeping the most detailed information
        merged_projects = {}
        for project in self.extracted_data['projects']:
            name = project.get('name', '').strip()
            if not name:
                continue

            name_key = name.lower().replace('-', ' ').replace('_', ' ')

            if name_key in merged_projects:
                # Merge: keep existing data but add new fields if they're missing
                existing = merged_projects[name_key]
                for key, value in project.items():
                    if value and not existing.get(key):
                        existing[key] = value
                    # For description, keep the longer one
                    elif key == 'description' and value:
                        if len(value) > len(existing.get(key, '')):
                            existing[key] = value
            else:
                merged_projects[name_key] = project.copy()

        # Now filter the merged projects
        seen_project_names = set()
        unique_projects = []

        # Invalid patterns for project names
        invalid_patterns = [
            'what makes', 'why', 'how', 'learn more', 'read more', 'click here',
            'view', 'explore', 'discover', 'see our', 'about the',
            # News/update patterns (these indicate news headlines, not project names)
            'update', 'q1 ', 'q2 ', 'q3 ', 'q4 ', 'quarter', 'results',
            'announces', 'reports', 'reported', 'closes', 'completes',
            'intersects', 'intercepts', 'drills', 'returns', 'confirms',
            'discovers', 'identifies', 'receives', 'commences', 'begins',
            'expands', 'extends', 'increases', 'produces', 'achieves',
            # Assay result patterns (e.g., "72.5 gpt Gold")
            ' gpt ', ' g/t ', ' oz/t ', ' ppm ', ' ppb ',
            # Tagline patterns
            'developing', 'advancing', 'building', 'creating', 'delivering',
            'two high-grade', 'district scale', 'historic mining',
            # Navigation/UI elements that get scraped as projects
            'projects map', 'project map', 'property map', 'map of', 'location map',
            'site map', 'interactive map', 'overview map',
            # Resource table headers that aren't projects
            'mineral resource', 'mineral reserve', 'resource estimate',
            'inferred resource', 'indicated resource', 'measured resource',
            'total resources', 'resource table', 'resource summary',
            # Generic navigation items
            'all projects', 'our projects', 'view projects', 'see projects',
            'all properties', 'our properties', 'back to', 'return to',
            # Date/time patterns that indicate news items
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            # Page section names that aren't projects
            'geology and mineralization', 'geology', 'mineralization',
            'photo gallery', 'gallery', 'photos', 'images', 'media',
            'technical reports', 'technical report', 'reports',
            'news releases', 'press releases', 'news', 'press',
            'investor relations', 'investors', 'corporate',
            'about us', 'about', 'overview', 'history', 'team', 'management',
            'contact us', 'contact', 'subscribe', 'sign up',
            'home', 'welcome', 'introduction',
        ]

        # Exact match invalid names (location-only names, generic terms)
        invalid_exact_names = [
            # Locations without project context
            'canada', 'usa', 'united states', 'mexico', 'peru', 'chile', 'australia',
            'nunavut', 'ontario', 'quebec', 'british columbia', 'alberta', 'saskatchewan',
            'manitoba', 'yukon', 'northwest territories', 'newfoundland', 'nova scotia',
            'nevada', 'alaska', 'arizona', 'california', 'colorado', 'idaho', 'montana',
            'oregon', 'utah', 'washington', 'wyoming', 'virginia', 'west virginia',
            # Location patterns like "Nunavut, Canada" or "Virginia, USA"
            'nunavut, canada', 'virginia, usa', 'nevada, usa', 'ontario, canada',
            'quebec, canada', 'british columbia, canada', 'yukon, canada',
            # Generic section names
            'overview', 'summary', 'details', 'information', 'data',
        ]

        for project in merged_projects.values():
            name = project.get('name', '').strip()
            name_lower = name.lower()

            # Skip if name is empty or too short
            if not name or len(name) < 5:
                continue

            # Skip if name is too long (likely a tagline or description)
            if len(name) > 80:
                continue

            # Skip if name matches invalid patterns (questions, CTAs, news titles, taglines)
            if any(pattern in name_lower for pattern in invalid_patterns):
                continue

            # Skip if name exactly matches invalid names (locations, generic terms)
            if name_lower in invalid_exact_names:
                continue

            # Skip if name looks like "Location, Country" pattern (e.g., "Nunavut, Canada")
            if re.match(r'^[A-Za-z\s]+,\s*[A-Za-z\s]+$', name) and len(name) < 30:
                # Check if it's just a location without "project", "property", "mine" etc.
                if not any(kw in name_lower for kw in ['project', 'property', 'mine', 'deposit', 'claim']):
                    continue

            # Skip if name looks like concatenated text (contains "&" followed by uppercase)
            if re.search(r'&[A-Z]', name):
                continue

            # Skip if name looks like a news title (company name followed by colon)
            if re.match(r'^[A-Z][a-z]+\s+(Silver|Gold|Mining|Resources|Corp).*:', name):
                continue

            # Skip if name looks like geochemistry/assay data labels
            # e.g., "Epworth Ag ppm", "Epworth Au ppb", "Epworth Cu pct", "Lake Sed Au Ag"
            geochemistry_patterns = [
                r'\b(ppm|ppb|ppt|g/t|oz/t|pct|%)\b',  # Unit suffixes
                r'\b(au|ag|cu|pb|zn|ni|co|pt|pd|li|u|mo|w|sn|fe|mn|as|sb|bi|cd|hg)\s+(ppm|ppb|ppt|g/t|%|pct)\b',  # Element + unit
                r'\bsed\s+(au|ag|cu|pb|zn)',  # Sediment samples like "Lake Sed Au Ag"
                r'\b(lake|stream|soil|rock)\s+sed\b',  # Sediment sample types
            ]
            if any(re.search(pattern, name_lower) for pattern in geochemistry_patterns):
                continue

            # Skip if already seen (case-insensitive, normalized)
            # Also normalize "The X Project" to "X Project"
            normalized_name = name_lower.replace('-', ' ').replace('_', ' ')
            normalized_name = re.sub(r'^the\s+', '', normalized_name)

            # Remove common suffixes for better deduplication
            # e.g., "True North Complex" and "True North Gold Project" should be considered duplicates
            # Also handles "Ixtaca Gold-Silver Deposit" vs "Ixtaca Gold-Silver Project" vs "Ixtaca Project"
            base_name = normalized_name
            # Order matters - remove longer/more specific suffixes first
            for suffix in [
                # Compound commodity + type suffixes (most specific first)
                ' gold silver deposit', ' gold silver project', ' gold silver property',
                ' gold silver mine', ' gold-silver deposit', ' gold-silver project',
                ' gold-silver property', ' gold-silver mine',
                # Single commodity + type suffixes
                ' gold project', ' gold mine', ' gold deposit', ' gold property',
                ' silver project', ' silver mine', ' silver deposit', ' silver property',
                ' copper project', ' copper mine', ' copper deposit', ' copper property',
                ' zinc project', ' zinc mine', ' zinc deposit', ' zinc property',
                # Generic type suffixes
                ' project', ' property', ' mine', ' deposit', ' complex',
                ' exploration', ' mill', ' tailings', ' underground',
                # Commodity-only suffixes (in case name is like "Ixtaca Gold-Silver")
                ' gold silver', ' gold-silver', ' gold', ' silver', ' copper', ' zinc',
            ]:
                if base_name.endswith(suffix):
                    base_name = base_name[:-len(suffix)]
                    break  # Only remove one suffix to preserve meaningful parts
            base_name = base_name.strip()

            # Check if this base name is already seen (to avoid duplicates like "True North Complex" and "True North Gold Project")
            if normalized_name in seen_project_names or base_name in seen_project_names:
                continue

            # Check if any existing project has a similar base name (fuzzy matching)
            # Be careful: only match if the base names are very similar in length
            # to avoid "philadelphia" matching "72.5 gpt gold reported on the philadelphia"
            is_duplicate = False
            for existing_base in seen_project_names:
                # If one base name contains the other, they might be duplicates
                # e.g., "ixtaca" matches "ixtaca gold silver"
                if base_name and len(base_name) > 4:
                    # Exact match is always a duplicate
                    if base_name == existing_base:
                        is_duplicate = True
                        break
                    # Containment check - but only if lengths are similar (within 2x)
                    # This prevents "philadelphia" matching "72.5 gpt ... philadelphia"
                    if len(existing_base) > 4:
                        len_ratio = max(len(base_name), len(existing_base)) / min(len(base_name), len(existing_base))
                        if len_ratio < 2.5:  # Only check containment if lengths are similar
                            if base_name in existing_base or existing_base in base_name:
                                is_duplicate = True
                                break

            if is_duplicate:
                continue

            seen_project_names.add(normalized_name)
            seen_project_names.add(base_name)  # Also track the base name
            unique_projects.append(project)

        self.extracted_data['projects'] = unique_projects

        # Merge contacts into company
        contacts = self.extracted_data.get('contacts', {})
        if contacts.get('ir_email'):
            self.extracted_data['company']['ir_contact_email'] = contacts['ir_email']
        if contacts.get('general_email'):
            self.extracted_data['company']['general_email'] = contacts['general_email']
        if contacts.get('media_email'):
            self.extracted_data['company']['media_email'] = contacts['media_email']
        if contacts.get('phone'):
            self.extracted_data['company']['general_phone'] = contacts['phone']
        if contacts.get('address'):
            self.extracted_data['company']['street_address'] = contacts['address']

        # Merge social media into company
        social = self.extracted_data.get('social_media', {})
        for platform, url in social.items():
            self.extracted_data['company'][f'{platform}_url'] = url


async def scrape_company_website(url: str, sections: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to scrape a company website.

    Args:
        url: Company website URL
        sections: Sections to scrape (default: all)

    Returns:
        Dictionary with extracted data
    """
    scraper = CompanyDataScraper()
    return await scraper.scrape_company(url, sections=sections)


# For testing
if __name__ == "__main__":
    async def test():
        result = await scrape_company_website("https://www.1911gold.com")
        print("\n" + "=" * 60)
        print("EXTRACTED DATA")
        print("=" * 60)

        company = result['data']['company']
        print(f"\nCompany: {company.get('name')}")
        print(f"Ticker: {company.get('ticker_symbol')} ({company.get('exchange')})")
        print(f"Description: {company.get('description', '')[:200]}...")

        print(f"\nPeople found: {len(result['data']['people'])}")
        for p in result['data']['people'][:5]:
            print(f"  - {p.get('full_name')}: {p.get('title')}")

        print(f"\nDocuments found: {len(result['data']['documents'])}")
        for d in result['data']['documents'][:5]:
            print(f"  - [{d.get('document_type')}] {d.get('title')}")

        print(f"\nNews items: {len(result['data']['news'])}")

        if result['errors']:
            print(f"\nErrors: {len(result['errors'])}")
            for e in result['errors']:
                print(f"  - {e}")

    asyncio.run(test())
