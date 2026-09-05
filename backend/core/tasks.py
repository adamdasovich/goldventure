"""
Background Tasks for Document Processing and News Scraping
Processes document queue jobs sequentially
"""

import os
import logging
import traceback
from celery import shared_task
from django.utils import timezone
from datetime import datetime
from .models import DocumentProcessingJob, Company, NewsRelease, Document
from .news_classification import (
    classify_release_type,
    is_material_release_type,
    VALID_RELEASE_TYPES,
)
from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from mcp_servers.website_crawler import crawl_news_releases
from django.db.models import Q
from django.core.cache import cache
import asyncio

# Configure task logger
logger = logging.getLogger(__name__)


# =============================================================================
# TASK FAILURE HANDLING - Dead Letter Queue Alternative
# =============================================================================

def log_task_failure(self, exc, task_id, args, kwargs, einfo):
    """
    Handler for permanent task failures (after all retries exhausted).
    Logs detailed information for debugging and monitoring.

    This serves as a 'dead letter queue' alternative - logging failed tasks
    so they can be investigated and potentially reprocessed manually.
    """
    logger.error(
        f"TASK PERMANENTLY FAILED: {self.name}\n"
        f"  Task ID: {task_id}\n"
        f"  Args: {args}\n"
        f"  Kwargs: {kwargs}\n"
        f"  Exception: {exc}\n"
        f"  Traceback: {einfo}",
        extra={
            'task_name': self.name,
            'task_id': task_id,
            'task_args': str(args),
            'task_kwargs': str(kwargs),
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
        }
    )

    # Optionally store failed tasks in database for later review
    try:
        from .models import FailedTaskLog
        FailedTaskLog.objects.create(
            task_name=self.name,
            task_id=task_id,
            args=str(args),
            kwargs=str(kwargs),
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            traceback=str(einfo),
        )
    except Exception as e:
        # FailedTaskLog model may not exist yet - just log to file
        logger.warning(f"Could not log failed task to database: {e}")

# =============================================================================
# CONSTANTS - Centralized configuration for consistency across tasks
# =============================================================================

# Financing detection keywords (used for flagging news releases for review)
FINANCING_KEYWORDS = [
    'private placement',
    'financing',
    'funding round',
    'capital raise',
    'bought deal',
    'equity financing',
    'debt financing',
    'flow-through',
    'warrant',
    'subscription',
    'offering'
]

# Strategic investment keywords (major miner investments in juniors)
STRATEGIC_KEYWORDS = [
    'strategic investment',
    'strategic partner',
    'equity stake',
    'strategic alliance',
    'strategic equity',
    'cornerstone investor',
]

# Major miner names to detect strategic investments
MAJOR_MINERS = [
    'barrick',
    'newmont',
    'agnico eagle',
    'franco-nevada',
    'kinross',
    'anglogold ashanti',
    'gold fields',
    'wheaton precious metals',
    'royal gold',
    'eldorado gold',
    'iamgold',
    'endeavour mining',
    'b2gold',
    'yamana gold',
]

# Combined keywords for news flagging
ALL_FINANCING_KEYWORDS = FINANCING_KEYWORDS + STRATEGIC_KEYWORDS + MAJOR_MINERS

# Technical-report detection keywords. Matched (case-insensitive) against news
# release titles to flag releases that announce NI 43-101 / PEA / PFS / DFS /
# MRE / other technical reports. The superuser then submits the report PDF URL
# from /admin/news-flags-reports and the existing docling GPU pipeline ingests it.
REPORT_KEYWORDS = [
    'ni 43-101',
    'ni43-101',
    '43-101',
    'preliminary economic assessment',
    'pea',
    'prefeasibility study',
    'pre-feasibility study',
    'pfs',
    'feasibility study',
    'definitive feasibility',
    'dfs',
    'mineral resource estimate',
    'resource estimate',
    'mre',
    'technical report',
    'scoping study',
    # Reserve disclosures. A reserve statement is always backed by a technical
    # report, and 'resource estimate' above does not catch them.
    'mineral reserve',
    'reserve estimate',
    'maiden resource',
    # Non-Canadian equivalents: JORC for ASX-listed issuers, S-K 1300 for SEC
    # filers. No historical matches for S-K 1300 in the news table yet, but US
    # filers are moving to it and the term costs nothing to watch for.
    'jorc',
    's-k 1300',
    'sk-1300',
    # Catches 'Positive Economic Assessment' etc. where 'preliminary' is absent.
    'economic assessment',
]

# Deliberately NOT in the list above: 'metallurgical'. It matches 119 titles in
# the news table, 115 of which no other keyword catches — and they are things
# like "POSITIVE METALLURGICAL TEST RESULTS", "Metallurgical Test Work
# Programme" and an acquisition of a metallurgical facility. Met results are a
# precursor to a technical report, not a technical report, so the keyword would
# have more than doubled a review queue that already stands at 218 pending and
# made it less likely the real reports get worked. 'technical report summary'
# is also absent, but only because 'technical report' already matches it — the
# word-boundary regex below stops at the space, not at the end of the phrase.


import re as _re

# Pre-compile a regex per report keyword with word boundaries so short acronyms
# like 'pea', 'mre', 'pfs', 'dfs' don't substring-match unrelated words
# (e.g. 'Peak', 'more', 'before'). Longer phrases work fine either way but the
# uniform regex keeps the logic single-path.
_REPORT_KEYWORD_PATTERNS = [
    (kw, _re.compile(r'(?<![a-z0-9])' + _re.escape(kw) + r'(?![a-z0-9])', _re.IGNORECASE))
    for kw in REPORT_KEYWORDS
]


def _detect_report_keywords(title_lower: str):
    """Return list of REPORT_KEYWORDS that appear as standalone tokens in the title."""
    return [kw for kw, pat in _REPORT_KEYWORD_PATTERNS if pat.search(title_lower)]


def _maybe_flag_report(news_release_obj, company, title, url, release_date, is_new_company, cutoff_days=None):
    """
    Flag a news release as a potential technical report if its title contains
    report keywords, the release is recent, and it hasn't been dismissed under
    the report scope. Mirrors the financing-flag logic but writes to
    NewsReportFlag and uses the 'report_false_positive' dismissal scope.

    `cutoff_days` overrides the default age cutoff. Used by the backfill
    management command (e.g. 120 days) to flag historical releases.
    """
    from datetime import timedelta
    from core.models import NewsReportFlag, DismissedNewsURL

    if not release_date:
        return

    title_lower = (title or '').lower()
    detected = _detect_report_keywords(title_lower)
    if not detected:
        return

    if cutoff_days is None:
        cutoff_days = REPORT_FLAG_DAYS_ONBOARDING if is_new_company else REPORT_FLAG_DAYS_DAILY
    cutoff_date = datetime.now().date() - timedelta(days=cutoff_days)
    if release_date < cutoff_date:
        logger.info(f"  [SKIP report] Old news (not flagging): {title[:50]}... (date: {release_date})")
        return

    is_similar, _matched = DismissedNewsURL.is_similar_to_dismissed(
        company=company,
        url=url,
        title=title,
        similarity_threshold=NEWS_SIMILARITY_THRESHOLD,
        reason='report_false_positive',
    )
    if is_similar:
        logger.info(f"  [SKIP report] Similar to previously dismissed: {title[:50]}...")
        return

    flag, created = NewsReportFlag.objects.get_or_create(
        news_release=news_release_obj,
        defaults={
            'detected_keywords': detected,
            'status': 'pending',
        }
    )
    if created:
        logger.info(f"   Flagged technical-report news: {title[:60]}...")
        logger.info(f"     Keywords: {', '.join(detected)}")

# News scraping configuration
NEWS_SCRAPE_MONTHS_ONBOARDING = 48  # Months to look back for new companies
NEWS_SCRAPE_MONTHS_DAILY = 3  # Months to look back for daily scrapes
NEWS_FLAG_DAYS_ONBOARDING = 90  # Days to flag financing news for new companies
NEWS_FLAG_DAYS_DAILY = 7  # Days to flag financing news for existing companies

# Technical-report flag windows, kept separate from the financing ones above.
# A financing decays — a placement announced eight months ago is not news, and
# the 7-day daily cutoff is right for it. A technical report does not: a 2023
# NI 43-101 is still the current technical report for its project and still the
# document the mining assistant needs to answer questions about it. Reusing the
# financing cutoffs is why 410 of the 632 keyword-matching releases in the news
# table carry no flag.
#
# These only ever apply to newly-created NewsRelease rows — _maybe_flag_report()
# is called inside `if created:` at both scrape sites — so a wider window means
# an older release found for the first time still gets flagged. It does not
# re-flag anything already in the table.
REPORT_FLAG_DAYS_ONBOARDING = 1460  # 48 months, matching NEWS_SCRAPE_MONTHS_ONBOARDING
REPORT_FLAG_DAYS_DAILY = 365  # Existing companies: a year of technical history
NEWS_SIMILARITY_THRESHOLD = 0.85  # Threshold for detecting duplicate news


def process_general_document(document_url: str, document_type: str,
                            company_name: str, processor: HybridDocumentProcessor) -> dict:
    """
    Process general documents (presentations, fact sheets, etc.) using Docling.
    Extracts text and stores it in RAG for chatbot access.

    Args:
        document_url: URL to the PDF document
        document_type: Type of document (presentation, fact_sheet, etc.)
        company_name: Name of the company
        processor: HybridDocumentProcessor instance

    Returns:
        dict with success status and processing stats
    """
    try:
        # Find company
        company = Company.objects.filter(
            Company.identity_q(company_name)
        ).first() if company_name else None

        if not company:
            return {"error": f"Company '{company_name}' not found"}

        # Download and process with Docling
        pdf_path = processor._download_pdf(document_url)
        docling_data = processor._process_with_docling(pdf_path)
        pdf_path.unlink()

        # Create document record
        doc_title_map = {
            'presentation': 'Corporate Presentation',
            'fact_sheet': 'Fact Sheet',
            'news_release': 'News Release',
            'financial_statement': 'Financial Statement',
            'pea': 'Preliminary Economic Assessment',
        }

        # Read the publication date out of the document itself. Stamping
        # datetime.now() here made every document look simultaneous, which
        # collapsed Resource Growth's timeline and left Grade Ranker unable to
        # tell which estimate superseded which. The titles assigned below are
        # generic ("Corporate Presentation"), so the text is the only source —
        # and it is already in hand. None is recorded when it cannot be read;
        # unknown beats a plausible lie.
        from core.document_dates import parse_date_from_body
        parsed_date, _how = parse_date_from_body(docling_data.get('text', ''))

        document = Document.objects.create(
            company=company,
            title=doc_title_map.get(document_type, 'Document'),
            document_type=document_type,
            document_date=parsed_date,
            file_url=document_url,
            description=f"Auto-processed on {datetime.now().strftime('%Y-%m-%d')}"
        )

        # Store document chunks for RAG/semantic search
        chunks_stored = 0
        try:
            from mcp_servers.rag_utils import RAGManager
            rag_manager = RAGManager()
            full_text = docling_data['text']
            chunks_stored = rag_manager.store_document_chunks(document, full_text)
            logger.info(f"Stored {chunks_stored} chunks for semantic search")
        except Exception as e:
            logger.error(f"Error storing document chunks for RAG: {str(e)}")

        return {
            "success": True,
            "method": "Docling extraction + RAG storage",
            "document_id": document.id,
            "company": company.name,
            "processing_stats": {
                "pages_processed": docling_data.get('page_count', 0),
                "tables_extracted": len(docling_data.get('tables', [])),
                "document_chunks_stored": chunks_stored
            },
            "message": f"{document_type} processed successfully"
        }

    except Exception as e:
        return {"error": f"Document processing failed: {str(e)}"}


def process_document_queue():
    """
    Process all pending document jobs in queue
    Runs sequentially to avoid overloading resources
    """
    pending_jobs = DocumentProcessingJob.objects.filter(status='pending').order_by('created_at')

    logger.info(f"Found {pending_jobs.count()} pending jobs to process")

    for job in pending_jobs:
        process_single_job(job)


