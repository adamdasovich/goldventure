"""
Django Management Command: Auto-discover and Process Company Documents
Automatically crawls company websites, discovers documents, and processes them.

Usage:
    # Process all companies with websites
    python manage.py auto_process_documents --all

    # Process specific company by ID
    python manage.py auto_process_documents --company-id 123

    # Process specific company by name
    python manage.py auto_process_documents --company-name "1911 Gold"

    # Dry run (discover but don't create jobs)
    python manage.py auto_process_documents --all --dry-run

    # Only process specific document types
    python manage.py auto_process_documents --all --types ni43101,news_release

    # Limit number of companies to process
    python manage.py auto_process_documents --all --limit 10
"""

from django.core.management.base import BaseCommand, CommandError
from core.models import Company, DocumentProcessingJob, Document
from core.security_utils import is_safe_document_url
from mcp_servers.website_crawler import crawl_company_website
from datetime import datetime
import asyncio
import requests


class Command(BaseCommand):
    help = 'Automatically discover and process company documents from their websites'

    def add_arguments(self, parser):
        # Company selection
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all companies with websites'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Process specific company by ID'
        )
        parser.add_argument(
            '--company-name',
            type=str,
            help='Process specific company by name (partial match)'
        )

        # Document type filter
        parser.add_argument(
            '--types',
            type=str,
            help='Comma-separated list of document types to process (ni43101,news_release,presentation,financial_statement,fact_sheet)'
        )

        # Processing options
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Discover documents but do not create processing jobs'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of companies to process'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip documents that are already in the system'
        )
        parser.add_argument(
            '--auto-process',
            action='store_true',
            help='Automatically start processing after creating jobs'
        )

    def handle(self, *args, **options):
        """Main command handler"""

        # Get companies to process
        companies = self._get_companies(options)

        if not companies:
            self.stdout.write(self.style.ERROR('No companies found to process'))
            return

        # Parse document types filter
        allowed_types = None
        if options['types']:
            allowed_types = [t.strip() for t in options['types'].split(',')]
            self.stdout.write(self.style.NOTICE(f'Filtering for document types: {", ".join(allowed_types)}'))

        # Process each company
        total_discovered = 0
        total_jobs_created = 0

        for company in companies:
            self.stdout.write(self.style.HTTP_INFO(f'\n{"="*80}'))
            self.stdout.write(self.style.HTTP_INFO(f'Processing: {company.name}'))
            self.stdout.write(self.style.HTTP_INFO(f'{"="*80}'))

            if not company.website:
                self.stdout.write(self.style.WARNING(f'  ⚠ No website URL for {company.name}, skipping'))
                continue

            # Discover documents
            try:
                documents = asyncio.run(crawl_company_website(company.website, max_depth=2))

                if not documents:
                    self.stdout.write(self.style.WARNING(f'  ⚠ No documents discovered for {company.name}'))
                    continue

                # Filter by document type if specified
                if allowed_types:
                    documents = [d for d in documents if d['document_type'] in allowed_types]

                self.stdout.write(self.style.SUCCESS(f'  ✓ Discovered {len(documents)} documents'))

                # Display discovered documents by type
                doc_types = {}
                for doc in documents:
                    doc_type = doc['document_type']
                    if doc_type not in doc_types:
                        doc_types[doc_type] = []
                    doc_types[doc_type].append(doc)

                for doc_type, docs in doc_types.items():
                    self.stdout.write(f'\n  {doc_type.upper()}: {len(docs)} documents')
                    for doc in docs[:3]:  # Show first 3 of each type
                        self.stdout.write(f'    - {doc["title"][:60]}...')
                    if len(docs) > 3:
                        self.stdout.write(f'    ... and {len(docs) - 3} more')

                total_discovered += len(documents)

                # Create processing jobs (unless dry-run)
                if not options['dry_run']:
                    jobs_created = self._create_processing_jobs(
                        company,
                        documents,
                        options['skip_existing']
                    )
                    total_jobs_created += jobs_created

                    if jobs_created > 0:
                        self.stdout.write(self.style.SUCCESS(f'\n  ✓ Created {jobs_created} processing jobs'))
                    else:
                        self.stdout.write(self.style.NOTICE(f'\n  ℹ No new jobs created (all documents already processed)'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing {company.name}: {str(e)}'))
                continue

        # Summary
        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*80}'))
        self.stdout.write(self.style.HTTP_INFO('SUMMARY'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*80}'))
        self.stdout.write(f'Companies processed: {len(companies)}')
        self.stdout.write(f'Documents discovered: {total_discovered}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'Jobs created: 0 (DRY RUN - no jobs created)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Jobs created: {total_jobs_created}'))

            # Auto-process if requested
            if options['auto_process'] and total_jobs_created > 0:
                self.stdout.write(self.style.HTTP_INFO(f'\nStarting automatic processing of {total_jobs_created} jobs...'))
                self._auto_process_queue()

    def _get_companies(self, options):
        """Get companies to process based on options"""

        if options['company_id']:
            try:
                company = Company.objects.get(id=options['company_id'])
                return [company]
            except Company.DoesNotExist:
                raise CommandError(f'Company with ID {options["company_id"]} not found')

        elif options['company_name']:
            companies = Company.objects.filter(name__icontains=options['company_name'])
            if not companies.exists():
                raise CommandError(f'No companies found matching "{options["company_name"]}"')
            return list(companies)

        elif options['all']:
            companies = Company.objects.filter(website__isnull=False).exclude(website='')

            if options['limit']:
                companies = companies[:options['limit']]

            return list(companies)

        else:
            raise CommandError('Must specify --all, --company-id, or --company-name')

    def _create_processing_jobs(self, company, documents, skip_existing=False):
        """Create DocumentProcessingJob records for discovered documents"""

        jobs_created = 0

        for doc in documents:
            # Skip if document already exists (optional)
            if skip_existing:
                existing = Document.objects.filter(
                    company=company,
                    file_url=doc['url']
                ).exists()

                if existing:
                    continue

                # Also check if there's already a pending/completed job for this URL
                existing_job = DocumentProcessingJob.objects.filter(
                    url=doc['url'],
                    status__in=['completed', 'processing']
                ).exists()

                if existing_job:
                    continue

            # SECURITY: Validate URL before fetching (SSRF prevention)
            is_safe, reason = is_safe_document_url(doc['url'])
            if not is_safe:
                self.stdout.write(self.style.WARNING(f"    Skipping unsafe URL ({reason}): {doc['url'][:60]}..."))
                continue

            # Validate URL is accessible before creating job
            try:
                response = requests.head(doc['url'], timeout=10, allow_redirects=True)
                if response.status_code >= 400:
                    self.stdout.write(self.style.WARNING(f"    Skipping broken link ({response.status_code}): {doc['url'][:60]}..."))
                    continue
            except requests.RequestException:
                self.stdout.write(self.style.WARNING(f"    Skipping unreachable URL: {doc['url'][:60]}..."))
                continue

            # Create processing job
            DocumentProcessingJob.objects.create(
                url=doc['url'],
                document_type=doc['document_type'],
                company_name=company.name,
                status='pending'
            )
            jobs_created += 1

        return jobs_created

    def _auto_process_queue(self):
        """Automatically start processing the job queue"""

        from core.tasks import process_document_queue

        try:
            process_document_queue()
            self.stdout.write(self.style.SUCCESS('✓ Processing queue completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error processing queue: {str(e)}'))
