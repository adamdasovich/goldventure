"""
Keep ChromaDB from outliving the Postgres rows it mirrors.

Chunks are deleted almost entirely by cascade — remove a NewsRelease,
CompanyNews or Document and its chunk rows go with it — but ChromaDB is a
separate store with no foreign keys, so its vectors stayed behind. A
retrieval that hit one cited a release that no longer existed.

That is not hypothetical: collapsing duplicate news releases on 2026-09-02
deleted 246 CompanyNews rows, 39 of which had chunks, and left 180 orphaned
vectors in `news_chunks`.

Two rules this module lives by:

* A delete must never fail because ChromaDB is down. The vector cleanup is
  best-effort and logs loudly; `manage.py reindex_chroma` remains the
  reconciler of record.
* The vectors go only after the database transaction commits. Deleting them
  inline would strand the embeddings if the transaction then rolled back,
  turning a no-op into permanent data loss.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# collection name -> chroma ids awaiting deletion, per transaction
_PENDING = {}
_BATCH = 500


def _still_live(collection_name, chroma_ids):
    """The subset of ids whose Postgres chunk row still exists.

    The queue is drained on commit, but nothing drains it on rollback — and
    Django offers no on_rollback hook. Rather than track transaction state,
    every flush re-checks the database and skips any id that still has a row.
    That makes the cleanup idempotent and, more to the point, means a stale
    queue entry from a rolled-back delete can never destroy a live vector.
    """
    from core.models import NewsChunk, DocumentChunk

    model = NewsChunk if collection_name == 'news_chunks' else DocumentChunk
    survivors = set(
        model.objects.filter(chroma_id__in=chroma_ids)
        .values_list('chroma_id', flat=True)
    )
    return [i for i in chroma_ids if i not in survivors]


def _flush(collection_name, chroma_ids):
    """Delete vectors from one collection. Never raises."""
    try:
        chroma_ids = _still_live(collection_name, chroma_ids)
        if not chroma_ids:
            return

        import os

        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.HttpClient(
            host=os.environ.get('CHROMA_HOST', 'localhost'),
            port=int(os.environ.get('CHROMA_PORT', 8002)),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = client.get_collection(collection_name)
        for start in range(0, len(chroma_ids), _BATCH):
            collection.delete(ids=chroma_ids[start:start + _BATCH])
        logger.info(
            "Removed %d orphaned vector(s) from ChromaDB collection %s",
            len(chroma_ids), collection_name,
        )
    except Exception:
        logger.exception(
            "Could not remove %d vector(s) from ChromaDB collection %s after "
            "their Postgres rows were deleted. The rows are gone; the vectors "
            "are not. Run `manage.py reindex_chroma` to reconcile.",
            len(chroma_ids), collection_name,
        )


def _queue(collection_name, chroma_id):
    """Batch one id, flushing once per transaction rather than per row.

    A callback is registered on every call, not only the first. Registering
    once looks tidier but breaks after a rollback: the queue survives (Django
    has no on_rollback), so the next delete sees a non-empty list, believes a
    callback is already pending, and registers nothing — and the flush stops
    happening entirely. Every call registering means the first callback to run
    drains everything and the rest find an empty list and do nothing. Any
    stale ids swept up that way are filtered by _still_live().
    """
    if not chroma_id:
        return
    _PENDING.setdefault(collection_name, []).append(chroma_id)

    def run(name=collection_name):
        ids = _PENDING.pop(name, [])
        if ids:
            _flush(name, ids)

    transaction.on_commit(run)


@receiver(post_delete, sender='core.NewsChunk', dispatch_uid='newschunk_chroma')
def _news_chunk_deleted(sender, instance, **kwargs):
    _queue('news_chunks', instance.chroma_id)


@receiver(post_delete, sender='core.DocumentChunk', dispatch_uid='docchunk_chroma')
def _document_chunk_deleted(sender, instance, **kwargs):
    _queue('document_chunks', instance.chroma_id)
