"""
Smoke-test the GA4 integration used by the weekly industry report.

Verifies that:
  1. GA4_PROPERTY_ID and GA4_CREDENTIALS_PATH env vars are set
  2. The service-account JSON exists and is readable
  3. The GA4 Data API responds with row data for the trailing 7 days
  4. /companies/{id}-{slug} paths join cleanly to Company records

Run on the server after dropping the service-account JSON in place:

    python manage.py test_ga4
    python manage.py test_ga4 --days 30 --top 50
"""

import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.reports.ga4 import _enabled, fetch_top_company_pageviews


class Command(BaseCommand):
    help = "Smoke-test the GA4 Data API integration."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7,
                            help='Window length in days (default 7).')
        parser.add_argument('--top', type=int, default=10,
                            help='Top N rows to display (default 10).')

    def handle(self, *args, **options):
        days = options['days']
        top = options['top']

        property_id = os.environ.get('GA4_PROPERTY_ID')
        creds_path = os.environ.get('GA4_CREDENTIALS_PATH')

        self.stdout.write(f"GA4_PROPERTY_ID:      {property_id or '(not set)'}")
        self.stdout.write(f"GA4_CREDENTIALS_PATH: {creds_path or '(not set)'}")

        if not _enabled():
            self.stdout.write(self.style.ERROR(
                "GA4 not enabled — both env vars must be set."
            ))
            return

        if creds_path and not os.path.exists(creds_path):
            self.stdout.write(self.style.ERROR(
                f"Credentials file not found at {creds_path}"
            ))
            return

        end = date.today()
        start = end - timedelta(days=days)
        self.stdout.write(f"Window: {start} -> {end}")

        rows = fetch_top_company_pageviews(start, end, top_n=top)
        if not rows:
            self.stdout.write(self.style.WARNING(
                "No rows returned. Either GA4 has no /companies/* pageviews "
                "in this window, the service-account lacks Viewer access to "
                "the property, or the GA4 client errored (check logs)."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"OK — {len(rows)} company pages with traffic:"
        ))
        for row in rows:
            self.stdout.write(
                f"  {row['ticker'] or '(no ticker)':10} "
                f"{row['company_name'][:40]:40} "
                f"{row['pageviews']:>6} views"
            )
