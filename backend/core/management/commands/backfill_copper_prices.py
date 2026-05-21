"""
One-off backfill of historical daily copper prices from Yahoo Finance.

Usage:
    python manage.py backfill_copper_prices
    python manage.py backfill_copper_prices --start 2026-01-01

Safe to re-run — days that already have a CU row are skipped.
"""

from django.core.management.base import BaseCommand

from mcp_servers.base_metals_scraper import backfill_copper


class Command(BaseCommand):
    help = 'Backfill historical daily copper prices into MetalPrice from Yahoo Finance.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            default='2026-01-01',
            help='Earliest date to backfill (YYYY-MM-DD). Default: 2026-01-01',
        )

    def handle(self, *args, **options):
        start = options['start']
        self.stdout.write(f'Backfilling copper prices from {start}...')

        result = backfill_copper(start_date=start)

        if not result.get('success'):
            self.stderr.write(self.style.ERROR(
                f"Backfill failed: {result.get('error', 'unknown error')}"
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Done — {result['created']} rows created, "
            f"{result.get('skipped', 0)} skipped (already present)."
        ))
        if result.get('first_day'):
            self.stdout.write(
                f"Range: {result['first_day']} → {result['last_day']}"
            )
