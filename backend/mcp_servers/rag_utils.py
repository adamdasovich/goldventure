"""
RAG (Retrieval-Augmented Generation) Utilities
Handles document chunking, embedding, and semantic search using ChromaDB
"""

import chromadb
from chromadb.config import Settings
import tiktoken
from typing import List, Dict, Tuple
from pathlib import Path
import anthropic
from django.conf import settings
from core.models import Document, DocumentChunk


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

        # Get or create collection for document chunks
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity for semantic search
        )

        # Initialize tokenizer for Claude's model
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Initialize Anthropic client for embeddings (will use Claude's embeddings)
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
        except:
            pass  # Ignore if IDs don't exist

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
