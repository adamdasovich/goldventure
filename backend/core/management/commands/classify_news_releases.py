"""
Backfill NewsRelease.release_type by classifying each record's title.

The scrapers historically stored every release with the literal string
'news_release' (not even a valid choice), so catalyst-impact analytics
collapsed into a single bucket. This command reclassifies stored records.

Usage:
    python manage.py classify_news_releases          # fix only unclassified
    python manage.py classify_news_releases --all    # reclassify everything
    python manage.py classify_news_releases --dry-run # report, change nothing
"""

from collections import Counter

from django.core.management.base import BaseCommand

from core.models import NewsRelease
from core.news_classification import classify_release_type, VALID_RELEASE_TYPES

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Classify NewsRelease.release_type from title keywords."

    def add_arguments(self, parser):
        parser.add_argument(
            '--all', action='store_true',
            help='Reclassify every record (default: only invalid/unclassified).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show the classification breakdown without saving.',
        )

    def handle(self, *args, **options):
        reclassify_all = options['all']
        dry_run = options['dry_run']

        queryset = NewsRelease.objects.all()
        if not reclassify_all:
            # Only touch records whose type is not a valid choice.
            queryset = queryset.exclude(release_type__in=VALID_RELEASE_TYPES)

        total = queryset.count()
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}Classifying {total} news release(s)"
            f" ({'all records' if reclassify_all else 'unclassified only'})…"
        )
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to do."))
            return

        counts = Counter()
        batch = []
        updated = 0

        for nr in queryset.only('id', 'title', 'release_type').iterator(
            chunk_size=BATCH_SIZE
        ):
            new_type = classify_release_type(nr.title)
            counts[new_type] += 1
            if nr.release_type != new_type:
                nr.release_type = new_type
                batch.append(nr)
            if len(batch) >= BATCH_SIZE and not dry_run:
                NewsRelease.objects.bulk_update(batch, ['release_type'])
                updated += len(batch)
                batch = []

        if batch and not dry_run:
            NewsRelease.objects.bulk_update(batch, ['release_type'])
            updated += len(batch)

        self.stdout.write("")
        self.stdout.write("Classification breakdown:")
        for release_type, n in counts.most_common():
            pct = n / total * 100
            self.stdout.write(f"  {release_type:<16} {n:>6}  ({pct:.1f}%)")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run — no records changed."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nDone — updated {updated} record(s).")
            )
