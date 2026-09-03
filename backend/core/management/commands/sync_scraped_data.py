"""
Bring the stores in line with "everything scraped lives in Postgres AND
ChromaDB" — the three gaps the 2026-09-03 dual-store audit found.

1. **Bodies** — NewsRelease.full_text and CompanyNews.content were empty on
   every row of both tables: the embed pipeline fetched each article, chunked
   it, and threw the text away. The pipeline now writes bodies as it fetches;
   this command recovers the ~9,000 already-fetched ones from their stored
   chunks, with no re-fetching. The chunker is deterministic (400 tokens,
   overlap 50), so a body is rebuilt by joining chunk token streams minus the
   overlap — and then PROVEN by re-chunking the result: only if that
   reproduces the stored chunk texts byte-for-byte is the body written.
   Anything that fails the proof is skipped and counted, never guessed at.

2. **Tags** — 1,905 NewsArticle rows held their category list in `summary`
   ("Analysis,Financing,News") because the card scraper's <p> fallback caught
   the category links. The scraper now routes these to `tags`; this moves
   the stored ones.

3. **Industry headlines** — NewsArticle was the one scraped dataset with no
   vectors at all. embed_industry_articles() (also run nightly) embeds the
   backlog of headlines.

Idempotent throughout: bodies are only written where empty, tag-summaries
only moved where they still look like tags, articles only embedded where no
chunk exists.

    python manage.py sync_scraped_data --dry-run
    python manage.py sync_scraped_data
"""

import re
import time

from django.core.management.base import BaseCommand

from core.models import CompanyNews, NewsArticle, NewsChunk, NewsRelease
from mcp_servers.news_scraper import _looks_like_tag_list

OVERLAP = 50
TITLE_PREFIX = re.compile(r'^Title: [^\n]*\n\n', re.S)
MIN_BODY = 50


class Command(BaseCommand):
    help = "Reconcile scraped data into both Postgres and ChromaDB."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry = options['dry_run']
        tag = '[DRY RUN] ' if dry else ''

        # ---------------------------------------------------------- 2. tags
        moved = 0
        for article in NewsArticle.objects.exclude(summary=''):
            if _looks_like_tag_list(article.summary):
                moved += 1
                if not dry:
                    NewsArticle.objects.filter(id=article.id).update(
                        tags=[t.strip() for t in article.summary.split(',')
                              if t.strip()],
                        summary='',
                    )
        self.stdout.write(f"{tag}tags: {moved} summary-held category lists "
                          f"{'would move' if dry else 'moved'} to tags")

        # --------------------------------------------------------- 1. bodies
        from mcp_servers.news_content_processor import NewsContentProcessor
        processor = NewsContentProcessor()

        started = time.time()
        for model, fk, body_field in (
            (NewsRelease, 'news_release_id', 'full_text'),
            (CompanyNews, 'company_news_id', 'content'),
        ):
            written = failed_proof = 0
            source_ids = (
                NewsChunk.objects.filter(**{f'{fk}__isnull': False})
                .values_list(fk, flat=True).distinct()
            )
            empty = model.objects.filter(
                id__in=source_ids, **{body_field: ''}
            ).values_list('id', flat=True)

            for source_id in empty:
                chunks = list(
                    NewsChunk.objects.filter(**{fk: source_id})
                    .order_by('chunk_index').values_list('text', flat=True)
                )
                if not chunks or not all(chunks):
                    failed_proof += 1
                    continue

                if len(chunks) == 1:
                    full = chunks[0]
                else:
                    tokens = processor.tokenizer.encode(chunks[0])
                    for piece in chunks[1:]:
                        tokens += processor.tokenizer.encode(piece)[OVERLAP:]
                    full = processor.tokenizer.decode(tokens)

                # The proof: reconstruction is accepted only if re-chunking it
                # reproduces the stored chunks exactly.
                rechunked = [c['text'] for c in processor._chunk_text(full)]
                if rechunked != chunks:
                    failed_proof += 1
                    continue

                body = TITLE_PREFIX.sub('', full, count=1)
                if len(body) < MIN_BODY:
                    failed_proof += 1
                    continue
                written += 1
                if not dry:
                    model.objects.filter(id=source_id).update(
                        **{body_field: body})

            self.stdout.write(
                f"{tag}bodies/{model.__name__}: {written} "
                f"{'provable' if dry else 'written'}, "
                f"{failed_proof} failed the re-chunk proof (left empty)"
            )
        self.stdout.write(f"  ({time.time() - started:.0f}s)")

        # ------------------------------------------------- 3. industry embeds
        pending = (NewsArticle.objects.filter(is_visible=True)
                   .exclude(id__in=NewsChunk.objects
                            .filter(news_article__isnull=False)
                            .values('news_article_id')).count())
        if dry:
            self.stdout.write(f"{tag}industry: {pending} headline(s) would embed")
        else:
            from core.tasks import embed_industry_articles
            result = embed_industry_articles(limit=pending or 1)
            self.stdout.write(f"industry: {result}")

        if dry:
            self.stdout.write("\nNothing written. Drop --dry-run to apply.")
