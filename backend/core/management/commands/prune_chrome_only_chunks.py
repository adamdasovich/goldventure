"""
Deal with the chunks that are almost entirely site chrome.

`clean_news_chunk_boilerplate` refuses to touch a chunk when stripping would
leave under 80 characters or under 35% of the original — gutting a chunk into
a meaningless vector is worse than leaving it. That was the right default,
but it left 64 chunks sitting in the index at roughly 84% navigation: one
LaFleur chunk is 1,331 characters of which 214 are the release.

A polluted vector is not harmless. It competes for retrieval slots against
chunks that are actually about the question.

Each one gets one of three outcomes:

* **deleted** — its real content already appears in a sibling chunk of the
  same article, so the index loses nothing. The post_delete signal removes
  the vector with the row.
* **cleaned** — it carries content no sibling has. A short accurate vector
  beats a long polluted one, so it is stripped even though it ends up small.
* **kept** — it is the only chunk for its article and stripping would leave
  almost nothing. Deleting would drop the article from RAG entirely, so it
  stays and is reported.

Coverage is measured on words of four or more characters, which ignores
articles and prepositions without needing a stopword list.

    python manage.py prune_chrome_only_chunks --dry-run
    python manage.py prune_chrome_only_chunks
"""

import re
import time

from django.core.management.base import BaseCommand

from core.models import NewsChunk
from mcp_servers.news_content_processor import _is_boilerplate_line

MARKERS = [
    "we use cookies", "cookie policy", "subscribe to our newsletter",
    "all rights reserved", "share on twitter", "follow us on",
    "sign up for", "privacy policy", "skip to content",
    "javascript is disabled", "site by",
]

MIN_KEPT_CHARS = 80
MIN_KEPT_RATIO = 0.35
# Above this share of its words found in siblings, a chunk adds nothing.
COVERED_AT = 0.80
# Below this, what survives is not worth embedding even on its own.
SALVAGE_FLOOR = 40

WORD = re.compile(r'[a-z0-9]{4,}')


class Command(BaseCommand):
    help = "Delete or clean news chunks that are almost entirely site chrome."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report the decisions without writing.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        candidates = self._thin_chunks()
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}{len(candidates)} chunk(s) are "
            f"mostly chrome"
        )

        to_delete, to_clean, kept = [], [], []
        for chunk, original, cleaned in candidates:
            siblings = self._siblings(chunk)
            if not siblings:
                if len(cleaned) >= SALVAGE_FLOOR:
                    to_clean.append((chunk, cleaned, "only chunk, salvageable"))
                else:
                    kept.append((chunk, original, cleaned,
                                 "only chunk for its article"))
                continue

            coverage = self._coverage(cleaned, siblings)
            if coverage >= COVERED_AT:
                to_delete.append((chunk, coverage, len(siblings)))
            elif len(cleaned) >= SALVAGE_FLOOR:
                to_clean.append(
                    (chunk, cleaned, f"unique ({coverage:.0%} covered)"))
            else:
                kept.append((chunk, original, cleaned,
                             f"unique but only {len(cleaned)} chars survive"))

        self.stdout.write(
            f"  delete : {len(to_delete)} (content already in a sibling)\n"
            f"  clean  : {len(to_clean)} (unique content, keep it short)\n"
            f"  keep   : {len(kept)} (would lose the article)"
        )
        for chunk, cov, n in to_delete[:5]:
            self.stdout.write(
                f"      del {chunk.id}: {cov:.0%} covered by {n} sibling(s) "
                f"[{(chunk.source_title or '')[:40]}]")
        for chunk, _o, _c, why in kept[:5]:
            self.stdout.write(
                f"      keep {chunk.id}: {why} "
                f"[{(chunk.source_title or '')[:40]}]")

        if dry_run:
            self.stdout.write("\nNothing written. Drop --dry-run to apply.")
            return

        started = time.time()
        collection = self._collection()
        if collection is None and to_clean:
            self.stderr.write("ChromaDB unreachable; aborting before any write.")
            return

        cleaned_n = 0
        embeddable = [(c, t) for c, t, _ in to_clean if c.chroma_id]
        if embeddable:
            try:
                # Re-embed first. If this fails, Postgres is untouched and the
                # stored text still matches the vector — better than Postgres
                # claiming a cleanliness the index does not have.
                collection.update(
                    ids=[c.chroma_id for c, _ in embeddable],
                    documents=[t for _, t in embeddable],
                )
            except Exception as exc:                        # noqa: BLE001
                self.stderr.write(f"  re-embed failed, nothing written: {exc}")
                return
            for chunk, text in embeddable:
                chunk.text = text
            NewsChunk.objects.bulk_update([c for c, _ in embeddable], ['text'])
            cleaned_n = len(embeddable)

        # A chunk with no chroma_id has no vector to fix, so cleaning its text
        # would only desynchronise the two stores. Report rather than guess.
        orphans = [c for c, _, _ in to_clean if not c.chroma_id]
        if orphans:
            self.stdout.write(self.style.WARNING(
                f"  {len(orphans)} chunk(s) have no chroma_id and were left "
                f"alone: {[c.id for c in orphans][:10]}"))

        # Vectors follow the rows: core.signals removes each chroma_id on
        # post_delete, after the transaction commits.
        deleted_n = 0
        if to_delete:
            deleted_n = NewsChunk.objects.filter(
                id__in=[c.id for c, _, _ in to_delete]).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f"\nDone in {time.time() - started:.0f}s — {deleted_n} deleted, "
            f"{cleaned_n} cleaned, {len(kept)} kept."
        ))

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _strip(text):
        return '\n'.join(
            line for line in (text or '').split('\n')
            if line.strip() and not _is_boilerplate_line(line)
        )

    def _thin_chunks(self):
        ids = set()
        for marker in MARKERS:
            ids |= set(NewsChunk.objects.filter(text__icontains=marker)
                       .values_list('id', flat=True))
        out = []
        for chunk in NewsChunk.objects.filter(id__in=ids):
            original = chunk.text or ''
            cleaned = self._strip(original)
            if cleaned == original:
                continue
            if (len(cleaned) < MIN_KEPT_CHARS
                    or (original and len(cleaned) / len(original) < MIN_KEPT_RATIO)):
                out.append((chunk, original, cleaned))
        return out

    @staticmethod
    def _siblings(chunk):
        """Other chunks from the same news item."""
        if chunk.news_release_id:
            field, value = 'news_release_id', chunk.news_release_id
        elif chunk.company_news_id:
            field, value = 'company_news_id', chunk.company_news_id
        elif chunk.news_article_id:
            field, value = 'news_article_id', chunk.news_article_id
        else:
            return []
        return list(NewsChunk.objects.filter(**{field: value})
                    .exclude(id=chunk.id))

    @staticmethod
    def _collection():
        """The news_chunks collection, or None if ChromaDB is unreachable."""
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

    @staticmethod
    def _coverage(cleaned, siblings):
        """Share of the chunk's own words that siblings already contain."""
        mine = set(WORD.findall(cleaned.lower()))
        if not mine:
            return 1.0
        theirs = set()
        for sibling in siblings:
            theirs |= set(WORD.findall((sibling.text or '').lower()))
        return len(mine & theirs) / len(mine)