def process_single_job(job: DocumentProcessingJob):
    """Process a single document processing job"""

    # Mark as processing
    job.status = 'processing'
    job.started_at = datetime.now()
    job.progress_message = "Starting document processing..."
    job.save()

    try:
        # Initialize processor
        processor = HybridDocumentProcessor()

        # Update progress
        job.progress_message = "Downloading PDF..."
        job.save()

        # Determine company and project names
        company_name = job.company_name if job.company_name else None
        project_name = job.project_name if job.project_name else None

        # Process based on document type
        if job.document_type == 'ni43101':
            job.progress_message = "Processing NI 43-101 report (this may take 30-90 minutes)..."
            job.save()

            result = processor._process_ni43101_hybrid(
                document_url=job.url,
                company_name=company_name,
                project_name=project_name
            )

        elif job.document_type == 'pea':
            # PEA reports use the same hybrid processor as NI 43-101 (they contain economic data)
            job.progress_message = "Processing PEA report (this may take 30-90 minutes)..."
            job.save()

            result = processor._process_ni43101_hybrid(
                document_url=job.url,
                company_name=company_name,
                project_name=project_name
            )

        elif job.document_type in ['presentation', 'fact_sheet', 'news_release', 'financial_statement']:
            # Process all general documents (presentations, fact sheets, news releases, financial statements)
            # These documents are processed with Docling extraction and stored in RAG for chatbot queries
            job.progress_message = f"Processing {job.get_document_type_display()}..."
            job.save()

            result = process_general_document(
                document_url=job.url,
                document_type=job.document_type,
                company_name=company_name,
                processor=processor
            )

        else:
            # For other/unknown document types, use basic processing
            job.progress_message = f"Processing {job.get_document_type_display()}..."
            job.save()

            # Fall back to general processing
            result = process_general_document(
                document_url=job.url,
                document_type=job.document_type,
                company_name=company_name,
                processor=processor
            )

        # Check result
        if result.get('success'):
            # Update job with success
            job.status = 'completed'
            job.progress_message = "Processing completed successfully"
            job.document_id = result.get('document_id')
            job.resources_created = result.get('processing_stats', {}).get('resources_stored', 0)
            job.chunks_created = result.get('processing_stats', {}).get('document_chunks_stored', 0)
            job.completed_at = datetime.now()

            # Calculate processing time
            if job.started_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                job.processing_time_seconds = int(duration)

            job.save()

            logger.info(f" Job {job.id} completed successfully")
            logger.info(f"  - Document ID: {job.document_id}")
            logger.info(f"  - Resources created: {job.resources_created}")
            logger.info(f"  - Chunks created: {job.chunks_created}")
            logger.info(f"  - Processing time: {job.duration_display}")

            # Send email notification for NI 43-101 reports
            if job.document_type == 'ni43101' and job.document_id:
                try:
                    from core.notifications import send_ni43101_discovery_notification
                    document = Document.objects.get(id=job.document_id)
                    if document.company:
                        send_ni43101_discovery_notification(document, document.company)
                except Exception as e:
                    logger.warning(f"Failed to send NI 43-101 notification: {str(e)}")

            # Update CompanyNews record if this was a news_release
            if job.document_type == 'news_release':
                try:
                    from core.models import CompanyNews
                    # Find the associated news record
                    news_record = CompanyNews.objects.filter(processing_job=job).first()
                    if news_record:
                        # Mark as processed and store extracted content
                        news_record.is_processed = True
                        # Get extracted content from the document if available
                        if job.document_id:
                            document = Document.objects.filter(id=job.document_id).first()
                            if document and document.raw_text:
                                # Store first 10000 chars of content
                                news_record.content = document.raw_text[:10000]
                                # Generate summary from extracted text (first 500 chars as basic summary)
                                if not news_record.summary and document.raw_text:
                                    news_record.summary = document.raw_text[:500].strip() + "..."
                        news_record.save()
                        logger.info(f"   Updated CompanyNews record: {news_record.title[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to update CompanyNews record: {str(e)}")

        else:
            # Processing failed
            error_msg = result.get('error', 'Unknown error occurred')
            job.status = 'failed'
            job.error_message = error_msg
            job.completed_at = datetime.now()

            if job.started_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                job.processing_time_seconds = int(duration)

            job.save()

            logger.error(f"Job {job.id} failed: {error_msg}")

    except Exception as e:
        # Handle unexpected errors
        job.status = 'failed'
        job.error_message = f"Unexpected error: {str(e)}"
        job.completed_at = datetime.now()

        if job.started_at:
            duration = (job.completed_at - job.started_at).total_seconds()
            job.processing_time_seconds = int(duration)

        job.save()

        logger.exception(f"Job {job.id} failed with exception: {str(e)}")


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, time_limit=1800, soft_time_limit=1740, on_failure=log_task_failure)
def scrape_company_news_task(self, company_id):
    """
    Background task to scrape news releases for a company.

    Args:
        company_id (int): ID of the company to scrape news for

    Returns:
        dict: Status information about the scraping operation
    """
    try:
        # Get the company
        company = Company.objects.get(id=company_id)

        if not company.website:
            return {
                'status': 'error',
                'message': f'Company {company.name} has no website configured',
                'news_count': 0
            }

        # Run the async crawler in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            news_releases, successful_url = loop.run_until_complete(
                crawl_news_releases(
                    url=company.website,
                    months=NEWS_SCRAPE_MONTHS_ONBOARDING,  # Use constant for consistency
                    max_depth=2,
                    custom_news_url=company.news_url if company.news_url else None
                )
            )
        finally:
            loop.close()

        # Cache the successful URL for future scrapes (major performance optimization)
        if successful_url and successful_url != company.last_working_news_url:
            company.last_working_news_url = successful_url
            company.save(update_fields=['last_working_news_url'])
            logger.info(f"  [ONBOARDING] Cached successful URL: {successful_url}")

        # Process and save news releases
        created_count = 0
        updated_count = 0

        # Check if this is a new company being onboarded (no existing NewsRelease records)
        # For new companies: use 90-day rule (3 months) to show recent financing history
        # For existing companies: use 7-day rule to avoid re-flagging old news daily
        # Use .exists() instead of .count() == 0 for better performance
        is_new_company = not NewsRelease.objects.filter(company=company).exists()
        if is_new_company:
            logger.info(f"  [ONBOARDING] New company detected - will flag financing from last 90 days")

        for news in news_releases:
            title = news.get('title', '').strip()
            url = news.get('url', '').strip()
            date_str = news.get('date')
            doc_type = news.get('document_type')
            release_type = (
                doc_type if doc_type in VALID_RELEASE_TYPES
                else classify_release_type(title)
            )

            # is_material flags genuine catalyst events (drilling, resources,
            # studies, financings, M&A) — distinct from the local
            # `is_financial` flag below which is only for financial-statement
            # press releases used to route documents.
            is_financial = any(keyword in title.lower() for keyword in [
                'financial', 'earnings', 'quarter', 'q1', 'q2', 'q3', 'q4',
                'annual report', 'md&a', 'interim', 'fiscal'
            ])
            is_material = is_material_release_type(release_type)

            # Parse date
            if date_str:
                try:
                    release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    release_date = None
            else:
                release_date = None

            # Skip if no URL
            if not url:
                continue

            # If no date provided, use today's date as fallback
            if not release_date:
                continue  # Skip entries without valid dates

            # Create or update news release (using URL as unique identifier)
            # SECURITY: Use update_or_create to prevent TOCTOU race condition
            obj, created = NewsRelease.upsert_from_scrape(
                company=company,
                url=url,
                defaults={
                    'title': title,
                    'release_type': release_type,
                    'release_date': release_date,
                    'summary': '',
                    'is_material': is_material,
                    'full_text': ''
                }
            )

            # Also create/update CompanyNews record (used by frontend API)
            from core.models import CompanyNews
            news_record, _ = CompanyNews.upsert_from_scrape(
                company=company,
                url=url,
                defaults={
                    "title": title,
                    "publication_date": release_date,
                    "news_type": "corporate",
                }
            )

            # PDF news releases are NOT queued to the GPU any more.
            #
            # This used to create a DocumentProcessingJob(document_type=
            # 'news_release') for any news URL ending in .pdf, because
            # NewsContentProcessor._fetch_content_from_url() refused PDFs
            # outright — so Docling on a GPU droplet was the only way to read
            # one. That produced 2,532 GPU jobs and left 15,163 news chunks in
            # document_chunks: 30% of the technical-document collection was news
            # releases, diluting NI 43-101 and PEA retrieval and costing
            # ~$1.57/hr of droplet time for content the news pipeline already
            # covers for free.
            #
            # The news processor now reads a PDF's text layer directly, so this
            # content reaches news_chunks through embed_recent_news_for_rag_task
            # like every other news item. A news release is a few pages of
            # digitally generated text; it never needed a GPU.
            #
            # Technical reports are unaffected — they are queued deliberately by
            # the report hunter and the flag-review page, not from here.

            if created:
                created_count += 1

                # TECHNICAL-REPORT DETECTION: flag releases that mention
                # NI 43-101, PEA, PFS, DFS, MRE, etc. Runs independently of
                # financing detection — a single release may produce both flags.
                try:
                    _maybe_flag_report(
                        news_release_obj=obj,
                        company=company,
                        title=title,
                        url=url,
                        release_date=release_date,
                        is_new_company=is_new_company,
                    )
                except Exception as e:
                    logger.warning(f"Report-flag detection error for {title[:50]}: {e}")

                # FINANCING DETECTION: Check for financing keywords in title
                # Uses centralized constants from top of file
                title_lower = title.lower()
                detected_keywords = [kw for kw in ALL_FINANCING_KEYWORDS if kw in title_lower]

                # If financing keywords detected, create flag for superuser review
                # For NEW companies (onboarding): use 90-day rule to show recent financing history
                # For EXISTING companies: use 7-day rule to avoid re-flagging old news daily
                if detected_keywords and release_date:
                    from core.models import NewsReleaseFlag, DismissedNewsURL
                    from datetime import timedelta

                    # Use different cutoff based on whether this is a new company
                    cutoff_days = NEWS_FLAG_DAYS_ONBOARDING if is_new_company else NEWS_FLAG_DAYS_DAILY
                    cutoff_date = datetime.now().date() - timedelta(days=cutoff_days)
                    if release_date < cutoff_date:
                        logger.info(f"  [SKIP] Old news (not flagging): {title[:50]}... (date: {release_date})")
                        continue

                    # Check if URL or title is similar to a previously dismissed news
                    is_similar, matched_dismissed = DismissedNewsURL.is_similar_to_dismissed(
                        company=company,
                        url=url,
                        title=title,
                        similarity_threshold=NEWS_SIMILARITY_THRESHOLD
                    )
                    if is_similar:
                        logger.info(f"  [SKIP] Similar to previously dismissed: {title[:50]}...")
                        continue

                    # Only create flag if one doesn't already exist
                    flag, flag_created = NewsReleaseFlag.objects.get_or_create(
                        news_release=obj,
                        defaults={
                            'detected_keywords': detected_keywords,
                            'status': 'pending'
                        }
                    )

                    logger.info(f"   Flagged financing-related news: {title[:60]}...")
                    logger.info(f"     Keywords: {', '.join(detected_keywords)}")

                    # Send email notification for new flags only
                    if flag_created:
                        try:
                            from core.notifications import send_financing_flag_notification
                            send_financing_flag_notification(flag, company, obj)
                        except Exception as e:
                            logger.warning(f"Failed to send financing flag notification: {str(e)}")

            else:
                updated_count += 1

        # Auto-process news content into vector database for semantic search
        # SIGSEGV-SAFE: Using subprocess isolation to protect against ChromaDB Rust binding crashes
        # See: https://github.com/chroma-core/chroma/issues/4365 - tokio-runtime segfaults
        # The subprocess isolation ensures SIGSEGV crashes don't kill the Celery worker
        if created_count > 0 and is_new_company:
            try:
                from core.chromadb_isolated import process_company_news_isolated

                logger.info(f"  Processing news into ChromaDB (subprocess-isolated)...")
                process_result = process_company_news_isolated(
                    company_name=company.name,
                    company_id=company.id,
                    limit=created_count + 5,
                    timeout=120  # 2 minute timeout per company
                )

                if process_result.get('success'):
                    inner_result = process_result.get('result', {})
                    chunks_created = inner_result.get('chunks_created', 0)
                    items_processed = inner_result.get('news_items_processed', 0)
                    logger.info(f"  ChromaDB: Processed {items_processed} news items into {chunks_created} searchable chunks")
                elif process_result.get('crash'):
                    # Subprocess crashed (SIGSEGV) but we survived
                    logger.warning(f"  ChromaDB: Subprocess crashed ({process_result.get('error', 'unknown')}), but worker survived")
                elif process_result.get('timeout'):
                    logger.warning(f"  ChromaDB: Processing timed out, skipping")
                else:
                    logger.warning(f"  ChromaDB: Processing failed: {process_result.get('error', 'unknown')}")
            except Exception as e:
                logger.warning(f"  Warning: News content processing failed: {str(e)}")
                # Don't fail the whole task if content processing fails

        return {
            'status': 'success',
            'company': company.name,
            'news_count': len(news_releases),
            'created': created_count,
            'updated': updated_count,
            'message': f'Successfully scraped {len(news_releases)} news releases for {company.name}'
        }

    except Company.DoesNotExist:
        return {
            'status': 'error',
            'message': f'Company with ID {company_id} not found',
            'news_count': 0
        }

    except Exception as e:
        # Retry on failure with exponential backoff (handled by retry_backoff=True)
        self.retry(exc=e)

        return {
            'status': 'error',
            'message': f'Error scraping news: {str(e)}',
            'news_count': 0
        }


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def scrape_metals_prices_task(self):
    """
    Scheduled task to scrape precious metals prices from Kitco.
    Runs twice daily (e.g., 9 AM and 4 PM ET).

    Returns:
        dict: Status information about the scraping operation
    """
    try:
        from mcp_servers.kitco_scraper import scrape_and_save_metals_prices

        result = scrape_and_save_metals_prices()

        if result['success']:
            logger.info(f"Successfully scraped {result['scraped']} metals prices from Kitco")
            return result
        else:
            logger.error(f"Metals scrape failed: {result.get('error', 'Unknown error')}")
            # Retry on failure
            raise Exception(result.get('error', 'Scraping failed'))

    except Exception as e:
        logger.error(f"Error in metals scraping task: {str(e)}")
        self.retry(exc=e)  # Retry with exponential backoff

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def fetch_base_metals_prices_task(self):
    """
    Scheduled task to fetch base / critical metals prices not covered by Kitco.

    Fetches daily copper (CU) from Yahoo Finance, plus Uranium, Cobalt
    Hydroxide and Lithium from Trading Economics. Runs once per weekday.

    A failure in one source does not block the other.

    Returns:
        dict: Status information about the fetch operation
    """
    try:
        from mcp_servers.base_metals_scraper import (
            fetch_daily_copper, fetch_daily_tradingeconomics_metals,
        )

        copper_result = fetch_daily_copper()
        te_result = fetch_daily_tradingeconomics_metals()

        if copper_result.get('success'):
            logger.info(f"Stored daily copper price: ${copper_result['price']}/lb "
                        f"({copper_result['date']})")
        else:
            logger.error(f"Copper fetch failed: {copper_result.get('error', 'Unknown error')}")

        if te_result.get('success'):
            logger.info(f"Trading Economics: stored {len(te_result['saved'])} metals")
        else:
            logger.error(f"Trading Economics fetch failed: {te_result.get('error', 'Unknown error')}")
        for err in te_result.get('errors', []):
            logger.warning(f"Trading Economics: {err}")

        # Retry only if BOTH sources failed (likely a transient network issue).
        if not copper_result.get('success') and not te_result.get('success'):
            raise Exception('All base-metal sources failed')

        return {'success': True, 'copper': copper_result, 'trading_economics': te_result}

    except Exception as e:
        logger.error(f"Error in base metals fetch task: {str(e)}")
        self.retry(exc=e)

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, time_limit=600, soft_time_limit=580, on_failure=log_task_failure)
def fetch_stock_prices_task(self):
    """
    Scheduled task to fetch and store daily stock prices for all companies.
    Runs weekdays after market close (4:30 PM ET / 21:30 UTC).

    Primary source: Stockwatch.com (for Canadian exchanges)
    Fallback: Alpha Vantage API

    Returns:
        dict: Status information about the scraping operation
    """
    try:
        from mcp_servers.stock_price_scraper import fetch_and_save_stock_prices

        result = fetch_and_save_stock_prices()

        if result['success']:
            logger.info(f"Successfully fetched {result['successful']} stock prices")
            logger.info(f"Failed: {result['failed']}, Skipped: {result['skipped']}")
            return result
        else:
            # Partial success - some companies had errors
            logger.info(f"Stock price fetch completed with errors:")
            logger.info(f"Successful: {result['successful']}, Failed: {result['failed']}")
            if result['errors']:
                for error in result['errors'][:5]:  # Show first 5 errors
                    logger.info(f"  - {error}")
            return result

    except Exception as e:
        logger.error(f"Error in stock price fetching task: {str(e)}")
        self.retry(exc=e)  # Retry with exponential backoff

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, time_limit=3600, soft_time_limit=3540, on_failure=log_task_failure)
def auto_discover_and_process_documents_task(self, company_ids=None, document_types=None,
                                             limit=None, dry_run=False):
    """
    Crawl company websites for technical documents and queue the credible ones.

    Rotation: companies are visited least-recently-first via
    Company.last_discovered_at, which is stamped after every visit — including
    failed crawls, so a broken site cannot pin the head of the rotation.

    Gate: a discovered document only becomes a DocumentProcessingJob if it
    passes check_discovered_document() — it must not read as an announcement,
    presentation or financial statement, and it must have a confirmed
    Content-Length at or above the report-size floor. Discovery has no news
    release to score against, so these are the two structural checks that
    transfer from the hunter; everything refused is logged with its reason.

    Jobs are left pending for the GPU orchestrator. This task used to end by
    calling process_document_queue(), which runs Docling in-process on the
    Celery worker — the exact thing CLAUDE.md forbids (the workers hold
    850M-2400M memory caps, a 300-page NI 43-101 does not fit) — while also
    racing the GPU worker for the same rows without its row locking.

    Args:
        company_ids: explicit companies, bypassing the rotation.
        document_types: optional pre-filter on crawler-emitted types.
        limit: companies per run.
        dry_run: crawl and report what would be queued, but write nothing —
            no jobs, no rotation stamps.
    """
    try:
        from core.models import Company
        from mcp_servers.website_crawler import crawl_company_website
        from mcp_servers.report_hunter import check_discovered_document
        
        # Get companies to process
        if company_ids:
            companies = Company.objects.filter(id__in=company_ids, website__isnull=False).exclude(website='')
        else:
            # Least-recently-visited first, never-visited before that. The old
            # selection sliced [:limit] off default ordering, which meant the
            # weekly run crawled the same 25 companies every Sunday and
            # coverage never advanced past them.
            from django.db.models import F
            companies = Company.objects.filter(
                website__isnull=False
            ).exclude(website='').order_by(
                F('last_discovered_at').asc(nulls_first=True), 'id'
            )

        if limit:
            companies = companies[:limit]

        companies = list(companies)
        
        if not companies:
            return {
                'status': 'warning',
                'message': 'No companies with websites found to process',
                'total_discovered': 0,
                'jobs_created': 0
            }
        
        # Track statistics
        total_discovered = 0
        total_jobs_created = 0
        total_gated = 0
        companies_processed = 0
        
        logger.info(f"Auto-discovery task: Processing {len(companies)} companies")
        
        for company in companies:
            try:
                logger.info(f"Crawling {company.name}...")
                
                # Discover documents
                documents = asyncio.run(crawl_company_website(company.website, max_depth=2))

                if not documents:
                    logger.info(f"  No documents discovered for {company.name}")
                    continue

                # Filter by document type if specified
                if document_types:
                    documents = [d for d in documents if d['document_type'] in document_types]

                # IMPORTANT: Filter to only important recent documents
                # Keep: most recent NI 43-101, most recent PEA, recent presentations, recent financials
                discovered_count = len(documents)
                filtered_docs = []
                seen_types = set()

                # Technical report types, in the canonical job vocabulary that
                # crawl_company_website() now guarantees. This list previously
                # read ['ni_43_101', 'pea', 'feasibility_study', 'resource_estimate'],
                # which no crawler emitted after canonicalization and which the
                # main crawler never emitted at all — so 'ni43101' documents
                # matched no branch below, fell off the end of the loop and were
                # dropped without ever being queued.
                priority_types = ['ni43101', 'pea']

                # Sort by date (newest first) if dates available
                documents.sort(key=lambda x: x.get('date') or '0000-00-00', reverse=True)

                for doc in documents:
                    doc_type = doc.get('document_type', 'other')

                    # For technical reports, keep the most recent of each
                    # distinct subtype. Deduplicating on document_type alone
                    # would keep one technical document per company, when a
                    # company can publish an NI 43-101, a feasibility study and
                    # an MRE that all canonicalize to 'ni43101'.
                    if doc_type in priority_types:
                        dedupe_key = doc.get('document_subtype') or doc_type
                        if dedupe_key not in seen_types:
                            filtered_docs.append(doc)
                            seen_types.add(dedupe_key)
                            logger.info(f"    [KEEP] {dedupe_key} ({doc_type}): {doc.get('title', 'No title')[:50]}")

                    # For presentations, keep most recent only
                    elif doc_type == 'presentation':
                        if 'presentation' not in seen_types:
                            filtered_docs.append(doc)
                            seen_types.add('presentation')
                            logger.info(f"    [KEEP] presentation: {doc.get('title', 'No title')[:50]}")

                    # Skip old financial statements, news releases (handled separately), and 'other' types
                    elif doc_type in ['financial_statement', 'news_release', 'other']:
                        continue

                    # Never drop silently. An unrecognized type reaching this
                    # branch means the crawler vocabulary and this filter have
                    # drifted apart again, which is the failure that hid the
                    # 'ni43101' drop for as long as it did.
                    else:
                        logger.warning(
                            f"    [DROP] Unhandled document_type {doc_type!r} for "
                            f"{company.name}: {doc.get('title', 'No title')[:50]}"
                        )

                documents = filtered_docs
                logger.info(f"  Filtered to {len(documents)} important documents (from {discovered_count} discovered)")
                total_discovered += len(documents)
                
                # Create processing jobs (skip existing)
                jobs_created = 0
                for doc in documents:
                    # Check if document already exists
                    existing = Document.objects.filter(
                        company=company,
                        file_url=doc['url']
                    ).exists()

                    if existing:
                        continue

                    # Structural gate before anything reaches the GPU.
                    # Discovery has no announcement to score against, so the
                    # anchored hunter scoring cannot apply — but the two checks
                    # that caught every wrong auto-queue do: announcement-
                    # shaped documents are refused, and the file must have a
                    # confirmed report-sized Content-Length. Refusals are log
                    # lines, never silent.
                    doc_text = f"{doc.get('title', '')} {doc.get('link_text', '')}"
                    ok, reason = check_discovered_document(doc['url'], doc_text)
                    if not ok:
                        total_gated += 1
                        logger.info(
                            f"    [GATED] {reason}: {doc.get('title', 'No title')[:56]} "
                            f"({doc['url'][-56:]})"
                        )
                        continue

                    if dry_run:
                        jobs_created += 1
                        logger.info(
                            f"    [DRY-RUN would queue] {reason}: "
                            f"{doc.get('title', 'No title')[:56]}"
                        )
                        continue

                    # Use get_or_create to avoid race condition (TOCTOU vulnerability)
                    # Only create job if status would be 'pending' (not already completed/processing)
                    job, job_created = DocumentProcessingJob.objects.get_or_create(
                        url=doc['url'],
                        defaults={
                            'document_type': doc['document_type'],
                            'company_name': company.name,
                            'status': 'pending'
                        }
                    )

                    # Only count if newly created (not existing completed/processing)
                    if job_created:
                        jobs_created += 1
                        logger.info(f"    [QUEUED] {reason}: {doc.get('title', 'No title')[:56]}")

                total_jobs_created += jobs_created
                companies_processed += 1

                logger.info(f"  Created {jobs_created} new processing jobs")

            except Exception as e:
                logger.warning(f"Error processing {company.name}: {str(e)}")
                continue
            finally:
                # Advance the rotation whatever happened. Stamping only on
                # success would let one broken site sit at the head of the
                # least-recently-visited order and block every company behind
                # it, every week.
                if not dry_run:
                    Company.objects.filter(pk=company.pk).update(
                        last_discovered_at=timezone.now()
                    )
        
        # Jobs are deliberately left pending for the GPU orchestrator (60s
        # poll). This used to call process_document_queue() here, which runs
        # Docling in-process on this Celery worker — the "never process
        # documents on CPU" case — while racing the GPU worker for the same
        # pending rows without its FOR UPDATE SKIP LOCKED claim.

        return {
            'status': 'success',
            'dry_run': dry_run,
            'companies_processed': companies_processed,
            'total_discovered': total_discovered,
            'gated': total_gated,
            'jobs_created': total_jobs_created,
            'message': (f'Auto-discovery completed: {companies_processed} companies, '
                        f'{total_discovered} documents discovered, {total_gated} gated, '
                        f'{total_jobs_created} jobs '
                        + ('would be created (dry run)' if dry_run else 'created'))
        }
        
    except Exception as e:
        logger.error(f"Error in auto-discovery task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Auto-discovery task failed: {str(e)}'
        }


