"""
Clean scraped URL cruft from Document titles.

Some Document.title values carry cache-busting query strings copied from
the source URL — e.g. '2022 yellowknife technical report?v=020506' or
'fact sheet v2?2kjnty'. Document titles never legitimately contain a '?'
(they are report / presentation / fact-sheet names), so everything from
the first '?' onward is trimmed.

Usage:
    python manage.py clean_document_titles            # apply
    python manage.py clean_document_titles --dry-run  # preview only
"""

from django.core.management.base import BaseCommand

from core.models import Document

BATCH_SIZE = 500


def clean_title(title: str) -> str:
    """Trim a Document title at the first '?' (URL query-string separator)."""
    if not title or '?' not in title:
        return title
    return title.split('?', 1)[0].strip()


class Command(BaseCommand):
    help = "Strip scraped URL query-string cruft from Document titles."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would change without saving.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        candidates = Document.objects.filter(title__contains='?')
        total = candidates.count()
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f"Checking {total} document title(s) containing '?'…"
        )
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to clean."))
            return

        batch = []
        changed = 0
        for doc in candidates.only('id', 'title').iterator(chunk_size=BATCH_SIZE):
            cleaned = clean_title(doc.title)
            # Skip no-op changes and never blank a title.
            if cleaned and cleaned != doc.title:
                self.stdout.write(f"  {doc.title!r}  ->  {cleaned!r}")
                doc.title = cleaned
                batch.append(doc)
                changed += 1
                if len(batch) >= BATCH_SIZE and not dry_run:
                    Document.objects.bulk_update(batch, ['title'])
                    batch = []

        if batch and not dry_run:
            Document.objects.bulk_update(batch, ['title'])

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\nDry run — {changed} title(s) would change.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nDone — cleaned {changed} title(s).")
            )
