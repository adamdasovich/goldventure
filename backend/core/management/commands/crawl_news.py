"""
Django Management Command: Crawl Company News Releases
Automatically crawls company websites for news releases and stores them in the database

Usage:
    python manage.py crawl_news --all                    # Crawl all companies
    python manage.py crawl_news --company "1911 Gold"    # Crawl specific company
    python manage.py crawl_news --months 12              # Last 12 months instead of 6
"""

import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from core.models import Company
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases


class Command(BaseCommand):
    help = 'Crawl company websites for news releases and store in database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Crawl all companies in database',
        )
        parser.add_argument(
            '--company',
            type=str,
            help='Company name to crawl (partial match)',
        )
        parser.add_argument(
            '--months',
            type=int,
            default=6,
            help='Number of months to look back (default: 6)',
        )
        parser.add_argument(
            '--depth',
            type=int,
            default=2,
            help='Max crawl depth (default: 2)',
        )

    def handle(self, *args, **options):
        """Execute the crawl command"""

        # Run async function
        asyncio.run(self.crawl_companies(options))

    async def crawl_companies(self, options):
        """Crawl companies asynchronously"""

        all_companies = options['all']
        company_name = options['company']
        months = options['months']
        max_depth = options['depth']

        # Get companies to crawl
        if all_companies:
            companies = await sync_to_async(list)(Company.objects.filter(website__isnull=False))
        elif company_name:
            companies = await sync_to_async(list)(
                Company.objects.filter(name__icontains=company_name, website__isnull=False)
            )
        else:
            self.stdout.write(self.style.ERROR('Error: Must specify --all or --company'))
            return

        if not companies:
            self.stdout.write(self.style.WARNING('No companies found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nCrawling {len(companies)} company(ies)'))
        self.stdout.write(f'Looking back: {months} months')
        self.stdout.write(f'Max depth: {max_depth}\n')

        total_created = 0
        total_skipped = 0
        total_errors = 0

        for company in companies:
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write(self.style.HTTP_INFO(f'Company: {company.name}'))
            self.stdout.write(f'Website: {company.website}')
            self.stdout.write(f'{"="*80}')

            try:
                # Crawl for news releases
                self.stdout.write('Crawling website...')
                news_releases = await crawl_news_releases(
                    url=company.website,
                    months=months,
                    max_depth=max_depth
                )

                self.stdout.write(f'Found {len(news_releases)} news releases\n')

                if news_releases:
                    # Show preview
                    self.stdout.write('Preview (latest 3):')
                    for i, news in enumerate(news_releases[:3], 1):
                        date = news.get('date', 'No date')
                        title = news.get('title', 'No title')[:60]
                        self.stdout.write(f'  {i}. [{date}] {title}')

                    # Store in database
                    self.stdout.write('\nStoring in database...')
                    store_async = sync_to_async(store_news_releases)
                    stats = await store_async(company.name, news_releases, overwrite_duplicates=False)

                    # Display results
                    created = stats['created']
                    skipped = stats['skipped']
                    errors = len(stats['errors'])

                    total_created += created
                    total_skipped += skipped
                    total_errors += errors

                    if created > 0:
                        self.stdout.write(self.style.SUCCESS(f'✓ Created: {created}'))
                    if skipped > 0:
                        self.stdout.write(self.style.WARNING(f'⊘ Skipped: {skipped}'))
                    if errors > 0:
                        self.stdout.write(self.style.ERROR(f'✗ Errors: {errors}'))
                        for error in stats['errors'][:2]:
                            self.stdout.write(f'  - {error}')
                else:
                    self.stdout.write(self.style.WARNING('No news releases found'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error crawling {company.name}: {str(e)}'))
                total_errors += 1

        # Summary
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('CRAWL COMPLETE'))
        self.stdout.write(f'{"="*80}')
        self.stdout.write(f'Companies crawled: {len(companies)}')
        self.stdout.write(self.style.SUCCESS(f'Total created: {total_created}'))
        self.stdout.write(self.style.WARNING(f'Total skipped: {total_skipped}'))
        if total_errors > 0:
            self.stdout.write(self.style.ERROR(f'Total errors: {total_errors}'))
        self.stdout.write('')
