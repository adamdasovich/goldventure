"""
Claude-powered validation for scraped company data.

This module uses Claude to intelligently filter and validate scraped data,
handling edge cases that rule-based systems miss.
"""

import os
import json
import asyncio
import anthropic
from typing import Dict, List, Optional


def get_claude_client():
    """Get Anthropic client with API key from environment."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def validate_projects_with_claude(projects: List[Dict], company_name: str) -> List[Dict]:
    """
    Use Claude to filter out invalid project names.

    Invalid items include:
    - CTAs and buttons ("Join Us!", "Subscribe Now")
    - Legal/regulatory sections ("National Instrument 43-101", "Qualified Person")
    - Page sections ("Property Access", "Contact Us", "About Us")
    - Geochemistry data labels
    - Navigation items

    Returns only valid mining/exploration projects.
    """
    if not projects:
        return []

    client = get_claude_client()
    if not client:
        # Fallback to basic filtering if no API key
        return _basic_project_filter(projects)

    project_names = [p.get('name', '') for p in projects if p.get('name')]

    if not project_names:
        return []

    prompt = f"""You are analyzing scraped data from a mining company website ({company_name}).

The following items were extracted as potential "projects". Your job is to identify which are REAL mining/exploration projects and which are garbage from the website.

KNOWN INVALID ITEMS (from 45+ companies we've processed):
- CTAs/buttons: "Join Us!", "Subscribe Now", "Join Lafleur Minerals Inc!", "Sign Up", "Learn More", "Click Here", "View More", "Read More"
- Legal/regulatory: "National Instrument 43-101", "NI 43-101 Disclosure", "Qualified Person", "QP Statement", "Cautionary Statement", "Forward-Looking Statements", "Disclaimer", "Technical Disclosure"
- Website sections: "Property Access", "Contact Us", "About Us", "Investors", "Corporate", "News", "Media", "Careers", "Team", "Board of Directors", "Management"
- Navigation: "Home", "Projects", "Exploration", "Resources", "Documents"
- Geology terms (not projects): "Alteration", "Geological Setting", "Mineralization", "Metallurgy", "Stratigraphy", "Lithology", "Structure"
- Geochemistry labels: "Au ppm", "Ag ppb", "Cu pct", anything with ppm/ppb/g/t units
- PDF/document titles: anything ending in ".pdf" or containing "Technical Report", "Presentation"
- Generic: "Overview", "Introduction", "Summary", "Highlights", "Key Facts"

REAL PROJECT CHARACTERISTICS:
- Named after geographic locations (rivers, mountains, lakes, regions, claims)
- Contains: "Mine", "Project", "Property", "Deposit", "Claim", "Belt", "Camp", "District"
- Examples of REAL projects: "Golden Summit Project", "Shorty Creek Project", "O'Brien Gold Project", "Douay Project", "Swanson Gold Deposit", "Beacon Gold Mill"

Items to evaluate:
{json.dumps(project_names, indent=2)}

Return a JSON array containing ONLY the names that are REAL mining/exploration projects. Be strict - when in doubt, exclude it.

Respond with ONLY the JSON array, no explanation:"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON response
        if result_text.startswith('['):
            valid_names = json.loads(result_text)
        else:
            # Try to extract JSON array from response
            import re
            match = re.search(r'\[.*?\]', result_text, re.DOTALL)
            if match:
                valid_names = json.loads(match.group())
            else:
                valid_names = []

        # Filter projects to only include valid names
        valid_names_lower = [n.lower() for n in valid_names]
        return [p for p in projects if p.get('name', '').lower() in valid_names_lower]

    except Exception as e:
        print(f"[CLAUDE VALIDATOR] Error validating projects: {e}")
        return _basic_project_filter(projects)


def validate_news_with_claude(news_items: List[Dict], company_name: str) -> List[Dict]:
    """
    Use Claude to validate and fix news items.

    Issues addressed:
    - Date-only titles ("January 5, 2026")
    - Generic titles ("News", "Press Release")
    - Non-news content

    Returns validated news items with proper titles.
    """
    if not news_items:
        return []

    client = get_claude_client()
    if not client:
        return _basic_news_filter(news_items)

    # Build a list of news items to validate
    items_to_check = []
    for i, item in enumerate(news_items[:50]):  # Limit to 50 items
        items_to_check.append({
            'index': i,
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'date': item.get('release_date', '')
        })

    if not items_to_check:
        return []

    prompt = f"""You are validating scraped news items from {company_name}'s website.

KNOWN INVALID TITLE PATTERNS (from 45+ companies):
- Date-only titles: "January 5, 2026", "December 31, 2025", "2025-12-30", "01/05/2026"
- Generic: "News", "Press Release", "Read More", "Continue Reading", "View", "PDF", "Download"
- Navigation: "News Releases", "Press Releases", "Media", "Recent News"
- Dates with month/day only: "January 5", "Dec 31"
- PDF link text: "View English PDF", "View French PDF", "View PDF", "Download PDF", "Share English PDF by Email"

VALID NEWS HEADLINE CHARACTERISTICS:
- Describes a company announcement, event, or development
- Contains action verbs: "Announces", "Reports", "Closes", "Completes", "Discovers", "Intersects"
- Mentions specific topics: financings, drill results, acquisitions, appointments, etc.
- Examples of VALID headlines:
  - "LaFleur Minerals Closes LIFE, Flow Thru and Final Hard Dollar Offering for $900,000"
  - "Company Announces Drill Results at Golden Summit Project"
  - "CEO Appointed to Board of Directors"
  - "Private Placement Financing Completed"

Items to validate:
{json.dumps(items_to_check, indent=2)}

Return a JSON array of objects with:
- "index": the original index
- "valid": true if the title is a REAL news headline, false if it's a date, generic text, or navigation

Example response:
[{{"index": 0, "valid": true}}, {{"index": 1, "valid": false}}]

Be strict - dates and generic text should be marked invalid.

Respond with ONLY the JSON array:"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON response
        if result_text.startswith('['):
            validations = json.loads(result_text)
        else:
            import re
            match = re.search(r'\[.*?\]', result_text, re.DOTALL)
            if match:
                validations = json.loads(match.group())
            else:
                validations = []

        # Build set of valid indices
        valid_indices = {v['index'] for v in validations if v.get('valid', False)}

        # Filter news items
        return [item for i, item in enumerate(news_items[:50]) if i in valid_indices]

    except Exception as e:
        print(f"[CLAUDE VALIDATOR] Error validating news: {e}")
        return _basic_news_filter(news_items)


def validate_description_with_claude(description: str, company_name: str) -> Optional[str]:
    """
    Use Claude to validate a company description.

    Returns None if the description is invalid (404 page, drill data, etc.)
    Returns the description if it's valid.
    """
    if not description or len(description) < 50:
        return None

    client = get_claude_client()
    if not client:
        return _basic_description_filter(description)

    prompt = f"""You are validating a scraped company description for {company_name}.

Description:
"{description[:1500]}"

KNOWN INVALID DESCRIPTIONS (from 45+ companies):
- 404 error pages: "Page not found", "We couldn't find the page", "Sorry, this page doesn't exist"
- Technical/drill data: Contains specific grades like "25-43Mt @ 1.44-1.57% Zn", "g/t Au", "g/t Ag", "block model", "exploration target", "JORC", "NI 43-101 compliant"
- Legal boilerplate: "Forward-looking statements", "Cautionary statement", "The TSX has not reviewed"
- Navigation/menu text: Lists of page names or section headers
- Team bios: Text that primarily describes executives/directors rather than the company
- Empty/placeholder: "Coming soon", "Under construction", "Description not available"
- Social media snippets: Twitter/LinkedIn post fragments

VALID DESCRIPTION CHARACTERISTICS:
- Explains the company's business focus (exploration, development, production)
- Mentions flagship projects or key properties
- Discusses geographic focus areas (Quebec, Ontario, Alaska, etc.)
- Reads as professional marketing/corporate copy
- Suitable for display on a company profile page

Is this description valid for display as a company profile summary?

Respond with ONLY "valid" or "invalid":"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text.strip().lower()

        if 'valid' in result and 'invalid' not in result:
            return description
        return None

    except Exception as e:
        print(f"[CLAUDE VALIDATOR] Error validating description: {e}")
        return _basic_description_filter(description)


def validate_scraped_data(data: Dict, url: str) -> Dict:
    """
    Validate all scraped data using Claude.

    This is the main entry point that validates:
    - Projects
    - News items
    - Company description

    Returns cleaned data dict.
    """
    company_name = data.get('company', {}).get('name', 'Unknown Company')

    # Validate projects
    original_projects = data.get('projects', [])
    if original_projects:
        validated_projects = validate_projects_with_claude(original_projects, company_name)
        data['projects'] = validated_projects
        print(f"[CLAUDE VALIDATOR] Projects: {len(original_projects)} -> {len(validated_projects)}")

    # Validate news
    original_news = data.get('news', [])
    if original_news:
        validated_news = validate_news_with_claude(original_news, company_name)
        data['news'] = validated_news
        print(f"[CLAUDE VALIDATOR] News: {len(original_news)} -> {len(validated_news)}")

    # Validate description
    description = data.get('company', {}).get('description')
    if description:
        validated_description = validate_description_with_claude(description, company_name)
        if validated_description:
            data['company']['description'] = validated_description
        else:
            data['company']['description'] = ''
            print(f"[CLAUDE VALIDATOR] Description marked as invalid")

    return data


# Fallback filters when Claude API is not available
# These contain all patterns learned from 45+ company onboardings

def _basic_project_filter(projects: List[Dict]) -> List[Dict]:
    """Basic project filtering without Claude - comprehensive patterns."""
    import re

    # All invalid patterns learned from past onboardings
    invalid_exact = {
        # CTAs and buttons
        'join us', 'subscribe', 'sign up', 'contact us', 'about us', 'investors',
        'click here', 'read more', 'learn more', 'view more', 'see more',
        'download', 'view pdf', 'get started', 'register', 'login',
        # Navigation
        'home', 'news', 'media', 'careers', 'team', 'corporate', 'governance',
        'board of directors', 'management', 'documents', 'resources', 'gallery',
        # Legal/regulatory (exact matches)
        'qualified person', 'qp statement', 'cautionary statement', 'disclaimer',
        'forward-looking statements', 'technical disclosure', 'privacy policy',
        'terms of use', 'cookie policy',
        # Website sections
        'property access', 'overview', 'introduction', 'summary', 'highlights',
        'key facts', 'quick facts', 'at a glance',
        # Geology terms (not projects)
        'alteration', 'geological setting', 'mineralization', 'metallurgy',
        'stratigraphy', 'lithology', 'structure', 'geochemistry', 'geophysics',
    }

    invalid_contains = [
        # Regulatory
        'national instrument', 'ni 43-101', 'ni43-101', '43-101 disclosure',
        # Geochemistry units
        'ppm', 'ppb', 'g/t', 'oz/t', 'pct',
        # Document types
        '.pdf', 'technical report', 'presentation', 'fact sheet',
        # CTAs with company name
        'join ',  # "Join Lafleur Minerals Inc!"
    ]

    valid_projects = []
    for p in projects:
        name = p.get('name', '').strip()
        name_lower = name.lower()

        # Skip empty or very short names
        if not name or len(name) < 3:
            continue

        # Check exact matches
        if name_lower in invalid_exact:
            continue

        # Check contains patterns
        if any(pattern in name_lower for pattern in invalid_contains):
            continue

        # Check for geochemistry data patterns (element + unit)
        if re.search(r'\b(au|ag|cu|pb|zn|ni|co|pt|pd|li|u|mo)\s*(ppm|ppb|g/t|pct)\b', name_lower):
            continue

        # Check if it's just punctuation or special chars
        if not re.search(r'[a-zA-Z]{3,}', name):
            continue

        valid_projects.append(p)

    return valid_projects


def _basic_news_filter(news_items: List[Dict]) -> List[Dict]:
    """Basic news filtering without Claude - comprehensive patterns."""
    import re

    # Date-only patterns
    date_patterns = [
        # "January 5, 2026" or "January 5 2026"
        re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$', re.IGNORECASE),
        # "Jan 5, 2026"
        re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}$', re.IGNORECASE),
        # "2026-01-05"
        re.compile(r'^\d{4}-\d{2}-\d{2}$'),
        # "01/05/2026"
        re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$'),
        # "January 5" (no year)
        re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}$', re.IGNORECASE),
    ]

    # Invalid exact titles
    invalid_exact = {
        'news', 'press release', 'press releases', 'news release', 'news releases',
        'read more', 'continue reading', 'view', 'pdf', 'download',
        'recent news', 'latest news', 'media', 'announcement', 'announcements',
        # PDF link text patterns (Globex Mining style)
        'view english pdf', 'view french pdf', 'view pdf', 'download pdf',
        'english pdf', 'french pdf', 'share english pdf', 'share french pdf',
        'share pdf', 'share english pdf by email', 'share french pdf by email',
    }

    # Invalid partial matches - titles containing these are likely garbage
    invalid_partial = [
        'view english', 'view french', 'view pdf', 'share pdf',
        'download pdf', 'click here', 'learn more', 'read full',
    ]

    valid_news = []
    for item in news_items:
        title = item.get('title', '').strip()

        # Skip empty or very short titles
        if not title or len(title) < 15:
            continue

        title_lower = title.lower()

        # Check exact matches
        if title_lower in invalid_exact:
            continue

        # Check partial matches
        if any(partial in title_lower for partial in invalid_partial):
            continue

        # Check date patterns
        is_date = any(pattern.match(title) for pattern in date_patterns)
        if is_date:
            continue

        valid_news.append(item)

    return valid_news