# Timeout for async operations (Celery's soft_time_limit doesn't work with asyncio)
ASYNC_SCRAPE_TIMEOUT = 300  # 5 minutes - enforced inside event loop


@shared_task(bind=True, max_retries=2, retry_backoff=True, retry_backoff_max=300, retry_jitter=True, time_limit=600, soft_time_limit=580, on_failure=log_task_failure)
def scrape_single_company_news_task(self, company_id: int):
    """
    Background task to scrape news releases for a SINGLE company.
    This task is spawned by scrape_all_companies_news_task for each company.

    Time limit: 10 minutes per company (but asyncio timeout at 5 min)

    NOTE: Celery's soft_time_limit doesn't work with asyncio because signals
    can't interrupt the event loop. We use asyncio.wait_for() to enforce timeout.
    """
    try:
        company = Company.objects.get(id=company_id)
        logger.info(f"Scraping news for {company.name}...")

        # Run the async crawler with explicit timeout
        # (Celery's soft_time_limit doesn't interrupt asyncio)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            news_releases, successful_url = loop.run_until_complete(
                asyncio.wait_for(
                    crawl_news_releases(
                        url=company.website,
                        months=NEWS_SCRAPE_MONTHS_DAILY,
                        max_depth=2,
                        custom_news_url=company.news_url if company.news_url else None,
                        cached_news_url=company.last_working_news_url if company.last_working_news_url else None
                    ),
                    timeout=ASYNC_SCRAPE_TIMEOUT
                )
            )
        except asyncio.TimeoutError:
            logger.error(f"   {company.name}: Timed out after {ASYNC_SCRAPE_TIMEOUT}s")
            return {'company_id': company_id, 'company_name': company.name, 'status': 'timeout', 'created': 0, 'updated': 0}
        finally:
            loop.close()

        # Cache the successful URL for future scrapes (major performance optimization)
        if successful_url and successful_url != company.last_working_news_url:
            company.last_working_news_url = successful_url
            company.save(update_fields=['last_working_news_url'])
            logger.info(f"   {company.name}: Cached successful URL: {successful_url}")

        # Process and save news releases
        created_count = 0
        updated_count = 0

        for news in news_releases:
            title = news.get('title', '').strip()
            url = news.get('url', '').strip()
            date_str = news.get('date')
            doc_type = news.get('document_type')
            release_type = (
                doc_type if doc_type in VALID_RELEASE_TYPES
                else classify_release_type(title)
            )

            if not url:
                continue

            # Parse date
            release_date = None
            if date_str:
                try:
                    release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    logger.warning(f"   {company.name}: Skipping news with unparseable date '{date_str}': {title[:60]}")
                    continue  # Skip entries without valid dates
            else:
                logger.debug(f"   {company.name}: Skipping news with no date: {title[:60]}")
                continue  # Skip entries without valid dates

            # Create or update news release
            # SECURITY: Use update_or_create to prevent TOCTOU race condition
            obj, created = NewsRelease.upsert_from_scrape(
                company=company,
                url=url,
                defaults={
                    'title': title,
                    'release_type': release_type,
                    'release_date': release_date,
                    'summary': '',
                    'is_material': is_material_release_type(release_type),
                    'full_text': ''
                }
            )

            if created:
                created_count += 1

                # TECHNICAL-REPORT DETECTION: flag releases that mention
                # NI 43-101, PEA, PFS, DFS, MRE, etc. Independent of financing.
                try:
                    _maybe_flag_report(
                        news_release_obj=obj,
                        company=company,
                        title=title,
                        url=url,
                        release_date=release_date,
                        is_new_company=False,
                    )
                except Exception as e:
                    logger.warning(f"Report-flag detection error for {title[:50]}: {e}")

                # Check for financing keywords and flag
                # Uses centralized constants from top of file (ALL_FINANCING_KEYWORDS)
                title_lower = title.lower()
                detected_keywords = [kw for kw in ALL_FINANCING_KEYWORDS if kw in title_lower]

                # Only flag recent news (within NEWS_FLAG_DAYS_DAILY) - older news is not actionable
                if detected_keywords and release_date:
                    from core.models import NewsReleaseFlag, DismissedNewsURL
                    from datetime import timedelta

                    # Only flag news releases within the configured days
                    cutoff_date = datetime.now().date() - timedelta(days=NEWS_FLAG_DAYS_DAILY)
                    if release_date < cutoff_date:
                        logger.info(f"  [SKIP] Old news (not flagging): {title[:50]}...")
                    else:
                        # Check if URL or title is similar to previously dismissed - never re-flag
                        is_similar, matched_dismissed = DismissedNewsURL.is_similar_to_dismissed(
                            company=company,
                            url=url,
                            title=title,
                            similarity_threshold=NEWS_SIMILARITY_THRESHOLD
                        )
                        if is_similar:
                            logger.info(f"  [SKIP] Similar to dismissed: {title[:50]}...")
                        else:
                            flag, flag_created = NewsReleaseFlag.objects.get_or_create(
                                news_release=obj,
                                defaults={
                                    'detected_keywords': detected_keywords,
                                    'status': 'pending'
                                }
                            )
                            if flag_created:
                                logger.info(f"  [FLAG] Flagged: {title[:50]}...")
                                try:
                                    from core.notifications import send_financing_flag_notification
                                    send_financing_flag_notification(flag, company, obj)
                                except Exception as e:
                                    logger.warning(f"Notification error: {str(e)}")
            else:
                updated_count += 1

        logger.info(f"   {company.name}: {created_count} new, {updated_count} updated")
        return {
            'company_id': company_id,
            'company_name': company.name,
            'status': 'success',
            'created': created_count,
            'updated': updated_count
        }

    except Company.DoesNotExist:
        return {'company_id': company_id, 'status': 'error', 'message': 'Company not found'}
    except Exception as e:
        logger.error(f"   Error scraping company {company_id}: {str(e)}")
        return {'company_id': company_id, 'status': 'error', 'message': str(e)}


