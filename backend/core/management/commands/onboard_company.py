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
from asgiref.sync import sync_to_async
import re
from decimal import Decimal
from core.models import (
    Company, Project, CompanyPerson, CompanyDocument,
    CompanyNews, ScrapingJob, FailedCompanyDiscovery, User,
    DocumentProcessingJob
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

    def _is_invalid_project_name(self, name: str) -> bool:
        """
        Check if a project name is invalid (geochemistry data, sample labels, etc.)
        Returns True if the name should be filtered out.
        """
        import re
        name_lower = name.lower()

        # Filter out geochemistry/assay data labels
        # e.g., "Epworth Ag ppm", "Epworth Au ppb", "Epworth Cu pct", "Lake Sed Au Ag"
        geochemistry_patterns = [
            r'\b(ppm|ppb|ppt|g/t|oz/t|pct)\b',  # Unit suffixes
            r'\b(au|ag|cu|pb|zn|ni|co|pt|pd|li|u|mo|w|sn|fe|mn|as|sb|bi|cd|hg)\s+(ppm|ppb|ppt|g/t|pct)\b',  # Element + unit
            r'\bsed\s+(au|ag|cu|pb|zn)',  # Sediment samples like "Lake Sed Au Ag"
            r'\b(lake|stream|soil|rock)\s+sed\b',  # Sediment sample types
        ]

        for pattern in geochemistry_patterns:
            if re.search(pattern, name_lower):
                return True

        # Filter out video/presentation/document titles that aren't actual project names
        media_keywords = [
            'video presentation', 'technical presentation', 'corporate presentation',
            'investor presentation', 'press release', 'news release',
            'annual report', 'quarterly report', 'financial statement',
            'technical video', 'webinar', 'interview'
        ]
        for keyword in media_keywords:
            if keyword in name_lower:
                return True

        # Filter out navigation/media page names that aren't actual projects
        navigation_keywords = [
            'maps & sections', 'maps and sections', 'maps & figures', 'maps and figures',
            'photo gallery', 'photo galleries', 'location map', 'project map', 'site map',
            'image gallery', 'video gallery', 'media gallery', 'downloads', 'documents',
            'resources', 'overview', 'all projects', 'our projects', 'project list',
            'feasibility study', 'preliminary economic assessment', 'mineral resource estimate',
            'technical report', 'ni 43-101'
        ]
        for keyword in navigation_keywords:
            if keyword in name_lower:
                return True

        # Filter out exact matches for common non-project names
        exact_invalid_names = [
            'maps', 'photos', 'gallery', 'galleries', 'videos', 'media',
            'resources', 'downloads', 'documents', 'overview', 'about',
            'contact', 'news', 'investors', 'corporate', 'highlights',
            'properties', 'assets', 'portfolio', 'locations', 'location',
            'recent posts', 'blog', 'articles', 'events', 'webinars',
            'subscribe', 'newsletter', 'email signup', 'social media',
            'technical information', 'project details', 'exploration',
            'drill program', 'drilling program', 'exploration program'
        ]
        if name_lower.strip() in exact_invalid_names:
            return True

        # Filter out project names that are actually page section labels
        section_labels = ['recent posts', 'latest news', 'featured', 'read more', 'learn more']
        if name_lower.strip() in section_labels:
            return True

        # Filter out year-based program names (e.g., "2024 Drill Program", "2025 Exploration")
        year_program_pattern = r'^20\d{2}\s+(drill|drilling|exploration|sampling|field)\s*(program|campaign|season)?'
        if re.search(year_program_pattern, name_lower):
            return True

        return False

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

    def _classify_news(self, title: str) -> dict:
        """
        Classify a news release based on its title.
        Returns a dict with news_type, is_material, financing info, and drill result info.
        """
        title_lower = title.lower()
        result = {
            'news_type': 'general',
            'is_material': False,
            'financing_type': 'none',
            'financing_amount': None,
            'financing_price_per_unit': None,
            'has_drill_results': False,
            'best_intercept': '',
        }

        # ===== DRILL RESULTS DETECTION =====
        drill_patterns = [
            r'drill\s*result',
            r'drilling\s*result',
            r'intersect',
            r'intercept',
            r'assay\s*result',
            r'returns?\s+\d+',  # "returns 5.2 g/t"
            r'\d+\.?\d*\s*g/t',  # grade mentions
            r'\d+\.?\d*\s*%\s*(cu|zn|pb|ni)',  # percentage grades
            r'metres?\s+of\s+\d+',  # "10 metres of 5 g/t"
            r'meters?\s+of\s+\d+',
            r'grading\s+\d+',
        ]
        for pattern in drill_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'drill_results'
                result['is_material'] = True
                result['has_drill_results'] = True
                # Try to extract best intercept
                intercept_match = re.search(
                    r'(\d+\.?\d*)\s*(m|metres?|meters?)\s*(of|@|at)\s*(\d+\.?\d*)\s*(g/t|%)',
                    title_lower
                )
                if intercept_match:
                    result['best_intercept'] = intercept_match.group(0)
                break

        # ===== RESOURCE ESTIMATE DETECTION =====
        resource_patterns = [
            r'resource\s*estimate',
            r'mineral\s*resource',
            r'indicated\s*resource',
            r'inferred\s*resource',
            r'measured\s*resource',
            r'resource\s*update',
            r'ni\s*43-?101',
            r'43-?101',
            r'million\s*(oz|ounces)',
            r'moz',
            r'resource\s*of\s*\d+',
        ]
        if result['news_type'] == 'general':
            for pattern in resource_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'resource_estimate'
                    result['is_material'] = True
                    break

        # ===== FINANCING DETECTION =====
        financing_patterns = {
            'private_placement': [
                r'private\s*placement',
                r'non-?brokered',
                r'closes?\s*private',
                r'announces?\s*private',
            ],
            'bought_deal': [
                r'bought\s*deal',
                r'brokered\s*offering',
                r'underwritten\s*offering',
                r'prospectus\s*offering',
            ],
            'flow_through': [
                r'flow-?through',
                r'flow\s*through\s*shares?',
                r'fts\s*financing',
            ],
            'rights_offering': [
                r'rights\s*offering',
                r'rights\s*issue',
            ],
            'warrant_exercise': [
                r'warrant\s*exercise',
                r'exercises?\s*warrants?',
            ],
            'debt': [
                r'debt\s*financing',
                r'loan\s*facility',
                r'credit\s*facility',
                r'convertible\s*debenture',
            ],
        }

        for financing_type, patterns in financing_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'financing'
                    result['is_material'] = True
                    result['financing_type'] = financing_type
                    # Try to extract financing amount
                    amount_match = re.search(
                        r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|m\b)',
                        title_lower
                    )
                    if amount_match:
                        try:
                            amount_str = amount_match.group(1).replace(',', '')
                            result['financing_amount'] = Decimal(amount_str) * 1000000
                        except:
                            pass
                    # Try to extract price per unit
                    price_match = re.search(
                        r'\$\s*(\d+\.?\d*)\s*per\s*(unit|share)',
                        title_lower
                    )
                    if price_match:
                        try:
                            result['financing_price_per_unit'] = Decimal(price_match.group(1))
                        except:
                            pass
                    break
            if result['financing_type'] != 'none':
                break

        # ===== ACQUISITION/MERGER DETECTION =====
        acquisition_patterns = [
            r'acqui(re|sition)',
            r'merger',
            r'amalgamat',
            r'take-?over',
            r'business\s*combination',
            r'purchase\s*agreement',
            r'option\s*agreement',
            r'earn-?in',
        ]
        if result['news_type'] == 'general':
            for pattern in acquisition_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'acquisition'
                    result['is_material'] = True
                    break

        # ===== MANAGEMENT CHANGE DETECTION =====
        management_patterns = [
            r'appoint',
            r'ceo\s*(change|transition|resign|depart)',
            r'new\s*(ceo|cfo|president|director)',
            r'board\s*(change|appointment)',
            r'management\s*change',
            r'executive\s*change',
        ]
        if result['news_type'] == 'general':
            for pattern in management_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'management'
                    break

        # ===== EXPLORATION UPDATE =====
        exploration_patterns = [
            r'exploration\s*update',
            r'exploration\s*program',
            r'field\s*program',
            r'sampling\s*result',
            r'geophysic',
            r'survey\s*result',
            r'commence.*drill',
            r'start.*drill',
        ]
        if result['news_type'] == 'general':
            for pattern in exploration_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'exploration'
                    break

        # ===== PRODUCTION UPDATE =====
        production_patterns = [
            r'production\s*update',
            r'production\s*result',
            r'quarterly\s*production',
            r'annual\s*production',
            r'gold\s*pour',
            r'first\s*pour',
            r'commercial\s*production',
        ]
        if result['news_type'] == 'general':
            for pattern in production_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'production'
                    result['is_material'] = True
                    break

        # ===== REGULATORY/PERMITTING =====
        regulatory_patterns = [
            r'permit',
            r'environmental\s*assessment',
            r'eia\b',
            r'regulatory\s*approv',
            r'license\s*grant',
            r'licence\s*grant',
        ]
        if result['news_type'] == 'general':
            for pattern in regulatory_patterns:
                if re.search(pattern, title_lower):
                    result['news_type'] = 'regulatory'
                    break

        return result

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
            @sync_to_async
            def create_job():
                return ScrapingJob.objects.create(
                    company_name_input=url,
                    website_url=url,
                    status='running',
                    started_at=timezone.now(),
                    sections_to_process=sections or ['all'],
                    initiated_by_id=user_id
                )
            job = await create_job()

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

            # Save to database (wrapped for async context)
            @sync_to_async
            def save_data():
                return self._save_company_data(data, url, update_existing)
            company = await save_data()

            if company:
                # Update job with success
                if job:
                    @sync_to_async
                    def update_job_success():
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
                    await update_job_success()

                self.stdout.write(self.style.SUCCESS(
                    f"\nCompany created/updated: {company.name} (ID: {company.id})"
                ))
                self.stdout.write(f"Completeness score: {company.data_completeness_score}%")

                # Process news content for RAG/semantic search
                # This makes all scraped news available to Claude's knowledge base
                news_count = len(data.get('news', []))
                if news_count > 0:
                    @sync_to_async
                    def process_news_for_rag():
                        try:
                            from mcp_servers.news_content_processor import NewsContentProcessor
                            processor = NewsContentProcessor()
                            result = processor._process_company_news(company.name, limit=50)
                            return result
                        except Exception as e:
                            return {"error": str(e)}

                    self.stdout.write(f"Processing {news_count} news items for RAG knowledge base...")
                    news_result = await process_news_for_rag()
                    if news_result.get('success'):
                        self.stdout.write(self.style.SUCCESS(
                            f"  Processed {news_result.get('news_items_processed', 0)} news items, "
                            f"created {news_result.get('chunks_created', 0)} searchable chunks"
                        ))
                    elif news_result.get('error'):
                        self.stdout.write(self.style.WARNING(
                            f"  Warning: News processing failed: {news_result.get('error')}"
                        ))

                # Store company profile data in knowledge base
                # This includes description, tagline, and project summaries
                @sync_to_async
                def store_company_profile_in_rag():
                    try:
                        from mcp_servers.rag_utils import RAGManager
                        import chromadb
                        from pathlib import Path
                        from django.conf import settings

                        # Build company profile text for RAG
                        profile_parts = []

                        # Company overview
                        if company.description:
                            profile_parts.append(f"Company Overview: {company.name}\n{company.description}")

                        if company.tagline:
                            profile_parts.append(f"Tagline: {company.tagline}")

                        # Stock info
                        if company.ticker_symbol and company.exchange:
                            profile_parts.append(f"Stock: {company.ticker_symbol} on {company.exchange.upper()}")

                        # Projects summary
                        projects = company.projects.all()
                        if projects:
                            project_texts = []
                            for project in projects:
                                project_text = f"Project: {project.name}"
                                if project.description:
                                    project_text += f"\n{project.description}"
                                if project.country:
                                    project_text += f"\nLocation: {project.country}"
                                if project.primary_commodity:
                                    project_text += f"\nCommodity: {project.primary_commodity}"
                                project_texts.append(project_text)
                            profile_parts.append("Projects:\n" + "\n\n".join(project_texts))

                        if not profile_parts:
                            return {"success": False, "message": "No profile data to store"}

                        full_profile = "\n\n".join(profile_parts)

                        # Store in ChromaDB company_profiles collection
                        chroma_path = Path(settings.BASE_DIR) / "chroma_db"
                        chroma_path.mkdir(exist_ok=True)

                        from chromadb.config import Settings as ChromaSettings
                        chroma_client = chromadb.PersistentClient(
                            path=str(chroma_path),
                            settings=ChromaSettings(anonymized_telemetry=False)
                        )

                        collection = chroma_client.get_or_create_collection(
                            name="company_profiles",
                            metadata={"hnsw:space": "cosine"}
                        )

                        # Delete existing profile for this company
                        try:
                            collection.delete(ids=[f"company_{company.id}_profile"])
                        except:
                            pass

                        # Add the profile
                        collection.add(
                            ids=[f"company_{company.id}_profile"],
                            documents=[full_profile],
                            metadatas=[{
                                "company_id": company.id,
                                "company_name": company.name,
                                "ticker": company.ticker_symbol or "",
                                "exchange": company.exchange or "",
                                "type": "company_profile"
                            }]
                        )

                        return {"success": True, "chars_stored": len(full_profile)}

                    except Exception as e:
                        return {"error": str(e)}

                self.stdout.write("Storing company profile in knowledge base...")
                profile_result = await store_company_profile_in_rag()
                if profile_result.get('success'):
                    self.stdout.write(self.style.SUCCESS(
                        f"  Stored {profile_result.get('chars_stored', 0)} chars of company profile data"
                    ))
                elif profile_result.get('error'):
                    self.stdout.write(self.style.WARNING(
                        f"  Warning: Profile storage failed: {profile_result.get('error')}"
                    ))
            else:
                raise Exception("Failed to create company record")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nError: {str(e)}"))

            if job:
                @sync_to_async
                def update_job_failed():
                    job.status = 'failed'
                    job.completed_at = timezone.now()
                    job.error_messages = [str(e)]
                    job.error_traceback = str(e)
                    job.save()
                await update_job_failed()

            # Record failed discovery
            if not dry_run:
                @sync_to_async
                def record_failure():
                    FailedCompanyDiscovery.objects.update_or_create(
                        website_url=url,
                        defaults={
                            'company_name': data.get('company', {}).get('name', url),
                            'failure_reason': str(e),
                        }
                    )
                await record_failure()

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
            # Skip data URLs for logo (base64 encoded, too long for URLField)
            'logo_url': company_data.get('logo_url', '') if not company_data.get('logo_url', '').startswith('data:') else '',
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

        # Save documents and create processing jobs for key document types
        documents_data = data.get('documents', [])
        processing_job_types = ['ni43101', 'pea', 'presentation', 'fact_sheet']
        doc_jobs_created = 0

        for doc_data in documents_data:
            doc_source_url = doc_data.get('source_url', '')
            doc_type = doc_data.get('document_type', 'other')

            # Skip documents with URLs that are too long (max 200 chars)
            if len(doc_source_url) > 200:
                self.stdout.write(self.style.WARNING(f"  Skipping document with URL too long: {doc_source_url[:60]}..."))
                continue

            CompanyDocument.objects.update_or_create(
                company=company,
                source_url=doc_source_url,
                defaults={
                    'document_type': doc_type,
                    'title': (doc_data.get('title', 'Untitled') or 'Untitled')[:500],  # Truncate title
                    'year': doc_data.get('year'),
                    'extracted_at': timezone.now(),
                }
            )

            # Create document processing job for key document types (if PDF)
            if doc_type in processing_job_types and doc_source_url and '.pdf' in doc_source_url.lower():
                existing_job = DocumentProcessingJob.objects.filter(url=doc_source_url).first()
                if not existing_job:
                    DocumentProcessingJob.objects.create(
                        url=doc_source_url,
                        document_type=doc_type,
                        company_name=company.name,
                        status='pending',
                    )
                    doc_jobs_created += 1

        if doc_jobs_created > 0:
            self.stdout.write(self.style.SUCCESS(f"  Created {doc_jobs_created} document processing jobs"))

        # Save news with classification and document processing
        news_data = data.get('news', [])
        saved_news_count = 0
        processing_jobs_created = 0
        material_news_count = 0

        for news_item in news_data:
            if saved_news_count >= 50:  # Limit to 50 news items
                break

            # IMPORTANT: Skip news items without dates - they are low quality
            pub_date = None
            if news_item.get('publication_date'):
                try:
                    pub_date = datetime.strptime(news_item['publication_date'], '%Y-%m-%d').date()
                except:
                    pass

            if not pub_date:
                continue  # Skip items without valid dates

            news_title = news_item.get('title', '').strip()

            # Skip items with no title or very short titles
            if not news_title or len(news_title) < 10:
                continue

            # Skip titles that are just dates (bad scrape artifacts)
            date_only_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$'
            if re.match(date_only_pattern, news_title, re.IGNORECASE):
                continue

            # Skip non-news items (investor reports, third-party coverage without attribution)
            skip_patterns = [
                r'Harbour Insight',  # Investor report, not a news release
                r'^The Northern Miner\s*[–—-]',  # Third-party coverage
                r'^Mining\.com\s*[–—-]',  # Third-party coverage
                r'^Kitco\s*[–—-]',  # Third-party coverage
                r'Skip to content',  # Navigation artifact
            ]
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, news_title, re.IGNORECASE):
                    should_skip = True
                    break
            if should_skip:
                continue

            # Truncate fields to fit DB constraints
            news_title = news_title[:500]  # title max_length=500
            source_url = news_item.get('source_url', '')[:200]  # source_url max_length=200
            is_pdf = '.pdf' in source_url.lower()

            # Classify the news item
            classification = self._classify_news(news_title)
            if classification['is_material']:
                material_news_count += 1

            # Create or update the news record with classification data
            news_record, created = CompanyNews.objects.update_or_create(
                company=company,
                source_url=source_url,
                defaults={
                    'title': news_title,
                    'publication_date': pub_date,
                    'is_pdf': is_pdf,
                    'news_type': classification['news_type'],
                    'is_material': classification['is_material'],
                    'financing_type': classification['financing_type'],
                    'financing_amount': classification['financing_amount'],
                    'financing_price_per_unit': classification['financing_price_per_unit'],
                    'has_drill_results': classification['has_drill_results'],
                    'best_intercept': classification['best_intercept'][:200] if classification['best_intercept'] else '',
                }
            )

            # Create DocumentProcessingJob for PDF news releases (material news prioritized)
            # Only create jobs for PDFs that haven't been processed yet
            if is_pdf and source_url and not news_record.is_processed:
                # Check if a job already exists for this URL
                existing_job = DocumentProcessingJob.objects.filter(url=source_url).first()
                if not existing_job:
                    job = DocumentProcessingJob.objects.create(
                        url=source_url,
                        document_type='news_release',
                        company_name=company.name,
                        project_name='',  # News may not be project-specific
                        status='pending',
                    )
                    # Link the news record to the processing job
                    news_record.processing_job = job
                    news_record.save(update_fields=['processing_job'])
                    processing_jobs_created += 1

            saved_news_count += 1

        # Log summary
        if material_news_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"  Found {material_news_count} material news items (drill results, financings, etc.)"
            ))
        if processing_jobs_created > 0:
            self.stdout.write(self.style.SUCCESS(
                f"  Created {processing_jobs_created} document processing jobs for PDF news releases"
            ))

        # Save projects
        projects_data = data.get('projects', [])
        for project_data in projects_data:
            if project_data.get('name'):
                project_name = project_data.get('name')

                # Skip invalid project names (geochemistry data, sample labels, etc.)
                if self._is_invalid_project_name(project_name):
                    continue

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
                    # Default country to empty string if not provided (DB requires non-null)
                    country = project_data.get('location') or ''
                    Project.objects.create(
                        company=company,
                        name=project_name,
                        description=project_data.get('description', ''),
                        country=country,
                        project_stage=stage,
                        primary_commodity=commodity,
                    )

        return company
