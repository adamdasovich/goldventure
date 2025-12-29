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
        for keyword in keywords:
            common_patterns = [
                f"{self.base_url}/{keyword}/",
                f"{self.base_url}/{keyword}",
                f"{self.base_url}/{keyword}s/",
                f"{self.base_url}/{keyword}s",
            ]
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
            ticker_patterns = [
                r'\b(TSX[V]?|TSXV|CSE|OTC|ASX|AIM)[:\s-]*([A-Z]{2,5})\b',
                r'\b([A-Z]{2,5})[:\s-]*(TSX[V]?|TSXV|CSE|OTC|ASX|AIM)\b',
            ]
            page_text = soup.get_text()
            for pattern in ticker_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    # Determine which group is exchange vs ticker
                    if groups[0].upper() in ['TSX', 'TSXV', 'CSE', 'OTC', 'ASX', 'AIM']:
                        self.extracted_data['company']['exchange'] = groups[0].upper()
                        self.extracted_data['company']['ticker_symbol'] = groups[1].upper()
                    else:
                        self.extracted_data['company']['ticker_symbol'] = groups[0].upper()
                        self.extracted_data['company']['exchange'] = groups[1].upper()
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

            # Find project containers
            project_selectors = [
                '.project', '.property', '[class*="project"]',
                '[class*="property"]', '.asset'
            ]

            for selector in project_selectors:
                projects = soup.select(selector)
                if projects:
                    for proj in projects:
                        project = self._extract_project_from_element(proj, url)
                        if project and project.get('name'):
                            self.extracted_data['projects'].append(project)
                    break

            print(f"[OK] Projects page scraped: {len(self.extracted_data['projects'])} projects found")

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

            # Find news items
            news_selectors = [
                '.news-item', '.press-release', '.news', '[class*="news"]',
                '[class*="release"]', 'article'
            ]

            for selector in news_selectors:
                items = soup.select(selector)
                if items:
                    for item in items[:20]:  # Limit to 20 news items
                        news = self._extract_news_from_element(item, url)
                        if news and news.get('title'):
                            self.extracted_data['news'].append(news)
                    break

            # Also find news links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text(strip=True)
                if ('/news/' in href or '/press' in href) and text and len(text) > 20:
                    news = {
                        'title': text,
                        'source_url': urljoin(url, link['href']),
                        'extracted_at': datetime.utcnow().isoformat(),
                    }
                    # Extract date from URL or text
                    date_match = re.search(r'(20\d{2})[/-](\d{2})[/-](\d{2})', href + text)
                    if date_match:
                        news['publication_date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    self.extracted_data['news'].append(news)

            print(f"[OK] News page scraped: {len(self.extracted_data['news'])} items found")

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

        # Deduplicate news by title
        seen_titles = set()
        unique_news = []
        for news in self.extracted_data['news']:
            title = news.get('title', '').lower()[:50]
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        self.extracted_data['news'] = unique_news

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
