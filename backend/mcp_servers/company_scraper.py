"""
Company Auto-Population Scraper
Uses Crawl4AI to automatically extract comprehensive company information from mining company websites.
"""

import asyncio
import re
import sys
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

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

        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )

        crawler_config = CrawlerRunConfig(
            cache_mode="bypass",
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # 1. Scrape homepage first (gets basic info, nav structure)
            if 'homepage' in sections:
                print(f"[SCRAPE] Scraping homepage: {self.base_url}")
                await self._scrape_homepage(crawler, crawler_config)

            # 2. Find and scrape About/Corporate section
            if 'about' in sections or 'team' in sections:
                about_urls = self._find_section_urls(['about', 'corporate', 'company', 'who-we-are'])
                for url in about_urls[:2]:  # Limit to 2 about pages
                    print(f"[SCRAPE] Scraping about page: {url}")
                    await self._scrape_about_page(crawler, crawler_config, url)

            # 3. Find and scrape Team/Management section
            if 'team' in sections:
                team_urls = self._find_section_urls(['team', 'management', 'leadership', 'board', 'directors', 'executives'])
                for url in team_urls[:3]:  # Limit to 3 team pages
                    print(f"[SCRAPE] Scraping team page: {url}")
                    await self._scrape_team_page(crawler, crawler_config, url)

            # 4. Find and scrape Investors section
            if 'investors' in sections:
                investor_urls = self._find_section_urls(['investor', 'shareholders', 'financial', 'reports', 'presentations'])
                for url in investor_urls[:3]:
                    print(f"[SCRAPE] Scraping investor page: {url}")
                    await self._scrape_investor_page(crawler, crawler_config, url)

            # 5. Find and scrape Projects section
            if 'projects' in sections:
                project_urls = self._find_section_urls(['project', 'properties', 'assets', 'operations', 'exploration'])
                for url in project_urls[:3]:
                    print(f"[SCRAPE] Scraping projects page: {url}")
                    await self._scrape_projects_page(crawler, crawler_config, url)

            # 6. Find and scrape News section
            if 'news' in sections:
                news_urls = self._find_section_urls(['news', 'press', 'media', 'releases'])
                for url in news_urls[:2]:
                    print(f"[SCRAPE] Scraping news page: {url}")
                    await self._scrape_news_page(crawler, crawler_config, url)

            # 7. Find and scrape Contact section
            if 'contact' in sections:
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
        for keyword in keywords:
            common_patterns = [
                f"{self.base_url}/{keyword}/",
                f"{self.base_url}/{keyword}",
                f"{self.base_url}/{keyword}s/",
                f"{self.base_url}/{keyword}s",
            ]
            # For news, also add year-specific patterns (current year and previous year)
            if keyword in ['news', 'press']:
                common_patterns.extend([
                    f"{self.base_url}/{keyword}/{keyword}-{current_year}/",
                    f"{self.base_url}/{keyword}/{keyword}-{current_year}",
                    f"{self.base_url}/{keyword}/{current_year}-{keyword}/",
                    f"{self.base_url}/{keyword}/{current_year}-{keyword}",
                ])

            for pattern in common_patterns:
                if pattern not in matching_urls:
                    matching_urls.append(pattern)

        return matching_urls

    async def _scrape_homepage(self, crawler, config):
        """Scrape homepage for basic company info and navigation."""
        try:
            result = await crawler.arun(url=self.base_url, config=config)
            if not result.success:
                self.errors.append(f"Failed to load homepage: {self.base_url}")
                return

            self.visited_urls.add(self.base_url)
            soup = BeautifulSoup(result.html, 'html.parser')

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

            # Extract description from meta tags
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                self.extracted_data['company']['description'] = meta_desc['content']

            # Extract ticker symbol (often in header)
            # Note: Be careful with OTC patterns - "OTCQB" and "OTCQX" are market tiers, not exchanges
            ticker_patterns = [
                # TSX patterns: "TSX: AMM", "TSX-V: AMM", "TSXV: AMM"
                r'\b(TSX[-\s]?V|TSXV)[:\s]+([A-Z]{2,5})\b',
                r'\b(TSX)[:\s]+([A-Z]{2,5})\b',
                # CSE patterns: "CSE: AMM"
                r'\b(CSE)[:\s]+([A-Z]{2,5})\b',
                # ASX/AIM patterns
                r'\b(ASX|AIM)[:\s]+([A-Z]{2,5})\b',
                # OTC patterns - specifically look for OTCQB/OTCQX followed by ticker
                r'\b(?:OTCQB|OTCQX)[:\s]+([A-Z]{3,5})\b',
                # Reverse patterns: "AMM: TSX"
                r'\b([A-Z]{2,5})[:\s]+(TSX[-\s]?V|TSXV|TSX|CSE|ASX|AIM)\b',
            ]
            page_text = soup.get_text()
            for pattern in ticker_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    # Handle OTCQB/OTCQX pattern (only has ticker, no exchange group)
                    if len(groups) == 1:
                        self.extracted_data['company']['ticker_symbol'] = groups[0].upper()
                        self.extracted_data['company']['exchange'] = 'OTC'
                    # Determine which group is exchange vs ticker
                    elif groups[0].upper() in ['TSX', 'TSXV', 'TSX-V', 'TSX V', 'CSE', 'ASX', 'AIM']:
                        exchange = groups[0].upper().replace(' ', '').replace('-', '')
                        if exchange == 'TSXV':
                            exchange = 'TSXV'
                        self.extracted_data['company']['exchange'] = exchange
                        self.extracted_data['company']['ticker_symbol'] = groups[1].upper()
                    else:
                        self.extracted_data['company']['ticker_symbol'] = groups[0].upper()
                        exchange = groups[1].upper().replace(' ', '').replace('-', '')
                        if exchange == 'TSXV':
                            exchange = 'TSXV'
                        self.extracted_data['company']['exchange'] = exchange
                    break

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

            # Extract social media links
            self._extract_social_media(soup)

            # Extract flagship project from homepage (many mining companies feature their main project)
            page_text = soup.get_text()
            project_keywords = ['deposit', 'mine', 'project', 'property']

            # Invalid project names to skip (too generic or just keywords)
            invalid_project_names = [
                'deposit', 'mine', 'project', 'property', 'claim', 'prospect',
                'the project', 'the deposit', 'the mine', 'our project', 'our projects',
                'projects', 'properties', 'operations', 'assets', 'home', 'about',
                'about us', 'contact', 'news', 'investors', 'team', 'management'
            ]

            # Look for project mentions in headers
            for header in soup.find_all(['h1', 'h2', 'h3']):
                header_text = header.get_text(strip=True)
                header_lower = header_text.lower().strip()

                # Skip invalid/generic names
                if header_lower in invalid_project_names or len(header_text) < 5:
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
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return

            self.visited_urls.add(url)
            soup = BeautifulSoup(result.html, 'html.parser')

            # Extract longer description
            content_selectors = [
                'article', '.content', '.main-content', '#content',
                '[class*="about"]', '[class*="corporate"]'
            ]
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Get all paragraphs
                    paragraphs = element.find_all('p')
                    if paragraphs:
                        description = ' '.join(p.get_text(strip=True) for p in paragraphs[:5])
                        if len(description) > len(self.extracted_data['company'].get('description', '')):
                            self.extracted_data['company']['description'] = description[:2000]
                    break

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

            # If no structured members found, try to find names and titles
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

            # Find all PDF links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    doc = self._classify_document(link, url)
                    if doc:
                        self.extracted_data['documents'].append(doc)

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
        elif any(kw in combined for kw in ['presentation', 'corporate presentation']):
            doc['document_type'] = 'presentation'
        elif any(kw in combined for kw in ['fact sheet', 'factsheet']):
            doc['document_type'] = 'fact_sheet'
        elif any(kw in combined for kw in ['annual report', 'annual-report']):
            doc['document_type'] = 'annual_report'
        elif any(kw in combined for kw in ['quarterly', 'q1', 'q2', 'q3', 'q4']):
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

            # Find project containers using CSS selectors
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
                            projects_found.append(project)
                    break

            # If no projects found via CSS, try to extract from page content
            if not projects_found:
                # Look for project names in headers
                headers = soup.find_all(['h1', 'h2', 'h3'])
                page_text = soup.get_text()

                # Mining project keywords that often appear in project names
                project_keywords = ['deposit', 'mine', 'project', 'property', 'claim', 'prospect']

                # Invalid project names to skip (too generic or just keywords)
                invalid_names = [
                    'deposit', 'mine', 'project', 'property', 'claim', 'prospect',
                    'the project', 'the deposit', 'the mine', 'our project', 'our projects',
                    'projects', 'properties', 'operations', 'assets', 'home', 'about',
                    'about us', 'contact', 'news', 'investors', 'team', 'management'
                ]

                for header in headers:
                    header_text = header.get_text(strip=True)
                    header_lower = header_text.lower().strip()

                    # Skip if the header is just a generic keyword or too short
                    if header_lower in invalid_names or len(header_text) < 5:
                        continue

                    # Skip if header looks like company name (all caps, contains "minerals", "mining", "resources")
                    if header_text.isupper() and len(header_text.split()) <= 3:
                        continue

                    # Check if header looks like a project name
                    if any(kw in header_lower for kw in project_keywords):
                        # Get description from following sibling paragraphs
                        description = ''
                        for sibling in header.find_next_siblings(['p', 'div'])[:3]:
                            sib_text = sibling.get_text(strip=True)
                            if sib_text and len(sib_text) > 20:
                                description = sib_text[:500]
                                break

                        # Extract location
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

                        # Avoid duplicates (case-insensitive)
                        if not any(p.get('name', '').lower() == project['name'].lower() for p in projects_found):
                            projects_found.append(project)

                # Also look for links to project subpages
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    text = link.get_text(strip=True)
                    text_lower = text.lower()

                    # Links that look like project pages
                    if any(kw in href for kw in ['/project', '/property', '/asset', '/deposit', '/mine']):
                        if text and len(text) > 5 and len(text) < 100:
                            # Skip navigation items and generic terms
                            if text_lower not in invalid_names and not text.isupper():
                                project = {
                                    'name': text[:200],
                                    'source_url': urljoin(url, link['href'])
                                }
                                if not any(p.get('name', '').lower() == project['name'].lower() for p in projects_found):
                                    projects_found.append(project)

            # Add found projects
            self.extracted_data['projects'].extend(projects_found)

            print(f"[OK] Projects page scraped: {len(projects_found)} projects found")

        except Exception as e:
            self.errors.append(f"Projects page error ({url}): {str(e)}")

    def _extract_project_from_element(self, element, source_url: str) -> Optional[Dict]:
        """Extract project info from element."""
        project = {'source_url': source_url}

        # Name
        name_elem = element.select_one('h2, h3, h4, .title, .name')
        if name_elem:
            project['name'] = name_elem.get_text(strip=True)

        # Description
        desc_elem = element.select_one('p, .description')
        if desc_elem:
            project['description'] = desc_elem.get_text(strip=True)[:500]

        # Location - look for country/region mentions
        text = element.get_text()
        locations = ['Canada', 'USA', 'United States', 'Mexico', 'Peru', 'Chile',
                     'Australia', 'Nevada', 'Ontario', 'Quebec', 'British Columbia']
        for loc in locations:
            if loc.lower() in text.lower():
                project['location'] = loc
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

            # Find news items using various selectors
            news_selectors = [
                '.news-item', '.press-release', '.news', '[class*="news"]',
                '[class*="release"]', 'article', '.post', '.entry'
            ]

            for selector in news_selectors:
                items = soup.select(selector)
                if items:
                    for item in items[:20]:  # Limit to 20 news items
                        news = self._extract_news_from_element(item, url)
                        if news and news.get('title') and len(news['title']) > 10:
                            news_found.append(news)
                    break

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
                            month_map = {'january': '01', 'february': '02', 'march': '03', 'april': '04',
                                        'may': '05', 'june': '06', 'july': '07', 'august': '08',
                                        'september': '09', 'october': '10', 'november': '11', 'december': '12'}
                            month = month_map.get(month_match.group(1).lower(), '01')
                            day = month_match.group(2).zfill(2)
                            year = month_match.group(3)
                            news['publication_date'] = f"{year}-{month}-{day}"

                    # Avoid duplicates
                    if not any(n.get('source_url') == news['source_url'] for n in news_found):
                        news_found.append(news)

            # Add found news to extracted data
            self.extracted_data['news'].extend(news_found[:50])  # Limit to 50 items

            print(f"[OK] News page scraped: {len(news_found)} items found")

        except Exception as e:
            self.errors.append(f"News page error ({url}): {str(e)}")

    def _extract_news_from_element(self, element, source_url: str) -> Optional[Dict]:
        """Extract news item from element."""
        news = {'source_url': source_url, 'extracted_at': datetime.utcnow().isoformat()}

        # Title
        title_elem = element.select_one('h2, h3, h4, .title, a')
        if title_elem:
            news['title'] = title_elem.get_text(strip=True)
            if title_elem.name == 'a' and title_elem.get('href'):
                news['source_url'] = urljoin(source_url, title_elem['href'])

        # Date
        date_elem = element.select_one('.date, time, [class*="date"]')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            date_match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', date_text)
            if date_match:
                news['publication_date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        return news if news.get('title') else None

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

            # Extract emails
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', page_text)
            for email in emails:
                email_lower = email.lower()
                if 'info@' in email_lower or 'contact@' in email_lower:
                    self.extracted_data['contacts']['general_email'] = email
                elif 'ir@' in email_lower or 'investor' in email_lower:
                    self.extracted_data['contacts']['ir_email'] = email
                elif 'media@' in email_lower or 'press@' in email_lower:
                    self.extracted_data['contacts']['media_email'] = email

            # Extract phone numbers
            phones = re.findall(r'[\+]?[\d\s\-\(\)]{10,20}', page_text)
            if phones:
                self.extracted_data['contacts']['phone'] = phones[0].strip()

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
        # Remove internal nav links
        self.extracted_data.pop('_nav_links', None)

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

        # Deduplicate and filter projects by name
        seen_project_names = set()
        unique_projects = []

        # Invalid patterns for project names
        invalid_patterns = [
            'what makes', 'why', 'how', 'learn more', 'read more', 'click here',
            'view', 'explore', 'discover', 'see our', 'about the',
            # News/update patterns
            'update', 'q1 ', 'q2 ', 'q3 ', 'q4 ', 'quarter', 'results',
            'announces', 'reports', 'closes', 'completes',
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

        for project in self.extracted_data['projects']:
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
            is_duplicate = False
            for existing_base in seen_project_names:
                # If one base name contains the other, they're likely duplicates
                # e.g., "ixtaca" matches "ixtaca gold silver"
                if base_name and len(base_name) > 4:
                    # Check if base names match or one contains the other
                    if (base_name == existing_base or
                        (len(existing_base) > 4 and base_name in existing_base) or
                        (len(existing_base) > 4 and existing_base in base_name)):
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