@shared_task(bind=True, max_retries=1, time_limit=300, on_failure=log_task_failure)
def scrape_all_companies_news_task(self):
    """
    Background task to queue news scraping for ALL companies with websites.
    Spawns individual tasks for each company with staggered delays.

    Scheduled to run daily in the morning via Celery Beat.

    IMPORTANT: Tasks are staggered with 30-second delays between each company
    to avoid overwhelming target websites and getting IP-blocked.

    Uses a distributed lock to prevent duplicate batches from running concurrently.
    """
    # Distributed lock to prevent duplicate batch runs
    LOCK_KEY = 'scrape_all_companies_news_lock'
    LOCK_TTL = 7200  # 2 hours - longer than expected batch duration

    # Try to acquire lock - returns True only if lock was successfully set
    lock_acquired = cache.add(LOCK_KEY, self.request.id, timeout=LOCK_TTL)

    if not lock_acquired:
        existing_task_id = cache.get(LOCK_KEY)
        logger.warning(f"Skipping scrape batch - another batch is already running (task: {existing_task_id})")
        return {
            'status': 'skipped',
            'reason': 'batch_already_running',
            'existing_task_id': existing_task_id,
            'message': f'A scrape batch is already running (task: {existing_task_id}). Skipping to prevent duplicates.'
        }

    logger.info("Starting company news scrape - spawning individual tasks with staggered delays...")
    logger.info(f"Acquired batch lock (key: {LOCK_KEY}, task: {self.request.id})")

    # Delay between each company scrape (seconds)
    # Reduced from 30s to 10s since each task hits DIFFERENT domains (no IP blocking risk)
    # Combined with URL caching optimization, this cuts total scrape time significantly
    SCRAPE_DELAY_SECONDS = 10

    try:
        # Get all companies with websites
        companies = Company.objects.filter(
            website__isnull=False
        ).exclude(website='').order_by('name')

        total_companies = companies.count()
        logger.info(f"Found {total_companies} companies with websites to scrape")
        logger.info(f"Staggering tasks with {SCRAPE_DELAY_SECONDS}s delay between each")
        logger.info(f"Estimated total time: {(total_companies * SCRAPE_DELAY_SECONDS) / 60:.1f} minutes")

        # Spawn individual tasks for each company with staggered delays
        task_ids = []
        for i, company in enumerate(companies):
            # Queue individual task with countdown delay
            # First company starts immediately, subsequent ones are delayed
            countdown = i * SCRAPE_DELAY_SECONDS
            task = scrape_single_company_news_task.apply_async(
                args=[company.id],
                countdown=countdown
            )
            task_ids.append(task.id)
            logger.info(f"  Queued: {company.name} (task {task.id}, delay: {countdown}s)")

        logger.info(f"\nQueued {len(task_ids)} individual scraping tasks with staggered delays")

        return {
            'status': 'success',
            'total_companies': total_companies,
            'tasks_queued': len(task_ids),
            'delay_between_tasks': SCRAPE_DELAY_SECONDS,
            'estimated_duration_minutes': (total_companies * SCRAPE_DELAY_SECONDS) / 60,
            'message': f"Queued {len(task_ids)} company news scraping tasks with {SCRAPE_DELAY_SECONDS}s stagger"
        }

    except Exception as e:
        logger.error(f"Error queuing company news scrape tasks: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Failed to queue company news scrape tasks: {str(e)}'
        }
    finally:
        # Always release lock when batch task completes (success or error)
        # Previously only released on error, relying on 2hr TTL for success —
        # this blocked manual re-triggers for up to 2 hours after completion
        cache.delete(LOCK_KEY)
        logger.info(f"Released batch lock (key: {LOCK_KEY})")


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, time_limit=600, soft_time_limit=580, on_failure=log_task_failure)
def scrape_mining_news_task(self):
    """
    Background task to scrape mining news from configured sources.
    Runs the async news scraper and saves articles to the database.

    Scheduled to run multiple times daily via Celery Beat.
    """
    from mcp_servers.news_scraper import run_scrape_job
    from .models import NewsScrapeJob

    logger.info("Starting mining news scrape task...")

    try:
        # Create a new scrape job record
        job = NewsScrapeJob.objects.create(
            status='pending',
            is_scheduled=True
        )
        logger.info(f"Created scrape job {job.id}")

        # Run the async scraper
        result = asyncio.run(run_scrape_job(job_id=job.id))

        logger.info(f"Mining news scrape completed: {result}")
        return {
            'status': 'success',
            'job_id': job.id,
            'sources_processed': result.get('sources_processed', 0),
            'articles_found': result.get('articles_found', 0),
            'message': f"Successfully scraped mining news: {result.get('articles_found', 0)} articles found"
        }

    except Exception as e:
        logger.error(f"Error in mining news scrape task: {str(e)}")
        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Mining news scrape failed after retries: {str(e)}'
            }


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=300, retry_jitter=True, time_limit=1200, soft_time_limit=1140, acks_late=True, on_failure=log_task_failure)
def scrape_company_website_task(self, job_id: int, sections: list = None):
    """
    Background task to scrape a company website using Crawl4AI.
    This task runs the heavy headless browser scraping in the background,
    preventing timeouts and server resource exhaustion.

    Args:
        job_id (int): ID of the ScrapingJob record
        sections (list, optional): List of sections to scrape

    Returns:
        dict: Status information about the scraping operation

    Notes:
        - time_limit=600: Hard limit of 10 minutes per task
        - soft_time_limit=580: Soft limit to allow graceful shutdown
        - acks_late=True: Task is only acknowledged after completion, so if worker
          crashes the task will be redelivered to another worker
    """
    from mcp_servers.company_scraper import scrape_company_website
    from .models import ScrapingJob
    from celery.exceptions import SoftTimeLimitExceeded

    logger.info(f"[ASYNC SCRAPE] Starting company scrape task for job {job_id}...")

    try:
        # Get the scraping job
        job = ScrapingJob.objects.get(id=job_id)

        # Check if job is already completed or failed (idempotency for acks_late redelivery)
        if job.status in ['success', 'partial', 'failed', 'cancelled']:
            logger.info(f"[ASYNC SCRAPE] Job {job_id} already has status '{job.status}', skipping")
            return {
                'status': 'skipped',
                'job_id': job_id,
                'message': f'Job already completed with status: {job.status}'
            }

        job.status = 'running'
        job.started_at = timezone.now()
        job.save()

        url = job.website_url
        logger.info(f"[ASYNC SCRAPE] Scraping URL: {url}")

        # Run the async scraper
        result = asyncio.run(scrape_company_website(url, sections=sections))

        # Update job with scraped data
        job.data_extracted = result['data']
        job.error_messages = result['errors']
        job.sections_completed = sections or ['all']
        job.status = 'success'
        job.completed_at = timezone.now()

        # Count extracted items
        data = result['data']
        job.documents_found = len(data.get('documents', []))
        job.people_found = len(data.get('people', []))
        job.news_found = len(data.get('news', []))
        job.save()

        logger.info(f"[ASYNC SCRAPE] Job {job_id} completed successfully")
        logger.info(f"  - Documents: {job.documents_found}")
        logger.info(f"  - People: {job.people_found}")
        logger.info(f"  - News: {job.news_found}")

        return {
            'status': 'success',
            'job_id': job_id,
            'data': result['data'],
            'errors': result['errors'],
            'urls_visited': result['urls_visited'],
            'message': f"Successfully scraped company website"
        }

    except ScrapingJob.DoesNotExist:
        logger.info(f"[ASYNC SCRAPE] Job {job_id} not found")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': f'ScrapingJob with ID {job_id} not found'
        }

    except SoftTimeLimitExceeded:
        # Task timed out - mark as failed with timeout message
        logger.info(f"[ASYNC SCRAPE] Job {job_id} timed out (exceeded 10 minute limit)")
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = ['Task timed out - exceeded 10 minute limit. The website may be too slow or complex.']
            job.save()
        except Exception as e:
            logger.error(f" Failed to update job {job_id} status on timeout: {e}")

        return {
            'status': 'error',
            'job_id': job_id,
            'error': 'Task timed out',
            'message': 'Company scrape timed out after 10 minutes'
        }

    except Exception as e:
        logger.exception(f"[ASYNC SCRAPE] Job {job_id} failed: {str(e)}")

        # Update job with failure
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = [str(e)]
            job.error_traceback = traceback.format_exc()
            job.save()
        except Exception as update_err:
            logger.error(f" Failed to update job {job_id} status on error: {update_err}")

        # Retry on failure (but not for timeouts)
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'job_id': job_id,
                'error': str(e),
                'message': f'Company scrape failed after retries: {str(e)}'
            }


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=300, retry_jitter=True, time_limit=1200, soft_time_limit=1140, acks_late=True, on_failure=log_task_failure)
def scrape_and_save_company_task(self, job_id: int, update_existing: bool = False, user_id: int = None):
    """
    Background task to scrape a company website AND save to database.
    This prevents timeout issues when onboarding companies with lots of content.

    Args:
        job_id (int): ID of the ScrapingJob record (already created by the view)
        update_existing (bool): Whether to update existing company if found
        user_id (int): ID of the user who initiated the request

    Returns:
        dict: Status information about the scraping operation
    """
    from mcp_servers.company_scraper import scrape_company_website
    from .models import ScrapingJob, Company, FailedCompanyDiscovery
    from django.contrib.auth import get_user_model
    from celery.exceptions import SoftTimeLimitExceeded

    # Import the save function from views
    import sys
    import importlib

    logger.info(f"[ASYNC SCRAPE+SAVE] Starting scrape and save task for job {job_id}...")

    try:
        # Get the scraping job
        job = ScrapingJob.objects.get(id=job_id)

        # Check if job is already completed (idempotency)
        if job.status in ['success', 'partial', 'failed', 'cancelled']:
            logger.info(f"[ASYNC SCRAPE+SAVE] Job {job_id} already has status '{job.status}', skipping")
            return {
                'status': 'skipped',
                'job_id': job_id,
                'message': f'Job already completed with status: {job.status}'
            }

        job.status = 'running'
        job.started_at = timezone.now()
        job.save()

        url = job.website_url
        sections = job.sections_to_process
        logger.info(f"[ASYNC SCRAPE+SAVE] Scraping URL: {url}")

        # Get user if provided
        User = get_user_model()
        user = User.objects.filter(id=user_id).first() if user_id else None

        # Run the async scraper
        result = asyncio.run(scrape_company_website(url, sections=sections if sections != ['all'] else None))
        data = result['data']
        errors = result['errors']

        # Import and call the save function
        from core.views import _save_scraped_company_data
        company = _save_scraped_company_data(data, url, update_existing, user)

        if company:
            # Update job with success
            job.company = company
            job.status = 'success'
            job.completed_at = timezone.now()
            job.data_extracted = data
            job.documents_found = len(data.get('documents', []))
            job.people_found = len(data.get('people', []))
            job.news_found = len(data.get('news', []))
            job.sections_completed = sections or ['all']
            job.error_messages = errors
            job.save()

            # Trigger comprehensive news scraping
            # scrape_company_website() has LIMITED news strategies
            # scrape_company_news_task uses crawl_news_releases() with ALL strategies
            scrape_company_news_task.delay(company.id)

            # Run Claude-powered verification to check data completeness
            # This will auto-fix missing descriptions and projects when possible
            verification = {'status': 'skipped', 'message': 'Verification not run'}
            try:
                from core.claude_validator import verify_onboarded_company
                verification = verify_onboarded_company(company.id)
            except Exception as e:
                logger.warning(f"[ASYNC SCRAPE+SAVE] Verification failed for company {company.id}: {e}")
                verification = {'status': 'error', 'message': str(e)}

            logger.info(f"[ASYNC SCRAPE+SAVE] Job {job_id} completed successfully")
            logger.info(f"  - Company: {company.name} (ID: {company.id})")
            logger.info(f"  - Documents: {job.documents_found}")
            logger.info(f"  - People: {job.people_found}")
            logger.info(f"  - News scraping triggered")
            logger.info(f"  - Verification: {verification.get('status', 'unknown')} (score: {verification.get('overall_score', 0)})")
            if verification.get('fixes_applied'):
                logger.info(f"  - Auto-fixes applied: {verification['fixes_applied']}")

            return {
                'status': 'success',
                'job_id': job_id,
                'company_id': company.id,
                'company_name': company.name,
                'documents_found': job.documents_found,
                'people_found': job.people_found,
                'news_found': job.news_found,
                'verification': verification,
                'message': f'Successfully scraped and saved {company.name}'
            }
        else:
            raise Exception("Failed to create company record")

    except ScrapingJob.DoesNotExist:
        logger.info(f"[ASYNC SCRAPE+SAVE] Job {job_id} not found")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': f'ScrapingJob with ID {job_id} not found'
        }

    except SoftTimeLimitExceeded:
        logger.info(f"[ASYNC SCRAPE+SAVE] Job {job_id} timed out")
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = ['Task timed out - exceeded 10 minute limit']
            job.save()
        except Exception as e:
            logger.error(f" Failed to update job {job_id} status on timeout: {e}")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': 'Task timed out',
            'message': 'Scrape and save timed out after 10 minutes'
        }

    except Exception as e:
        logger.exception(f"[ASYNC SCRAPE+SAVE] Job {job_id} failed: {str(e)}")

        # Update job with failure
        fallback_company = None
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = [str(e)]
            job.error_traceback = traceback.format_exc()
            job.save()

            # FALLBACK: If scraping failed but we have a URL, try to create a minimal
            # company and let Claude verification populate it with data.
            # This handles cases where the scraper couldn't extract company name
            # but the website is valid and contains useful information.
            if job.website_url:
                from urllib.parse import urlparse
                from .models import Company

                # Extract a fallback name from the domain (e.g., "libertygold.ca" -> "Libertygold")
                parsed_url = urlparse(job.website_url)
                domain = parsed_url.netloc.replace('www.', '')
                fallback_name = domain.split('.')[0].title()  # "libertygold" -> "Libertygold"

                # Check if company already exists with this URL
                existing = Company.objects.filter(website__icontains=domain).first()
                if existing:
                    logger.info(f"[FALLBACK] Company already exists for {domain}: {existing.name} (ID: {existing.id})")
                    fallback_company = existing
                else:
                    # Create minimal company record - Claude verification will populate it
                    logger.info(f"[FALLBACK] Creating minimal company record for {job.website_url}")
                    fallback_company = Company.objects.create(
                        name=f"{fallback_name} (pending verification)",
                        website=job.website_url,
                        headquarters_country='Canada',  # Default for junior mining
                        description='Company data pending verification - scraped data incomplete.',
                    )
                    logger.info(f"[FALLBACK] Created fallback company: {fallback_company.name} (ID: {fallback_company.id})")

                # Run Claude verification to populate the company with real data
                # This can extract: proper company name, description, projects from website
                if fallback_company:
                    # CRITICAL: Link the job to the fallback company to prevent orphaned jobs
                    job.company = fallback_company
                    job.save(update_fields=['company'])
                    logger.info(f"[FALLBACK] Linked ScrapingJob {job.id} to company {fallback_company.id}")

                    logger.info(f"[FALLBACK] Running Claude verification on company {fallback_company.id}...")
                    from core.claude_validator import verify_onboarded_company
                    verification = verify_onboarded_company(fallback_company.id)
                    logger.info(f"[FALLBACK] Verification result: {verification.get('status', 'unknown')}")
                    if verification.get('fixes_applied'):
                        logger.info(f"[FALLBACK] Auto-fixes applied: {verification['fixes_applied']}")

                    # Also trigger news scraping
                    scrape_company_news_task.delay(fallback_company.id)
                    logger.info(f"[FALLBACK] News scraping triggered for company {fallback_company.id}")
            else:
                # Record failed discovery only if we couldn't create a fallback
                FailedCompanyDiscovery.objects.update_or_create(
                    website_url=job.website_url or 'unknown',
                    defaults={
                        'company_name': job.website_url or 'unknown',
                        'failure_reason': str(e),
                    }
                )
        except Exception as fallback_error:
            logger.exception(f"[FALLBACK] Failed to create fallback company: {fallback_error}")

        # Return appropriate response
        if fallback_company:
            return {
                'status': 'partial_success',
                'job_id': job_id,
                'company_id': fallback_company.id,
                'company_name': fallback_company.name,
                'error': str(e),
                'message': f'Scraping failed but fallback company created. Claude verification will populate data.'
            }

        return {
            'status': 'error',
            'job_id': job_id,
            'error': str(e),
            'message': f'Scrape and save failed: {str(e)}'
        }


# ---------------------------------------------------------------------------
# Bounded retry for transient document-processing failures
# ---------------------------------------------------------------------------

