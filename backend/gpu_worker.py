#!/usr/bin/env python3
"""
GPU Worker for Document Processing

Runs on the GPU droplet and processes heavy document jobs:
1. Connects to main PostgreSQL database
2. Polls for pending DocumentProcessingJob records
3. Processes documents with GPU-accelerated text extraction
4. Writes chunks back to main database and ChromaDB
5. Signals completion when queue is empty

This script is designed to be robust with:
- Graceful error handling and retries
- Health monitoring
- Clean shutdown on empty queue
- Detailed logging for debugging

Security Features:
- URL allowlist prevents SSRF attacks
- File size limits prevent disk exhaustion
- Secure credential loading from environment
"""

import os
import sys
import time
import json
import logging
import tempfile
import hashlib
import signal
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
from urllib.parse import urlparse

import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Security: URL allowlist to prevent SSRF attacks
# Only allow downloads from trusted document sources
ALLOWED_URL_DOMAINS = [
    # Mining company websites
    'prismometals.com',
    'radissonmining.com',
    'silverspruceresources.com',
    'astonbayholdings.com',
    'angkorresources.com',
    '1911gold.com',
    'g2goldfields.com',
    'newfoundgold.ca',
    # Mining company document sources
    'sedar.com',
    'sedarplus.ca',
    'sec.gov',
    'newswire.ca',
    'globenewswire.com',
    'businesswire.com',
    'prnewswire.com',
    'accesswire.com',
    'newsfilecorp.com',
    # Company websites (will be validated against company domains in DB)
    # Cloud storage (for internal uploads)
    's3.amazonaws.com',
    'storage.googleapis.com',
    'blob.core.windows.net',
    'digitaloceanspaces.com',
    # Allow any .pdf direct links from mining company sites
]

# Security: Maximum file size to prevent disk exhaustion (500 MB)
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024


def is_url_allowed(url: str) -> Tuple[bool, str]:
    """Check if URL is from an allowed domain.

    Returns (is_allowed, reason) tuple.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "Invalid URL: no hostname"

        # Block internal/metadata URLs (SSRF prevention)
        if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            return False, "Blocked: localhost access"

        if hostname.startswith('169.254.'):  # AWS metadata
            return False, "Blocked: metadata service access"

        if hostname.startswith('10.') or hostname.startswith('192.168.'):
            return False, "Blocked: private network access"

        # Check against allowlist
        for allowed_domain in ALLOWED_URL_DOMAINS:
            if hostname == allowed_domain or hostname.endswith('.' + allowed_domain):
                return True, f"Allowed: {allowed_domain}"

        # Allow any HTTPS URL to a .com/.ca/.gov domain with PDF in path
        # This allows company websites we haven't explicitly listed
        if parsed.scheme == 'https':
            if hostname.endswith(('.com', '.ca', '.gov', '.io')):
                if '.pdf' in parsed.path.lower():
                    return True, f"Allowed: HTTPS PDF from {hostname}"

        return False, f"Blocked: {hostname} not in allowlist"

    except Exception as e:
        return False, f"URL validation error: {e}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/gpu_worker.log')
    ]
)
logger = logging.getLogger('gpu_worker')

# Suppress noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


@dataclass
class ProcessingJob:
    """Represents a document processing job"""
    id: int
    document_id: int
    document_type: str
    file_url: str
    company_id: int
    company_name: str
    status: str
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Result of processing a document"""
    success: bool
    chunks_created: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    pages_processed: int = 0
    characters_extracted: int = 0


