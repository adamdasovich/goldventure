"""
Management command to backfill financing flags for historical news releases.

This command scans existing news releases from the past N months and applies the
financing detection logic retroactively. It creates NewsReleaseFlag records for
any historical news that matches financing or strategic investment keywords.

Usage:
    python manage.py backfill_financing_flags --months 3
    python manage.py backfill_financing_flags --months 6 --dry-run
    python manage.py backfill_financing_flags --company-id 5
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import NewsRelease, NewsReleaseFlag, Company


class Command(BaseCommand):
    help = 'Backfill financing flags for historical news releases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='Number of months to backfill (default: 3)'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Only backfill for specific company ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be flagged without creating records'
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='Send email notifications for newly flagged items (default: False for backfill)'
        )

    def handle(self, *args, **options):
        months = options['months']
        company_id = options.get('company_id')
        dry_run = options['dry_run']
        send_emails = options['send_emails']

        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('BACKFILL FINANCING FLAGS'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))

        # Calculate date range
        cutoff_date = timezone.now() - timedelta(days=months * 30)
        self.stdout.write(f'[Date] Scanning news releases from: {cutoff_date.strftime("%Y-%m-%d")}')
        self.stdout.write(f'{"[Mode] Dry run - no flags will be created" if dry_run else "[Mode] Creating flags for matches"}\n')

        # Get news releases to scan
        queryset = NewsRelease.objects.filter(
            release_date__gte=cutoff_date.date()
        ).select_related('company')

        if company_id:
            queryset = queryset.filter(company_id=company_id)
            company = Company.objects.get(id=company_id)
            self.stdout.write(f'[Company] Filtering to company: {company.name}\n')

        total_news = queryset.count()
        self.stdout.write(f'[Total] News releases to scan: {total_news}\n')

        # Define detection keywords
        financing_keywords = [
            'private placement',
            'financing',
            'funding round',
            'capital raise',
            'bought deal',
            'equity financing',
            'debt financing',
            'flow-through',
            'warrant',
            'subscription',
            'offering',
        ]

        # Strategic investment keywords (for major miner investments)
        strategic_keywords = [
            'strategic investment',
            'strategic partner',
            'equity stake',
            'strategic alliance',
            'strategic equity',
            'cornerstone investor',
        ]

        # Major miner names to detect
        major_miners = [
            'barrick',
            'newmont',
            'agnico eagle',
            'franco-nevada',
            'kinross',
            'anglogold ashanti',
            'gold fields',
            'wheaton precious metals',
            'royal gold',
            'eldorado gold',
            'iamgold',
            'endeavour mining',
            'b2gold',
            'yamana gold',
        ]

        all_keywords = financing_keywords + strategic_keywords + major_miners

        # Scan news releases
        matches = []
        already_flagged = 0
        processed = 0

        for news in queryset:
            processed += 1
            if processed % 100 == 0:
                self.stdout.write(f'[Progress] Processed {processed}/{total_news}...')

            # Check if already flagged
            existing_flag = NewsReleaseFlag.objects.filter(news_release=news).first()
            if existing_flag:
                already_flagged += 1
                continue

            # Detect keywords in title
            title_lower = news.title.lower()
            detected_keywords = [kw for kw in all_keywords if kw in title_lower]

            if detected_keywords:
                # Categorize as financing or strategic investment
                is_strategic = any(kw in detected_keywords for kw in strategic_keywords + major_miners)
                category = 'Strategic Investment' if is_strategic else 'Financing'

                matches.append({
                    'news': news,
                    'keywords': detected_keywords,
                    'category': category
                })

        # Display results
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('SCAN RESULTS'))
        self.stdout.write(f'{"="*80}\n')
        self.stdout.write(f'Total news releases scanned: {total_news}')
        self.stdout.write(f'Already flagged (skipped): {already_flagged}')
        self.stdout.write(f'New matches found: {len(matches)}\n')

        if not matches:
            self.stdout.write(self.style.WARNING('[Info] No new financing-related news releases found.'))
            return

        # Display matches
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('DETECTED MATCHES'))
        self.stdout.write(f'{"="*80}\n')

        for i, match in enumerate(matches, 1):
            news = match['news']
            keywords = match['keywords']
            category = match['category']

            self.stdout.write(f'\n{i}. [{category}] {news.company.name}')
            self.stdout.write(f'   Date: {news.release_date}')
            self.stdout.write(f'   Title: {news.title[:80]}...' if len(news.title) > 80 else f'   Title: {news.title}')
            self.stdout.write(f'   Keywords: {", ".join(keywords)}')
            self.stdout.write(f'   URL: {news.url}')

        # Create flags if not dry run
        if not dry_run:
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write(self.style.SUCCESS('CREATING FLAGS'))
            self.stdout.write(f'{"="*80}\n')

            created_count = 0
            for match in matches:
                news = match['news']
                keywords = match['keywords']

                flag = NewsReleaseFlag.objects.create(
                    news_release=news,
                    detected_keywords=keywords,
                    status='pending'
                )
                created_count += 1

                self.stdout.write(f'[Created] Flag #{flag.id} for {news.company.name}')

                # Send email notification if requested
                if send_emails:
                    try:
                        from core.notifications import send_financing_flag_notification
                        send_financing_flag_notification(flag, news.company, news)
                        self.stdout.write(f'   [Email] Sent notification')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   [Warning] Failed to send email: {str(e)}'))

            self.stdout.write(f'\n{self.style.SUCCESS(f"[Success] Created {created_count} flags")}')

            if not send_emails:
                self.stdout.write(self.style.WARNING('\n[Info] Email notifications were NOT sent (use --send-emails to enable)'))

        else:
            self.stdout.write(f'\n{self.style.WARNING("[Dry Run] No flags were created")}')
            self.stdout.write(f'   Run without --dry-run to create {len(matches)} flags')

        # Summary
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(f'{"="*80}\n')
        self.stdout.write(f'Period scanned: {cutoff_date.strftime("%Y-%m-%d")} to {timezone.now().strftime("%Y-%m-%d")}')
        self.stdout.write(f'News releases scanned: {total_news}')
        self.stdout.write(f'Already flagged: {already_flagged}')
        self.stdout.write(f'New matches: {len(matches)}')
        if not dry_run:
            self.stdout.write(f'Flags created: {created_count}')
            self.stdout.write(f'Emails sent: {created_count if send_emails else 0}')
        self.stdout.write(f'\n{self.style.SUCCESS("[Complete] Backfill finished!")}\n')
