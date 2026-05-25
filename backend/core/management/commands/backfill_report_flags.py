"""
Backfill technical-report flags (NI 43-101 / PEA / PFS / DFS / MRE / ...)
for historical news releases.

Mirrors backfill_financing_flags.py but writes to NewsReportFlag and checks
the 'report_false_positive' dismissal scope so it doesn't re-flag releases
that have already been dismissed as report false-positives.

Usage:
    python manage.py backfill_report_flags --months 4
    python manage.py backfill_report_flags --months 4 --dry-run
    python manage.py backfill_report_flags --company-id 5
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    NewsRelease,
    NewsReportFlag,
    DismissedNewsURL,
    Company,
)
from core.tasks import REPORT_KEYWORDS, NEWS_SIMILARITY_THRESHOLD


class Command(BaseCommand):
    help = 'Backfill technical-report flags for historical news releases'

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=4,
                            help='Months of history to scan (default: 4)')
        parser.add_argument('--company-id', type=int,
                            help='Restrict to a single company')
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be flagged without writing rows')

    def handle(self, *args, **options):
        months = options['months']
        company_id = options.get('company_id')
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('BACKFILL TECHNICAL-REPORT FLAGS'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))

        cutoff_date = (timezone.now() - timedelta(days=months * 30)).date()
        self.stdout.write(f'[Date] Scanning news releases since: {cutoff_date}')
        self.stdout.write(f'[Mode] {"Dry run (no writes)" if dry_run else "Creating flags for matches"}\n')

        qs = NewsRelease.objects.filter(
            release_date__gte=cutoff_date
        ).select_related('company').order_by('release_date')

        if company_id:
            qs = qs.filter(company_id=company_id)
            company = Company.objects.get(id=company_id)
            self.stdout.write(f'[Company] Filtering to: {company.name}\n')

        total = qs.count()
        self.stdout.write(f'[Total] News releases to scan: {total}\n')

        matches = []
        already_flagged = 0
        suppressed_dismissed = 0
        processed = 0

        for news in qs.iterator(chunk_size=500):
            processed += 1
            if processed % 500 == 0:
                self.stdout.write(f'[Progress] Processed {processed}/{total}...')

            if NewsReportFlag.objects.filter(news_release=news).exists():
                already_flagged += 1
                continue

            title = news.title or ''
            title_lower = title.lower()
            detected = [kw for kw in REPORT_KEYWORDS if kw in title_lower]
            if not detected:
                continue

            # Respect dismissals scoped to the report category only.
            is_similar, _matched = DismissedNewsURL.is_similar_to_dismissed(
                company=news.company,
                url=news.url,
                title=title,
                similarity_threshold=NEWS_SIMILARITY_THRESHOLD,
                reason='report_false_positive',
            )
            if is_similar:
                suppressed_dismissed += 1
                continue

            matches.append({'news': news, 'keywords': detected})

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('SCAN RESULTS'))
        self.stdout.write(f'{"="*80}\n')
        self.stdout.write(f'Scanned:                  {total}')
        self.stdout.write(f'Already flagged (skip):   {already_flagged}')
        self.stdout.write(f'Suppressed by dismissals: {suppressed_dismissed}')
        self.stdout.write(f'New matches:              {len(matches)}\n')

        if not matches:
            self.stdout.write(self.style.WARNING('[Info] No new report-related releases found.'))
            return

        # Cap detailed print to first 50 so output stays usable on large backfills
        preview = matches[:50]
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS(f'PREVIEW (first {len(preview)} of {len(matches)})'))
        self.stdout.write(f'{"="*80}\n')
        for i, m in enumerate(preview, 1):
            n = m['news']
            self.stdout.write(f"\n{i}. {n.company.name}")
            self.stdout.write(f"   Date:     {n.release_date}")
            t = n.title or ''
            self.stdout.write(f"   Title:    {t[:100]}{'...' if len(t) > 100 else ''}")
            self.stdout.write(f"   Keywords: {', '.join(m['keywords'])}")
            self.stdout.write(f"   URL:      {n.url}")

        if dry_run:
            self.stdout.write(f'\n{self.style.WARNING("[Dry Run] No flags written.")}')
            self.stdout.write(f'   Run without --dry-run to create {len(matches)} flag(s).')
            return

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('CREATING FLAGS'))
        self.stdout.write(f'{"="*80}\n')

        created_count = 0
        for m in matches:
            news = m['news']
            NewsReportFlag.objects.create(
                news_release=news,
                detected_keywords=m['keywords'],
                status='pending',
            )
            created_count += 1
        self.stdout.write(self.style.SUCCESS(f'[Success] Created {created_count} flag(s)'))

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(f'{"="*80}')
        self.stdout.write(f'Period: {cutoff_date} -> {timezone.now().date()}')
        self.stdout.write(f'Scanned: {total}, Already-flagged: {already_flagged}, '
                          f'Dismissed: {suppressed_dismissed}, Created: {created_count}\n')
        self.stdout.write(self.style.SUCCESS('[Complete] Backfill finished.\n'))
