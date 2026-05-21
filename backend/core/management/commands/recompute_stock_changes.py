"""
Recompute StockPrice.change_amount / change_percent from consecutive closes.

The stock scraper historically stored change_percent from a fragile
positional HTML parse, producing values unrelated to the close prices
(e.g. a 0.17 close tagged '+10%' when the prior close was 0.23). This
recomputes both fields as the true day-over-day move from each company's
own price series.

Usage:
    python manage.py recompute_stock_changes
    python manage.py recompute_stock_changes --dry-run
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import StockPrice

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Recompute StockPrice change_amount/change_percent from consecutive closes."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report how many rows would change without saving.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        company_ids = list(
            StockPrice.objects.values_list('company_id', flat=True).distinct()
        )
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f"Recomputing changes for {len(company_ids)} companies…"
        )

        batch = []
        updated = 0

        for company_id in company_ids:
            rows = list(
                StockPrice.objects.filter(company_id=company_id).order_by('date')
            )
            prev_close = None
            for row in rows:
                if prev_close and prev_close > 0:
                    delta = row.close_price - prev_close
                    change_amount = delta.quantize(Decimal('0.0001'))
                    change_percent = (
                        delta / prev_close * Decimal('100')
                    ).quantize(Decimal('0.01'))
                else:
                    change_amount = Decimal('0')
                    change_percent = Decimal('0')

                if (row.change_amount != change_amount
                        or row.change_percent != change_percent):
                    row.change_amount = change_amount
                    row.change_percent = change_percent
                    batch.append(row)
                    updated += 1
                    if len(batch) >= BATCH_SIZE and not dry_run:
                        StockPrice.objects.bulk_update(
                            batch, ['change_amount', 'change_percent'],
                        )
                        batch = []

                prev_close = row.close_price

        if batch and not dry_run:
            StockPrice.objects.bulk_update(
                batch, ['change_amount', 'change_percent'],
            )

        verb = 'would be corrected' if dry_run else 'corrected'
        self.stdout.write(
            self.style.SUCCESS(f"Done — {updated} StockPrice row(s) {verb}.")
        )