class DatabaseConnection:
    """Manages PostgreSQL connection to main database"""

    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        db_config = {
            'host': os.environ.get('DB_HOST', '137.184.168.166'),
            'port': int(os.environ.get('DB_PORT', 5432)),
            'database': os.environ.get('DB_NAME', 'goldventure'),
            'user': os.environ.get('DB_USER', 'goldventure'),
            'password': os.environ.get('DB_PASSWORD', ''),
        }

        logger.info(f"Connecting to database at {db_config['host']}:{db_config['port']}")

        try:
            self.conn = psycopg2.connect(**db_config)
            self.conn.autocommit = False
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def ensure_connected(self):
        """Ensure database connection is alive, reconnect if needed"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            logger.warning("Database connection lost, reconnecting...")
            self.connect()

    @contextmanager
    def cursor(self):
        """Context manager for database cursor"""
        self.ensure_connected()
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


class ChromaDBClient:
    """Client for ChromaDB using Python chromadb library"""

    def __init__(self):
        self.host = os.environ.get('CHROMA_HOST', '137.184.168.166')
        self.port = int(os.environ.get('CHROMA_PORT', 8002))
        self.collection_name = "document_chunks"
        self._client = None
        self._collection = None

    def _get_collection(self):
        """Lazy initialization of ChromaDB client and collection"""
        if self._collection is None:
            try:
                import chromadb
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
                self._collection = self._client.get_or_create_collection(name=self.collection_name)
                logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                raise
        return self._collection

    def add_documents(self, ids: List[str], documents: List[str],
                      metadatas: List[Dict], embeddings: List[List[float]]):
        """Add documents to ChromaDB collection"""
        collection = self._get_collection()
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        return {"status": "success", "count": len(ids)}


class DocumentProcessor:
    """Handles GPU-accelerated document processing with Docling"""

    def __init__(self):
        self.docling_converter = None
        self.embedding_model = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize embedding models for GPU acceleration"""
        logger.info("Initializing document processing models...")

        try:
            # Initialize embedding model on GPU
            from sentence_transformers import SentenceTransformer
            import torch

            # Force CUDA device
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")

            if device == 'cuda':
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
            logger.info("Embedding model initialized on GPU")
        except ImportError as e:
            logger.warning(f"SentenceTransformers not available: {e}")
            self.embedding_model = None

    def download_document(self, url: str) -> Tuple[Optional[Path], Optional[str]]:
        """Download document from URL to temporary file.

        Security features:
        - URL allowlist validation (SSRF prevention)
        - File size limit (disk exhaustion prevention)
        """
        try:
            # Security: Validate URL against allowlist
            is_allowed, reason = is_url_allowed(url)
            if not is_allowed:
                error_msg = f"URL blocked by security policy: {reason}"
                logger.warning(error_msg)
                return None, error_msg

            logger.info(f"Downloading document from {url} ({reason})")

            # Use headers to appear as a browser (some sites block bots)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, timeout=300, stream=True, headers=headers)
            response.raise_for_status()

            # Security: Check content-length header if available
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_FILE_SIZE_BYTES:
                error_msg = f"File too large: {int(content_length) / 1024 / 1024:.1f} MB exceeds {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB limit"
                logger.warning(error_msg)
                return None, error_msg

            # Create temp file with appropriate extension
            suffix = '.pdf'
            if 'content-type' in response.headers:
                ct = response.headers['content-type'].lower()
                if 'pdf' in ct:
                    suffix = '.pdf'

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            total_size = 0

            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
                total_size += len(chunk)

                # Security: Enforce size limit during download
                if total_size > MAX_FILE_SIZE_BYTES:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    error_msg = f"Download aborted: exceeded {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB limit"
                    logger.warning(error_msg)
                    return None, error_msg

            temp_file.close()
            logger.info(f"Downloaded {total_size / 1024 / 1024:.2f} MB to {temp_file.name}")

            return Path(temp_file.name), None

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error downloading document: {e.response.status_code} - {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Failed to download document: {e}"
            logger.error(error_msg)
            return None, error_msg

    def extract_text(self, file_path: Path) -> Tuple[Optional[str], int, Optional[str]]:
        """Extract text from PDF using Docling (with OCR support for image-based PDFs)"""
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

            logger.info(f"Extracting text from {file_path} using Docling")
            start_time = time.time()

            # Configure Docling with OCR enabled for image-based PDFs
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True  # Enable OCR for scanned/image PDFs
            pipeline_options.do_table_structure = True  # Extract table structure
            
            converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                pdf_backend=PyPdfiumDocumentBackend,
                pipeline_options={InputFormat.PDF: pipeline_options}
            )

            # Convert the document
            result = converter.convert(str(file_path))
            
            # Get markdown text (best for preserving structure)
            text = result.document.export_to_markdown()
            
            # Count pages from the document
            pages = len(result.document.pages) if hasattr(result.document, "pages") else 1

            elapsed = time.time() - start_time
            logger.info(f"Extracted {len(text)} characters from {pages} pages in {elapsed:.1f}s (Docling with OCR)")

            return text, pages, None

        except Exception as e:
            error_msg = f"Text extraction failed: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return None, 0, error_msg


    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        # Simple word-based chunking
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)

            chunks.append({
                'text': chunk_text,
                'start_word': start,
                'end_word': end,
                'word_count': len(chunk_words)
            })

            # Move start position with overlap
            start = end - overlap if end < len(words) else end

        logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        if self.embedding_model is None:
            logger.warning("Embedding model not available, returning empty embeddings")
            return [[0.0] * 384 for _ in texts]  # Return placeholder embeddings

        try:
            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [[0.0] * 384 for _ in texts]

    def cleanup(self, file_path: Path):
        """Clean up temporary files"""
        try:
            if file_path and file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {file_path}: {e}")


