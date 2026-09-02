"""
Embed a profile vector for every company.

The `company_profiles` collection held 4 vectors for 396 companies, because
its only writer — store_company_profile_in_rag_task — is dispatched from the
onboard_company management command alone, so only companies onboarded that
particular way ever got one. Nothing read the collection either, until
`mining_find_companies_by_description` was added.

Unlike the news backfill, this is cheap: a profile is assembled from fields
the database already holds (description, tagline, ticker, projects), so there
is no article to fetch. The whole platform is minutes, not hours.

Idempotent: store_company_profile_isolated deletes a company's existing
vector before writing the new one, so re-running refreshes rather than
duplicates. Worth re-running after a batch of renames or description edits.

    python manage.py backfill_company_profiles --dry-run
    python manage.py backfill_company_profiles
    python manage.py backfill_company_profiles --only-missing
"""

import time

from django.core.management.base import BaseCommand

from core.models import Company


class Command(BaseCommand):
    help = "Write a company_profiles vector for every company."

    def add_arguments(self, parser):
        parser.add_argument('--only-missing', action='store_true',
                            help='Skip companies that already have a vector.')
        parser.add_argument('--limit', type=int, default=None,
                            help='Stop after this many companies.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report the work without writing anything.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        companies = list(
            Company.objects.filter(is_deleted=False)
            .order_by('name').values_list('id', 'name')
        )

        existing = self._existing_ids()
        if options['only_missing'] and existing is not None:
            companies = [c for c in companies if c[0] not in existing]
        if options['limit']:
            companies = companies[:options['limit']]

        have = 'unknown' if existing is None else len(existing)
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}{len(companies)} companies to "
            f"embed (collection currently holds {have} vector(s))"
        )
        if dry_run:
            for _, name in companies[:10]:
                self.stdout.write(f"    {name[:60]}")
            if len(companies) > 10:
                self.stdout.write(f"    ... and {len(companies) - 10} more")
            self.stdout.write("Nothing written. Drop --dry-run to run.")
            return

        from core.chromadb_isolated import store_company_profile_isolated

        started = time.time()
        written = skipped = failed = 0
        for idx, (cid, name) in enumerate(companies, 1):
            try:
                result = store_company_profile_isolated(cid, timeout=120)
            except Exception as exc:                       # noqa: BLE001
                failed += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{idx}/{len(companies)}] {name[:40]:42s} RAISED {exc}"))
                continue

            inner = result.get('result') or {}
            if result.get('success') and inner.get('status') == 'success':
                written += 1
                note = f"{inner.get('chars_stored', 0):5d} chars"
            elif inner.get('status') == 'skipped':
                # No description, tagline or projects — nothing to embed.
                skipped += 1
                note = "skipped (no profile data)"
            else:
                failed += 1
                note = self.style.WARNING(
                    f"FAILED {str(result.get('error') or inner.get('message'))[:44]}")

            if idx % 25 == 0 or idx == len(companies) or 'FAILED' in str(note):
                rate = idx / (time.time() - started)
                self.stdout.write(
                    f"  [{idx}/{len(companies)}] {name[:40]:42s} {note}  "
                    f"(~{(len(companies) - idx) / rate / 60:.1f} min left)"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone in {(time.time() - started) / 60:.1f} min — "
            f"{written} written, {skipped} skipped (no data), {failed} failed."
        ))

    @staticmethod
    def _existing_ids():
        """Company ids already in the collection, or None if unreachable."""
        try:
            import os

            import chromadb
            from chromadb.config import Settings as ChromaSettings

            client = chromadb.HttpClient(
                host=os.environ.get('CHROMA_HOST', 'localhost'),
                port=int(os.environ.get('CHROMA_PORT', 8002)),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            collection = client.get_collection('company_profiles')
            batch = collection.get(limit=10000, include=['metadatas'])
            return {
                (m or {}).get('company_id')
                for m in (batch.get('metadatas') or [])
            }
        except Exception:                                   # noqa: BLE001
            return None
