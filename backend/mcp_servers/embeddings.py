"""
Embedding utilities for RAG functionality.

Uses Voyage AI for fast, high-quality embeddings.
Falls back to ChromaDB's default embeddings if Voyage AI is not configured.
"""

import logging
import os

logger = logging.getLogger(__name__)
from typing import List, Optional
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# Is voyageai installed? Answered WITHOUT importing it: find_spec locates the
# module but does not execute it.
#
# This used to be a plain `import voyageai` in a try/except, and that probe
# alone cost ~800MB of RSS on every process that reached this module - voyageai
# imports langchain_text_splitters, which imports transformers, which imports
# torch. The chain runs core/views/companies.py -> claude_integration/client.py
# -> document_search.py -> rag_utils.py -> here, so it was paid by gunicorn and
# every celery worker just to set a boolean.
#
# voyageai itself is imported where it is actually used: VoyageEmbeddingFunction
# .__init__ and embed_query.
from importlib.util import find_spec


VOYAGE_AVAILABLE = find_spec('voyageai') is not None


def _voyage_api_key() -> str:
    """
    Resolve the Voyage key from Django settings, falling back to os.environ.

    config/celery.py removes VOYAGE_API_KEY from a worker's environment so the
    Chromium processes those workers spawn cannot inherit it, which makes
    os.getenv alone insufficient inside Celery. This module is also imported by
    standalone MCP tooling with no Django configured, so the import is guarded
    and the environment remains the fallback.
    """
    try:
        from django.conf import settings
        key = getattr(settings, 'VOYAGE_API_KEY', '')
        if key:
            return key
    except Exception:
        pass
    return os.getenv('VOYAGE_API_KEY', '')


class VoyageEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Custom ChromaDB embedding function using Voyage AI.

    Voyage AI provides fast, high-quality embeddings optimized for retrieval.
    Model: voyage-2 (best balance of speed and quality)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "voyage-2"):
        """
        Initialize the Voyage AI embedding function.

        Args:
            api_key: Voyage AI API key. If not provided, resolved by
                     _voyage_api_key(): Django settings first, then the
                     VOYAGE_API_KEY environment variable.
            model: Voyage AI model to use. Options:
                   - voyage-2 (recommended, best balance)
                   - voyage-large-2 (higher quality, slower)
                   - voyage-code-2 (optimized for code)
        """
        if not VOYAGE_AVAILABLE:
            raise ImportError("voyageai package not installed. Run: pip install voyageai")

        self.api_key = api_key or _voyage_api_key()
        if not self.api_key:
            raise ValueError("Voyage AI API key not provided. Set VOYAGE_API_KEY environment variable.")

        self.model = model
        import voyageai  # deferred: see the note at the top of this module
        self.client = voyageai.Client(api_key=self.api_key)

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for a list of documents.

        Args:
            input: List of text documents to embed

        Returns:
            List of embedding vectors
        """
        if not input:
            return []

        # Voyage AI supports batching up to 128 documents
        # Process in batches to handle large inputs
        all_embeddings = []
        batch_size = 128

        for i in range(0, len(input), batch_size):
            batch = input[i:i + batch_size]
            result = self.client.embed(
                texts=batch,
                model=self.model,
                input_type="document"  # Use "query" for search queries
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings


def get_embedding_function() -> Optional[EmbeddingFunction]:
    """
    Get the best available embedding function.

    Returns:
        VoyageEmbeddingFunction if Voyage AI is configured,
        None to use ChromaDB's default (all-MiniLM-L6-v2)
    """
    # Check for Voyage AI configuration
    api_key = _voyage_api_key()

    if api_key and VOYAGE_AVAILABLE:
        try:
            return VoyageEmbeddingFunction(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Voyage AI embeddings: {e}")
            logger.info("Falling back to ChromaDB default embeddings.")
            return None

    # No Voyage AI - use ChromaDB's default (CPU-based all-MiniLM-L6-v2)
    if not api_key:
        logger.info("VOYAGE_API_KEY not set. Using slower CPU-based embeddings.")

    return None


def embed_query(query: str) -> Optional[List[float]]:
    """
    Generate embedding for a search query.

    Uses Voyage AI with input_type="query" for better search performance.

    Args:
        query: The search query text

    Returns:
        Embedding vector, or None if embedding fails
    """
    api_key = _voyage_api_key()

    if not api_key or not VOYAGE_AVAILABLE:
        return None  # Let ChromaDB handle it

    try:
        import voyageai  # deferred: see the note at the top of this module
        client = voyageai.Client(api_key=api_key)
        result = client.embed(
            texts=[query],
            model="voyage-2",
            input_type="query"  # Optimized for search queries
        )
        return result.embeddings[0]
    except Exception as e:
        logger.warning(f"Query embedding failed: {e}")
        return None