def _basic_description_filter(description: str) -> Optional[str]:
    """Basic description filtering without Claude - comprehensive patterns."""
    if not description or len(description) < 50:
        return None

    desc_lower = description.lower()

    # 404/error page indicators
    error_indicators = [
        'page not found', '404', "couldn't find", "could not find",
        "can't find", "cannot find", 'the page you were looking for',
        'page does not exist', 'page has been moved', 'page has been removed',
        'sorry, this page', 'oops', 'error loading'
    ]

    # Technical/drill data indicators
    technical_indicators = [
        'block model', 'exploration target', 'drill program', 'drill hole',
        'mineral resource', 'ore reserves', 'jorc', 'ni 43-101', 'ni43-101',
        'inferred resource', 'indicated resource', 'measured resource',
        'tonnes @', 'mt @', 'zneq', 'aueq', 'ageq', 'cueq',
        'g/t ag', 'g/t au', 'g/t zn', 'g/t cu', 'g/t pb',
        'omnigeo', 'intercept', 'assay result',
    ]

    # Legal boilerplate
    legal_indicators = [
        'forward-looking statement', 'cautionary statement',
        'the tsx has not reviewed', 'neither tsx venture',
        'this news release is not for distribution'
    ]

    # Navigation/menu text
    nav_indicators = [
        'click here to', 'go back to', 'return to homepage',
        'sign-up to follow', 'subscribe to', 'newsletter sign up',
        'use the navigation', 'explore other pages'
    ]

    # Role lists (often from team pages)
    role_indicators = [
        'chairman ceo cfo', 'ceo cfo', 'director director',
        'president vice president', 'corporate secretary'
    ]

    all_indicators = (
        error_indicators + technical_indicators + legal_indicators +
        nav_indicators + role_indicators
    )

    if any(indicator in desc_lower for indicator in all_indicators):
        return None

    return description


