"""
RAG (Retrieval-Augmented Generation) Utilities
Handles document chunking, embedding, and semantic search using ChromaDB.
Supports both technical documents (NI 43-101) and news content.

Uses Voyage AI for fast embeddings when available, falls back to local model.
"""

import chromadb
from chromadb.config import Settings
import tiktoken
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import anthropic
from django.conf import settings
from core.models import Document, DocumentChunk
from .embeddings import get_embedding_function


class RAGManager:
    """Manages document chunking, embeddings, and semantic search"""

    def __init__(self):
        """Initialize ChromaDB client and embedding model"""
        # Initialize ChromaDB (persistent storage)
        chroma_path = Path(settings.BASE_DIR) / "chroma_db"
        chroma_path.mkdir(exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

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
                'document_type': document.document_type,
                'document_date': str(document.document_date),
                'document_title': document.title[:100]  # Truncate for metadata
            })

        # Batch insert into ChromaDB (it will auto-generate embeddings)
        if chroma_ids:
            self.collection.add(
                ids=chroma_ids,
                documents=chroma_texts,
                metadatas=chroma_metadatas
            )

        return len(chunks)

    def search_documents(self, query: str, n_results: int = 5, filter_company: str = None) -> List[Dict]:
        """
        Semantic search across all document chunks

        Args:
            query: User's question or search query
            n_results: Number of results to return
            filter_company: Optional company name to filter results

        Returns:
            List of relevant chunks with metadata and scores
        """
        # Build filter if company specified
        where_filter = None
        if filter_company:
            where_filter = {"company": filter_company}

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        if results and results['documents']:
            for idx in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][idx],
                    'metadata': results['metadatas'][0][idx],
                    'distance': results['distances'][0][idx] if results.get('distances') else None,
                    'document_id': results['metadatas'][0][idx]['document_id'],
                    'chunk_index': results['metadatas'][0][idx]['chunk_index']
                })

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
        Semantic search across news content chunks

        Args:
            query: User's question or search query
            n_results: Number of results to return
            filter_company: Optional company name to filter results

        Returns:
            List of relevant news chunks with metadata
        """
        # Build filter if company specified
        where_filter = None
        if filter_company:
            where_filter = {"company": filter_company}

        # Query news collection
        results = self.news_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        formatted_results = []
        if results and results['documents'] and results['documents'][0]:
            for idx in range(len(results['documents'][0])):
                meta = results['metadatas'][0][idx]
                formatted_results.append({
                    'text': results['documents'][0][idx],
                    'metadata': meta,
                    'distance': results['distances'][0][idx] if results.get('distances') else None,
                    'source_type': 'news',
                    'title': meta.get('title', 'Unknown'),
                    'date': meta.get('date', ''),
                    'company': meta.get('company', '')
                })

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
