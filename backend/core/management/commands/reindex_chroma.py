"""
Reconcile ChromaDB against PostgreSQL.

Background
----------
`RAGManager.store_document_chunks()` writes to PostgreSQL and ChromaDB in two
separate, non-atomic steps: the DocumentChunk rows (including their `chroma_id`)
are committed first, then `collection.add()` embeds and stores the vectors. If
the embedding call fails — Voyage rate limit, timeout, network blip — the
Postgres rows survive with a `chroma_id` pointing at a vector that was never
written, and nothing retries. Over time that produced a large silent gap:
32,228 DocumentChunk rows against 3,147 vectors indexed.

This command finds chunks that Postgres thinks are indexed but ChromaDB does not
have, and re-embeds only those. It is idempotent and resumable — rerun it freely.

Separately, the `news_chunks` collection's HNSW segment is corrupt: under
chromadb 1.3.7 both `.count()` and `.query()` on it abort the process with
SIGSEGV inside the Rust binding, so it cannot be reconciled in place and must be
dropped and rebuilt. Use `--rebuild` for that; it never reads the old vectors.

    Back up chroma_db/ before running --rebuild.

Usage
-----
    python manage.py reindex_chroma --dry-run
    python manage.py reindex_chroma --collection documents
    python manage.py reindex_chroma --collection news --rebuild
    python manage.py reindex_chroma            # both collections
"""

import time

from django.core.management.base import BaseCommand

from core.models import DocumentChunk, NewsChunk


