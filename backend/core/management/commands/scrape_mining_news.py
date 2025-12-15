"""
Django management command to scrape mining industry news articles.
Can be run manually or scheduled via cron.

Usage:
    python manage.py scrape_mining_news          # Run scrape job
    python manage.py scrape_mining_news --init   # Initialize default news sources

Cron Example (daily at 6 AM EST):
    0 6 * * * cd /var/www/goldventure/backend && /var/www/goldventure/backend/venv/bin/python manage.py scrape_mining_news
"""

import asyncio
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Scrape mining industry news articles from configured sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--init',
            action='store_true',
            help='Initialize default news sources (Northern Miner, Mining.com)'
        )
        parser.add_argument(
            '--job-id',
            type=int,
            help='Resume an existing job by ID'
        )

    def handle(self, *args, **options):
        from core.models import NewsSource, NewsScrapeJob

        if options['init']:
            self._initialize_default_sources()
            return

        # Check if there's already a running job
        running_job = NewsScrapeJob.objects.filter(status='running').first()
        if running_job:
            self.stdout.write(
                self.style.WARNING(
                    f'A scrape job is already running (ID: {running_job.id}, started: {running_job.started_at})'
                )
            )
            return

        # Create or get job
        if options.get('job_id'):
            try:
                job = NewsScrapeJob.objects.get(id=options['job_id'])
                self.stdout.write(f'Resuming job ID: {job.id}')
            except NewsScrapeJob.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Job ID {options["job_id"]} not found'))
                return
        else:
            job = NewsScrapeJob.objects.create(
                status='pending',
                is_scheduled=True
            )
            self.stdout.write(f'Created new scrape job ID: {job.id}')

        # Run the scrape job
        self.stdout.write('Starting news scrape...')
        self.stdout.write('-' * 60)

        try:
            from mcp_servers.news_scraper import run_scrape_job
            result = asyncio.run(run_scrape_job(job.id))

            self.stdout.write('-' * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Scrape completed!\n'
                    f'  Sources processed: {result["sources_processed"]}\n'
                    f'  Articles found: {result["articles_found"]}\n'
                    f'  New articles saved: {result["articles_new"]}'
                )
            )

            if result.get('errors'):
                self.stdout.write(self.style.WARNING('Errors:'))
                for error in result['errors']:
                    self.stdout.write(f'  - {error}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scrape failed: {str(e)}'))
            job.status = 'failed'
            job.errors = [str(e)]
            job.completed_at = timezone.now()
            job.save()

    def _initialize_default_sources(self):
        """Initialize default mining news sources"""
        from core.models import NewsSource

        default_sources = [
            {
                'name': 'The Northern Miner',
                'url': 'https://www.northernminer.com/',
                'scrape_selector': '',
            },
            {
                'name': 'Mining.com',
                'url': 'https://mining.com/',
                'scrape_selector': '',
            },
        ]

        created_count = 0
        for source_data in default_sources:
            source, created = NewsSource.objects.get_or_create(
                url=source_data['url'],
                defaults={
                    'name': source_data['name'],
                    'is_active': True,
                    'scrape_selector': source_data['scrape_selector'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created source: {source.name}'))
            else:
                self.stdout.write(f'Source already exists: {source.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\nInitialization complete. {created_count} new sources created.')
        )
