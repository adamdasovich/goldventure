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


class Command(BaseCommand):
    help = "Embed historical news releases that have no vectors yet."

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=6,
                            help='How far back to embed (default 6).')
        parser.add_argument('--max-companies', type=int, default=None,
                            help='Stop after this many companies.')
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

        from core.chromadb_isolated import process_company_news_isolated

        started = time.time()
        done_items = done_chunks = failed = 0
        for idx, (cid, n_pending) in enumerate(order, 1):
            name = names.get(cid, str(cid))
            # A company with 99 releases cannot finish inside the default 180s.
            timeout = max(MIN_TIMEOUT, n_pending * SECONDS_PER_ITEM + 60)
            t0 = time.time()
            try:
                result = process_company_news_isolated(
                    company_name=name,
                    company_id=cid,
                    limit=n_pending,
                    timeout=timeout,
                )
            except Exception as exc:                      # noqa: BLE001
                failed += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{idx}/{len(order)}] {name[:38]:40s} RAISED {exc}"))
                continue

            if result.get('success'):
                inner = result.get('result', {})
                items = inner.get('news_items_processed', 0)
                chunks = inner.get('chunks_created', 0)
                done_items += items
                done_chunks += chunks
                note = f"{items:3d} items {chunks:4d} chunks"
            else:
                failed += 1
                note = self.style.WARNING(
                    f"FAILED {str(result.get('error'))[:40]}")

            elapsed = time.time() - started
            rate = done_items / elapsed if elapsed else 0
            remaining = (total_items - done_items) / rate / 3600 if rate else 0
            self.stdout.write(
                f"  [{idx}/{len(order)}] {name[:38]:40s} {note}  "
                f"({time.time() - t0:.0f}s, ~{remaining:.1f}h left)"
            )

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