# Checked FIRST. These describe the document or the host, not a bad moment, and
# will fail identically on a retry — so retrying only spends GPU minutes to
# reconfirm the same error. Measured against the 151 historical failures: 52
# were 403s (all but a handful from one host, which needs a User-Agent change
# rather than a retry), 48 were Docling pipeline failures on specific PDFs, 22
# were 404s, and the remainder were unsupported media types or company names
# that could not be resolved.
_TERMINAL_JOB_ERROR = _re.compile(
    r'\b40[0-9]\b'                      # 403, 404, 415 and friends
    r'|Docling|StandardPdfPipeline'     # the PDF itself will not convert
    r'|Unsupported\s+Media'
    r'|No\s+content\s+extracted'
    r"|Company\s+'.*'\s+not\s+found",
    _re.IGNORECASE,
)

# Worth another attempt: the failure was in the moment, not in the document.
_RETRYABLE_JOB_ERROR = _re.compile(
    r'timed?\s*out|timeout'
    r'|ConnectionPool|Connection\s*(?:refused|reset|error|aborted)'
    r'|NameResolution|SSL|Max\s+retries\s+exceeded'
    r'|\b5\d\d\b'                       # 500, 502, 503, 504
    r'|\b429\b|Too\s+Many\s+Requests'   # rate limited: retry later, slowly
    r'|stuck\s+in\s+processing',        # worker crash or restart mid-job
    _re.IGNORECASE,
)

# Rate limiting is retryable, but on a different clock. 41 jobs failed 429
# against a single host within minutes because a bulk requeue had the worker
# downloading from it back to back. 429 matched neither the terminal pattern
# (\b40[0-9]\b stops at 409) nor the retryable one, so those jobs were being
# dropped silently — and retrying them on the ordinary half-hour backoff would
# just reproduce the burst that caused them.
_RATE_LIMITED_ERROR = _re.compile(r'\b429\b|Too\s+Many\s+Requests', _re.IGNORECASE)
RATE_LIMIT_BACKOFF_HOURS = 6

MAX_JOB_RETRIES = 2

# Requeued per cleanup run. The task runs every 15 minutes, and every requeued
# job can wake a GPU droplet, so this keeps a backlog from arriving all at once.
MAX_REQUEUES_PER_RUN = 5

# Minimum wait before retrying, multiplied by the attempt already made. A host
# that just timed out is unlikely to be healthy sixty seconds later.
RETRY_BACKOFF_MINUTES = 30


def _is_retryable_job_error(message: str) -> bool:
    """Transient failures only; terminal patterns win when both appear."""
    if not message:
        return False
    if _TERMINAL_JOB_ERROR.search(message):
        return False
    return bool(_RETRYABLE_JOB_ERROR.search(message))


def requeue_transient_document_failures(now):
    """
    Return failed DocumentProcessingJob rows to 'pending' when the failure looks
    transient and the job has retries left.

    Called from cleanup_stuck_jobs_task, which already runs every 15 minutes.
    Nothing else re-queued these: 151 jobs had failed permanently with no path
    back, 22 of them technical reports that were correctly identified and then
    lost.
    """
    from datetime import timedelta
    from urllib.parse import urlparse

    from .models import DocumentProcessingJob

    candidates = DocumentProcessingJob.objects.filter(
        status='failed',
        retry_count__lt=MAX_JOB_RETRIES,
    ).exclude(error_message='').order_by('-completed_at')

    requeued = 0
    hosts_this_run = set()
    for job in candidates.iterator(chunk_size=200):
        if requeued >= MAX_REQUEUES_PER_RUN:
            break
        if not _is_retryable_job_error(job.error_message):
            continue

        # Back off from the last attempt rather than retrying immediately.
        if _RATE_LIMITED_ERROR.search(job.error_message or ''):
            wait = timedelta(hours=RATE_LIMIT_BACKOFF_HOURS * (job.retry_count + 1))
        else:
            wait = timedelta(minutes=RETRY_BACKOFF_MINUTES * (job.retry_count + 1))
        last_attempt = job.completed_at or job.started_at or job.created_at
        if last_attempt and now - last_attempt < wait:
            continue

        # At most one job per host per run. The 429 burst came from requeuing
        # many documents that all live on the same site, so spacing them across
        # runs stops a retry recreating the condition it is recovering from.
        host = (urlparse(job.url or '').hostname or '').lower()
        if host and host in hosts_this_run:
            continue
        if host:
            hosts_this_run.add(host)

        previous = (job.error_message or '')[:200]
        job.status = 'pending'
        job.retry_count += 1
        job.error_message = ''
        job.progress_message = (
            f'Retry {job.retry_count}/{MAX_JOB_RETRIES} after a transient '
            f'failure: {previous}'
        )
        job.started_at = None
        job.completed_at = None
        job.save(update_fields=[
            'status', 'retry_count', 'error_message', 'progress_message',
            'started_at', 'completed_at',
        ])
        requeued += 1
        logger.info(
            f'[CLEANUP] Requeued DocumentProcessingJob {job.id} '
            f'(attempt {job.retry_count}/{MAX_JOB_RETRIES}): {previous[:80]}'
        )

    return requeued