async def _fetch_page_with_playwright(url: str) -> Optional[str]:
    """
    Fetch a page using Playwright via crawl4ai.
    This handles Cloudflare protection and JavaScript-rendered content.
    Includes retry logic for bot challenge pages.
    """
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from bs4 import BeautifulSoup

        # Bot challenge indicators - these indicate the page hasn't fully loaded
        challenge_indicators = [
            'one moment', 'just a moment', 'please wait', 'checking your browser',
            'cloudflare', 'ddos protection', 'attention required', 'robot challenge',
            'checking the site connection', 'enable cookies', 'security check'
        ]

        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # First attempt with standard wait
            config = CrawlerRunConfig(
                cache_mode="bypass",
                delay_before_return_html=5.0,
                page_timeout=60000,
                wait_until='domcontentloaded',
            )

            result = await crawler.arun(url=url, config=config)

            if result and result.html:
                soup = BeautifulSoup(result.html, 'html.parser')
                title = soup.find('title')
                title_text = (title.get_text(strip=True) if title else "").lower()
                body_text = soup.get_text()[:500].lower()

                # Check if we hit a bot challenge page
                is_challenge = any(ind in title_text or ind in body_text for ind in challenge_indicators)

                if is_challenge:
                    print(f"[VERIFICATION] Bot challenge detected for {url}, retrying with longer wait...")
                    await asyncio.sleep(8)  # Wait for challenge to process

                    # Retry with longer delay
                    retry_config = CrawlerRunConfig(
                        cache_mode="bypass",
                        delay_before_return_html=12.0,  # 12 second delay
                        page_timeout=120000,  # 2 minute timeout
                        wait_until='networkidle',  # Wait for all network requests to complete
                    )

                    result = await crawler.arun(url=url, config=retry_config)
                    if result and result.html:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        title = soup.find('title')
                        title_text = (title.get_text(strip=True) if title else "").lower()

                        # If still showing challenge, give up
                        if any(ind in title_text for ind in challenge_indicators):
                            print(f"[VERIFICATION] Could not bypass bot protection for {url}")
                            return None

                # Extract content
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                return soup.get_text(separator=' ', strip=True)[:3000]

    except Exception as e:
        print(f"[VERIFICATION] Playwright fetch failed for {url}: {e}")

    return None


