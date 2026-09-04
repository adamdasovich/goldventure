"""
News Content Processor
Fetches full content from news releases and articles, processes them for RAG/semantic search.
Stores chunks in both PostgreSQL (NewsChunk) and ChromaDB for embedding-based retrieval.

Uses Voyage AI for fast embeddings when available, falls back to local model.
"""

import re
import logging
import asyncio
import os
import requests

logger = logging.getLogger(__name__)

# Site furniture that survives tag-level stripping: cookie notices, share
# bars and newsletter forms usually sit in plain divs whose class or id
# says what they are. Matched as substrings against class + id.
# Site furniture identified by class/id. Two tiers, matched per class name:
#
# * a SEGMENT hint matches when it equals one hyphen/underscore-separated
#   segment of the name — "cookie" hits "cookie-notice" but not a name that
#   merely contains the letters;
# * an EXACT hint must equal the whole class name — "share" widgets stay
#   here because mining releases legitimately carry classes like
#   "share-structure-table".
#
# This replaces a substring match that destroyed real articles: 'sidebar' in
# "content-sidebar-wrap" — the wrapper Genesis-family WordPress themes put
# around the WHOLE page, sidebar and article alike — decomposed the article.
# 'sidebar' is gone entirely; true sidebars live in <aside>, which the tag
# pass already removes, and stray menu links fall to the line filter.
_CHROME_SEGMENT_HINTS = frozenset({
    'cookie', 'cookies', 'consent', 'gdpr', 'newsletter',
    'breadcrumb', 'breadcrumbs', 'sharedaddy', 'addthis', 'addtoany',
})
_CHROME_EXACT_HINTS = frozenset({
    'social-share', 'share-buttons', 'share-this', 'social-links',
    'social-icons', 'site-footer', 'site-header', 'colophon',
    'menu-toggle', 'skip-link', 'back-to-top', 'related-posts',
    'subscribe-form', 'newsletter-signup',
})
_NAME_SEGMENTS = re.compile(r'[^a-z0-9]+')


def _is_chrome_name(name):
    """True when one class or id names site furniture."""
    name = (name or '').lower()
    if not name:
        return False
    if name in _CHROME_EXACT_HINTS:
        return True
    return any(seg in _CHROME_SEGMENT_HINTS
               for seg in _NAME_SEGMENTS.split(name) if seg)

# Lines that are chrome wherever they appear. Anchored to the whole line,
# so a release that merely mentions a privacy policy in a sentence is left
# alone -- an earlier unanchored version matched a loan agreement and a
# resource estimate.
_BOILERPLATE_LINE = re.compile(
    r'^(?:'
    r'we use cookies.*|.*cookie policy.*|accept (?:all )?cookies.*|'
    r'subscribe to our newsletter.*|sign up for (?:our |the )?newsletter.*|'
    r'follow us on.*|share this.*|share on .*|'
    r'skip to (?:main )?content|javascript is disabled.*|'
    r'.*all rights reserved.*|site by.*|powered by.*|'
    r'ok|okay|accept|got it|i agree|close|next|previous|prev|back|home|menu'
    r')$',
    re.IGNORECASE,
)


# Navigation rendered as markdown: a bullet or line that is nothing but a
# link, a bare URL, or a share widget's query string. Real release text
# always has prose around its links, so 'link and nothing else' is a
# reliable tell.
_LINK_ONLY_LINE = re.compile(
    r'^(?:[-*+]\s*)?\[[^\]]*\]\([^)]*\)[\s.*_-]*$'
)
_BARE_URL_LINE = re.compile(r'^(?:[-*+]\s*)?https?://\S+$', re.IGNORECASE)
_SHARE_QUERY = re.compile(
    r'(?:tw_document_href|u=https?%3A|share\?|sharer\.php|'
    r'utm_source=share|/intent/tweet)',
    re.IGNORECASE,
)
_CHROME_HEADING = re.compile(
    r'^#{1,6}\s*(?:subscribe|follow|share|newsletter|menu|navigation|'
    r'quick links|connect with us)\b.*$',
    re.IGNORECASE,
)


