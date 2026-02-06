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

# Try to import voyageai
try:
    import voyageai
    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False


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
            api_key: Voyage AI API key. If not provided, uses VOYAGE_API_KEY env var.
            model: Voyage AI model to use. Options:
                   - voyage-2 (recommended, best balance)
                   - voyage-large-2 (higher quality, slower)
                   - voyage-code-2 (optimized for code)
        """
        if not VOYAGE_AVAILABLE:
            raise ImportError("voyageai package not installed. Run: pip install voyageai")

        self.api_key = api_key or os.getenv('VOYAGE_API_KEY', '')
        if not self.api_key:
            raise ValueError("Voyage AI API key not provided. Set VOYAGE_API_KEY environment variable.")

        self.model = model
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
    api_key = os.getenv('VOYAGE_API_KEY', '')

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
    api_key = os.getenv('VOYAGE_API_KEY', '')

    if not api_key or not VOYAGE_AVAILABLE:
        return None  # Let ChromaDB handle it

    try:
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