def _fetch_pages_with_playwright(base_url: str) -> tuple:
    """
    Synchronous wrapper to fetch homepage and projects page using Playwright.
    Returns (homepage_content, projects_content).
    """
    from urllib.parse import urljoin

    async def _fetch_all():
        homepage_content = None
        projects_content = None

        # Fetch homepage
        homepage_content = await _fetch_page_with_playwright(base_url)

        # Try projects page URLs
        projects_urls = [
            urljoin(base_url, '/projects/'),
            urljoin(base_url, '/projects'),
            urljoin(base_url, '/properties/'),
            urljoin(base_url, '/properties'),
            urljoin(base_url, '/assets/'),
            urljoin(base_url, '/our-projects/'),
        ]

        for projects_url in projects_urls:
            content = await _fetch_page_with_playwright(projects_url)
            if content and len(content) > 100:
                projects_content = content
                print(f"[VERIFICATION] Found projects page at: {projects_url}")
                break

        return homepage_content, projects_content

    # Run async code in sync context
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already an event loop running (e.g., in Celery),
            # create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _fetch_all())
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(_fetch_all())
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(_fetch_all())
    except Exception as e:
        print(f"[VERIFICATION] Playwright wrapper failed: {e}")
        return None, None


def _extract_tradingview_ticker(website_url: str) -> tuple:
    """
    Extract ticker from TradingView widget on a company website.
    TradingView widgets embed the ticker in formats like:
    - Plain JSON: "symbol": "TSXV:MFG"
    - URL-encoded: %22symbol%22%3A%22TSXV%3AMFG%22

    Returns: (ticker, exchange) or (None, None)
    """
    import re

    async def _fetch_raw_html():
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

            browser_config = BrowserConfig(headless=True, verbose=False)
            async with AsyncWebCrawler(config=browser_config) as crawler:
                config = CrawlerRunConfig(
                    cache_mode="bypass",
                    delay_before_return_html=5.0,
                    page_timeout=60000,
                    wait_until='domcontentloaded',
                )
                result = await crawler.arun(url=website_url, config=config)
                return result.html if result else None
        except Exception as e:
            print(f"[VERIFICATION] Playwright fetch failed for TradingView: {e}")
            return None

    # Get raw HTML using Playwright (httpx gets blocked by captchas)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _fetch_raw_html())
                raw_html = future.result(timeout=90)
        else:
            raw_html = loop.run_until_complete(_fetch_raw_html())
    except RuntimeError:
        raw_html = asyncio.run(_fetch_raw_html())
    except Exception as e:
        print(f"[VERIFICATION] TradingView extraction exception: {e}")
        return None, None

    if not raw_html:
        return None, None

    # TradingView widgets can have ticker in two formats:
    # 1. Plain JSON in script: "symbol": "TSXV:MFG" or "symbol":"TSXV:MFG"
    # 2. URL-encoded in iframe: %22symbol%22%3A%22TSXV%3AMFG%22

    exchange_map = {'TSXV': 'TSXV', 'TSX': 'TSX', 'CSE': 'CSE', 'NEO': 'NEO', 'NYSE': 'NYSE', 'AMEX': 'NYSE'}

    # Pattern 1: Plain JSON format - "symbol": "EXCHANGE:TICKER"
    # Look for TradingView script with symbol
    json_pattern = r'"symbol"\s*:\s*"([A-Z]+):([A-Z]+)"'
    json_matches = re.findall(json_pattern, raw_html, re.IGNORECASE)

    if json_matches:
        for exchange_code, ticker_code in json_matches:
            exchange_code = exchange_code.upper()
            ticker_code = ticker_code.upper()
            if exchange_code in exchange_map and 2 <= len(ticker_code) <= 5:
                print(f"[VERIFICATION] Found TradingView ticker (JSON): {exchange_code}:{ticker_code}")
                return ticker_code, exchange_map[exchange_code]

    # Pattern 2: URL-encoded format - %22symbol%22%3A%22EXCHANGE%3ATICKER%22
    encoded_pattern = r'%22symbol%22%3A%22([A-Z]+)%3A([A-Z]+)%22'
    encoded_matches = re.findall(encoded_pattern, raw_html, re.IGNORECASE)

    if encoded_matches:
        for exchange_code, ticker_code in encoded_matches:
            exchange_code = exchange_code.upper()
            ticker_code = ticker_code.upper()
            if exchange_code in exchange_map and 2 <= len(ticker_code) <= 5:
                print(f"[VERIFICATION] Found TradingView ticker (encoded): {exchange_code}:{ticker_code}")
                return ticker_code, exchange_map[exchange_code]

    return None, None