def _is_boilerplate_line(line):
    """True when a line is site chrome rather than release text."""
    stripped = line.strip()
    if not stripped:
        return True
    if _BOILERPLATE_LINE.match(stripped):
        return True
    if _CHROME_HEADING.match(stripped):
        return True
    if _SHARE_QUERY.search(stripped):
        return True
    if _BARE_URL_LINE.match(stripped):
        return True
    # A markdown link with no prose around it is a menu entry.
    return bool(_LINK_ONLY_LINE.match(stripped))

from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import tiktoken
import chromadb
from chromadb.config import Settings
from django.db import transaction

from core.models import (
    Company, NewsRelease, NewsArticle, CompanyNews, NewsChunk
)
from core.security_utils import is_safe_url, validate_redirect_url
from .base import BaseMCPServer
from .embeddings import get_embedding_function


class NewsContentProcessor(BaseMCPServer):
    """
    Processes news releases and articles for semantic search.

    Workflow:
    1. Fetches full content from news URLs
    2. Cleans and extracts text
    3. Chunks text into manageable pieces
    4. Stores chunks in PostgreSQL and ChromaDB
    5. Enables semantic search across all news content
    """

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id=company_id, user=user)

        # Initialize tokenizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # ChromaDB and the embedding function are built on first use, not here.
        #
        # get_embedding_function() returns the Voyage function, which imports
        # voyageai -> transformers -> torch: 795MB, measured. ClaudeClient
        # constructs one of these servers on every AI chat request, so every
        # chat paid for it even though only the news-processing tools ever
        # touch the collection.
        self._chroma_client = None
        self._embedding_function = None
        self._collection = None

    @property
    def embedding_function(self):
        if self._embedding_function is None:
            self._embedding_function = get_embedding_function()
        return self._embedding_function

    @property
    def chroma_client(self):
        """Talk to chromadb.service over HTTP, not to the store on disk.

        This used to be a PersistentClient on ./chroma_db — the same directory
        `chroma run` serves on :8002, and the same news_chunks collection
        RAGManager reads. Chroma's persistent client assumes exclusive access
        to its SQLite file and HNSW segments, so that put a second independent
        writer on a store the server already owned. rag_utils.py was moved to
        HttpClient for exactly this reason; its comment names news_chunks as
        the segment that later aborted the process with SIGSEGV on any read.
        This file was the remaining writer.

        core/chromadb_isolated.py runs _process_company_news in a subprocess to
        contain those crashes. That stays as defence in depth, but with the
        writes going through the server there should be nothing left to
        contain here.
        """
        if self._chroma_client is None:
            host = os.environ.get('CHROMA_HOST', 'localhost')
            port = int(os.environ.get('CHROMA_PORT', 8002))
            self._chroma_client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False),
            )
            # Fail here rather than at first query, so a stopped
            # chromadb.service is an obvious error rather than a confusing
            # retrieval failure. Same reasoning as RAGManager.
            self._chroma_client.heartbeat()
        return self._chroma_client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.chroma_client.get_or_create_collection(
                name="news_chunks",
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function
            )
        return self._collection

    def _register_tools(self):
        """Register MCP tools"""
        self.register_tool(
            name="process_company_news",
            description="""Process all unprocessed news releases for a company.
            Fetches full content, extracts text, and stores for semantic search.
            Use this to make the chatbot smarter about a company's news.""",
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to process news for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of news items to process (default: 20)",
                        "default": 20
                    },
                    "reprocess": {
                        "type": "boolean",
                        "description": "Whether to reprocess already processed news (default: false)",
                        "default": False
                    }
                },
                "required": ["company_name"]
            },
            handler=self._process_company_news
        )

        self.register_tool(
            name="search_news_content",
            description="""Search across all processed news content using semantic search.
            Returns relevant news excerpts with sources.
            Use this when users ask about news topics, announcements, or updates.""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'drilling results', 'financing announcement')"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Optional: Filter to specific company"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            handler=self._search_news_content
        )

        self.register_tool(
            name="get_news_context",
            description="""Get formatted context from news for answering questions.
            Returns relevant news excerpts formatted for Claude to use.""",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to find news context for"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Optional: Filter to specific company"
                    }
                },
                "required": ["question"]
            },
            handler=self._get_news_context
        )

    def get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions for Claude"""
        return [
            {
                "name": "process_company_news",
                "description": "Process news releases for a company to enable semantic search. Makes chatbot smarter about company news.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "Company name"},
                        "limit": {"type": "integer", "default": 20},
                        "reprocess": {"type": "boolean", "default": False}
                    },
                    "required": ["company_name"]
                }
            },
            {
                "name": "search_news_content",
                "description": "Semantic search across processed news content. Use for questions about announcements, updates, news topics.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "company_name": {"type": "string", "description": "Optional company filter"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_news_context",
                "description": "Get formatted news context for answering questions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "company_name": {"type": "string"}
                    },
                    "required": ["question"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool by name"""
        if tool_name == "process_company_news":
            # Support both company_name and company_id
            company_name = parameters.get('company_name')
            if not company_name and parameters.get('company_id'):
                company = Company.objects.filter(id=parameters.get('company_id')).first()
                company_name = company.name if company else None
            return self._process_company_news(
                company_name,
                parameters.get('limit', 20),
                parameters.get('reprocess', False)
            )
        elif tool_name == "search_news_content":
            return self._search_news_content(
                parameters.get('query'),
                parameters.get('company_name'),
                parameters.get('max_results', 5)
            )
        elif tool_name == "get_news_context":
            return self._get_news_context(
                parameters.get('question'),
                parameters.get('company_name')
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    # Bounds for PDF news releases. These are announcements — a few pages — not
    # technical reports, so anything past these limits is not a news release and
    # is not worth the CPU. The ceiling also keeps a mislabelled 300-page
    # NI 43-101 from being parsed here instead of on the GPU.
    MAX_PDF_BYTES = 25 * 1024 * 1024
    MAX_PDF_PAGES = 40

    @classmethod
    def _extract_pdf_text(cls, data: bytes, url: str) -> Optional[str]:
        """
        Pull the text layer out of a news-release PDF.

        Text extraction, not OCR: pdfplumber reads the layer that digitally
        generated PDFs already carry, which is what an issuer's news release is.
        A scanned PDF has no such layer and yields nothing, which is the same
        outcome as before — no regression, just no gain.

        This is emphatically not the "never process documents on CPU" case in
        CLAUDE.md. That warning is about running Docling with OCR over
        300-page technical reports; this is a page-count-bounded text read of a
        two-page announcement and costs milliseconds.
        """
        if not data or len(data) > cls.MAX_PDF_BYTES:
            return None
        try:
            import io

            import pdfplumber

            parts = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages[:cls.MAX_PDF_PAGES]:
                    try:
                        parts.append(page.extract_text() or '')
                    except Exception:
                        continue
            text = '\n'.join(p for p in parts if p)
        except Exception as e:
            logger.warning(f"PDF text extraction failed for {url}: {e}")
            return None

        lines = [
            line.strip()
            for line in text.split('\n')
            if line.strip() and not _is_boilerplate_line(line)
        ]
        text = '\n'.join(lines)
        return text if len(text) > 100 else None

    def _fetch_content_from_url(self, url: str) -> Optional[str]:
        """Fetch and extract text content from a URL"""
        # Tracked so the finally below can close it. With stream=True a
        # response only releases its socket once the body is consumed or
        # close() is called, and this function returns early from several
        # places — an unsafe redirect, an oversize PDF, a mid-stream overflow —
        # none of which consume the body. In a long-lived Celery worker those
        # early returns accumulated half-open connections until GC got around
        # to them.
        response = None
        try:
            # SECURITY: Validate URL before fetching (SSRF prevention)
            is_safe, reason = is_safe_url(url, resolve_dns=True)
            if not is_safe:
                return None  # Silently skip unsafe URLs

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            # Disable automatic redirects to validate each redirect
            response = requests.get(url, headers=headers, timeout=15,
                                    allow_redirects=False, stream=True)

            # Handle redirects manually with validation
            redirect_count = 0
            max_redirects = 5
            while response.is_redirect and redirect_count < max_redirects:
                redirect_url = response.headers.get('Location')
                if not redirect_url:
                    break

                # SECURITY: Validate redirect destination
                is_safe, reason = validate_redirect_url(url, redirect_url)
                if not is_safe:
                    return None  # Block unsafe redirects

                # Release the superseded response's socket before replacing it.
                response.close()
                response = requests.get(redirect_url, headers=headers, timeout=15,
                                        allow_redirects=False, stream=True)
                redirect_count += 1

            response.raise_for_status()

            # PDFs are read here rather than refused. This used to return None
            # on the URL suffix, the Content-Type and the %PDF signature, which
            # is why PDF news releases were routed to the GPU Docling pipeline
            # instead — 2,532 GPU jobs and 15,163 chunks that filled the
            # technical-document collection with news and diluted NI 43-101
            # retrieval. Reading the text layer here keeps that content in
            # news_chunks, where the rest of the news lives, at no GPU cost.
            content_type = response.headers.get('Content-Type', '').lower()
            # Decided from headers and the URL, never by reading the body:
            # response.content would pull the whole payload into memory before
            # any size check, so a very large PDF could exhaust the scrape
            # worker (MemoryMax 2400M) before _extract_pdf_text got to reject
            # it. With stream=True the body is only read below, under a cap.
            looks_pdf = (
                'pdf' in content_type
                or url.lower().split('?')[0].endswith('.pdf')
            )
            if looks_pdf:
                declared = response.headers.get('Content-Length')
                if declared and declared.isdigit() and int(declared) > self.MAX_PDF_BYTES:
                    return None
                data = bytearray()
                for piece in response.iter_content(chunk_size=65536):
                    data.extend(piece)
                    if len(data) > self.MAX_PDF_BYTES:
                        return None  # bigger than any news release
                return self._extract_pdf_text(bytes(data), url)

            # Other binary payloads still have no text to extract.
            if 'application/octet-stream' in content_type:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script, style, nav, footer elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            # Tag names alone miss the furniture most sites put in plain
            # divs. Their class or id almost always says what they are.
            for element in (soup.find_all(attrs={'class': True})
                            + soup.find_all(attrs={'id': True})):
                names = (element.get('class') or []) + [element.get('id')]
                if any(_is_chrome_name(n) for n in names):
                    element.decompose()

            # Try to find main content area
            content = None
            for selector in ['article', 'main', '.content', '.post-content', '.entry-content', '#content']:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem
                    break

            if not content:
                content = soup.body if soup.body else soup

            # Extract text
            text = content.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            lines = [
                line.strip()
                for line in text.split(chr(10))
                if line.strip() and not _is_boilerplate_line(line)
            ]
            text = '\n'.join(lines)

            return text if len(text) > 100 else None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

    def _sanitize_text(self, text: str) -> str:
        """Remove NUL characters and other problematic bytes"""
        if not text:
            return ""
        # Remove NUL bytes and other control characters except newlines/tabs
        cleaned = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127))
        return cleaned

    def _chunk_text(self, text: str, max_tokens: int = 400, overlap_tokens: int = 50) -> List[Dict]:
        """Split text into overlapping chunks"""
        # Sanitize text first
        text = self._sanitize_text(text)
        tokens = self.tokenizer.encode(text)
        chunks = []
        start_idx = 0

        while start_idx < len(tokens):
            end_idx = min(start_idx + max_tokens, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                'text': chunk_text,
                'token_count': len(chunk_tokens)
            })

            start_idx = end_idx - overlap_tokens
            if end_idx >= len(tokens):
                break

        return chunks

    def _process_news_item(
        self,
        content_type: str,
        source_id: int,
        company: Company,
        title: str,
        url: str,
        source_date: datetime.date,
        existing_text: str = None
    ) -> int:
        """
        Process a single news item and store chunks.

        Returns: Number of chunks created
        """
        # Generate unique prefix for chroma IDs
        prefix = f"{content_type}_{source_id}"

        # Delete existing chunks
        NewsChunk.objects.filter(
            content_type=content_type,
            **{f"{content_type}_id": source_id}
        ).delete()

        # Remove from ChromaDB
        try:
            existing_ids = [f"{prefix}_chunk_{i}" for i in range(100)]
            self.collection.delete(ids=existing_ids)
        except Exception:
            pass  # ChromaDB may not have these IDs

        # Get content - use existing or fetch from URL
        text = existing_text
        if not text and url:
            text = self._fetch_content_from_url(url)

        if not text or len(text) < 50:
            return 0

        # Sanitize text and title
        text = self._sanitize_text(text)
        title = self._sanitize_text(title)

        # Persist the body to its source row. Until 2026-09-03 the fetch
        # was thrown away after chunking: ~9,000 items were fetched for
        # embedding while NewsRelease.full_text and CompanyNews.content
        # stayed empty on every row of both tables — so a re-embed meant a
        # re-fetch, and a rotted URL lost text we had already held.
        # A queryset update, so no save() side effects and no race.
        if content_type == 'news_release':
            NewsRelease.objects.filter(id=source_id).update(full_text=text)
        elif content_type == 'company_news':
            CompanyNews.objects.filter(id=source_id).update(content=text)

        # Prepend title for context
        full_text = f"Title: {title}\n\n{text}"

        # Chunk the text
        chunks = self._chunk_text(full_text)

        # Prepare ChromaDB data
        chroma_ids = []
        chroma_texts = []
        chroma_metadatas = []

        # Store chunks
        with transaction.atomic():
            for idx, chunk_data in enumerate(chunks):
                chroma_id = f"{prefix}_chunk_{idx}"

                # Create NewsChunk
                chunk_kwargs = {
                    'company': company,
                    'content_type': content_type,
                    'chunk_index': idx,
                    'text': chunk_data['text'],
                    'token_count': chunk_data['token_count'],
                    'chroma_id': chroma_id,
                    'source_title': title[:500],
                    'source_url': url or '',
                    'source_date': source_date,
                }

                # Set the appropriate foreign key
                if content_type == 'news_release':
                    chunk_kwargs['news_release_id'] = source_id
                elif content_type == 'news_article':
                    chunk_kwargs['news_article_id'] = source_id
                elif content_type == 'company_news':
                    chunk_kwargs['company_news_id'] = source_id

                NewsChunk.objects.create(**chunk_kwargs)

                # Prepare ChromaDB entry
                chroma_ids.append(chroma_id)
                chroma_texts.append(chunk_data['text'])
                chroma_metadatas.append({
                    'content_type': content_type,
                    'source_id': source_id,
                    'company': company.name if company else 'Unknown',
                    'company_id': company.id if company else 0,
                    'title': title[:100],
                    'url': url or '',
                    'date': str(source_date) if source_date else '',
                    'chunk_index': idx
                })

        # Batch insert into ChromaDB
        if chroma_ids:
            self.collection.add(
                ids=chroma_ids,
                documents=chroma_texts,
                metadatas=chroma_metadatas
            )

        return len(chunks)

    def _process_company_news(
        self,
        company_name: str,
        limit: int = 20,
        reprocess: bool = False
    ) -> Dict:
        """Process news for a company"""
        try:
            # Find company
            company = Company.objects.filter(Company.name_q(company_name)).first()
            if not company:
                return {"error": f"Company '{company_name}' not found"}

            processed_count = 0
            chunks_created = 0
            errors = []

            # Process NewsRelease items
            news_releases = NewsRelease.objects.filter(company=company).order_by('-release_date')[:limit]
            for nr in news_releases:
                # Skip if already processed (unless reprocess=True)
                if not reprocess and NewsChunk.objects.filter(news_release=nr).exists():
                    continue

                try:
                    # Use full_text if available, otherwise fetch from URL
                    text = nr.full_text if nr.full_text else None
                    num_chunks = self._process_news_item(
                        content_type='news_release',
                        source_id=nr.id,
                        company=company,
                        title=nr.title,
                        url=nr.url,
                        source_date=nr.release_date,
                        existing_text=text
                    )
                    if num_chunks > 0:
                        processed_count += 1
                        chunks_created += num_chunks
                except Exception as e:
                    errors.append(f"NewsRelease {nr.id}: {str(e)}")

            # Process CompanyNews items (scraped news)
            company_news = CompanyNews.objects.filter(company=company).order_by('-publication_date')[:limit]
            for cn in company_news:
                if not reprocess and NewsChunk.objects.filter(company_news=cn).exists():
                    continue

                try:
                    text = cn.content if cn.content else None
                    num_chunks = self._process_news_item(
                        content_type='company_news',
                        source_id=cn.id,
                        company=company,
                        title=cn.title,
                        url=cn.source_url,
                        source_date=cn.publication_date,
                        existing_text=text
                    )
                    if num_chunks > 0:
                        processed_count += 1
                        chunks_created += num_chunks
                except Exception as e:
                    errors.append(f"CompanyNews {cn.id}: {str(e)}")

            return {
                "success": True,
                "company": company.name,
                "news_items_processed": processed_count,
                "chunks_created": chunks_created,
                "errors": errors if errors else None,
                "message": f"Processed {processed_count} news items, created {chunks_created} searchable chunks"
            }

        except Exception as e:
            logger.error(f"News processing failed: {str(e)}")
            return {"error": "News processing failed. Please try again later."}

    def _search_news_content(
        self,
        query: str,
        company_name: str = None,
        max_results: int = 5
    ) -> Dict:
        """Search across processed news content"""
        try:
            # Build filter
            where_filter = None
            if company_name:
                company = Company.objects.filter(Company.name_q(company_name)).first()
                if company:
                    where_filter = {"company_id": company.id}

            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results,
                where=where_filter
            )

            if not results or not results['documents'] or not results['documents'][0]:
                return {
                    "found": False,
                    "message": f"No news content found for: {query}",
                    "results": []
                }

            # Format results
            formatted_results = []
            for idx in range(len(results['documents'][0])):
                meta = results['metadatas'][0][idx]
                distance = results['distances'][0][idx] if results.get('distances') else None

                formatted_results.append({
                    "rank": idx + 1,
                    "relevance_score": round(1 - distance, 3) if distance else None,
                    "text": results['documents'][0][idx],
                    "source": {
                        "type": meta.get('content_type', 'unknown'),
                        "title": meta.get('title', 'Unknown'),
                        "url": meta.get('url', ''),
                        "date": meta.get('date', ''),
                        "company": meta.get('company', '')
                    }
                })

            return {
                "found": True,
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results
            }

        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return {"error": "News search failed. Please try again later.", "found": False}

    def _get_news_context(self, question: str, company_name: str = None) -> Dict:
        """Get formatted context from news for answering questions"""
        try:
            results = self._search_news_content(question, company_name, max_results=5)

            if not results.get('found'):
                return {
                    "success": False,
                    "context": "No relevant news content found.",
                    "message": "Could not find news related to the question."
                }

            # Format context for Claude
            context_parts = []
            for result in results['results']:
                source = result['source']
                context_parts.append(
                    f"[News Source: {source['title']} ({source['date']})]\n"
                    f"Company: {source['company']}\n"
                    f"{result['text']}\n"
                )

            context = "\n---\n".join(context_parts)

            return {
                "success": True,
                "question": question,
                "context": context,
                "sources_count": len(results['results']),
                "message": "Use this news context to answer the question. Cite the sources."
            }

        except Exception as e:
            logger.error(f"News context retrieval failed: {str(e)}")
            return {"success": False, "error": "Failed to retrieve news context.", "context": ""}


# Utility function for batch processing
def process_all_company_news(limit_per_company: int = 50) -> Dict:
    """Process news for all companies with news releases"""
    processor = NewsContentProcessor()

    companies = Company.objects.filter(is_active=True)
    results = {
        "companies_processed": 0,
        "total_news_items": 0,
        "total_chunks": 0,
        "errors": []
    }

    for company in companies:
        # Check if company has any news
        has_news = (
            NewsRelease.objects.filter(company=company).exists() or
            CompanyNews.objects.filter(company=company).exists()
        )

        if not has_news:
            continue

        result = processor._process_company_news(company.name, limit=limit_per_company)

        if result.get('success'):
            results["companies_processed"] += 1
            results["total_news_items"] += result.get('news_items_processed', 0)
            results["total_chunks"] += result.get('chunks_created', 0)

        if result.get('errors'):
            results["errors"].extend(result['errors'])

    return results
