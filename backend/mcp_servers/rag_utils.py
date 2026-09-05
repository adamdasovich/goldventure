"""
RAG (Retrieval-Augmented Generation) Utilities
Handles document chunking, embedding, and semantic search using ChromaDB.
Supports both technical documents (NI 43-101) and news content.

Uses Voyage AI for fast embeddings when available, falls back to local model.
"""

import logging
import os
import threading

import chromadb
from chromadb.config import Settings
import tiktoken
from typing import List, Dict
from pathlib import Path
import anthropic
from django.conf import settings
from core.models import Document, DocumentChunk, NewsChunk
from .embeddings import get_embedding_function
from .retrieval_enhancements import (
    rerank_results, bm25_search_postgres, reciprocal_rank_fusion,
    mmr_diversify, apply_relevance_threshold
)

logger = logging.getLogger(__name__)


class RAGManager:
    """Manages document chunking, embeddings, and semantic search"""

    def __init__(self):
        """Initialize ChromaDB client and embedding model"""
        # Talk to the chromadb.service HTTP server rather than opening the
        # on-disk store directly.
        #
        # Both were happening at once: `chroma run --path ./chroma_db` serves
        # the GPU worker over :8002, while every Django and Celery process also
        # held a PersistentClient on the same directory. Chroma's persistent
        # client assumes exclusive access to its SQLite file and HNSW segments,
        # so two independent writers can interleave — which is the most likely
        # explanation for the news_chunks segment that later aborted the
        # process with SIGSEGV on any read.
        #
        # Routing through the server leaves exactly one process with file
        # handles. Embeddings are still computed client-side by the embedding
        # function, so retrieval behaviour is unchanged.
        host = os.environ.get('CHROMA_HOST', 'localhost')
        port = int(os.environ.get('CHROMA_PORT', 8002))

        self.chroma_client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False),
        )
        # Fail here rather than at first query, so a stopped chromadb.service is
        # an obvious startup error instead of a confusing retrieval failure.
        self.chroma_client.heartbeat()

        # Get embedding function (Voyage AI if available, else ChromaDB default)
        self.embedding_function = get_embedding_function()

        # Get or create collection for document chunks (technical reports)
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"},  # Cosine similarity for semantic search
            embedding_function=self.embedding_function
        )

        # Get or create collection for news chunks
        self.news_collection = self.chroma_client.get_or_create_collection(
            name="news_chunks",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
        )

        # Initialize tokenizer for Claude's model
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Initialize Anthropic client for LLM calls
        self.claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def chunk_text(self, text: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[Dict]:
        """
        Split text into overlapping chunks based on token count

        Args:
            text: The full document text to chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of overlapping tokens between chunks

        Returns:
            List of chunks with metadata
        """
        # Tokenize the full text
        tokens = self.tokenizer.encode(text)

        chunks = []
        start_idx = 0

        while start_idx < len(tokens):
            # Get chunk tokens
            end_idx = min(start_idx + max_tokens, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                'text': chunk_text,
                'token_count': len(chunk_tokens),
                'start_token': start_idx,
                'end_token': end_idx
            })

            # Move start index forward (with overlap)
            start_idx = end_idx - overlap_tokens

            # Prevent infinite loop on last chunk
            if end_idx >= len(tokens):
                break

        return chunks

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using Claude's embedding model

        Note: Anthropic doesn't provide embeddings directly, so we'll use
        a simple approach: call Claude to generate semantic representations
        For production, you'd use a dedicated embedding model like Voyage AI or OpenAI

        For now, I'll use a workaround with ChromaDB's default embedding function
        """
        # ChromaDB can use its default embedding function (all-MiniLM-L6-v2)
        # This is a lightweight model that works well for semantic search
        return None  # Let ChromaDB handle embeddings automatically

    def store_document_chunks(self, document: Document, text: str) -> int:
        """
        Chunk a document, generate embeddings, and store in both PostgreSQL and ChromaDB

        Args:
            document: Django Document instance
            text: Full document text extracted by Docling

        Returns:
            Number of chunks created
        """
        # Delete existing chunks for this document
        DocumentChunk.objects.filter(document=document).delete()

        # Also remove from ChromaDB
        existing_ids = [f"doc_{document.id}_chunk_{i}" for i in range(1000)]  # Assume max 1000 chunks
        try:
            self.collection.delete(ids=existing_ids)
        except Exception:
            pass  # Ignore if IDs don't exist in ChromaDB

        # Create chunks
        chunks = self.chunk_text(text)

        # Prepare data for ChromaDB batch insert
        chroma_ids = []
        chroma_texts = []
        chroma_metadatas = []

        # Create DocumentChunk records and prepare ChromaDB data
        for idx, chunk_data in enumerate(chunks):
            chroma_id = f"doc_{document.id}_chunk_{idx}"

            # Save to PostgreSQL
            DocumentChunk.objects.create(
                document=document,
                chunk_index=idx,
                text=chunk_data['text'],
                token_count=chunk_data['token_count'],
                chroma_id=chroma_id
            )

            # Prepare for ChromaDB
            chroma_ids.append(chroma_id)
            chroma_texts.append(chunk_data['text'])
            chroma_metadatas.append({
                'document_id': document.id,
                'chunk_index': idx,
                'company': document.company.name,
                # company_id is what filtered retrieval matches on — the name
                # string varies with how a caller types it. Every other writer
                # (reindex, reconcile) already includes it; omitting it here
                # would make this writer's chunks invisible to company-scoped
                # search.
                'company_id': document.company_id,
                'document_type': document.document_type,
                'document_date': str(document.document_date),
                'document_title': document.title[:100]  # Truncate for metadata
            })

        # Batch insert into ChromaDB (it will auto-generate embeddings).
        #
        # This write is not in the same transaction as the DocumentChunk rows
        # above, which are already committed with their chroma_ids. If it fails
        # silently, Postgres claims those chunks are indexed when they are not —
        # that is how the index drifted to ~10% coverage. Failing loudly here
        # lets the caller retry; `manage.py reindex_chroma` repairs the backlog.
        if chroma_ids:
            try:
                self.collection.add(
                    ids=chroma_ids,
                    documents=chroma_texts,
                    metadatas=chroma_metadatas
                )
            except Exception:
                logger.exception(
                    "ChromaDB add failed for document %s (%d chunks). "
                    "Postgres rows are committed but unindexed — "
                    "run `manage.py reindex_chroma` to repair.",
                    document.id, len(chroma_ids),
                )
                raise

        return len(chunks)

    def _hydrate_bm25_metadata(self, bm25_results: List[Dict]) -> None:
        """
        Fill in document metadata for BM25 chunk hits, in place.

        Mirrors the metadata written to ChromaDB in `store_document_chunks`, so
        a caller cannot tell which retrieval leg a result came from.
        """
        if not bm25_results:
            return

        chunk_ids = [r.get('id') for r in bm25_results if r.get('id')]
        rows = (
            DocumentChunk.objects
            .filter(id__in=chunk_ids)
            .select_related('document', 'document__company')
        )
        by_id = {c.id: c for c in rows}

        for result in bm25_results:
            chunk = by_id.get(result.get('id'))
            if not chunk:
                # Fall back to the old stub rather than dropping the result.
                result.setdefault('metadata', {
                    'document_id': result.get('id', ''),
                    'chunk_index': result.get('chunk_index', 0),
                })
                continue

            doc = chunk.document
            meta = {
                'document_id': doc.id,
                'chunk_index': chunk.chunk_index,
                'company': doc.company.name,
                'company_id': doc.company_id,
                'document_type': doc.document_type,
                'document_date': str(doc.document_date),
                'document_title': (doc.title or '')[:100],
            }
            if chunk.page_number is not None:
                meta['page_number'] = chunk.page_number
            if chunk.section_title:
                meta['section_title'] = chunk.section_title

            result['metadata'] = meta
            result['document_id'] = doc.id
            result['chunk_index'] = chunk.chunk_index

    def _hydrate_bm25_news_metadata(self, bm25_results: List[Dict]) -> None:
        """Fill in news metadata for BM25 chunk hits, in place."""
        if not bm25_results:
            return

        chunk_ids = [r.get('id') for r in bm25_results if r.get('id')]
        rows = (
            NewsChunk.objects
            .filter(id__in=chunk_ids)
            .select_related('company')
        )
        by_id = {c.id: c for c in rows}

        for result in bm25_results:
            result['source_type'] = 'news'
            chunk = by_id.get(result.get('id'))
            if not chunk:
                result.setdefault('metadata', {
                    'source_id': result.get('id', ''),
                    'chunk_index': result.get('chunk_index', 0),
                })
                continue

            company_name = chunk.company.name if chunk.company else ''
            meta = {
                'chunk_index': chunk.chunk_index,
                'company': company_name,
                'company_id': chunk.company_id,
                'content_type': chunk.content_type,
                'title': (chunk.source_title or '')[:100],
                'url': chunk.source_url or '',
                'date': str(chunk.source_date) if chunk.source_date else '',
            }
            result['metadata'] = meta
            # search_news's vector leg also exposes these at the top level.
            result['title'] = meta['title']
            result['date'] = meta['date']
            result['company'] = company_name

    def _resolve_company_filter(self, filter_company):
        """
        Resolve a human-typed company name to (company_id, canonical_name).

        Chat callers pass whatever the user typed — "Nobel Resources" — while
        chunk metadata and the companies table store "Nobel Resources Corp.".
        Both retrieval legs used to filter by exact string equality, so any
        non-verbatim name returned zero chunks and the assistant concluded the
        documents did not exist: measured 2026-09-05 with the Cuprita 43-101,
        the morning after it was ingested, when "give me the highlights of
        Nobel Resources latest 43-101" came back "no report has been filed".

        Every chunk's metadata carries company_id, so resolve the name once
        and filter on the id. Ambiguous or unknown names fall back to the old
        literal behaviour — no worse than before.
        """
        if not filter_company:
            return None, None
        from core.models import Company
        name = filter_company.strip()
        company = Company.objects.filter(name__iexact=name).first()
        if not company:
            matches = list(Company.objects.filter(name__icontains=name)[:2])
            if len(matches) == 1:
                company = matches[0]
        if company:
            return company.id, company.name
        return None, name

    def search_documents(self, query: str, n_results: int = 5, filter_company: str = None) -> List[Dict]:
        """
        Hybrid search across document chunks: vector (ChromaDB) + BM25 (PostgreSQL),
        merged via Reciprocal Rank Fusion, then re-ranked with a cross-encoder.

        Pipeline: ChromaDB top-4x + BM25 top-4x → RRF merge → cross-encoder → top-k

        Args:
            query: User's question or search query
            n_results: Number of results to return
            filter_company: Optional company name to filter results

        Returns:
            List of relevant chunks with metadata and scores
        """
        # Filter on company_id, resolved from whatever name the caller typed.
        # See _resolve_company_filter for why exact-name matching failed.
        company_id, canonical_name = self._resolve_company_filter(filter_company)
        where_filter = None
        if company_id:
            where_filter = {"company_id": company_id}
        elif canonical_name:
            where_filter = {"company": canonical_name}

        # Over-fetch 4x candidates from each source for merging + re-ranking
        fetch_count = n_results * 4

        # --- Vector search (ChromaDB) ---
        results = self.collection.query(
            query_texts=[query],
            n_results=fetch_count,
            where=where_filter
        )

        vector_results = []
        if results and results['documents']:
            for idx in range(len(results['documents'][0])):
                vector_results.append({
                    'text': results['documents'][0][idx],
                    'metadata': results['metadatas'][0][idx],
                    'distance': results['distances'][0][idx] if results.get('distances') else None,
                    'document_id': results['metadatas'][0][idx]['document_id'],
                    'chunk_index': results['metadatas'][0][idx]['chunk_index']
                })

        # --- BM25 keyword search (PostgreSQL) ---
        bm25_results = bm25_search_postgres(
            query, DocumentChunk, top_k=fetch_count,
            filter_company=canonical_name, filter_company_id=company_id,
        )
        # Normalize BM25 results to match vector result format.
        #
        # bm25_search_postgres returns raw chunk rows (id/text/chunk_index) with
        # no document context. Stubbing metadata here left every BM25-sourced
        # passage with no company or document title, so citations rendered blank
        # whenever a hit came from the keyword leg rather than the vector leg.
        # Hydrate from Postgres in one query so both legs carry the same shape.
        self._hydrate_bm25_metadata(bm25_results)

        # --- Reciprocal Rank Fusion ---
        merged = reciprocal_rank_fusion(vector_results, bm25_results)

        # --- MMR diversity (select 2x top_k diverse candidates for re-ranking) ---
        diverse = mmr_diversify(merged, top_k=n_results * 2, lambda_param=0.7)

        # --- Cross-encoder re-ranking on diverse set ---
        formatted_results = rerank_results(query, diverse, top_k=n_results)

        # --- Relevance threshold (filter out clearly irrelevant results) ---
        formatted_results = apply_relevance_threshold(formatted_results)

        return formatted_results

    def get_context_for_query(self, query: str, company: str = None, max_chunks: int = 5) -> str:
        """
        Get relevant context from documents to answer a query

        Args:
            query: User's question
            company: Optional company name to filter results
            max_chunks: Maximum number of chunks to include

        Returns:
            Formatted context string to include in Claude prompt
        """
        results = self.search_documents(query, n_results=max_chunks, filter_company=company)

        if not results:
            return "No relevant document content found."

        # Format context
        context_parts = []
        for idx, result in enumerate(results, 1):
            meta = result['metadata']
            context_parts.append(
                f"[Source {idx}: {meta['document_title']} ({meta['document_date']})]\n"
                f"{result['text']}\n"
            )

        return "\n---\n".join(context_parts)

    def search_news(self, query: str, n_results: int = 5, filter_company: str = None) -> List[Dict]:
        """
        Hybrid search across news chunks: vector (ChromaDB) + BM25 (PostgreSQL),
        merged via Reciprocal Rank Fusion, then re-ranked with a cross-encoder.

        Args:
            query: User's question or search query
            n_results: Number of results to return
            filter_company: Optional company name to filter results

        Returns:
            List of relevant news chunks with metadata
        """
        # Filter on company_id, resolved from whatever name the caller typed.
        # See _resolve_company_filter for why exact-name matching failed.
        company_id, canonical_name = self._resolve_company_filter(filter_company)
        where_filter = None
        if company_id:
            where_filter = {"company_id": company_id}
        elif canonical_name:
            where_filter = {"company": canonical_name}

        # Over-fetch 4x candidates from each source
        fetch_count = n_results * 4

        # --- Vector search (ChromaDB) ---
        results = self.news_collection.query(
            query_texts=[query],
            n_results=fetch_count,
            where=where_filter
        )

        vector_results = []
        if results and results['documents'] and results['documents'][0]:
            for idx in range(len(results['documents'][0])):
                meta = results['metadatas'][0][idx]
                vector_results.append({
                    'text': results['documents'][0][idx],
                    'metadata': meta,
                    'distance': results['distances'][0][idx] if results.get('distances') else None,
                    'source_type': 'news',
                    'title': meta.get('title', 'Unknown'),
                    'date': meta.get('date', ''),
                    'company': meta.get('company', '')
                })

        # --- BM25 keyword search (PostgreSQL) ---
        bm25_results = bm25_search_postgres(
            query, NewsChunk, top_k=fetch_count,
            filter_company=canonical_name, filter_company_id=company_id,
        )
        # Same hydration as search_documents: without it, keyword-sourced hits
        # reach the caller with no title, date or company attribution.
        self._hydrate_bm25_news_metadata(bm25_results)

        # --- Reciprocal Rank Fusion ---
        merged = reciprocal_rank_fusion(vector_results, bm25_results)

        # --- MMR diversity (select 2x top_k diverse candidates for re-ranking) ---
        diverse = mmr_diversify(merged, top_k=n_results * 2, lambda_param=0.7)

        # --- Cross-encoder re-ranking on diverse set ---
        formatted_results = rerank_results(query, diverse, top_k=n_results)

        # --- Relevance threshold (filter out clearly irrelevant results) ---
        formatted_results = apply_relevance_threshold(formatted_results)

        return formatted_results

    def search_all(
        self,
        query: str,
        n_results: int = 5,
        filter_company: str = None,
        include_documents: bool = True,
        include_news: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Search across both technical documents and news content

        Args:
            query: User's question
            n_results: Number of results per source type
            filter_company: Optional company name filter
            include_documents: Whether to search technical documents
            include_news: Whether to search news content

        Returns:
            Dictionary with 'documents' and 'news' result lists
        """
        results = {
            'documents': [],
            'news': [],
            'combined': []
        }

        if include_documents:
            results['documents'] = self.search_documents(
                query, n_results=n_results, filter_company=filter_company
            )

        if include_news:
            results['news'] = self.search_news(
                query, n_results=n_results, filter_company=filter_company
            )

        # Combine and sort by relevance
        combined = []

        for doc in results['documents']:
            combined.append({
                **doc,
                'source_type': 'document',
                'relevance': 1 - doc['distance'] if doc.get('distance') else 0.5
            })

        for news in results['news']:
            combined.append({
                **news,
                'source_type': 'news',
                'relevance': 1 - news['distance'] if news.get('distance') else 0.5
            })

        # Sort by relevance (highest first)
        combined.sort(key=lambda x: x['relevance'], reverse=True)
        results['combined'] = combined[:n_results * 2]  # Return up to 2x n_results

        return results

    def get_combined_context(
        self,
        query: str,
        company: str = None,
        max_chunks: int = 5
    ) -> str:
        """
        Get context from both documents and news for answering questions

        Args:
            query: User's question
            company: Optional company filter
            max_chunks: Max chunks from each source type

        Returns:
            Formatted context string with both document and news sources
        """
        results = self.search_all(
            query=query,
            n_results=max_chunks,
            filter_company=company
        )

        context_parts = []

        # Add document context
        if results['documents']:
            context_parts.append("=== TECHNICAL DOCUMENTS ===")
            for idx, result in enumerate(results['documents'][:max_chunks], 1):
                meta = result['metadata']
                context_parts.append(
                    f"[Document {idx}: {meta.get('document_title', 'Unknown')} ({meta.get('document_date', '')})]\n"
                    f"{result['text']}"
                )

        # Add news context
        if results['news']:
            context_parts.append("\n=== NEWS & PRESS RELEASES ===")
            for idx, result in enumerate(results['news'][:max_chunks], 1):
                context_parts.append(
                    f"[News {idx}: {result.get('title', 'Unknown')} ({result.get('date', '')})]\n"
                    f"Company: {result.get('company', 'Unknown')}\n"
                    f"{result['text']}"
                )

        if not context_parts:
            return "No relevant content found in documents or news."

        return "\n\n---\n\n".join(context_parts)


_shared_rag_manager: RAGManager = None
_shared_rag_manager_lock = threading.Lock()


def get_rag_manager() -> RAGManager:
    """
    Process-wide shared RAGManager.

    Constructing a RAGManager connects to ChromaDB and (via the embedding
    function) pulls in the voyageai → transformers → torch import chain —
    ~25s cold, measured 2026-09-04. Before this existed, every chat request
    built one per tool server (insights and ni43101 EACH built their own in a
    single request), so the cost was paid repeatedly instead of once per
    process. Callers on the chat path must use this instead of RAGManager().
    """
    global _shared_rag_manager
    if _shared_rag_manager is None:
        with _shared_rag_manager_lock:
            if _shared_rag_manager is None:
                _shared_rag_manager = RAGManager()
    return _shared_rag_manager