def verify_onboarded_company(company_id: int) -> Dict:
    """
    Post-save verification of onboarded company data using Claude.

    This function runs AFTER a company is saved to verify:
    1. Description is present and meaningful
    2. Projects were captured (if company has projects)
    3. Key company info is complete (ticker, exchange, etc.)
    4. News items were captured

    Returns a verification report with issues and suggestions.
    """
    from core.models import Company, Project, NewsRelease

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return {'status': 'error', 'message': f'Company {company_id} not found'}

    # Gather current data
    projects = list(Project.objects.filter(company=company).values('name', 'country', 'primary_commodity'))
    news_count = NewsRelease.objects.filter(company=company).count()

    current_data = {
        'name': company.name,
        'ticker': company.ticker_symbol,
        'exchange': company.exchange,
        'description': company.description[:500] if company.description else None,
        'website': company.website,
        'projects_count': len(projects),
        'projects': [p['name'] for p in projects],
        'news_count': news_count,
        'has_logo': bool(company.logo_url),
    }

    # Fetch the website to compare - fetch MULTIPLE pages for complete data
    # Mining companies typically have projects on /projects/, /properties/, or /assets/
    # Use Playwright to handle Cloudflare-protected sites (httpx fails on these)
    website_content = None
    projects_content = None
    extracted_ticker = None
    extracted_exchange = None

    if company.website:
        print(f"[VERIFICATION] Fetching pages with Playwright for {company.website}...")
        website_content, projects_content = _fetch_pages_with_playwright(company.website)

        if website_content:
            print(f"[VERIFICATION] Homepage content fetched: {len(website_content)} chars")
        else:
            print(f"[VERIFICATION] Warning: Could not fetch homepage")

        if projects_content:
            print(f"[VERIFICATION] Projects page content fetched: {len(projects_content)} chars")
        else:
            print(f"[VERIFICATION] Warning: No projects page found")

        # Try to extract ticker from TradingView widget (if ticker is missing)
        if not current_data['ticker']:
            extracted_ticker, extracted_exchange = _extract_tradingview_ticker(company.website)
            if extracted_ticker:
                print(f"[VERIFICATION] Found TradingView ticker: {extracted_exchange}:{extracted_ticker}")

    # Use Claude to verify
    client = get_claude_client()
    if not client:
        # Basic verification without Claude
        return _basic_verification(current_data)

    prompt = f"""You are verifying onboarded company data for a mining intelligence platform.

COMPANY DATA SAVED:
- Name: {current_data['name']}
- Ticker: {current_data['ticker'] or 'NOT CAPTURED'}
- Exchange: {current_data['exchange'] or 'NOT CAPTURED'}
- Description: {current_data['description'] or 'NOT CAPTURED'}
- Projects: {current_data['projects_count']} projects: {', '.join(current_data['projects']) if current_data['projects'] else 'NONE'}
- News Items: {current_data['news_count']} {'(CRITICAL: NO NEWS CAPTURED!)' if current_data['news_count'] == 0 else ''}
- Has Logo: {current_data['has_logo']}

WEBSITE URL: {company.website}

HOMEPAGE CONTENT:
{website_content[:3000] if website_content else 'COULD NOT FETCH'}

PROJECTS PAGE CONTENT (from /projects/ or similar):
{projects_content[:3000] if projects_content else 'NO PROJECTS PAGE FOUND - check homepage for project mentions'}

VERIFICATION TASK:
1. Check if the DESCRIPTION is present and meaningful. If missing or empty, extract what should be the description from the website content.

2. **CRITICAL FOR PROJECTS**:
   - The saved data shows {current_data['projects_count']} projects
   - Look in BOTH the homepage AND the projects page content for project names
   - If you find ANY projects on the website that are NOT in the saved data, you MUST add them to "missing_projects"
   - IMPORTANT: If projects_count is 0 and you find projects on the website, ALL those projects should go in "missing_projects"
   - Extract project names like "La Plata", "Keno Silver", "Black Pine", etc.

3. Check if TICKER/EXCHANGE is correct by looking at the website header (often shows "TSX-V: XXX" or "TSX: XXX").
   IMPORTANT: Canadian companies often have BOTH TSX and NYSE/OTC tickers. Always use the PRIMARY TSX/TSX-V ticker, not the US secondary ticker.

4. **CRITICAL**: If News Items is 0, this is a MAJOR issue - flag it as critical severity with field "news".

5. Identify any other MISSING DATA that should have been captured.

Respond with JSON only:
{{
  "status": "complete" | "incomplete" | "needs_review",
  "issues": [
    {{"field": "projects", "severity": "critical", "message": "0 projects captured but website shows X projects"}}
  ],
  "missing_projects": ["Project Name 1", "Project Name 2"],
  "suggested_description": "..." (only if description is missing or poor),
  "suggested_ticker": "..." (only if ticker appears wrong or missing),
  "overall_score": 0-100 (completeness percentage - should be LOW if projects are missing!)
}}

IMPORTANT: If saved projects count is 0 but you find projects on the website, put ALL found projects in "missing_projects" and set status to "incomplete"."""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON - extract the JSON object even if there's extra text
        import re

        # Find the first complete JSON object (handles nested braces)
        def extract_json(text):
            start = text.find('{')
            if start == -1:
                return None
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
            return None

        json_str = extract_json(result_text)
        if json_str:
            try:
                verification = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"[VERIFICATION] JSON parse error: {e}")
                verification = {'status': 'error', 'message': f'JSON parse error: {e}'}
        else:
            verification = {'status': 'error', 'message': 'Could not find JSON in Claude response'}

        # Auto-fix issues if possible
        fixes_applied = []

        # Fix missing ticker from TradingView extraction (takes precedence over Claude suggestion)
        if extracted_ticker and not current_data['ticker']:
            company.ticker_symbol = extracted_ticker
            if extracted_exchange:
                company.exchange = extracted_exchange
                company.save(update_fields=['ticker_symbol', 'exchange'])
                fixes_applied.append(f'Added ticker from TradingView: {extracted_exchange}:{extracted_ticker}')
                print(f"[VERIFICATION] Auto-fixed: Ticker {extracted_exchange}:{extracted_ticker} for {company.name}")
            else:
                company.save(update_fields=['ticker_symbol'])
                fixes_applied.append(f'Added ticker from TradingView: {extracted_ticker}')
                print(f"[VERIFICATION] Auto-fixed: Ticker {extracted_ticker} for {company.name}")

        # Fix missing description
        if verification.get('suggested_description') and not current_data['description']:
            company.description = verification['suggested_description'][:1000]
            company.save(update_fields=['description'])
            fixes_applied.append('Added missing description')
            print(f"[VERIFICATION] Auto-fixed: Added description for {company.name}")

        # Add missing projects
        missing_projects = verification.get('missing_projects', [])
        for project_name in missing_projects[:5]:  # Limit to 5 auto-adds
            if project_name and len(project_name) > 2:
                # Check if project already exists
                if not Project.objects.filter(company=company, name__iexact=project_name).exists():
                    Project.objects.create(
                        company=company,
                        name=project_name,
                        project_stage='exploration',
                    )
                    fixes_applied.append(f'Added project: {project_name}')
                    print(f"[VERIFICATION] Auto-fixed: Added project '{project_name}' for {company.name}")

        # Fix ticker if suggested and different (only if not already fixed by TradingView extraction)
        suggested_ticker = verification.get('suggested_ticker')
        if suggested_ticker and suggested_ticker != current_data['ticker'] and not extracted_ticker:
            old_ticker = company.ticker_symbol
            company.ticker_symbol = suggested_ticker
            company.save(update_fields=['ticker_symbol'])
            fixes_applied.append(f'Fixed ticker: {old_ticker} -> {suggested_ticker}')
            print(f"[VERIFICATION] Auto-fixed: Ticker {old_ticker} -> {suggested_ticker} for {company.name}")

        # Trigger news scrape if no news captured
        if current_data['news_count'] == 0:
            try:
                from core.tasks import scrape_company_news_task
                scrape_company_news_task.delay(company.id)
                fixes_applied.append('Triggered news scrape (0 news items found)')
                print(f"[VERIFICATION] Auto-triggered news scrape for {company.name} (0 news)")
            except Exception as e:
                print(f"[VERIFICATION] Could not trigger news scrape: {e}")

        # Clean up duplicate news items (e.g., same news with different URL paths)
        if current_data['news_count'] > 0:
            cleanup_result = cleanup_duplicate_news(company_id)
            if cleanup_result.get('removed', 0) > 0:
                fixes_applied.append(f"Removed {cleanup_result['removed']} duplicate news items")
                print(f"[VERIFICATION] Cleaned up {cleanup_result['removed']} duplicate news for {company.name}")

        verification['fixes_applied'] = fixes_applied
        verification['company_id'] = company_id
        verification['company_name'] = company.name

        # Log the verification result
        _log_verification_result(company, verification)

        return verification

    except Exception as e:
        print(f"[VERIFICATION] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e), 'company_id': company_id}


def _basic_verification(current_data: Dict) -> Dict:
    """Basic verification without Claude API."""
    issues = []

    if not current_data['description']:
        issues.append({
            'field': 'description',
            'severity': 'critical',
            'message': 'No company description captured'
        })

    if not current_data['ticker']:
        issues.append({
            'field': 'ticker',
            'severity': 'warning',
            'message': 'No ticker symbol captured'
        })

    if current_data['projects_count'] == 0:
        issues.append({
            'field': 'projects',
            'severity': 'warning',
            'message': 'No projects captured'
        })

    if current_data['news_count'] == 0:
        issues.append({
            'field': 'news',
            'severity': 'warning',
            'message': 'No news items captured'
        })

    # Calculate score
    score = 100
    for issue in issues:
        if issue['severity'] == 'critical':
            score -= 25
        else:
            score -= 10

    status = 'complete' if not issues else ('needs_review' if any(i['severity'] == 'critical' for i in issues) else 'incomplete')

    return {
        'status': status,
        'issues': issues,
        'overall_score': max(0, score),
        'missing_projects': [],
        'fixes_applied': []
    }


def _log_verification_result(company, verification: Dict):
    """Log verification results for review."""
    from core.models import CompanyVerificationLog

    try:
        CompanyVerificationLog.objects.create(
            company=company,
            status=verification.get('status', 'unknown'),
            overall_score=verification.get('overall_score', 0),
            issues=verification.get('issues', []),
            fixes_applied=verification.get('fixes_applied', []),
        )
    except Exception as e:
        # Model might not exist yet, just log to console
        print(f"[VERIFICATION] Result for {company.name}: {verification.get('status')} (score: {verification.get('overall_score', 0)})")
        if verification.get('issues'):
            for issue in verification['issues']:
                print(f"  - [{issue.get('severity', 'info')}] {issue.get('field')}: {issue.get('message')}")
        if verification.get('fixes_applied'):
            for fix in verification['fixes_applied']:
                print(f"  - [FIXED] {fix}")


def _extract_url_slug(url: str) -> str:
    """Extract the meaningful slug from a news URL."""
    clean_url = url.split('?')[0].rstrip('/')
    parts = clean_url.split('/')
    slug = parts[-1] if parts else ''
    if slug.isdigit() and len(slug) == 4 and len(parts) > 1:
        slug = parts[-2]
    return slug.lower()


def cleanup_duplicate_news(company_id: int) -> Dict:
    """
    Detect and remove duplicate news items for a company.

    Duplicates are identified by:
    1. Same URL slug (e.g., /news/article vs /news/2026/article)
    2. Same title + date combination

    Returns a report of what was cleaned up.
    """
    from core.models import Company, NewsRelease

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return {'status': 'error', 'message': f'Company {company_id} not found'}

    news_items = list(NewsRelease.objects.filter(company=company))

    if not news_items:
        return {'status': 'ok', 'message': 'No news items to clean', 'removed': 0}

    # Track duplicates by slug
    slug_to_news = {}  # Map slug -> list of news items
    for news in news_items:
        slug = _extract_url_slug(news.url)
        if slug and len(slug) > 10:  # Only meaningful slugs
            if slug not in slug_to_news:
                slug_to_news[slug] = []
            slug_to_news[slug].append(news)

    # Also track by title+date
    title_date_to_news = {}
    for news in news_items:
        key = f"{news.title.lower().strip()}|{news.release_date}"
        if key not in title_date_to_news:
            title_date_to_news[key] = []
        title_date_to_news[key].append(news)

    # Find and remove duplicates
    to_delete = set()

    # Remove slug duplicates (keep the one with shortest URL path - usually canonical)
    for slug, items in slug_to_news.items():
        if len(items) > 1:
            # Sort by URL depth (fewer slashes = more canonical)
            items.sort(key=lambda x: x.url.count('/'))
            # Keep first, delete rest
            for item in items[1:]:
                to_delete.add(item.id)

    # Remove title+date duplicates that weren't caught by slug
    for key, items in title_date_to_news.items():
        remaining = [i for i in items if i.id not in to_delete]
        if len(remaining) > 1:
            # Keep one, delete rest
            for item in remaining[1:]:
                to_delete.add(item.id)

    # Delete duplicates
    if to_delete:
        deleted_count = NewsRelease.objects.filter(id__in=to_delete).delete()[0]
        print(f"[CLEANUP] Removed {deleted_count} duplicate news items for {company.name}")
        return {
            'status': 'cleaned',
            'company_id': company_id,
            'company_name': company.name,
            'removed': deleted_count,
            'remaining': len(news_items) - deleted_count,
            'message': f'Removed {deleted_count} duplicate news items'
        }

    return {
        'status': 'ok',
        'company_id': company_id,
        'company_name': company.name,
        'removed': 0,
        'remaining': len(news_items),
        'message': 'No duplicates found'
    }
