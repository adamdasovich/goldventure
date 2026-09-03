"""
Strip site chrome out of news chunks that were embedded before the extractor
learned to remove it.

`_fetch_content_from_url` now drops cookie banners, footers and nav labels
before chunking, so anything embedded from here on is clean. The chunks
already stored are not: measured with unambiguous phrases, 2,674 of 59,468
(4.5%) carry some, almost always as a tail. One 309-character Fireweed chunk
was mostly "SITE BY EXPLORATIONSITES.COM / We use cookies to ensure that we
give you the best experience".

No article is re-fetched. The text is already in Postgres, so this is a
clean-and-re-embed: strip the boilerplate lines, update NewsChunk.text, and
replace that chunk's vector. Roughly a thousand times cheaper than the
backfill that created them.

A chunk is only rewritten when stripping actually removes something and
leaves enough behind to be worth embedding; anything that would be gutted is
reported and left alone for a human.

    python manage.py clean_news_chunk_boilerplate --dry-run
    python manage.py clean_news_chunk_boilerplate
"""

import time

from django.core.management.base import BaseCommand

from core.models import NewsChunk
from mcp_servers.news_content_processor import _is_boilerplate_line

# Phrases that identify a chunk worth examining. Deliberately literal — an
# earlier regex sweep matched a loan agreement on "terms" and a resource
# estimate on "ok", so candidate selection stays unambiguous and the
# line-level classifier does the actual work.
MARKERS = [
    "we use cookies", "cookie policy", "subscribe to our newsletter",
    "all rights reserved", "share on twitter", "follow us on",
    "sign up for", "privacy policy", "skip to content",
    "javascript is disabled", "site by",
]

# Below this, a chunk has lost so much that re-embedding it would be worse
# than leaving it: report instead.
MIN_KEPT_CHARS = 80
MIN_KEPT_RATIO = 0.35


class Command(BaseCommand):
    help = "Remove site boilerplate from already-embedded news chunks."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change without writing.')
        parser.add_argument('--limit', type=int, default=None,
                            help='Stop after this many chunks.')
        parser.add_argument('--batch-size', type=int, default=200,
                            help='Chunks per ChromaDB update call (default 200).')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        candidate_ids = set()
        for marker in MARKERS:
            candidate_ids |= set(
                NewsChunk.objects.filter(text__icontains=marker)
                .values_list('id', flat=True)
            )
        candidates = list(NewsChunk.objects.filter(id__in=candidate_ids)
                          .order_by('id'))
        if options['limit']:
            candidates = candidates[:options['limit']]

        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}{len(candidates)} candidate "
            f"chunk(s) of {NewsChunk.objects.count()} contain a marker"
        )

        planned, gutted, unchanged = [], [], 0
        removed_chars = 0
        for chunk in candidates:
            original = chunk.text or ''
            kept = '\n'.join(
                line for line in original.split('\n')
                if line.strip() and not _is_boilerplate_line(line)
            )
            if kept == original:
                unchanged += 1
                continue
            if (len(kept) < MIN_KEPT_CHARS
                    or (original and len(kept) / len(original) < MIN_KEPT_RATIO)):
                gutted.append((chunk, len(original), len(kept)))
                continue
            planned.append((chunk, kept))
            removed_chars += len(original) - len(kept)

        self.stdout.write(
            f"  to clean : {len(planned)}  "
            f"(~{removed_chars:,} chars of chrome, "
            f"{removed_chars / max(len(planned), 1):.0f} per chunk)\n"
            f"  untouched: {unchanged} (marker matched inside real prose)\n"
            f"  too thin : {len(gutted)} (left alone — stripping would gut them)"
        )
        for chunk, before, after in gutted[:5]:
            self.stdout.write(
                f"      chunk {chunk.id}: {before} -> {after} chars "
                f"[{(chunk.source_title or '')[:44]}]"
            )

        if dry_run:
            for chunk, kept in planned[:3]:
                self.stdout.write(
                    f"\n    chunk {chunk.id} [{(chunk.source_title or '')[:44]}]"
                    f"\n      was: ...{(chunk.text or '')[-140:]!r}"
                    f"\n      now: ...{kept[-140:]!r}"
                )
            self.stdout.write("\nNothing written. Drop --dry-run to apply.")
            return

        if not planned:
            self.stdout.write(self.style.SUCCESS("Nothing to clean."))
            return

        collection = self._collection()
        if collection is None:
            self.stderr.write("ChromaDB unreachable; aborting before any write.")
            return

        started = time.time()
        batch_size = options['batch_size']
        updated = failed = 0
        for start in range(0, len(planned), batch_size):
            batch = planned[start:start + batch_size]
            # Only chunks that actually have a vector. Updating Postgres for
            # a chunk with no chroma_id would leave cleaned text behind a
            # stale embedding — the two stores must move together.
            embeddable = [(c, k) for c, k in batch if c.chroma_id]
            skipped_here = len(batch) - len(embeddable)
            if skipped_here:
                failed += skipped_here
                self.stderr.write(
                    f"  {skipped_here} chunk(s) in this batch have no chroma_id; "
                    f"left untouched")
            if not embeddable:
                continue
            try:
                # Re-embeds from the cleaned text; the id is unchanged, so the
                # vector is replaced rather than duplicated.
                collection.update(
                    ids=[c.chroma_id for c, _ in embeddable],
                    documents=[k for _, k in embeddable],
                )
            except Exception as exc:                        # noqa: BLE001
                failed += len(embeddable)
                self.stderr.write(f"  batch failed, Postgres left untouched: {exc}")
                continue

            for chunk, kept in embeddable:
                chunk.text = kept
            NewsChunk.objects.bulk_update([c for c, _ in embeddable], ['text'])
            updated += len(embeddable)
            self.stdout.write(
                f"  {updated}/{len(planned)} cleaned "
                f"({time.time() - started:.0f}s)"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone in {(time.time() - started) / 60:.1f} min — "
            f"{updated} chunks cleaned, {failed} failed, "
            f"{removed_chars:,} chars of chrome removed."
        ))

    @staticmethod
    def _collection():
        try:
            import os

            import chromadb
            from chromadb.config import Settings as ChromaSettings

            from mcp_servers.embeddings import get_embedding_function

            client = chromadb.HttpClient(
                host=os.environ.get('CHROMA_HOST', 'localhost'),
                port=int(os.environ.get('CHROMA_PORT', 8002)),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            client.heartbeat()
            return client.get_collection(
                'news_chunks', embedding_function=get_embedding_function())
        except Exception:                                    # noqa: BLE001
            return None
