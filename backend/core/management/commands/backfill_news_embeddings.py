"""
Embed historical news that has no vectors, oldest backlog first.

Why this is a supervised command and not a beat task
----------------------------------------------------
Neither NewsRelease.full_text nor CompanyNews.content is ever populated — the
scrapers deliberately skip body extraction, because fetching every article
would add hundreds of requests per company to the nightly crawl. So embedding
an item means fetching its article, roughly 5 seconds each. The nightly
`embed_recent_news_for_rag_task` keeps up with new news, about 20 items a day.
Clearing the historical backlog is a different size of job: six months is
~4,000 items and ~6 hours of crawling against ~340 external sites, which
wants a person watching it.

Resumable by construction
-------------------------
Nothing is tracked. Each run recomputes what is still missing, and
_process_company_news skips individual items that already have chunks, so
interrupting this and re-running it simply continues. Re-running after it
finishes is a no-op.

Usage
-----
    python manage.py backfill_news_embeddings --months 6 --dry-run
    python manage.py backfill_news_embeddings --months 6
    python manage.py backfill_news_embeddings --months 6 --max-companies 25
"""

import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Company, CompanyNews, NewsChunk, NewsRelease

# Per-item budget observed live: ~5.3s, dominated by the article fetch.
SECONDS_PER_ITEM = 6
MIN_TIMEOUT = 180
# Importing voyageai -> transformers -> torch, paid once per subprocess.
SUBPROCESS_STARTUP = 40


class Command(BaseCommand):
    help = "Embed historical news releases that have no vectors yet."

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=6,
                            help='How far back to embed (default 6).')
        parser.add_argument('--max-companies', type=int, default=None,
                            help='Stop after this many companies.')
        parser.add_argument('--batch-size', type=int, default=10,
                            help='Companies per subprocess (default 10). '
                                 'Larger amortises startup further but widens what one SIGSEGV interrupts.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report the work without embedding anything.')

    def handle(self, *args, **options):
        months = options['months']
        dry_run = options['dry_run']
        cutoff = timezone.localtime().date() - timedelta(days=months * 30 + 2)

        pending = self._pending_by_company(cutoff)
        # Smallest first: the long tail finishes early, so an interrupted run
        # still leaves the most companies with usable coverage.
        order = sorted(pending.items(), key=lambda kv: kv[1])
        if options['max_companies']:
            order = order[:options['max_companies']]

        total_items = sum(n for _, n in order)
        names = dict(
            Company.objects.filter(id__in=[c for c, _ in order])
            .values_list('id', 'name')
        )

        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f"{len(order)} companies, {total_items} unembedded items since "
            f"{cutoff} — est {total_items * SECONDS_PER_ITEM / 3600:.1f}h"
        )
        if dry_run:
            for cid, n in order[-12:]:
                self.stdout.write(f"    {names.get(cid, cid)[:44]:46s} {n}")
            self.stdout.write("Nothing embedded. Drop --dry-run to run.")
            return

        from core.chromadb_isolated import process_news_companies_isolated

        started = time.time()
        done_items = done_chunks = failed = done_companies = 0
        batch_size = options['batch_size']

        for start in range(0, len(order), batch_size):
            batch = order[start:start + batch_size]
            specs = [{'id': cid, 'limit': n} for cid, n in batch]
            # One interpreter for the whole batch, so the ~16s of importing
            # torch is paid once instead of per company.
            budget = (SUBPROCESS_STARTUP
                      + sum(n for _, n in batch) * SECONDS_PER_ITEM
                      + len(batch) * 20)
            t0 = time.time()
            result = process_news_companies_isolated(
                specs, timeout=max(MIN_TIMEOUT, budget))

            # Present whether the batch succeeded, crashed or timed out: the
            # child reports each company as it finishes, so the ones that
            # completed before a SIGSEGV are still here.
            per_company = result.get('results', {})
            for cid, n_pending in batch:
                name = names.get(cid, str(cid))
                done_companies += 1
                item = per_company.get(cid) or per_company.get(str(cid))
                if item is None:
                    failed += 1
                    note = self.style.WARNING("no result (batch cut short)")
                elif item.get('success'):
                    inner = item.get('result', {})
                    items = inner.get('news_items_processed', 0)
                    chunks = inner.get('chunks_created', 0)
                    done_items += items
                    done_chunks += chunks
                    note = f"{items:3d} items {chunks:4d} chunks"
                else:
                    failed += 1
                    note = self.style.WARNING(
                        f"FAILED {str(item.get('error'))[:40]}")
                self.stdout.write(
                    f"  [{done_companies}/{len(order)}] {name[:38]:40s} {note}")

            elapsed = time.time() - started
            rate = done_companies / elapsed if elapsed else 0
            remaining = (len(order) - done_companies) / rate / 3600 if rate else 0
            self.stdout.write(
                f"    batch of {len(batch)} in {time.time() - t0:.0f}s "
                f"({(time.time() - t0) / len(batch):.1f}s/company) — "
                f"~{remaining:.1f}h left"
            )
            if not result.get('success') and not per_company:
                self.stdout.write(self.style.WARNING(
                    f"    batch produced nothing: {str(result.get('error'))[:70]}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone in {(time.time() - started) / 3600:.2f}h — "
            f"{done_items} items embedded, {done_chunks} chunks, {failed} failed. "
            f"NewsChunk total now {NewsChunk.objects.count()}."
        ))

    @staticmethod
    def _pending_by_company(cutoff):
        """{company_id: unembedded item count} within the window."""
        embedded_nr = set(
            NewsChunk.objects.filter(news_release__isnull=False)
            .values_list('news_release_id', flat=True)
        )
        embedded_cn = set(
            NewsChunk.objects.filter(company_news__isnull=False)
            .values_list('company_news_id', flat=True)
        )
        counts = {}
        for cid, rid in NewsRelease.objects.filter(
                release_date__gte=cutoff).values_list('company_id', 'id'):
            if rid not in embedded_nr:
                counts[cid] = counts.get(cid, 0) + 1
        for cid, rid in CompanyNews.objects.filter(
                publication_date__gte=cutoff).values_list('company_id', 'id'):
            if rid not in embedded_cn:
                counts[cid] = counts.get(cid, 0) + 1
        return counts