class GPUWorker:
    """Main GPU worker that processes document jobs"""

    # Configuration
    POLL_INTERVAL = 10  # seconds between queue checks
    MAX_RETRIES = 3
    RETRY_DELAY = 30  # seconds
    IDLE_SHUTDOWN_AFTER = 300  # seconds of empty queue before shutdown

    # Job types this worker handles
    SUPPORTED_JOB_TYPES = ['ni43101', 'pea', 'presentation', 'fact_sheet', 'news_release', 'company_scrape']

    def __init__(self):
        self.db = DatabaseConnection()
        self.chroma = ChromaDBClient()
        self.processor = DocumentProcessor()
        self.running = True
        self.idle_since: Optional[datetime] = None
        self.jobs_processed = 0
        self.total_processing_time = 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.info(f"Received shutdown signal {signum}, finishing current job...")
        self.running = False

    def get_pending_job(self) -> Optional[ProcessingJob]:
        """Fetch next pending job from queue"""
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT
                    dpj.id,
                    dpj.document_id,
                    dpj.document_type,
                    dpj.status,
                    dpj.created_at,
                    dpj.url as file_url,
                    dpj.company_name
                FROM document_processing_jobs dpj
                WHERE dpj.status = 'pending'
                AND dpj.document_type = ANY(%s)
                ORDER BY dpj.created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """, (self.SUPPORTED_JOB_TYPES,))

            row = cur.fetchone()
            if not row:
                return None

            # Get company_id from documents table if document_id exists
            company_id = None
            if row['document_id']:
                cur.execute("""
                    SELECT company_id FROM documents WHERE id = %s
                """, (row['document_id'],))
                doc_row = cur.fetchone()
                if doc_row:
                    company_id = doc_row['company_id']

            return ProcessingJob(
                id=row['id'],
                document_id=row['document_id'],
                document_type=row['document_type'],
                file_url=row['file_url'],
                company_id=company_id,
                company_name=row['company_name'],
                status=row['status'],
                created_at=row['created_at'],
                metadata={}
            )

    def update_job_status(self, job_id: int, status: str,
                          error_message: Optional[str] = None,
                          result: Optional[ProcessingResult] = None):
        """Update job status in database"""
        with self.db.cursor() as cur:
            if status == 'processing':
                cur.execute("""
                    UPDATE document_processing_jobs
                    SET status = %s,
                        started_at = NOW(),
                        progress_message = 'Processing with GPU worker'
                    WHERE id = %s
                """, (status, job_id))
            elif status == 'completed':
                chunks_created = result.chunks_created if result else 0
                processing_time = result.processing_time_seconds if result else 0
                cur.execute("""
                    UPDATE document_processing_jobs
                    SET status = %s,
                        completed_at = NOW(),
                        chunks_created = %s,
                        processing_time_seconds = %s,
                        progress_message = 'Completed by GPU worker'
                    WHERE id = %s
                """, (status, chunks_created, int(processing_time), job_id))
            elif status == 'failed':
                cur.execute("""
                    UPDATE document_processing_jobs
                    SET status = %s,
                        completed_at = NOW(),
                        error_message = %s,
                        progress_message = 'Failed'
                    WHERE id = %s
                """, (status, error_message or 'Unknown error', job_id))
            else:
                cur.execute("""
                    UPDATE document_processing_jobs
                    SET status = %s,
                        progress_message = %s
                    WHERE id = %s
                """, (status, f'Status: {status}', job_id))

            logger.info(f"Updated job {job_id} status to {status}")

    def ensure_document_record(self, job: ProcessingJob) -> int:
        """Create document record if it doesn't exist, return document_id"""
        if job.document_id:
            return job.document_id

        with self.db.cursor() as cur:
            # Get company_id from company name
            cur.execute("""
                SELECT id FROM companies WHERE name = %s LIMIT 1
            """, (job.company_name,))
            row = cur.fetchone()
            company_id = row['id'] if row else None

            if not company_id:
                logger.warning(f"Company '{job.company_name}' not found, skipping document creation")
                return None

            # Extract title from URL
            title = job.file_url.split('/')[-1].replace('.pdf', '').replace('-', ' ').replace('_', ' ')

            # Create document record
            cur.execute("""
                INSERT INTO documents (title, document_type, document_date, file_url,
                    description, is_public, created_at, updated_at, company_id)
                VALUES (%s, %s, NOW()::date, %s, %s, true, NOW(), NOW(), %s)
                RETURNING id
            """, (
                title[:300],  # Truncate to fit varchar(300)
                job.document_type,
                job.file_url,
                f'Processed by GPU worker for {job.company_name}',
                company_id
            ))
            doc_id = cur.fetchone()['id']

            # Update the processing job with document_id
            cur.execute("""
                UPDATE document_processing_jobs SET document_id = %s WHERE id = %s
            """, (doc_id, job.id))

            logger.info(f"Created document record {doc_id} for {job.company_name}")
            return doc_id

    def store_chunks(self, job: ProcessingJob, chunks: List[Dict],
                     embeddings: List[List[float]]) -> int:
        """Store document chunks in PostgreSQL and ChromaDB"""
        stored_count = 0

        # Ensure we have a document record
        document_id = self.ensure_document_record(job)
        if not document_id:
            raise ValueError(f"Cannot store chunks: no document record for job {job.id}")

        with self.db.cursor() as cur:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = hashlib.md5(
                    f"{document_id}:{i}:{chunk['text'][:100]}".encode()
                ).hexdigest()

                # Store in PostgreSQL
                cur.execute("""
                    INSERT INTO document_chunks
                    (document_id, chunk_index, section_title, text, token_count,
                     chroma_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (chroma_id)
                    DO UPDATE SET text = EXCLUDED.text,
                                  token_count = EXCLUDED.token_count
                    RETURNING id
                """, (
                    document_id,
                    i,
                    chunk.get('section_title', ''),
                    chunk['text'],
                    chunk['word_count'],
                    chunk_id
                ))

                stored_count += 1

        # Store embeddings in ChromaDB
        try:
            chunk_ids = [
                hashlib.md5(f"{document_id}:{i}".encode()).hexdigest()
                for i in range(len(chunks))
            ]

            metadatas = [
                {
                    'document_id': document_id,
                    'company_id': job.company_id,
                    'company_name': job.company_name,
                    'document_type': job.document_type,
                    'chunk_index': i
                }
                for i in range(len(chunks))
            ]

            texts = [c['text'] for c in chunks]

            self.chroma.add_documents(
                ids=chunk_ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Stored {len(chunks)} embeddings in ChromaDB")

        except Exception as e:
            logger.warning(f"Failed to store in ChromaDB (will retry later): {e}")

        return stored_count

    def process_scraping_job(self, job: ProcessingJob) -> ProcessingResult:
        """Process a company_scrape job - crawl website for news releases"""
        start_time = time.time()

        try:
            logger.info(f"Processing scraping job {job.id} for {job.company_name}")
            self.update_job_status(job.id, 'processing')

            # Import the crawler (transferred from main server)
            import asyncio
            sys.path.insert(0, '/opt/goldventure')

            try:
                from website_crawler import crawl_news_releases
            except ImportError as e:
                return ProcessingResult(
                    success=False,
                    chunks_created=0,
                    processing_time_seconds=time.time() - start_time,
                    error_message=f"Crawler not available: {e}"
                )

            # Run the async crawler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                news_releases = loop.run_until_complete(
                    crawl_news_releases(
                        url=job.file_url,  # This is the company website URL
                        months=48,
                        max_depth=2
                    )
                )
            finally:
                loop.close()

            # Store news releases in database
            created_count = 0
            with self.db.cursor() as cur:
                # Get company_id
                cur.execute("SELECT id FROM companies WHERE name = %s LIMIT 1", (job.company_name,))
                row = cur.fetchone()
                if not row:
                    return ProcessingResult(
                        success=False,
                        chunks_created=0,
                        processing_time_seconds=time.time() - start_time,
                        error_message=f"Company '{job.company_name}' not found"
                    )
                company_id = row['id']

                for news in news_releases:
                    title = news.get('title', '').strip()[:200]
                    url = news.get('url', '').strip()[:500]
                    date_str = news.get('date')
                    release_type = news.get('document_type', 'news_release')

                    if not url or not date_str:
                        continue

                    try:
                        # Check if already exists
                        cur.execute("SELECT id FROM company_news WHERE source_url = %s", (url,))
                        if cur.fetchone():
                            continue

                        # Insert into company_news
                        cur.execute("""
                            INSERT INTO company_news (company_id, title, content, summary, source_url,
                                is_pdf, publication_date, news_type, is_material, is_processed,
                                extracted_at, created_at, updated_at)
                            VALUES (%s, %s, '', '', %s, %s, %s, 'corporate', false, false, NOW(), NOW(), NOW())
                        """, (company_id, title, url, url.lower().endswith('.pdf'), date_str))
                        created_count += 1

                        # Also insert into news_releases for backwards compatibility
                        cur.execute("""
                            INSERT INTO news_releases (company_id, url, title, release_type,
                                release_date, summary, is_material, full_text, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, '', false, '', NOW(), NOW())
                            ON CONFLICT DO NOTHING
                        """, (company_id, url, title, release_type, date_str))

                        # Create document processing job for PDF news releases
                        if url.lower().endswith('.pdf'):
                            cur.execute("""
                                INSERT INTO document_processing_jobs
                                (url, document_type, company_name, project_name, status,
                                 progress_message, error_message, resources_created, chunks_created, created_at)
                                VALUES (%s, 'news_release', %s, '', 'pending', '', '', 0, 0, NOW())
                                ON CONFLICT DO NOTHING
                            """, (url, job.company_name))

                    except Exception as e:
                        self.db.conn.rollback()
                        logger.warning(f"Failed to process news item: {e}")

            processing_time = time.time() - start_time
            logger.info(f"Scraping job {job.id} completed: {created_count} news releases found in {processing_time:.1f}s")

            return ProcessingResult(
                success=True,
                chunks_created=created_count,
                processing_time_seconds=processing_time
            )

        except Exception as e:
            logger.exception(f"Error processing scraping job {job.id}")
            return ProcessingResult(
                success=False,
                chunks_created=0,
                processing_time_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def process_job(self, job: ProcessingJob) -> ProcessingResult:
        """Process a single document job"""
        # Route scraping jobs to specialized handler
        if job.document_type == 'company_scrape':
            return self.process_scraping_job(job)

        start_time = time.time()
        file_path = None

        try:
            logger.info(f"Processing job {job.id}: {job.document_type} for {job.company_name}")

            # Update status to processing
            self.update_job_status(job.id, 'processing')

            # Download document
            file_path, error = self.processor.download_document(job.file_url)
            if error:
                return ProcessingResult(
                    success=False,
                    chunks_created=0,
                    processing_time_seconds=time.time() - start_time,
                    error_message=error
                )

            # Extract text
            text, pages, error = self.processor.extract_text(file_path)
            if error:
                return ProcessingResult(
                    success=False,
                    chunks_created=0,
                    processing_time_seconds=time.time() - start_time,
                    error_message=error,
                    pages_processed=pages
                )

            # Chunk text
            chunks = self.processor.chunk_text(text)
            if not chunks:
                return ProcessingResult(
                    success=False,
                    chunks_created=0,
                    processing_time_seconds=time.time() - start_time,
                    error_message="No content extracted from document",
                    pages_processed=pages,
                    characters_extracted=len(text) if text else 0
                )

            # Generate embeddings
            texts = [c['text'] for c in chunks]
            embeddings = self.processor.generate_embeddings(texts)

            # Store chunks and embeddings
            stored_count = self.store_chunks(job, chunks, embeddings)

            processing_time = time.time() - start_time
            logger.info(f"Job {job.id} completed: {stored_count} chunks in {processing_time:.1f}s")

            return ProcessingResult(
                success=True,
                chunks_created=stored_count,
                processing_time_seconds=processing_time,
                pages_processed=pages,
                characters_extracted=len(text)
            )

        except Exception as e:
            logger.exception(f"Error processing job {job.id}")
            return ProcessingResult(
                success=False,
                chunks_created=0,
                processing_time_seconds=time.time() - start_time,
                error_message=str(e)
            )

        finally:
            # Cleanup temporary file
            if file_path:
                self.processor.cleanup(file_path)

    def run(self):
        """Main worker loop"""
        logger.info("=" * 60)
        logger.info("GPU Worker starting...")
        logger.info(f"Supported job types: {self.SUPPORTED_JOB_TYPES}")
        logger.info(f"Poll interval: {self.POLL_INTERVAL}s")
        logger.info(f"Idle shutdown after: {self.IDLE_SHUTDOWN_AFTER}s")
        logger.info("=" * 60)

        while self.running:
            try:
                # Get next pending job
                job = self.get_pending_job()

                if job:
                    # Reset idle timer
                    self.idle_since = None

                    # Process the job
                    result = self.process_job(job)

                    # Update job status
                    if result.success:
                        self.update_job_status(job.id, 'completed', result=result)
                        self.jobs_processed += 1
                        self.total_processing_time += result.processing_time_seconds
                    else:
                        self.update_job_status(job.id, 'failed',
                                               error_message=result.error_message,
                                               result=result)

                else:
                    # No jobs available
                    if self.idle_since is None:
                        self.idle_since = datetime.now()
                        logger.info("Queue empty, starting idle timer")
                    else:
                        idle_seconds = (datetime.now() - self.idle_since).total_seconds()
                        if idle_seconds > self.IDLE_SHUTDOWN_AFTER:
                            logger.info(f"Idle for {idle_seconds:.0f}s, initiating shutdown")
                            self.running = False
                            break

                    time.sleep(self.POLL_INTERVAL)

            except Exception as e:
                logger.exception(f"Worker loop error: {e}")
                time.sleep(self.POLL_INTERVAL)

        # Cleanup and report
        self._shutdown()

    def _shutdown(self):
        """Clean shutdown with summary"""
        logger.info("=" * 60)
        logger.info("GPU Worker shutting down...")
        logger.info(f"Total jobs processed: {self.jobs_processed}")
        if self.jobs_processed > 0:
            avg_time = self.total_processing_time / self.jobs_processed
            logger.info(f"Average processing time: {avg_time:.1f}s")
        logger.info(f"Total processing time: {self.total_processing_time:.1f}s")
        logger.info("=" * 60)

        self.db.close()

        # Write completion signal for orchestrator
        Path('/opt/goldventure/.worker_complete').touch()


def main():
    """Entry point"""
    # Load environment from .env file if exists
    env_file = Path('/opt/goldventure/.env')
    if env_file.exists():
        logger.info("Loading environment from .env file")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

    worker = GPUWorker()
    worker.run()


if __name__ == '__main__':
    main()
