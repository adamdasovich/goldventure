"""
Claude-powered validation for scraped company data.

This module uses Claude to intelligently filter and validate scraped data,
handling edge cases that rule-based systems miss.
"""

import os
import json
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
            'url': item.get('source_url', ''),
            'date': item.get('publication_date', '')
        })

    if not items_to_check:
        return []

    prompt = f"""You are validating scraped news items from {company_name}'s website.

KNOWN INVALID TITLE PATTERNS (from 45+ companies):
- Date-only titles: "January 5, 2026", "December 31, 2025", "2025-12-30", "01/05/2026"
- Generic: "News", "Press Release", "Read More", "Continue Reading", "View", "PDF", "Download"
- Navigation: "News Releases", "Press Releases", "Media", "Recent News"
- Dates with month/day only: "January 5", "Dec 31"

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


def validate_scraped_data(data: Dict, source_url: str) -> Dict:
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
        'recent news', 'latest news', 'media', 'announcement', 'announcements'
    }

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
    from core.models import Company, Project, CompanyNews
    import httpx
    from bs4 import BeautifulSoup

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return {'status': 'error', 'message': f'Company {company_id} not found'}

    # Gather current data
    projects = list(Project.objects.filter(company=company).values('name', 'country', 'primary_commodity'))
    news_count = CompanyNews.objects.filter(company=company).count()

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

    # Fetch the website to compare
    website_content = None
    if company.website:
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = client.get(company.website, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Extract text from main content
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    website_content = soup.get_text(separator=' ', strip=True)[:5000]
        except Exception as e:
            print(f"[VERIFICATION] Could not fetch website: {e}")

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
- News Items: {current_data['news_count']}
- Has Logo: {current_data['has_logo']}

WEBSITE URL: {company.website}

WEBSITE CONTENT (first 5000 chars):
{website_content[:5000] if website_content else 'COULD NOT FETCH'}

VERIFICATION TASK:
1. Check if the DESCRIPTION is present and meaningful. If missing or empty, extract what should be the description from the website content.
2. Check if PROJECTS are complete. Look for project names in the website content that weren't captured.
3. Check if TICKER/EXCHANGE is correct by looking at the website header (often shows "TSX-V: XXX" or similar).
4. Identify any other MISSING DATA that should have been captured.

Respond with JSON only:
{{
  "status": "complete" | "incomplete" | "needs_review",
  "issues": [
    {{"field": "description", "severity": "critical" | "warning", "message": "...", "suggested_value": "..."}}
  ],
  "missing_projects": ["Project Name 1", "Project Name 2"],
  "suggested_description": "..." (only if description is missing),
  "overall_score": 0-100 (completeness percentage)
}}

Be thorough but only flag real issues."""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON
        import re
        if result_text.startswith('{'):
            verification = json.loads(result_text)
        else:
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if match:
                verification = json.loads(match.group())
            else:
                verification = {'status': 'error', 'message': 'Could not parse Claude response'}

        # Auto-fix issues if possible
        fixes_applied = []

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