class Command(BaseCommand):
    help = "Re-embed PostgreSQL chunks that are missing from ChromaDB."

    def add_arguments(self, parser):
        parser.add_argument(
            '--collection',
            choices=['documents', 'news', 'both'],
            default='both',
            help="Which collection to reconcile (default: both).",
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=128,
            help="Chunks per embedding call (default: 128).",
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help="Stop after this many chunks. 0 = no limit.",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Report the gap without writing anything.",
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help=(
                "Drop the collection and re-embed every Postgres chunk from "
                "scratch. Required when the existing HNSW segment is corrupt — "
                "the old vectors are never read. Back up chroma_db/ first."
            ),
        )

    def handle(self, *args, **opts):
        from mcp_servers.rag_utils import RAGManager

        rag = RAGManager()
        names = {'documents': 'document_chunks', 'news': 'news_chunks'}
        labels = (
            ['documents', 'news'] if opts['collection'] == 'both'
            else [opts['collection']]
        )

        for label in labels:
            collection = (
                self._recreate(rag, names[label], opts)
                if opts['rebuild'] else
                (rag.collection if label == 'documents' else rag.news_collection)
            )
            self._reconcile(label, collection, opts)

    # ------------------------------------------------------------------

    def _recreate(self, rag, name, opts):
        """Drop and recreate a collection without reading its vectors."""
        self.stdout.write(self.style.WARNING(f"  Dropping collection '{name}'..."))
        if opts['dry_run']:
            self.stdout.write(self.style.NOTICE("  Dry run — not dropping."))
            return rag.chroma_client.get_collection(name)
        try:
            rag.chroma_client.delete_collection(name)
        except Exception as exc:
            self.stdout.write(f"  (delete returned: {exc})")
        return rag.chroma_client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=rag.embedding_function,
        )

    def _reconcile(self, label, collection, opts):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== {label} ==="))

        pg_ids = self._postgres_ids(label)
        self.stdout.write(f"  PostgreSQL chunks : {len(pg_ids):,}")

        if opts['rebuild']:
            # The collection was just recreated (or, in a dry run, is unreadable
            # because its segment is corrupt) — everything counts as missing.
            indexed = set()
            self.stdout.write("  ChromaDB vectors  : 0 (rebuilt)")
        else:
            indexed = self._chroma_ids(collection)
            self.stdout.write(f"  ChromaDB vectors  : {len(indexed):,}")

        missing = [cid for cid in pg_ids if cid not in indexed]
        self.stdout.write(
            self.style.WARNING(f"  Missing from index: {len(missing):,}")
            if missing else
            self.style.SUCCESS("  In sync — nothing to do.")
        )
        if not missing:
            return

        if opts['limit']:
            missing = missing[:opts['limit']]
            self.stdout.write(f"  Limited to        : {len(missing):,}")

        if opts['dry_run']:
            self.stdout.write(self.style.NOTICE("  Dry run — no writes."))
            return

        batch_size = opts['batch_size']
        done = failed = 0
        started = time.time()

        for start in range(0, len(missing), batch_size):
            batch_ids = missing[start:start + batch_size]
            payload = self._build_payload(label, batch_ids)
            if not payload['ids']:
                continue
            try:
                # upsert, not add: safe to rerun over partially-indexed batches.
                collection.upsert(
                    ids=payload['ids'],
                    documents=payload['documents'],
                    metadatas=payload['metadatas'],
                )
                done += len(payload['ids'])
            except Exception as exc:
                failed += len(payload['ids'])
                self.stderr.write(self.style.ERROR(
                    f"  batch at offset {start} failed: {exc}"
                ))
                # Back off briefly; the usual cause is an embedding rate limit.
                time.sleep(5)

            elapsed = time.time() - started
            rate = done / elapsed if elapsed else 0
            self.stdout.write(
                f"  {done:,}/{len(missing):,} re-embedded "
                f"({rate:.0f}/s, {failed:,} failed)",
                ending='\r',
            )
            self.stdout.flush()

        self.stdout.write("")
        style = self.style.SUCCESS if not failed else self.style.WARNING
        self.stdout.write(style(
            f"  Done: {done:,} re-embedded, {failed:,} failed, "
            f"{time.time() - started:.0f}s"
        ))
        try:
            self.stdout.write(f"  ChromaDB now holds: {collection.count():,}")
        except Exception as exc:
            # A count that aborts means the segment is still unhealthy.
            self.stderr.write(self.style.ERROR(f"  count() failed: {exc}"))

    # ------------------------------------------------------------------

    def _postgres_ids(self, label):
        model = DocumentChunk if label == 'documents' else NewsChunk
        return list(
            model.objects.exclude(chroma_id__isnull=True)
                         .exclude(chroma_id='')
                         .values_list('chroma_id', flat=True)
        )

    def _chroma_ids(self, collection):
        """Page through the collection to collect every stored id."""
        found = set()
        offset, page = 0, 5000
        while True:
            batch = collection.get(limit=page, offset=offset, include=[])
            ids = batch.get('ids') or []
            if not ids:
                break
            found.update(ids)
            offset += len(ids)
            if len(ids) < page:
                break
        return found

    @staticmethod
    def _news_source_id(chunk):
        """The originating row id, whichever news table the chunk came from."""
        return (
            chunk.company_news_id
            or chunk.news_release_id
            or chunk.news_article_id
            or ''
        )

    def _build_payload(self, label, chroma_ids):
        """Rebuild documents+metadata for the given chroma_ids from Postgres."""
        ids, documents, metadatas = [], [], []

        if label == 'documents':
            rows = (
                DocumentChunk.objects
                .filter(chroma_id__in=chroma_ids)
                .select_related('document', 'document__company')
            )
            for chunk in rows:
                doc = chunk.document
                if not chunk.text:
                    continue
                ids.append(chunk.chroma_id)
                documents.append(chunk.text)
                meta = {
                    'document_id': doc.id,
                    'chunk_index': chunk.chunk_index,
                    'company': doc.company.name,
                    # company_id was missing from the original write path, which
                    # forced every filtered search to string-match on name.
                    'company_id': doc.company_id,
                    'document_type': doc.document_type,
                    'document_date': str(doc.document_date),
                    'document_title': (doc.title or '')[:100],
                }
                if doc.project_id:
                    meta['project_id'] = doc.project_id
                if chunk.page_number is not None:
                    meta['page_number'] = chunk.page_number
                if chunk.section_title:
                    meta['section_title'] = chunk.section_title[:200]
                metadatas.append(meta)
        else:
            rows = (
                NewsChunk.objects
                .filter(chroma_id__in=chroma_ids)
                .select_related('company')
            )
            for chunk in rows:
                if not chunk.text:
                    continue
                ids.append(chunk.chroma_id)
                documents.append(chunk.text)
                metadatas.append({
                    'chunk_index': chunk.chunk_index,
                    # Chroma rejects None metadata values, and industry
                    # article chunks have no company. 0 is matched by no
                    # real company filter.
                    'company_id': chunk.company_id or 0,
                    # `company` (the name) must stay: RAGManager.search_news
                    # filters with where={"company": <name>}, so dropping it
                    # silently breaks every company-scoped news search.
                    'company': chunk.company.name if chunk.company else '',
                    'source_id': self._news_source_id(chunk),
                    'content_type': chunk.content_type,
                    'title': (chunk.source_title or '')[:100],
                    'url': chunk.source_url or '',
                    'date': str(chunk.source_date) if chunk.source_date else '',
                })

        return {'ids': ids, 'documents': documents, 'metadatas': metadatas}