@shared_task(bind=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def cleanup_stuck_jobs_task(self):
    """
    Periodic task to clean up stuck jobs.
    Runs every 15 minutes to detect and mark as failed any jobs that have been
    stuck in 'running' or 'pending' status for too long.

    A job is considered stuck if:
    - Status is 'running' and started_at is more than 15 minutes ago
    - Status is 'pending' and created_at is more than 30 minutes ago

    This handles cases where:
    - Celery worker crashed during task execution
    - Task was lost due to broker issues
    - Worker was restarted before task completed
    """
    from .models import ScrapingJob, DocumentProcessingJob
    from datetime import timedelta

    logger.info("[CLEANUP] Running stuck jobs cleanup task...")

    now = timezone.now()
    stuck_running_threshold = now - timedelta(minutes=15)
    stuck_pending_threshold = now - timedelta(minutes=30)

    # Cleanup stuck ScrapingJobs - running too long
    stuck_scraping_running = ScrapingJob.objects.filter(
        status='running',
        started_at__lt=stuck_running_threshold
    )

    # Find jobs stuck in pending (never started) for more than 5 minutes
    stuck_pending_threshold_short = now - timedelta(minutes=5)
    stuck_scraping_pending = ScrapingJob.objects.filter(
        status='pending',
        started_at__isnull=True,
        created_at__lt=stuck_pending_threshold_short
    )

    scraping_fixed = 0
    scraping_retried = 0

    # Mark stuck running jobs as failed
    for job in stuck_scraping_running:
        duration = (now - job.started_at).total_seconds() / 60
        logger.info(f"[CLEANUP] Marking stuck ScrapingJob {job.id} as failed (running for {duration:.1f} minutes)")
        job.status = 'failed'
        job.completed_at = now
        job.error_messages = [f'Job stuck in running state for {duration:.1f} minutes. Likely worker crash or restart.']
        job.save()
        scraping_fixed += 1

    # RETRY stuck pending jobs by re-queueing them
    for job in stuck_scraping_pending:
        age_minutes = (now - job.created_at).total_seconds() / 60
        logger.warning(f"[CLEANUP] ScrapingJob {job.id} stuck in pending for {age_minutes:.1f} minutes - retrying...")
        try:
            # Re-queue the task
            from core.tasks import scrape_and_save_company_task
            task = scrape_and_save_company_task.delay(job_id=job.id, update_existing=False)
            logger.info(f"[CLEANUP] Re-queued task {task.id} for ScrapingJob {job.id}")
            scraping_retried += 1
        except Exception as e:
            # If retry fails, mark as failed
            logger.error(f"[CLEANUP] Failed to retry ScrapingJob {job.id}: {e}")
            job.status = 'failed'
            job.completed_at = now
            job.error_messages = [f'Job stuck in pending for {age_minutes:.1f} minutes. Retry failed: {str(e)}']
            job.save()
            scraping_fixed += 1

    # Cleanup stuck DocumentProcessingJobs.
    #
    # These get their own, much longer threshold. GPU document processing is
    # legitimately slow — Docling with OCR runs around 5 seconds per page, so a
    # 300-page NI 43-101 takes roughly half an hour of honest work. The shared
    # 15-minute scraping threshold was killing exactly the largest and most
    # valuable documents mid-conversion and recording them as "Job stuck in
    # processing state... Likely worker crash", which then looked like a worker
    # problem rather than a timeout that was too short.
    document_stuck_threshold = now - timedelta(minutes=90)
    stuck_processing = DocumentProcessingJob.objects.filter(
        status='processing',
        started_at__lt=document_stuck_threshold
    )

    processing_fixed = 0
    for job in stuck_processing:
        duration = (now - job.started_at).total_seconds() / 60
        logger.info(f"[CLEANUP] Marking stuck DocumentProcessingJob {job.id} as failed (processing for {duration:.1f} minutes)")
        job.status = 'failed'
        job.completed_at = now
        job.error_message = f'Job stuck in processing state for {duration:.1f} minutes. Likely worker crash or restart.'
        job.save()
        processing_fixed += 1

    # Give transient document failures another attempt. Nothing else did this,
    # so a timeout or a worker crash meant the document was lost for good.
    documents_requeued = requeue_transient_document_failures(now)

    total_fixed = scraping_fixed + processing_fixed
    logger.info(f"[CLEANUP] Fixed {total_fixed} stuck jobs (ScrapingJobs: {scraping_fixed}, DocumentProcessingJobs: {processing_fixed}), Retried: {scraping_retried}, Documents requeued: {documents_requeued}")

    return {
        'status': 'success',
        'scraping_jobs_fixed': scraping_fixed,
        'scraping_jobs_retried': scraping_retried,
        'processing_jobs_fixed': processing_fixed,
        'documents_requeued': documents_requeued,
        'total_fixed': total_fixed
    }


@shared_task(bind=True, time_limit=120, soft_time_limit=100, on_failure=log_task_failure)
def cleanup_browser_processes_task(self):
    """
    Periodic task to clean up orphaned Chrome/Chromium processes.

    These processes are spawned by crawl4ai/playwright during web scraping.
    If a Celery worker crashes or gets OOM-killed, the browser processes
    can become orphaned and accumulate, consuming memory.

    This task:
    1. Finds Chrome processes older than 10 minutes (should complete within that time)
    2. Kills them gracefully, then forcefully if needed
    3. Cleans up /tmp/playwright* directories

    Runs every 10 minutes to prevent memory accumulation.
    """
    import subprocess
    import os

    logger.info("[BROWSER-CLEANUP] Starting browser process cleanup...")

    killed_count = 0
    errors = []

    try:
        # Find Chrome/Chromium processes older than 10 minutes
        # Using ps with elapsed time (etime) to find old processes
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                # Look for Chrome/Chromium processes
                if 'chrome' in line.lower() or 'chromium' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        try:
                            # Check process age using /proc/<pid>/stat
                            stat_file = f'/proc/{pid}/stat'
                            if os.path.exists(stat_file):
                                # Get process start time
                                with open(stat_file, 'r') as f:
                                    stat = f.read().split()
                                    # Field 22 is starttime (in clock ticks since boot)
                                    if len(stat) > 21:
                                        starttime = int(stat[21])
                                        # Get system uptime
                                        with open('/proc/uptime', 'r') as u:
                                            uptime = float(u.read().split()[0])
                                        # Get clock ticks per second
                                        clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                                        # Calculate process age in seconds
                                        process_age = uptime - (starttime / clk_tck)

                                        # Kill if older than 10 minutes (600 seconds)
                                        if process_age > 600:
                                            logger.info(f"[BROWSER-CLEANUP] Killing old Chrome process {pid} (age: {process_age/60:.1f} min)")
                                            # Try graceful kill first
                                            subprocess.run(['kill', '-15', pid], timeout=5)
                                            # Give it a moment
                                            import time
                                            time.sleep(1)
                                            # Force kill if still running
                                            if os.path.exists(f'/proc/{pid}'):
                                                subprocess.run(['kill', '-9', pid], timeout=5)
                                            killed_count += 1
                        except (ValueError, FileNotFoundError, PermissionError) as e:
                            # Process may have already exited
                            pass
                        except Exception as e:
                            errors.append(f"Error checking process {pid}: {e}")

        # Clean up old playwright temp directories
        import glob
        import shutil
        playwright_dirs = glob.glob('/tmp/playwright_*')
        cleaned_dirs = 0
        for pdir in playwright_dirs:
            try:
                # Check if directory is older than 15 minutes
                dir_age = time.time() - os.path.getmtime(pdir)
                if dir_age > 900:  # 15 minutes
                    shutil.rmtree(pdir, ignore_errors=True)
                    cleaned_dirs += 1
            except Exception as e:
                errors.append(f"Error cleaning {pdir}: {e}")

        logger.info(f"[BROWSER-CLEANUP] Killed {killed_count} old Chrome processes, cleaned {cleaned_dirs} temp dirs")

    except Exception as e:
        logger.error(f"[BROWSER-CLEANUP] Error during cleanup: {e}")
        errors.append(str(e))

    return {
        'status': 'success',
        'killed_processes': killed_count,
        'errors': errors[:5] if errors else []  # Limit errors in response
    }


@shared_task(bind=True, time_limit=60, soft_time_limit=50, on_failure=log_task_failure)
def celery_worker_health_check_task(self):
    """
    Periodic health check task that verifies Celery workers are responsive.

    This task simply runs and returns success. If Celery workers are frozen
    or unresponsive, this task will timeout and the failure will be logged.

    Additionally, it logs memory usage to help detect memory pressure issues
    before they cause OOM kills.
    """
    import subprocess

    logger.info("[HEALTH-CHECK] Celery worker health check running...")

    health_data = {
        'status': 'healthy',
        'worker_id': self.request.id,
        'timestamp': timezone.now().isoformat()
    }

    try:
        # Check memory usage
        result = subprocess.run(
            ['free', '-m'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    if len(parts) >= 3:
                        total_mb = int(parts[1])
                        used_mb = int(parts[2])
                        free_mb = int(parts[3]) if len(parts) > 3 else 0
                        health_data['memory'] = {
                            'total_mb': total_mb,
                            'used_mb': used_mb,
                            'free_mb': free_mb,
                            'percent_used': round(used_mb / total_mb * 100, 1)
                        }

                        # Warn if memory is critically low (< 500MB free)
                        if free_mb < 500:
                            logger.warning(f"[HEALTH-CHECK] LOW MEMORY WARNING: Only {free_mb}MB free!")
                            health_data['status'] = 'warning'
                            health_data['warning'] = f'Low memory: {free_mb}MB free'

        # Count Chrome processes
        result = subprocess.run(
            ['bash', '-c', 'ps aux | grep -c "[c]hrome"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            chrome_count = int(result.stdout.strip())
            health_data['chrome_processes'] = chrome_count

            # Warn if too many Chrome processes (> 30)
            if chrome_count > 30:
                logger.warning(f"[HEALTH-CHECK] HIGH CHROME COUNT: {chrome_count} processes!")
                health_data['status'] = 'warning'
                health_data['warning'] = f'High Chrome count: {chrome_count}'

    except Exception as e:
        logger.error(f"[HEALTH-CHECK] Error collecting health data: {e}")
        health_data['error'] = str(e)

    logger.info(f"[HEALTH-CHECK] Health check complete: {health_data.get('status')}")
    return health_data


@shared_task(bind=True, max_retries=2, retry_backoff=True, retry_backoff_max=300, retry_jitter=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def process_company_news_for_rag_task(self, company_id: int, limit: int = 20):
    """
    Background Celery task to process a company's news into the RAG knowledge base.

    This task:
    1. Fetches full content from news URLs
    2. Chunks the text into manageable pieces
    3. Generates embeddings using Voyage AI
    4. Stores chunks in PostgreSQL (NewsChunk) and ChromaDB

    SIGSEGV-SAFE: Uses subprocess isolation to protect against ChromaDB Rust binding crashes.

    Args:
        company_id: ID of the Company to process news for
        limit: Maximum number of news items to process (default 20)

    Returns:
        dict: Processing result with counts
    """
    from .models import Company, NewsChunk
    from core.chromadb_isolated import process_company_news_isolated

    logger.info(f"[RAG TASK] Starting news processing for company {company_id}...")

    try:
        company = Company.objects.get(id=company_id)

        # Check if already has chunks (avoid reprocessing)
        existing_chunks = NewsChunk.objects.filter(company=company).count()
        if existing_chunks > 0:
            logger.info(f"[RAG TASK] Company {company.name} already has {existing_chunks} chunks, skipping")
            return {
                'status': 'skipped',
                'company': company.name,
                'existing_chunks': existing_chunks,
                'message': 'Company already has news chunks processed'
            }

        # Process news using subprocess isolation (protects against SIGSEGV crashes)
        result = process_company_news_isolated(
            company_name=company.name,
            company_id=company.id,
            limit=limit,
            timeout=180  # 3 minute timeout
        )

        if result.get('success'):
            inner_result = result.get('result', {})
            logger.info(f"[RAG TASK] Processed {inner_result.get('news_items_processed', 0)} news items, "
                  f"created {inner_result.get('chunks_created', 0)} chunks for {company.name}")
            return {
                'status': 'success',
                'company': company.name,
                'news_items_processed': inner_result.get('news_items_processed', 0),
                'chunks_created': inner_result.get('chunks_created', 0),
                'errors': inner_result.get('errors')
            }
        elif result.get('crash'):
            # Subprocess crashed (SIGSEGV) but we survived
            logger.warning(f"[RAG TASK] ChromaDB subprocess crashed for {company.name}: {result.get('error')}")
            return {
                'status': 'crash',
                'company': company.name,
                'error': result.get('error', 'Subprocess crashed'),
                'message': 'ChromaDB subprocess crashed (SIGSEGV), worker survived'
            }
        elif result.get('timeout'):
            logger.warning(f"[RAG TASK] Processing timed out for {company.name}")
            return {
                'status': 'timeout',
                'company': company.name,
                'error': 'Processing timed out'
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"[RAG TASK] Processing failed for {company.name}: {error_msg}")
            return {
                'status': 'error',
                'company': company.name,
                'error': error_msg
            }

    except Company.DoesNotExist:
        logger.info(f"[RAG TASK] Company {company_id} not found")
        return {
            'status': 'error',
            'company_id': company_id,
            'error': f'Company with ID {company_id} not found'
        }

    except Exception as e:
        logger.exception(f"[RAG TASK] Error processing company {company_id}: {str(e)}")

        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'company_id': company_id,
                'error': str(e),
                'message': 'RAG processing failed after retries'
            }



def embed_industry_articles(limit=300):
    """
    Embed industry news headlines (NewsArticle) into news_chunks.

    These are trade-press articles from outside publishers, so their bodies
    are not fetched — the headline is embedded, with source, url and date in
    the metadata. That is enough for semantic "what is happening in the
    sector" retrieval, costs no crawling of third-party sites, and closes the
    last scraped dataset with no vectors: 1,961 articles, zero embedded.

    Postgres rows are written first; if the ChromaDB add then fails, the
    hourly reconcile_chroma_index_task re-embeds exactly the chunks Postgres
    has and Chroma lacks, so nothing is lost either way.
    """
    from .models import NewsArticle, NewsChunk

    pending = list(
        NewsArticle.objects.filter(is_visible=True)
        .exclude(id__in=NewsChunk.objects.filter(news_article__isnull=False)
                 .values('news_article_id'))
        .select_related('source')
        .order_by('-published_at')[:limit]
    )
    if not pending:
        return {'embedded': 0, 'skipped': 0}

    rows, ids, docs, metas = [], [], [], []
    skipped = 0
    for a in pending:
        text = (a.title or '').strip()
        if len(text) < 15:
            skipped += 1
            continue
        chroma_id = f"news_article_{a.id}_chunk_0"
        rows.append(NewsChunk(
            company=None, news_article=a, content_type='news_article',
            chunk_index=0, text=text, token_count=max(1, len(text) // 4),
            chroma_id=chroma_id, source_title=text[:500],
            source_url=a.url or '',
            source_date=a.published_at.date() if a.published_at else None,
        ))
        ids.append(chroma_id)
        docs.append(text)
        metas.append({
            'chunk_index': 0,
            'company_id': 0,          # Chroma rejects None; 0 matches no company
            'company': '',
            'source_id': a.id,
            'content_type': 'news_article',
            'title': text[:100],
            'url': a.url or '',
            'date': str(a.published_at.date()) if a.published_at else '',
        })

    NewsChunk.objects.bulk_create(rows, ignore_conflicts=True)

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        from mcp_servers.embeddings import get_embedding_function

        client = chromadb.HttpClient(
            host=os.environ.get('CHROMA_HOST', 'localhost'),
            port=int(os.environ.get('CHROMA_PORT', 8002)),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = client.get_or_create_collection(
            name='news_chunks', metadata={'hnsw:space': 'cosine'},
            embedding_function=get_embedding_function(),
        )
        for start in range(0, len(ids), 200):
            collection.add(ids=ids[start:start + 200],
                           documents=docs[start:start + 200],
                           metadatas=metas[start:start + 200])
    except Exception:
        logger.exception(
            "Industry-article embed: Postgres rows written but the ChromaDB "
            "add failed for %d article(s); reconcile_chroma_index_task will "
            "repair them.", len(ids))

    logger.info("[NEWS RAG] industry articles embedded: %d (skipped %d)",
                len(rows), skipped)
    return {'embedded': len(rows), 'skipped': skipped}



@shared_task(bind=True, time_limit=3600, soft_time_limit=3540, on_failure=log_task_failure)
def embed_recent_news_for_rag_task(self, days: int = 7, max_companies: int = 40,
                                   limit_per_company: int = 10, dry_run: bool = False):
    """
    Embed recently published news that has no vectors yet.

    Nothing was keeping the news_chunks collection current. The only writer,
    process_company_news_for_rag_task, is called from the onboard_company
    command alone, and it returns early if the company has ANY chunk at all —
    so the 84 companies that were embedded once at onboarding never gained
    another vector, and the other 312 never gained a first one. Coverage sat
    at 8% of NewsRelease with nothing added since 2026-01-29.

    This runs item-wise instead: it looks only at companies whose recent news
    is missing chunks, and leans on _process_company_news, which already skips
    individual items that have them.

    Deliberately bounded. Neither NewsRelease.full_text nor CompanyNews.content
    is ever populated by the scrapers, so embedding an item means fetching its
    article — roughly 9 seconds each. A day's new releases is about 20 items,
    a couple of minutes; the full historical backlog is 30,000 items and some
    38 hours of crawling, which belongs in a supervised command, not a beat
    schedule. `max_companies` is the ceiling that keeps a quiet day cheap and
    a surprise flood from turning into an all-night crawl.

    Args:
        days: how far back to consider news
        max_companies: most companies to touch in one run
        limit_per_company: most news items to look at per company
        dry_run: report what would be processed, embed nothing
    """
    from datetime import timedelta

    from .models import Company, CompanyNews, NewsChunk, NewsRelease
    from core.chromadb_isolated import process_company_news_isolated

    cutoff = timezone.localtime().date() - timedelta(days=days)

    embedded_nr = NewsChunk.objects.filter(
        news_release__isnull=False).values('news_release_id')
    embedded_cn = NewsChunk.objects.filter(
        company_news__isnull=False).values('company_news_id')

    # Companies with recent news that has no vectors.
    pending = set(
        NewsRelease.objects
        .filter(release_date__gte=cutoff)
        .exclude(id__in=embedded_nr)
        .values_list('company_id', flat=True)
    ) | set(
        CompanyNews.objects
        .filter(publication_date__gte=cutoff)
        .exclude(id__in=embedded_cn)
        .values_list('company_id', flat=True)
    )

    # Shuffled, not sorted. With pending above the cap, a stable order means
    # the same low-id companies claim the slots every night — a company whose
    # links are dead re-fails daily while high-id companies never get a first
    # attempt until its items age out of the window. Random order spreads the
    # cap fairly across nights.
    import random
    pending_list = list(pending)
    random.shuffle(pending_list)
    company_ids = pending_list[:max_companies]
    logger.info(
        "[NEWS RAG] %d companies have unembedded news since %s; processing %d "
        "(cap %d)%s",
        len(pending), cutoff, len(company_ids), max_companies,
        " [DRY RUN]" if dry_run else "",
    )

    if dry_run:
        names = list(
            Company.objects.filter(id__in=company_ids)
            .values_list('name', flat=True)[:20]
        )
        return {
            'status': 'dry_run',
            'companies_pending': len(pending),
            'would_process': len(company_ids),
            'sample': names,
        }

    processed = chunks = failed = 0
    for company_id in company_ids:
        company = Company.objects.filter(id=company_id).first()
        if not company:
            continue
        try:
            result = process_company_news_isolated(
                company_name=company.name,
                company_id=company.id,
                limit=limit_per_company,
                timeout=180,
            )
        except Exception as exc:
            failed += 1
            logger.warning("[NEWS RAG] %s raised: %s", company.name, exc)
            continue

        if result.get('success'):
            inner = result.get('result', {})
            processed += inner.get('news_items_processed', 0)
            chunks += inner.get('chunks_created', 0)
        else:
            # A SIGSEGV in the Chroma binding is why this runs in a subprocess
            # at all; one bad company must not end the run.
            failed += 1
            logger.warning(
                "[NEWS RAG] %s failed: %s", company.name,
                result.get('error', 'unknown'),
            )

    # Industry headlines ride along: no fetching, a handful a day.
    industry = embed_industry_articles(limit=300)

    logger.info(
        "[NEWS RAG] done — %d companies, %d items embedded, %d chunks, %d failed",
        len(company_ids), processed, chunks, failed,
    )
    return {
        'status': 'success',
        'companies_pending': len(pending),
        'companies_processed': len(company_ids),
        'news_items_embedded': processed,
        'chunks_created': chunks,
        'failed': failed,
        'industry_articles': industry,
    }


@shared_task(bind=True, time_limit=600, soft_time_limit=580, on_failure=log_task_failure)
def store_company_profile_in_rag_task(self, company_id: int):
    """
    Background task to store a company's profile in the RAG knowledge base.

    Stores company overview, description, tagline, stock info, and project summaries
    in ChromaDB for semantic search.

    SIGSEGV-SAFE: Uses subprocess isolation to protect against ChromaDB Rust binding crashes.

    Args:
        company_id: ID of the Company to store profile for

    Returns:
        dict: Storage result
    """
    from core.chromadb_isolated import store_company_profile_isolated

    logger.info(f"[RAG TASK] Storing profile for company {company_id} (subprocess-isolated)...")

    try:
        result = store_company_profile_isolated(company_id=company_id, timeout=120)

        if result.get('success'):
            inner_result = result.get('result', {})
            if inner_result.get('status') == 'skipped':
                return inner_result
            logger.info(f"[RAG TASK] Stored {inner_result.get('chars_stored', 0)} chars of profile for {inner_result.get('company', 'unknown')}")
            return inner_result
        elif result.get('crash'):
            logger.warning(f"[RAG TASK] ChromaDB subprocess crashed for company {company_id}: {result.get('error')}")
            return {
                'status': 'crash',
                'company_id': company_id,
                'error': result.get('error', 'Subprocess crashed'),
                'message': 'ChromaDB subprocess crashed (SIGSEGV), worker survived'
            }
        elif result.get('timeout'):
            logger.warning(f"[RAG TASK] Profile storage timed out for company {company_id}")
            return {
                'status': 'timeout',
                'company_id': company_id,
                'error': 'Processing timed out'
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"[RAG TASK] Profile storage failed for company {company_id}: {error_msg}")
            return {'status': 'error', 'error': error_msg}

    except Exception as e:
        logger.error(f"[RAG TASK] Error storing profile for {company_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def send_weekly_briefings_task():
    """
    Email the weekly watchlist briefing to every opted-in user (runs Mondays).
    Skips users whose watchlist is empty.
    """
    from core.models import User
    from core.views.dashboard import build_briefing, briefing_email_token
    from core.email_service import EmailService

    users = User.objects.filter(
        email_briefing_enabled=True, is_active=True,
    ).exclude(email='')

    sent = skipped = failed = 0
    for user in users:
        try:
            briefing = build_briefing(user)
            if not briefing.get('has_watchlist'):
                skipped += 1
                continue
            token = briefing_email_token(user)
            unsubscribe_url = (
                'https://juniorminingintelligence.com'
                f'/api/briefing-email/unsubscribe/?token={token}'
            )
            if EmailService.send_weekly_briefing(user, briefing, unsubscribe_url):
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Weekly briefing failed for user {user.id}: {str(e)}")
            failed += 1

    logger.info(
        f"Weekly briefings: sent={sent} skipped={skipped} failed={failed}"
    )
    return {'sent': sent, 'skipped': skipped, 'failed': failed}


# =============================================================================
# Weekly industry report (Friday 5:30 PM ET, after fetch_stock_prices_task)
# =============================================================================

def _most_recent_friday(today=None):
    """Return today if today is Friday, else the previous Friday."""
    from datetime import date, timedelta
    d = today or timezone.localtime().date()
    # weekday(): Mon=0 ... Fri=4 ... Sun=6
    return d - timedelta(days=(d.weekday() - 4) % 7)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def generate_weekly_industry_report_task(self, week_ending: str = None):
    """
    Build the Friday weekly industry report. Idempotent on (week_ending):
    re-running for the same week overwrites the existing row.

    Args:
        week_ending: Optional 'YYYY-MM-DD'. Defaults to the most recent
            Friday in local time (so the scheduled 5:30 PM ET run picks up
            today's date when running on a Friday).
    """
    from datetime import date as date_cls
    from django.core.files.base import ContentFile

    from core.models import User, WeeklyIndustryReport
    from core.reports.weekly_industry import collect_weekly_data
    from core.reports.scoring import annotate
    from core.reports.narrative import attach_narrative
    from core.reports.render import render_report
    from core.email_service import EmailService

    if week_ending:
        wk = date_cls.fromisoformat(week_ending)
    else:
        wk = _most_recent_friday()

    started = timezone.now()

    report, _ = WeeklyIndustryReport.objects.update_or_create(
        week_ending=wk,
        defaults={'status': 'generating', 'generated_at': started, 'error_message': ''},
    )

    try:
        data = collect_weekly_data(wk)
        data = annotate(data)
        data = attach_narrative(data)

        html, pdf_bytes = render_report(data)

        report.html = html
        report.data_snapshot = data
        report.executive_summary = (data.get('narrative') or {}).get('executive_summary', '')

        if pdf_bytes:
            report.pdf_file.save(
                f'weekly-{wk.isoformat()}.pdf',
                ContentFile(pdf_bytes),
                save=False,
            )

        report.status = 'completed'
        report.generation_duration_seconds = int((timezone.now() - started).total_seconds())
        report.save()

    except Exception as exc:
        logger.exception("Weekly industry report generation failed for %s", wk)
        report.status = 'failed'
        report.error_message = f"{type(exc).__name__}: {exc}"
        report.generation_duration_seconds = int((timezone.now() - started).total_seconds())
        report.save()
        raise self.retry(exc=exc)

    # Email opted-in recipients
    public_url = f"https://juniorminingintelligence.com/api/reports/weekly/{wk.isoformat()}/"
    sent = failed = 0
    for user in User.objects.filter(
        email_weekly_industry_report_enabled=True, is_active=True,
    ).exclude(email=''):
        try:
            if EmailService.send_weekly_industry_report(user, report, public_url):
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Weekly industry report email failed for user {user.id}: {e}")
            failed += 1

    logger.info(
        f"Weekly industry report week_ending={wk.isoformat()} "
        f"status={report.status} duration={report.generation_duration_seconds}s "
        f"emails_sent={sent} emails_failed={failed}"
    )
    return {
        'week_ending': wk.isoformat(),
        'status': report.status,
        'duration_seconds': report.generation_duration_seconds,
        'emails_sent': sent,
        'emails_failed': failed,
    }


# =============================================================================
# CHROMADB / POSTGRESQL INDEX RECONCILIATION
# =============================================================================

@shared_task(bind=True, time_limit=900, soft_time_limit=840, on_failure=log_task_failure)
def backfill_document_dates_task(self):
    """Date documents the GPU worker ingested without one.

    The GPU worker inserts document_date NULL because it has no publication
    date at insert time, and stamping today's date made every document look
    simultaneous — which collapsed Resource Growth's timeline and left Grade
    Ranker unable to tell which estimate superseded which. The text lands in
    Postgres a moment later, so the date is recovered here rather than guessed
    there.

    A no-op when nothing is undated.
    """
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    call_command('backfill_document_dates', stdout=out)
    summary = next((ln for ln in out.getvalue().splitlines() if 'recovered' in ln), '')
    logger.info("backfill_document_dates: %s", summary or 'nothing to do')
    return summary


@shared_task(bind=True, time_limit=1800, soft_time_limit=1740, on_failure=log_task_failure)
def reconcile_chroma_index_task(self, repair_limit=2000):
    """
    Detect and heal drift between PostgreSQL chunk rows and the ChromaDB index.

    `RAGManager.store_document_chunks` commits DocumentChunk rows (chroma_id
    included) before embedding them, and the two steps share no transaction. A
    Voyage timeout therefore leaves Postgres asserting an index entry that was
    never written. That went unnoticed until the index had drifted to 3,147
    vectors against 32,228 rows — roughly 90% of the technical corpus silently
    unsearchable, with no error anywhere.

    This task closes that loop. Small drift is repaired in place so it never
    accumulates; drift larger than `repair_limit` is left alone and logged at
    ERROR, because a large gap means something systemic broke and re-embedding
    tens of thousands of chunks unattended would burn API budget without
    addressing the cause. Run `manage.py reindex_chroma` for that.

    Args:
        repair_limit: Maximum chunks to re-embed per collection per run.
                      0 disables repair (report only).
    """
    from .models import DocumentChunk, NewsChunk

    logger.info("[CHROMA-RECONCILE] Starting index reconciliation...")

    try:
        from mcp_servers.rag_utils import RAGManager
        rag = RAGManager()
    except Exception as exc:
        logger.error(f"[CHROMA-RECONCILE] Could not open ChromaDB: {exc}")
        return {'success': False, 'error': str(exc)}

    collections = [
        ('document_chunks', rag.collection, DocumentChunk),
        ('news_chunks', rag.news_collection, NewsChunk),
    ]

    report = {}
    healthy = True

    for name, collection, model in collections:
        pg_count = model.objects.exclude(chroma_id__isnull=True).exclude(chroma_id='').count()

        try:
            chroma_count = collection.count()
        except Exception as exc:
            # A count that aborts means a corrupt segment — that is how the
            # news_chunks collection failed, and it takes the worker with it.
            logger.error(
                f"[CHROMA-RECONCILE] {name}: count() failed ({exc}). "
                f"Segment may be corrupt — rebuild with "
                f"`manage.py reindex_chroma --collection {name} --rebuild`."
            )
            report[name] = {'postgres': pg_count, 'chroma': None, 'error': str(exc)}
            healthy = False
            continue

        drift = pg_count - chroma_count
        entry = {'postgres': pg_count, 'chroma': chroma_count, 'drift': drift, 'repaired': 0}

        if drift <= 0:
            logger.info(f"[CHROMA-RECONCILE] {name}: in sync ({pg_count:,})")
            report[name] = entry
            continue

        healthy = False
        pct = (drift / pg_count * 100) if pg_count else 0
        logger.warning(
            f"[CHROMA-RECONCILE] {name}: {drift:,} chunks missing "
            f"({pct:.1f}% of {pg_count:,})"
        )

        if not repair_limit:
            report[name] = entry
            continue

        if drift > repair_limit:
            logger.error(
                f"[CHROMA-RECONCILE] {name}: drift of {drift:,} exceeds the "
                f"{repair_limit:,}-chunk repair limit — not auto-repairing. "
                f"Investigate, then run `manage.py reindex_chroma`."
            )
            report[name] = entry
            continue

        entry['repaired'] = _repair_chroma_gap(name, collection, repair_limit)
        entry['drift_after'] = pg_count - entry['repaired'] - chroma_count
        report[name] = entry

    logger.info(f"[CHROMA-RECONCILE] Done. healthy={healthy} report={report}")
    return {'success': True, 'healthy': healthy, 'collections': report}


def _repair_chroma_gap(name, collection, limit):
    """
    Re-embed chunks Postgres claims are indexed but ChromaDB does not hold.

    Returns the number of vectors actually added, measured from the collection
    itself rather than trusting the command's own tally.
    """
    from django.core.management import call_command
    from io import StringIO

    try:
        before = collection.count()
    except Exception as exc:
        logger.error(f"[CHROMA-RECONCILE] {name}: cannot count before repair: {exc}")
        return 0

    out = StringIO()
    try:
        call_command(
            'reindex_chroma',
            collection=('documents' if name == 'document_chunks' else 'news'),
            limit=limit,
            batch_size=128,
            stdout=out,
            stderr=out,
        )
    except Exception as exc:
        logger.error(f"[CHROMA-RECONCILE] {name}: repair failed: {exc}")
        return 0

    try:
        added = max(0, collection.count() - before)
    except Exception:
        added = 0

    logger.info(f"[CHROMA-RECONCILE] {name}: re-embedded {added:,} chunks")
    return added


@shared_task
def notify_expiring_comp_grants_task(days_ahead: int = 5):
    """Warn early-access comp-grant holders before their access lapses.

    Comp grants carry no Stripe subscription, so nothing external tells the
    holder they are about to drop back to Explorer - PlatformSubscription
    .is_active simply starts returning False once the expiry passes. Without
    this, the first signal a user gets is the product quietly doing less.

    Runs daily. Each subscription is warned once, tracked by
    expiry_notice_sent_at, so a longer window or a re-run can't double-send.
    """
    from django.conf import settings
    from datetime import timedelta

    from .email_service import EmailService
    from .models import PlatformSubscription

    now = timezone.now()
    cutoff = now + timedelta(days=days_ahead)

    candidates = PlatformSubscription.objects.select_related('user').filter(
        stripe_subscription_id='',      # comp grants only
        expiry_notice_sent_at__isnull=True,
        tier__in=('prospector', 'miner'),
    )

    promo_code = getattr(settings, 'STRIPE_LAUNCH_PROMO_CODE', '') or None

    sent = skipped = failed = 0
    for sub in candidates:
        expiry = sub.trial_end or sub.current_period_end
        # No expiry means the grant never lapses, so there is nothing to warn about.
        if expiry is None or expiry > cutoff:
            skipped += 1
            continue
        if not sub.is_active:
            # Already lapsed - a warning now would be worse than none.
            skipped += 1
            continue

        # Round up, don't truncate: timedelta.days on 2.9 days gives 2, and the
        # email would tell someone with nearly three days left that they have two.
        import math
        days_left = max(0, math.ceil((expiry - now).total_seconds() / 86400))
        ok = EmailService.send_grant_expiry_notice(
            sub.user, sub, days_left, promo_code=promo_code
        )
        if ok:
            sub.expiry_notice_sent_at = now
            sub.save(update_fields=['expiry_notice_sent_at', 'updated_at'])
            sent += 1
        else:
            failed += 1

    logger.info(
        f"[GRANT-EXPIRY] sent={sent} skipped={skipped} failed={failed} "
        f"(window: {days_ahead}d)"
    )
    return {'sent': sent, 'skipped': skipped, 'failed': failed}


@shared_task(bind=True, max_retries=3, retry_backoff=True, time_limit=120,
             soft_time_limit=110, on_failure=log_task_failure)
def notify_editor_question_task(self, thread_id: int, message_id: int):
    """Email the editor about a new "Ask the Editor" question.

    Dispatched from EditorChatConsumer, which runs in the ASGI event loop -
    send_mail is a blocking SMTP round trip and must not happen there.

    Throttled to one email per thread per 15 minutes: someone typing four
    short messages in a row is one question, not four, and the inbox link is
    the same either way. The key is claimed BEFORE the send so a retry storm
    can't multiply the mail - but it is released again on failure, because a
    throttle that outlives a failed send silently eats the retry, and the
    question the editor never hears about is the whole point of the feature.

    Retries on failure. send_editor_question_notification swallows its own
    exceptions and returns False, so the bool is the only failure signal
    there is; without this, one bad send lost the alert permanently. That is
    exactly what happened to the first two questions on 2026-08-27, when a
    memory-starved box pushed the SMTP call past the soft time limit.
    """
    from celery.exceptions import SoftTimeLimitExceeded
    from .models import EditorQuestionThread, EditorQuestionMessage
    from .notifications import send_editor_question_notification

    throttle_key = f'editor_question_notified:{thread_id}'
    if cache.get(throttle_key):
        logger.info(f"[ASK-EDITOR] alert for thread {thread_id} throttled")
        return {'sent': False, 'reason': 'throttled'}
    cache.set(throttle_key, 1, 15 * 60)

    try:
        thread = EditorQuestionThread.objects.select_related('user').get(id=thread_id)
        message = EditorQuestionMessage.objects.get(id=message_id)
    except (EditorQuestionThread.DoesNotExist, EditorQuestionMessage.DoesNotExist):
        logger.warning(f"[ASK-EDITOR] thread {thread_id} / message {message_id} vanished")
        return {'sent': False, 'reason': 'missing'}

    try:
        sent = send_editor_question_notification(thread, message)
    except SoftTimeLimitExceeded:
        # The send outlived the task. Release the claim so the retry is not
        # throttled out, then let it propagate - re-raising inside the
        # handler is what stops this being swallowed as a silent success.
        cache.delete(throttle_key)
        logger.error(f"[ASK-EDITOR] alert for thread {thread_id} hit the soft time limit")
        raise

    if not sent:
        cache.delete(throttle_key)
        logger.warning(
            f"[ASK-EDITOR] alert for thread {thread_id} failed; "
            f"retry {self.request.retries + 1}/{self.max_retries}"
        )
        raise self.retry(
            exc=RuntimeError(f'editor alert send failed for thread {thread_id}'),
            countdown=30 * (2 ** self.request.retries),
        )

    return {'sent': True}


# Seconds to wait before re-testing a failed credential check. Well inside the
# task's 280s soft limit even if every check fails and is retried.
CREDENTIAL_RECHECK_DELAY = 20

@shared_task(bind=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def check_credentials_task(self, notify=True):
    """
    Weekly liveness check of every external credential, emailing on failure.

    These credentials all fail silently -- an expired DigitalOcean token stops
    GPU document processing with nothing but 401s in a log, a dead Anthropic key
    drops paying subscribers to the templated briefing because
    _generate_ai_briefing() swallows every exception, and a revoked SendGrid key
    still passes is_configured(), which only inspects the 'SG.' prefix. Without
    this, the first sign of a dead credential is a user noticing something is
    missing, or nobody noticing at all.

    See core/credential_checks.py for what each check does and why.
    """
    import time
    from core.credential_checks import run_checks, send_alert, format_report

    results = run_checks()
    failed = [r for r in results if r.failed]

    if failed:
        # Re-test ONLY what failed, once, after a pause. A weekly alert that
        # cries wolf over a transient DNS hiccup or a provider's 30-second blip
        # gets ignored, and an ignored alert is worse than no alert at all. A
        # credential that is genuinely dead fails both times; a network blip
        # does not. The names in `only` match CheckResult.name for every check.
        time.sleep(CREDENTIAL_RECHECK_DELAY)
        retried = {r.name: r for r in run_checks(only={r.name for r in failed})}
        recovered = sorted(n for n, r in retried.items() if not r.failed)
        if recovered:
            logger.warning('Credential checks recovered on retry, treating as transient: %s', ', '.join(recovered))
        results = [retried.get(r.name, r) for r in results]
        failed = [r for r in results if r.failed]

    # send_alert() builds its own subject; only the body is logged here.
    _, body = format_report(results)

    if failed:
        logger.error('Credential checks: %d FAILING\n%s', len(failed), body)
        if notify:
            send_alert(results)
    else:
        logger.info('Credential checks: all clear\n%s', body)

    return {
        'checked': len(results),
        'failed': len(failed),
        'failures': [{'name': r.name, 'detail': r.detail} for r in failed],
        'results': {r.name: r.status for r in results},
    }


@shared_task(bind=True, time_limit=3600, soft_time_limit=3480, on_failure=log_task_failure)
def hunt_technical_reports_task(self, flag_ids=None, max_companies=None, dry_run=False,
                                chain_discovery_limit=None):
    """
    Find the technical report each pending NewsReportFlag refers to.

    A flag marks a news release whose title mentions a report; the report itself
    is a separate document on the company's website. This task derives what to
    look for, searches the release page and then the company's technical and
    project pages, ranks candidates, and either queues the best one to the GPU
    or leaves a ranked shortlist for review.

    Work is batched by company: 218 pending flags belong to 113 companies, so
    per-flag crawling would fetch the same sites twice over. Flags whose title
    implies no document (drill results, corporate actions, forward-looking
    statements) are filtered out before any browser starts.
    """
    from datetime import timedelta

    from core.models import NewsReportFlag, DocumentProcessingJob, Project
    from core.security_utils import is_safe_url
    from mcp_servers.report_hunter import (
        AUTO_QUEUE_THRESHOLD,
        FILING_GRACE_DAYS,
        FILING_WINDOW_DAYS,
        HUNTABLE_CATEGORIES,
        HUNT_BACKOFF_DAYS,
        MAX_HUNT_ATTEMPTS,
        build_target,
        is_auto_queueable,
        gather_company_candidates,
        rank_candidates,
    )

    now = timezone.now()
    today = now.date()

    HUNT_STATE_FIELDS = [
        'document_category', 'project_name', 'hunt_status',
        'next_hunt_at', 'expected_filing_by',
    ]

    qs = NewsReportFlag.objects.filter(status='pending').select_related(
        'news_release__company'
    )
    if flag_ids:
        qs = qs.filter(id__in=flag_ids)
    else:
        # Never searched, or the backoff has elapsed.
        qs = qs.filter(
            Q(next_hunt_at__isnull=True) | Q(next_hunt_at__lte=now)
        ).exclude(hunt_status__in=['auto_queued', 'exhausted', 'not_expected'])

    stats = {
        'considered': 0, 'skipped_no_document': 0, 'companies_crawled': 0,
        'flags_hunted': 0, 'candidates_found': 0, 'auto_queued': 0,
        'awaiting_review': 0, 'not_found': 0, 'exhausted': 0,
    }

    # Triage first, so a company whose flags all lack a document never gets
    # crawled at all.
    by_company = {}
    # Project names for every company involved, in one query rather than one
    # per flag. Flags cluster heavily by company — 218 of them across 113
    # companies — so the per-flag lookup repeated the same query about twice
    # over for no benefit.
    flags = list(qs)
    projects_by_company = {}
    company_ids = {f.news_release.company_id for f in flags}
    if company_ids:
        for cid, pname in Project.objects.filter(
                company_id__in=company_ids).values_list('company_id', 'name'):
            names = projects_by_company.setdefault(cid, [])
            if len(names) < 40:  # same per-company cap as before
                names.append(pname)

    for flag in flags:
        stats['considered'] += 1
        company = flag.news_release.company
        project_names = projects_by_company.get(company.id, [])
        target = build_target(flag, project_names)

        flag.document_category = target.category
        flag.project_name = target.project

        if flag.news_release.release_date:
            flag.expected_filing_by = (
                flag.news_release.release_date
                + timedelta(days=FILING_WINDOW_DAYS + FILING_GRACE_DAYS)
            )

        if target.category not in HUNTABLE_CATEGORIES:
            flag.hunt_status = 'not_expected'
            flag.next_hunt_at = None
            stats['skipped_no_document'] += 1
            if not dry_run:
                flag.save(update_fields=HUNT_STATE_FIELDS)
            continue

        # Give up once the filing window plus grace has passed with nothing
        # found. Continuing to crawl costs browser time for a report that was
        # either never filed or is not on the site.
        window_closed = (
            flag.expected_filing_by
            and today > flag.expected_filing_by
            and flag.hunt_attempts > 0
        )
        if window_closed or flag.hunt_attempts >= MAX_HUNT_ATTEMPTS:
            flag.hunt_status = 'exhausted'
            flag.next_hunt_at = None
            stats['exhausted'] += 1
            if not dry_run:
                flag.save(update_fields=HUNT_STATE_FIELDS)
            continue

        by_company.setdefault(company.id, {'company': company, 'items': []})
        by_company[company.id]['items'].append((flag, target))

    if max_companies:
        by_company = dict(list(by_company.items())[:max_companies])

    logger.info(
        f"[HUNT] {stats['considered']} flag(s) considered, "
        f"{stats['skipped_no_document']} skipped as no-document, "
        f"{stats['exhausted']} exhausted, "
        f"{len(by_company)} company site(s) to crawl"
    )

    if dry_run:
        logger.info("[HUNT] Dry run - no crawling, no writes.")
        stats['companies_to_crawl'] = len(by_company)
        return stats

    valid_report_types = {c[0] for c in NewsReportFlag.REPORT_TYPE_CHOICES}

    # Documents a superuser already rejected from the queue. Cancelling a job
    # returns its flag to review, so without this the next hunt would rank the
    # same top candidate, auto-queue it again, and the reviewer would cancel it
    # again — an endless loop that spends GPU time on every pass. A rejected URL
    # can still be picked by hand; it just never auto-queues.
    rejected_urls = set(
        DocumentProcessingJob.objects.filter(status='cancelled')
        .values_list('url', flat=True)
    )

    for entry in by_company.values():
        company = entry['company']
        targets = [t for _flag, t in entry['items']]
        try:
            per_flag = asyncio.run(
                gather_company_candidates(company.website or '', targets)
            )
            stats['companies_crawled'] += 1
        except Exception as e:
            logger.warning(f"[HUNT] Crawl failed for {company.name}: {e}")
            per_flag = {t.flag_id: [] for t in targets}

        for flag, target in entry['items']:
            stats['flags_hunted'] += 1
            ranked = rank_candidates(per_flag.get(flag.id, []), target)

            # Only keep candidates that pass the SSRF gate: a reviewer can
            # submit one with a single click, and the worker then fetches it.
            safe_ranked = []
            for cand in ranked:
                ok, _reason = is_safe_url(cand['url'])
                if ok:
                    safe_ranked.append(cand)

            flag.candidates = safe_ranked
            flag.hunt_attempts += 1
            flag.last_hunt_at = now
            stats['candidates_found'] += len(safe_ranked)

            # hunt_attempts was just incremented, so subtract one to index the
            # schedule: attempt 1 waits HUNT_BACKOFF_DAYS[0]. Indexing on the
            # incremented value skipped the 1-day entry entirely — the first
            # re-check of a 'results' flag, whose report can be filed any day
            # inside its 45-day window, waited 3 days instead of 1 and the
            # documented 1/3/7/14/21/30 schedule started at 3.
            backoff_days = HUNT_BACKOFF_DAYS[
                min(flag.hunt_attempts - 1, len(HUNT_BACKOFF_DAYS) - 1)
            ]
            save_fields = HUNT_STATE_FIELDS + [
                'candidates', 'hunt_attempts', 'last_hunt_at',
            ]

            top = safe_ranked[0] if safe_ranked else None
            if top and is_auto_queueable(top) and top['url'] not in rejected_urls:
                doc_type = 'pea' if target.report_type == 'pea' else 'ni43101'
                try:
                    job, _created = DocumentProcessingJob.objects.get_or_create(
                        url=top['url'],
                        defaults={
                            'document_type': doc_type,
                            'company_name': company.name,
                            'status': 'pending',
                        },
                    )
                    # get_or_create matches on URL alone, so an existing FAILED
                    # job comes back too — and linking the flag to it would
                    # close the flag as processed against a job nothing will
                    # ever run (terminal failures are not retried). Leave the
                    # flag for a human instead: the reviewer sees the ranked
                    # candidates plus the old job's error and decides.
                    if job.status == 'failed':
                        logger.info(
                            f"[HUNT] Not auto-queueing flag {flag.id}: existing "
                            f"job {job.id} for this URL is failed "
                            f"({(job.error_message or '')[:60]})"
                        )
                        flag.hunt_status = 'found'
                        flag.next_hunt_at = now + timedelta(days=backoff_days)
                        stats['awaiting_review'] += 1
                        flag.save(update_fields=save_fields)
                        continue
                    reasons = '; '.join(top.get('score_reasons', []))
                    flag.hunt_status = 'auto_queued'
                    flag.next_hunt_at = None
                    # mark_as_processed saves the row, so the hunt fields are
                    # written first and the review fields ride along with it.
                    flag.save(update_fields=save_fields)
                    flag.mark_as_processed(
                        reviewer=None,
                        job=job,
                        report_url=top['url'],
                        report_type=(target.report_type
                                     if target.report_type in valid_report_types else 'other'),
                        notes=f"Auto-queued by report hunter (score {top['score']}): {reasons}",
                    )
                    stats['auto_queued'] += 1
                    logger.info(
                        f"[HUNT] AUTO-QUEUED {company.name} "
                        f"score={top['score']} {top['url'][:90]}"
                    )
                    continue
                except Exception as e:
                    logger.error(f"[HUNT] Could not queue job for flag {flag.id}: {e}")
                    flag.hunt_status = 'found'
                    flag.next_hunt_at = now + timedelta(days=backoff_days)
                    stats['awaiting_review'] += 1
            elif safe_ranked:
                flag.hunt_status = 'found'
                flag.next_hunt_at = now + timedelta(days=backoff_days)
                stats['awaiting_review'] += 1
            else:
                flag.hunt_status = 'not_found'
                flag.next_hunt_at = now + timedelta(days=backoff_days)
                stats['not_found'] += 1

            flag.save(update_fields=save_fields)

    logger.info(f"[HUNT] Complete: {stats}")

    # Chain daily discovery behind the hunt rather than co-scheduling it on its
    # own cron. A fixed 4:30 start could not guarantee the shared droplet: on a
    # quiet night the hunter's one small job finishes by ~4:15, the droplet
    # self-destroys after 5 idle minutes, and discovery's jobs at ~4:35 pay a
    # SECOND spin-up — DigitalOcean bills the droplet by the hour, so that is
    # up to a full extra billed hour every day it happens. And on a long night
    # the cron fired while the hunt was still crawling, putting both browser
    # loads on the two-slot scrape queue at once. Dispatching here means
    # discovery starts the moment the hunt ends, every time, whatever the hunt
    # took — its gated finds land while the droplet is still working the
    # hunt's reports (a large NI 43-101 alone runs ~30 minutes), and a night
    # where neither finds anything spins no droplet at all.
    if chain_discovery_limit and not dry_run:
        auto_discover_and_process_documents_task.delay(limit=chain_discovery_limit)
        logger.info(f"[HUNT] Chained discovery for {chain_discovery_limit} companies")

    return stats


# ---------------------------------------------------------------------------
# Morning audit of overnight technical-report ingestions
# ---------------------------------------------------------------------------

# What an announcement sounds like, tested against the first ingested chunk.
# The URL/size gates run before ingestion and are blind to content; this runs
# after, when the document has told us what it is. An image-heavy news-release
# PDF ('2026-04-20-Cisco-MRE-vFINAL-1.pdf', clean filename, over the 2.5MB
# floor) got through both structural gates on 2026-09-05 and opened with
# "Q2 Metals Announces Inferred Mineral Resource Estimate on the Cisco
# Lithium Project" — while every genuine report ingested that night opened
# with report furniture: "NI 43-101 Technical Report", "Prepared for:",
# "Qualified Person".
_ANNOUNCE_VERB = _re.compile(
    r'\b(announces?|is\s+pleased\s+to\s+(?:announce|report)|'
    r'reports?\s+(?:results|positive|record|an?\s))',
    _re.IGNORECASE,
)
_ANNOUNCE_CORROBORATOR = _re.compile(
    r'\((?:TSX|TSXV|TSX\.V|CSE|NYSE|OTC|OTCQ[BX]|ASX|NASDAQ|FSE|NYSEA)\b'
    r'|news\s+release|press\s+release'
    r'|\b(?:british\s+columbia|ontario|alberta|quebec)\s*[-–—]',
    _re.IGNORECASE,
)
_REPORT_FURNITURE = _re.compile(
    r'prepared\s+(?:for|by)\s*:?|qualified\s+persons?|effective\s+date\s*:'
    r'|technical\s+report\s+on|report\s+date\s*:',
    _re.IGNORECASE,
)

# An announcement is a few pages. Every genuine report ingested so far runs 30+
# chunks; the two announcement PDFs that slipped through ran 7 and 13. The
# ceiling means a long document can never be reverted by this task, whatever
# its first page sounds like.
_AUDIT_MAX_CHUNKS = 50


def _reads_as_announcement(first_chunk_text: str) -> bool:
    """True when a document's opening is a news release, not a report."""
    text = (first_chunk_text or '')[:3000]
    if _REPORT_FURNITURE.search(text):
        return False
    return bool(_ANNOUNCE_VERB.search(text) and _ANNOUNCE_CORROBORATOR.search(text))


@shared_task(bind=True, time_limit=300, soft_time_limit=280, on_failure=log_task_failure)
def verify_overnight_technical_ingestions_task(self, hours=26, dry_run=False):
    """
    Morning self-audit: revert announcement PDFs that were ingested as reports.

    Scans technical documents created in the last `hours` and reads what the
    document actually says about itself. A short document whose first chunk
    opens like a news release — an announce verb plus a ticker or dateline,
    and none of a report's own furniture — is reverted exactly the way the
    manual morning review did it: the job is cancelled (which also bars the
    URL from ever auto-queueing again), any originating flag reopens with its
    ranked candidates intact, and the document and its chunks are deleted.
    The content is not lost to the platform; a news release belongs to the
    news pipeline, which covers it separately.

    Deliberately conservative in three ways: only short documents (a genuine
    report can never trip it past _AUDIT_MAX_CHUNKS), only when report
    furniture is absent, and everything it does is loudly logged so the
    morning glance at /admin/document-queue shows exactly what happened.
    """
    from datetime import timedelta

    from django.db import transaction

    from .models import Document, DocumentProcessingJob, NewsReportFlag

    cutoff = timezone.now() - timedelta(hours=hours)
    candidates = Document.objects.filter(
        created_at__gte=cutoff,
        document_type__in=['ni43101', 'pea', 'technical_report'],
    )

    checked = 0
    reverted = []
    for doc in candidates:
        checked += 1
        chunks = doc.chunks.order_by('chunk_index')
        count = chunks.count()
        if count == 0 or count > _AUDIT_MAX_CHUNKS:
            continue
        first = chunks.first()
        if not _reads_as_announcement(first.text):
            continue

        logger.warning(
            f"[AUDIT] Document {doc.id} ({count} chunks) reads as an "
            f"announcement: {first.text[:90]!r} url={doc.file_url[-70:]}"
        )
        if dry_run:
            reverted.append(doc.id)
            continue

        with transaction.atomic():
            for job in DocumentProcessingJob.objects.filter(document_id=doc.id):
                job.status = 'cancelled'
                job.error_message = (
                    'Auto-reverted by the morning ingestion audit: the document '
                    'opens like a news release, not a technical report.'
                )
                job.document = None
                job.save(update_fields=['status', 'error_message', 'document'])
                for flag in NewsReportFlag.objects.filter(processing_job=job):
                    flag.status = 'pending'
                    flag.hunt_status = 'found' if flag.candidates else 'not_found'
                    flag.processing_job = None
                    flag.report_url = ''
                    flag.report_type = ''
                    flag.reviewed_by = None
                    flag.reviewed_at = None
                    flag.review_notes = (
                        'Reopened by the morning ingestion audit: the '
                        'auto-queued document was an announcement PDF. '
                        'Candidates intact.'
                    )
                    flag.save()
                    logger.warning(f"[AUDIT] Flag {flag.id} reopened")
            doc.delete()
        reverted.append(doc.id)

    logger.info(f"[AUDIT] Checked {checked} overnight technical documents, "
                f"reverted {len(reverted)}: {reverted or 'none'}")
    return {'checked': checked, 'reverted': reverted, 'dry_run': dry_run}
