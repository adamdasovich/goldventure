"""
Management command to automatically onboard a company by scraping its website.
Uses Crawl4AI to extract company information and populate the database.

Usage:
    python manage.py onboard_company https://www.companywebsite.com
    python manage.py onboard_company https://www.companywebsite.com --dry-run
    python manage.py onboard_company --batch companies.txt
"""

import asyncio
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import (
    Company, Project, CompanyPerson, CompanyDocument,
    CompanyNews, ScrapingJob, FailedCompanyDiscovery, User
)


class Command(BaseCommand):
    help = 'Automatically onboard a company by scraping its website'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            nargs='?',
            type=str,
            help='Company website URL to scrape'
        )
        parser.add_argument(
            '--batch',
            type=str,
            help='Path to file with list of URLs (one per line)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Scrape and show data without saving to database'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing company if found (by ticker or name)'
        )
        parser.add_argument(
            '--sections',
            type=str,
            default='all',
            help='Sections to scrape: all, homepage, about, team, investors, projects, news, contact (comma-separated)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to associate with this scraping job'
        )

    def handle(self, *args, **options):
        url = options.get('url')
        batch_file = options.get('batch')
        dry_run = options.get('dry_run')

        if not url and not batch_file:
            raise CommandError('Please provide a URL or --batch file')

        if batch_file:
            urls = self._load_batch_file(batch_file)
            self.stdout.write(f"Processing {len(urls)} companies from batch file...")
            for i, url in enumerate(urls, 1):
                self.stdout.write(f"\n[{i}/{len(urls)}] Processing: {url}")
                try:
                    asyncio.run(self._process_company(url, options))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed: {str(e)}"))
        else:
            asyncio.run(self._process_company(url, options))

    def _load_batch_file(self, filepath):
        """Load URLs from a batch file."""
        urls = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
        return urls

    def _infer_commodity_from_name(self, name: str) -> str:
        """
        Infer the primary commodity from a project name.
        Looks for commodity keywords in the name and returns the appropriate commodity code.
        Defaults to 'gold' if no commodity is detected.
        """
        name_lower = name.lower()

        # Check for specific commodities in order of specificity
        # Check compound commodities first
        if 'gold-silver' in name_lower or 'gold silver' in name_lower:
            return 'gold'  # Gold-silver projects typically listed as gold primary
        if 'silver-gold' in name_lower or 'silver gold' in name_lower:
            return 'silver'

        # Check individual commodities
        if 'silver' in name_lower:
            return 'silver'
        if 'copper' in name_lower:
            return 'copper'
        if 'zinc' in name_lower:
            return 'zinc'
        if 'nickel' in name_lower:
            return 'nickel'
        if 'lithium' in name_lower:
            return 'lithium'
        if 'uranium' in name_lower:
            return 'uranium'
        if 'cobalt' in name_lower:
            return 'cobalt'
        if 'platinum' in name_lower or 'palladium' in name_lower or 'pgm' in name_lower:
            return 'pgm'
        if 'rare earth' in name_lower or 'ree' in name_lower:
            return 'ree'
        if 'base metal' in name_lower:
            return 'base metals'
        if 'gold' in name_lower:
            return 'gold'

        # Default to gold for mining companies
        return 'gold'

    def _infer_project_stage_from_name(self, name: str) -> str:
        """
        Infer the project stage from a project name.
        Looks for stage-related keywords in the name.
        Defaults to 'early_exploration' if no stage is detected.
        """
        name_lower = name.lower()

        # Production/Operating indicators
        if any(kw in name_lower for kw in ['mine', 'operation', 'operating', 'producer', 'producing', 'mill']):
            return 'production'

        # Development indicators
        if any(kw in name_lower for kw in ['development', 'construction', 'building']):
            return 'development'

        # Permitting indicators
        if any(kw in name_lower for kw in ['permitting', 'permitted']):
            return 'permitting'

        # Feasibility indicators
        if any(kw in name_lower for kw in ['feasibility', 'fs ']):
            return 'fs'

        # PFS indicators
        if 'pfs' in name_lower or 'pre-feasibility' in name_lower or 'prefeasibility' in name_lower:
            return 'pfs'

        # PEA indicators
        if 'pea' in name_lower or 'preliminary economic' in name_lower:
            return 'pea'

        # Resource stage indicators
        if any(kw in name_lower for kw in ['resource', 'deposit']):
            return 'resource'

        # Advanced exploration indicators
        if any(kw in name_lower for kw in ['advanced', 'drill', 'drilling']):
            return 'advanced_exploration'

        # Grassroots indicators
        if any(kw in name_lower for kw in ['grassroots', 'greenfield', 'early stage']):
            return 'grassroots'

        # Default - most scraped projects are exploration stage
        return 'early_exploration'

    async def _process_company(self, url: str, options: dict):
        """Process a single company URL."""
        from mcp_servers.company_scraper import scrape_company_website

        dry_run = options.get('dry_run')
        update_existing = options.get('update')
        sections_str = options.get('sections', 'all')
        user_id = options.get('user_id')

        # Parse sections
        if sections_str == 'all':
            sections = None
        else:
            sections = [s.strip() for s in sections_str.split(',')]

        # Create scraping job record
        job = None
        if not dry_run:
            job = ScrapingJob.objects.create(
                company_name_input=url,
                website_url=url,
                status='running',
                started_at=timezone.now(),
                sections_to_process=sections or ['all'],
                initiated_by_id=user_id
            )

        try:
            self.stdout.write(f"\nScraping: {url}")
            self.stdout.write("-" * 60)

            # Run the scraper
            result = await scrape_company_website(url, sections=sections)

            data = result['data']
            errors = result['errors']

            # Display extracted data
            self._display_extracted_data(data)

            if errors:
                self.stdout.write(self.style.WARNING(f"\nWarnings/Errors: {len(errors)}"))
                for error in errors:
                    self.stdout.write(f"  - {error}")

            if dry_run:
                self.stdout.write(self.style.SUCCESS("\n[DRY RUN] No data saved to database"))
                return

            # Save to database
            company = self._save_company_data(data, url, update_existing)

            if company:
                # Update job with success
                if job:
                    job.company = company
                    job.status = 'success'
                    job.completed_at = timezone.now()
                    job.data_extracted = data
                    job.documents_found = len(data.get('documents', []))
                    job.people_found = len(data.get('people', []))
                    job.news_found = len(data.get('news', []))
                    job.sections_completed = sections or ['all']
                    job.error_messages = errors
                    job.save()

                self.stdout.write(self.style.SUCCESS(
                    f"\nCompany created/updated: {company.name} (ID: {company.id})"
                ))
                self.stdout.write(f"Completeness score: {company.data_completeness_score}%")
            else:
                raise Exception("Failed to create company record")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nError: {str(e)}"))

            if job:
                job.status = 'failed'
                job.completed_at = timezone.now()
                job.error_messages = [str(e)]
                job.error_traceback = str(e)
                job.save()

            # Record failed discovery
            if not dry_run:
                FailedCompanyDiscovery.objects.update_or_create(
                    website_url=url,
                    defaults={
                        'company_name': data.get('company', {}).get('name', url),
                        'failure_reason': str(e),
                    }
                )

            raise

    def _display_extracted_data(self, data: dict):
        """Display extracted data in a readable format."""
        company = data.get('company', {})

        self.stdout.write(self.style.SUCCESS("\nExtracted Company Data:"))
        self.stdout.write(f"  Name: {company.get('name', 'N/A')}")
        self.stdout.write(f"  Ticker: {company.get('ticker_symbol', 'N/A')} ({company.get('exchange', 'N/A')})")
        self.stdout.write(f"  Tagline: {company.get('tagline', 'N/A')[:60]}...")
        self.stdout.write(f"  Description: {company.get('description', 'N/A')[:100]}...")
        self.stdout.write(f"  Logo URL: {company.get('logo_url', 'N/A')}")

        if company.get('ir_contact_email'):
            self.stdout.write(f"  IR Email: {company.get('ir_contact_email')}")

        # Social media
        social_platforms = ['linkedin_url', 'twitter_url', 'facebook_url', 'youtube_url']
        social_found = [p for p in social_platforms if company.get(p)]
        if social_found:
            self.stdout.write(f"  Social Media: {', '.join(p.replace('_url', '') for p in social_found)}")

        # People
        people = data.get('people', [])
        self.stdout.write(f"\nPeople Found: {len(people)}")
        for person in people[:5]:
            self.stdout.write(f"  - {person.get('full_name')}: {person.get('title', 'N/A')}")
        if len(people) > 5:
            self.stdout.write(f"  ... and {len(people) - 5} more")

        # Documents
        documents = data.get('documents', [])
        self.stdout.write(f"\nDocuments Found: {len(documents)}")
        doc_types = {}
        for doc in documents:
            doc_type = doc.get('document_type', 'other')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        for doc_type, count in doc_types.items():
            self.stdout.write(f"  - {doc_type}: {count}")

        # News
        news = data.get('news', [])
        self.stdout.write(f"\nNews Items Found: {len(news)}")

        # Projects
        projects = data.get('projects', [])
        self.stdout.write(f"\nProjects Found: {len(projects)}")
        for project in projects[:3]:
            self.stdout.write(f"  - {project.get('name')}")

    def _save_company_data(self, data: dict, source_url: str, update_existing: bool) -> Company:
        """Save extracted data to database models."""
        company_data = data.get('company', {})

        if not company_data.get('name'):
            raise Exception("No company name extracted - cannot create record")

        # Check for existing company
        existing_company = None
        if company_data.get('ticker_symbol'):
            existing_company = Company.objects.filter(
                ticker_symbol__iexact=company_data['ticker_symbol']
            ).first()

        if not existing_company:
            existing_company = Company.objects.filter(
                name__iexact=company_data['name']
            ).first()

        if existing_company and not update_existing:
            self.stdout.write(self.style.WARNING(
                f"Company already exists: {existing_company.name} (ID: {existing_company.id}). Use --update to update."
            ))
            return existing_company

        # Prepare company fields
        company_fields = {
            'name': company_data.get('name'),
            'legal_name': company_data.get('legal_name', company_data.get('name')),
            'ticker_symbol': company_data.get('ticker_symbol', ''),
            'description': company_data.get('description', '')[:2000] if company_data.get('description') else '',
            'tagline': company_data.get('tagline', ''),
            'logo_url': company_data.get('logo_url', ''),
            'website': source_url,
            'source_website_url': source_url,
            'auto_populated': True,
            'last_scraped_at': timezone.now(),
            # Contact info
            'ir_contact_email': company_data.get('ir_contact_email', ''),
            'general_email': company_data.get('general_email', ''),
            'media_email': company_data.get('media_email', ''),
            'general_phone': company_data.get('general_phone', ''),
            'street_address': company_data.get('street_address', ''),
            # Social media
            'linkedin_url': company_data.get('linkedin_url', ''),
            'twitter_url': company_data.get('twitter_url', ''),
            'facebook_url': company_data.get('facebook_url', ''),
            'youtube_url': company_data.get('youtube_url', ''),
        }

        # Map exchange to choices
        exchange_map = {
            'TSX': 'tsx',
            'TSXV': 'tsxv',
            'TSX-V': 'tsxv',
            'CSE': 'cse',
            'OTC': 'otc',
            'ASX': 'asx',
            'AIM': 'aim',
        }
        if company_data.get('exchange'):
            exchange_upper = company_data['exchange'].upper()
            company_fields['exchange'] = exchange_map.get(exchange_upper, 'other')

        # Market data
        if company_data.get('market_cap_usd'):
            company_fields['market_cap_usd'] = company_data['market_cap_usd']
        if company_data.get('shares_outstanding'):
            company_fields['shares_outstanding'] = company_data['shares_outstanding']

        # Set status based on ticker/exchange
        if company_fields.get('ticker_symbol') and company_fields.get('exchange'):
            company_fields['status'] = 'public'
        else:
            company_fields['status'] = 'private'

        # Create or update company
        if existing_company:
            for field, value in company_fields.items():
                if value:  # Only update non-empty values
                    setattr(existing_company, field, value)
            existing_company.save()
            company = existing_company
        else:
            company = Company.objects.create(**company_fields)

        # Calculate completeness score
        company.calculate_completeness_score()
        company.save()

        # Save people
        people_data = data.get('people', [])
        for i, person_data in enumerate(people_data):
            CompanyPerson.objects.update_or_create(
                company=company,
                full_name=person_data.get('full_name'),
                defaults={
                    'role_type': person_data.get('role_type', 'executive'),
                    'title': person_data.get('title', ''),
                    'biography': person_data.get('biography', ''),
                    'photo_url': person_data.get('photo_url', ''),
                    'linkedin_url': person_data.get('linkedin_url', ''),
                    'source_url': person_data.get('source_url', ''),
                    'extracted_at': timezone.now(),
                    'display_order': i,
                }
            )

        # Save documents
        documents_data = data.get('documents', [])
        for doc_data in documents_data:
            CompanyDocument.objects.update_or_create(
                company=company,
                source_url=doc_data.get('source_url'),
                defaults={
                    'document_type': doc_data.get('document_type', 'other'),
                    'title': doc_data.get('title', 'Untitled'),
                    'year': doc_data.get('year'),
                    'extracted_at': timezone.now(),
                }
            )

        # Save news
        news_data = data.get('news', [])
        for news_item in news_data[:50]:  # Limit to 50 news items
            pub_date = None
            if news_item.get('publication_date'):
                try:
                    pub_date = datetime.strptime(news_item['publication_date'], '%Y-%m-%d').date()
                except:
                    pass

            CompanyNews.objects.update_or_create(
                company=company,
                source_url=news_item.get('source_url', ''),
                defaults={
                    'title': news_item.get('title', 'Untitled'),
                    'publication_date': pub_date,
                    'is_pdf': '.pdf' in news_item.get('source_url', '').lower(),
                }
            )

        # Save projects
        projects_data = data.get('projects', [])
        for project_data in projects_data:
            if project_data.get('name'):
                project_name = project_data.get('name')

                # Check if project already exists
                existing_project = Project.objects.filter(
                    company=company,
                    name=project_name
                ).first()

                if existing_project:
                    # Only update description and location, preserve commodity and stage
                    # (to avoid overwriting manual corrections)
                    if project_data.get('description'):
                        existing_project.description = project_data.get('description', '')
                    if project_data.get('location'):
                        existing_project.country = project_data.get('location', '')
                    existing_project.save()
                else:
                    # New project - infer commodity and stage from name
                    commodity = self._infer_commodity_from_name(project_name)
                    stage = self._infer_project_stage_from_name(project_name)
                    Project.objects.create(
                        company=company,
                        name=project_name,
                        description=project_data.get('description', ''),
                        country=project_data.get('location', ''),
                        project_stage=stage,
                        primary_commodity=commodity,
                    )

        return company
