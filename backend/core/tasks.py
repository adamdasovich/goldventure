"""
Background Tasks for Document Processing and News Scraping
Processes document queue jobs sequentially
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from .models import DocumentProcessingJob, Company, NewsRelease, Document
from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from mcp_servers.website_crawler import crawl_news_releases
from django.db.models import Q
import asyncio


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
            Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
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

        document = Document.objects.create(
            company=company,
            title=doc_title_map.get(document_type, 'Document'),
            document_type=document_type,
            document_date=datetime.now().date(),
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
            print(f"Stored {chunks_stored} chunks for semantic search")
        except Exception as e:
            print(f"Error storing document chunks for RAG: {str(e)}")

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

    print(f"Found {pending_jobs.count()} pending jobs to process")

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

            print(f" Job {job.id} completed successfully")
            print(f"  - Document ID: {job.document_id}")
            print(f"  - Resources created: {job.resources_created}")
            print(f"  - Chunks created: {job.chunks_created}")
            print(f"  - Processing time: {job.duration_display}")

            # Send email notification for NI 43-101 reports
            if job.document_type == 'ni43101' and job.document_id:
                try:
                    from core.notifications import send_ni43101_discovery_notification
                    document = Document.objects.get(id=job.document_id)
                    if document.company:
                        send_ni43101_discovery_notification(document, document.company)
                except Exception as e:
                    print(f"   Failed to send NI 43-101 notification: {str(e)}")

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
                        print(f"   Updated CompanyNews record: {news_record.title[:50]}...")
                except Exception as e:
                    print(f"   Failed to update CompanyNews record: {str(e)}")

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

            print(f" Job {job.id} failed: {error_msg}")

    except Exception as e:
        # Handle unexpected errors
        job.status = 'failed'
        job.error_message = f"Unexpected error: {str(e)}"
        job.completed_at = datetime.now()

        if job.started_at:
            duration = (job.completed_at - job.started_at).total_seconds()
            job.processing_time_seconds = int(duration)

        job.save()

        print(f" Job {job.id} failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


@shared_task(bind=True, max_retries=3)
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
            news_releases = loop.run_until_complete(
                crawl_news_releases(
                    url=company.website,
                    months=48,  # Increased from 6 to 48 months to capture older news
                    max_depth=2
                )
            )
        finally:
            loop.close()

        # Process and save news releases
        created_count = 0
        updated_count = 0

        # Check if this is a new company being onboarded (no existing NewsRelease records)
        # For new companies: use 90-day rule (3 months) to show recent financing history
        # For existing companies: use 7-day rule to avoid re-flagging old news daily
        existing_news_count = NewsRelease.objects.filter(company=company).count()
        is_new_company = existing_news_count == 0
        if is_new_company:
            print(f"  [ONBOARDING] New company detected - will flag financing from last 90 days")

        for news in news_releases:
            title = news.get('title', '').strip()
            url = news.get('url', '').strip()
            date_str = news.get('date')
            release_type = news.get('document_type', 'news_release')

            # Determine if this is a financial report
            is_financial = any(keyword in title.lower() for keyword in [
                'financial', 'earnings', 'quarter', 'q1', 'q2', 'q3', 'q4',
                'annual report', 'md&a', 'interim', 'fiscal'
            ])

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
            # First check if record exists - don't overwrite existing dates
            existing = NewsRelease.objects.filter(company=company, url=url).first()
            if existing:
                # Only update title if needed, preserve existing date
                if existing.title != title:
                    existing.title = title
                    existing.save(update_fields=['title', 'updated_at'])
                obj = existing
                created = False
            else:
                # Create new record
                obj = NewsRelease.objects.create(
                    company=company,
                    url=url,
                    title=title,
                    release_type=release_type,
                    release_date=release_date,
                    summary='',
                    is_material=is_financial,
                    full_text=''
                )
                created = True

            # Also create/update CompanyNews record (used by frontend API)
            from core.models import CompanyNews
            news_record, _ = CompanyNews.objects.update_or_create(
                company=company,
                source_url=url,
                defaults={
                    "title": title,
                    "publication_date": release_date,
                    "news_type": "corporate",
                }
            )

            # Create document processing job for PDF news releases (for vector DB)
            if url and '.pdf' in url.lower():
                from core.models import DocumentProcessingJob
                # Use get_or_create to avoid race condition (TOCTOU vulnerability)
                job, job_created = DocumentProcessingJob.objects.get_or_create(
                    url=url,
                    defaults={
                        'document_type': 'news_release',
                        'company_name': company.name,
                        'status': 'pending'
                    }
                )
                if job_created:
                    news_record.processing_job = job
                    news_record.save(update_fields=['processing_job'])

            if created:
                created_count += 1

                # FINANCING DETECTION: Check for financing keywords in title
                financing_keywords = [
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

                # STRATEGIC INVESTMENT DETECTION: Major miner investments in juniors
                strategic_keywords = [
                    'strategic investment',
                    'strategic partner',
                    'equity stake',
                    'strategic alliance',
                    'strategic equity',
                    'cornerstone investor',
                ]

                # Major miner names to detect strategic investments
                major_miners = [
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

                all_keywords = financing_keywords + strategic_keywords + major_miners

                title_lower = title.lower()
                detected_keywords = [kw for kw in all_keywords if kw in title_lower]

                # If financing keywords detected, create flag for superuser review
                # For NEW companies (onboarding): use 90-day rule to show recent financing history
                # For EXISTING companies: use 7-day rule to avoid re-flagging old news daily
                if detected_keywords and release_date:
                    from core.models import NewsReleaseFlag, DismissedNewsURL
                    from datetime import timedelta

                    # Use different cutoff based on whether this is a new company
                    cutoff_days = 90 if is_new_company else 7
                    cutoff_date = datetime.now().date() - timedelta(days=cutoff_days)
                    if release_date < cutoff_date:
                        print(f"  [SKIP] Old news (not flagging): {title[:50]}... (date: {release_date})")
                        continue

                    # Check if URL or title is similar to a previously dismissed news
                    is_similar, matched_dismissed = DismissedNewsURL.is_similar_to_dismissed(
                        company=company,
                        url=url,
                        title=title,
                        similarity_threshold=0.85
                    )
                    if is_similar:
                        print(f"  [SKIP] Similar to previously dismissed: {title[:50]}...")
                        continue

                    # Only create flag if one doesn't already exist
                    flag, flag_created = NewsReleaseFlag.objects.get_or_create(
                        news_release=obj,
                        defaults={
                            'detected_keywords': detected_keywords,
                            'status': 'pending'
                        }
                    )

                    print(f"   Flagged financing-related news: {title[:60]}...")
                    print(f"     Keywords: {', '.join(detected_keywords)}")

                    # Send email notification for new flags only
                    if flag_created:
                        try:
                            from core.notifications import send_financing_flag_notification
                            send_financing_flag_notification(flag, company, obj)
                        except Exception as e:
                            print(f"      Failed to send financing flag notification: {str(e)}")

            else:
                updated_count += 1

        # Auto-process news content into vector database for semantic search
        # ONLY during onboarding (is_new_company=True) - skip during daily scrapes
        # Daily scrapes were taking 500+ seconds per company due to URL fetching here
        if created_count > 0 and is_new_company:
            try:
                from mcp_servers.news_content_processor import NewsContentProcessor
                processor = NewsContentProcessor(company_id=company.id)
                process_result = processor._process_company_news(company.name, limit=created_count + 5)
                chunks_created = process_result.get('chunks_created', 0)
                print(f"  Processed {process_result.get('news_items_processed', 0)} news items into {chunks_created} searchable chunks")
            except Exception as e:
                print(f"  Warning: News content processing failed: {str(e)}")
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
        # Retry on failure
        self.retry(exc=e, countdown=60)  # Retry after 60 seconds

        return {
            'status': 'error',
            'message': f'Error scraping news: {str(e)}',
            'news_count': 0
        }


@shared_task(bind=True, max_retries=3)
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
            print(f"Successfully scraped {result['scraped']} metals prices from Kitco")
            return result
        else:
            print(f"Metals scrape failed: {result.get('error', 'Unknown error')}")
            # Retry on failure
            raise Exception(result.get('error', 'Scraping failed'))

    except Exception as e:
        print(f"Error in metals scraping task: {str(e)}")
        self.retry(exc=e, countdown=300)  # Retry after 5 minutes

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
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
            print(f"Successfully fetched {result['successful']} stock prices")
            print(f"Failed: {result['failed']}, Skipped: {result['skipped']}")
            return result
        else:
            # Partial success - some companies had errors
            print(f"Stock price fetch completed with errors:")
            print(f"Successful: {result['successful']}, Failed: {result['failed']}")
            if result['errors']:
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
            return result

    except Exception as e:
        print(f"Error in stock price fetching task: {str(e)}")
        self.retry(exc=e, countdown=300)  # Retry after 5 minutes

        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def auto_discover_and_process_documents_task(self, company_ids=None, document_types=None, limit=None):
    """
    Celery task to automatically discover and process documents for companies.
    Can be scheduled to run periodically (e.g., daily, weekly).
    
    Args:
        company_ids (list, optional): List of company IDs to process. If None, processes all companies.
        document_types (list, optional): List of document types to filter for. If None, processes all types.
        limit (int, optional): Limit number of companies to process.
    
    Returns:
        dict: Status information about the discovery and processing operation
    """
    try:
        from core.models import Company
        from mcp_servers.website_crawler import crawl_company_website
        
        # Get companies to process
        if company_ids:
            companies = Company.objects.filter(id__in=company_ids, website__isnull=False).exclude(website='')
        else:
            companies = Company.objects.filter(website__isnull=False).exclude(website='')
        
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
        companies_processed = 0
        
        print(f"Auto-discovery task: Processing {len(companies)} companies")
        
        for company in companies:
            try:
                print(f"Crawling {company.name}...")
                
                # Discover documents
                documents = asyncio.run(crawl_company_website(company.website, max_depth=2))

                if not documents:
                    print(f"  No documents discovered for {company.name}")
                    continue

                # Filter by document type if specified
                if document_types:
                    documents = [d for d in documents if d['document_type'] in document_types]

                # IMPORTANT: Filter to only important recent documents
                # Keep: most recent NI 43-101, most recent PEA, recent presentations, recent financials
                filtered_docs = []
                seen_types = set()

                # Important document types - keep only the most recent of each
                priority_types = ['ni_43_101', 'pea', 'feasibility_study', 'resource_estimate']

                # Sort by date (newest first) if dates available
                documents.sort(key=lambda x: x.get('date') or '0000-00-00', reverse=True)

                for doc in documents:
                    doc_type = doc.get('document_type', 'other')

                    # For priority types, only keep the most recent one
                    if doc_type in priority_types:
                        if doc_type not in seen_types:
                            filtered_docs.append(doc)
                            seen_types.add(doc_type)
                            print(f"    [KEEP] {doc_type}: {doc.get('title', 'No title')[:50]}")

                    # For presentations, keep most recent only
                    elif doc_type == 'presentation':
                        if 'presentation' not in seen_types:
                            filtered_docs.append(doc)
                            seen_types.add('presentation')
                            print(f"    [KEEP] presentation: {doc.get('title', 'No title')[:50]}")

                    # Skip old financial statements, news releases (handled separately), and 'other' types
                    elif doc_type in ['financial_statement', 'news_release', 'other']:
                        continue

                documents = filtered_docs
                print(f"  Filtered to {len(documents)} important documents (from {len(documents)} discovered)")
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
                
                total_jobs_created += jobs_created
                companies_processed += 1
                
                print(f"  Created {jobs_created} new processing jobs")
                
            except Exception as e:
                print(f"  Error processing {company.name}: {str(e)}")
                continue
        
        # Auto-process the queue
        if total_jobs_created > 0:
            print(f"\nAuto-processing {total_jobs_created} new jobs...")
            process_document_queue()
        
        return {
            'status': 'success',
            'companies_processed': companies_processed,
            'total_discovered': total_discovered,
            'jobs_created': total_jobs_created,
            'message': f'Auto-discovery completed: {companies_processed} companies, {total_discovered} documents discovered, {total_jobs_created} jobs created'
        }
        
    except Exception as e:
        print(f"Error in auto-discovery task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Auto-discovery task failed: {str(e)}'
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=60, time_limit=600, soft_time_limit=580)
def scrape_single_company_news_task(self, company_id: int):
    """
    Background task to scrape news releases for a SINGLE company.
    This task is spawned by scrape_all_companies_news_task for each company.

    Time limit: 10 minutes per company
    """
    try:
        company = Company.objects.get(id=company_id)
        print(f"Scraping news for {company.name}...")

        # Run the async crawler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            news_releases = loop.run_until_complete(
                crawl_news_releases(
                    url=company.website,
                    months=3,  # Last 3 months for daily scrapes
                    max_depth=2
                )
            )
        finally:
            loop.close()

        # Process and save news releases
        created_count = 0
        updated_count = 0

        for news in news_releases:
            title = news.get('title', '').strip()
            url = news.get('url', '').strip()
            date_str = news.get('date')
            release_type = news.get('document_type', 'news_release')

            if not url:
                continue

            # Parse date
            release_date = None
            if date_str:
                try:
                    release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    continue  # Skip entries without valid dates
            else:
                continue  # Skip entries without valid dates

            # Create or update news release
            # First check if record exists - don't overwrite existing dates
            existing = NewsRelease.objects.filter(company=company, url=url).first()
            if existing:
                # Only update title if needed, preserve existing date
                if existing.title != title:
                    existing.title = title
                    existing.save(update_fields=['title', 'updated_at'])
                obj = existing
                created = False
            else:
                # Create new record
                obj = NewsRelease.objects.create(
                    company=company,
                    url=url,
                    title=title,
                    release_type=release_type,
                    release_date=release_date,
                    summary='',
                    is_material=False,
                    full_text=''
                )
                created = True

            if created:
                created_count += 1

                # Check for financing keywords and flag
                # NOTE: Keep in sync with scrape_company_news_task financing keywords
                financing_keywords = [
                    'private placement', 'financing', 'funding round',
                    'capital raise', 'bought deal', 'equity financing',
                    'debt financing', 'flow-through', 'warrant', 'subscription', 'offering'
                ]

                # STRATEGIC INVESTMENT DETECTION: Major miner investments in juniors
                strategic_keywords = [
                    'strategic investment', 'strategic partner', 'equity stake',
                    'strategic alliance', 'strategic equity', 'cornerstone investor'
                ]

                # Major miner names to detect strategic investments
                major_miners = [
                    'barrick', 'newmont', 'agnico eagle', 'franco-nevada', 'kinross',
                    'anglogold ashanti', 'gold fields', 'wheaton precious metals',
                    'royal gold', 'eldorado gold', 'iamgold', 'endeavour mining',
                    'b2gold', 'yamana gold'
                ]

                all_keywords = financing_keywords + strategic_keywords + major_miners
                title_lower = title.lower()
                detected_keywords = [kw for kw in all_keywords if kw in title_lower]

                # Only flag recent news (within 7 days) - older news is not actionable
                if detected_keywords and release_date:
                    from core.models import NewsReleaseFlag, DismissedNewsURL
                    from datetime import timedelta

                    # Only flag news releases within the last 7 days
                    cutoff_date = datetime.now().date() - timedelta(days=7)
                    if release_date < cutoff_date:
                        print(f"  [SKIP] Old news (not flagging): {title[:50]}...")
                    else:
                        # Check if URL or title is similar to previously dismissed - never re-flag
                        is_similar, matched_dismissed = DismissedNewsURL.is_similar_to_dismissed(
                            company=company,
                            url=url,
                            title=title,
                            similarity_threshold=0.85
                        )
                        if is_similar:
                            print(f"  [SKIP] Similar to dismissed: {title[:50]}...")
                        else:
                            flag, flag_created = NewsReleaseFlag.objects.get_or_create(
                                news_release=obj,
                                defaults={
                                    'detected_keywords': detected_keywords,
                                    'status': 'pending'
                                }
                            )
                            if flag_created:
                                print(f"  [FLAG] Flagged: {title[:50]}...")
                                try:
                                    from core.notifications import send_financing_flag_notification
                                    send_financing_flag_notification(flag, company, obj)
                                except Exception as e:
                                    print(f"  [WARN] Notification error: {str(e)}")
            else:
                updated_count += 1

        print(f"   {company.name}: {created_count} new, {updated_count} updated")
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
        print(f"   Error scraping company {company_id}: {str(e)}")
        return {'company_id': company_id, 'status': 'error', 'message': str(e)}


@shared_task(bind=True, max_retries=1, time_limit=300)
def scrape_all_companies_news_task(self):
    """
    Background task to queue news scraping for ALL companies with websites.
    Spawns individual tasks for each company to run in parallel.

    Scheduled to run daily in the morning via Celery Beat.
    """
    print("Starting company news scrape - spawning individual tasks...")

    try:
        # Get all companies with websites
        companies = Company.objects.filter(
            website__isnull=False
        ).exclude(website='').order_by('name')

        total_companies = companies.count()
        print(f"Found {total_companies} companies with websites to scrape")

        # Spawn individual tasks for each company (run in batches)
        task_ids = []
        for company in companies:
            # Queue individual task for each company
            task = scrape_single_company_news_task.delay(company.id)
            task_ids.append(task.id)
            print(f"  Queued: {company.name} (task {task.id})")

        print(f"\nQueued {len(task_ids)} individual scraping tasks")
        print("Tasks will run in parallel based on worker concurrency")

        return {
            'status': 'success',
            'total_companies': total_companies,
            'tasks_queued': len(task_ids),
            'message': f"Queued {len(task_ids)} company news scraping tasks"
        }

    except Exception as e:
        print(f"Error queuing company news scrape tasks: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': f'Failed to queue company news scrape tasks: {str(e)}'
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_mining_news_task(self):
    """
    Background task to scrape mining news from configured sources.
    Runs the async news scraper and saves articles to the database.

    Scheduled to run multiple times daily via Celery Beat.
    """
    from mcp_servers.news_scraper import run_scrape_job
    from .models import NewsScrapeJob

    print("Starting mining news scrape task...")

    try:
        # Create a new scrape job record
        job = NewsScrapeJob.objects.create(
            status='pending',
            is_scheduled=True
        )
        print(f"Created scrape job {job.id}")

        # Run the async scraper
        result = asyncio.run(run_scrape_job(job_id=job.id))

        print(f"Mining news scrape completed: {result}")
        return {
            'status': 'success',
            'job_id': job.id,
            'sources_processed': result.get('sources_processed', 0),
            'articles_found': result.get('articles_found', 0),
            'message': f"Successfully scraped mining news: {result.get('articles_found', 0)} articles found"
        }

    except Exception as e:
        print(f"Error in mining news scrape task: {str(e)}")
        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Mining news scrape failed after retries: {str(e)}'
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=60, time_limit=600, soft_time_limit=580, acks_late=True)
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

    print(f"[ASYNC SCRAPE] Starting company scrape task for job {job_id}...")

    try:
        # Get the scraping job
        job = ScrapingJob.objects.get(id=job_id)

        # Check if job is already completed or failed (idempotency for acks_late redelivery)
        if job.status in ['success', 'partial', 'failed', 'cancelled']:
            print(f"[ASYNC SCRAPE] Job {job_id} already has status '{job.status}', skipping")
            return {
                'status': 'skipped',
                'job_id': job_id,
                'message': f'Job already completed with status: {job.status}'
            }

        job.status = 'running'
        job.started_at = timezone.now()
        job.save()

        url = job.website_url
        print(f"[ASYNC SCRAPE] Scraping URL: {url}")

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

        print(f"[ASYNC SCRAPE] Job {job_id} completed successfully")
        print(f"  - Documents: {job.documents_found}")
        print(f"  - People: {job.people_found}")
        print(f"  - News: {job.news_found}")

        return {
            'status': 'success',
            'job_id': job_id,
            'data': result['data'],
            'errors': result['errors'],
            'urls_visited': result['urls_visited'],
            'message': f"Successfully scraped company website"
        }

    except ScrapingJob.DoesNotExist:
        print(f"[ASYNC SCRAPE] Job {job_id} not found")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': f'ScrapingJob with ID {job_id} not found'
        }

    except SoftTimeLimitExceeded:
        # Task timed out - mark as failed with timeout message
        print(f"[ASYNC SCRAPE] Job {job_id} timed out (exceeded 10 minute limit)")
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = ['Task timed out - exceeded 10 minute limit. The website may be too slow or complex.']
            job.save()
        except Exception as e:
            print(f"[ERROR] Failed to update job {job_id} status on timeout: {e}")

        return {
            'status': 'error',
            'job_id': job_id,
            'error': 'Task timed out',
            'message': 'Company scrape timed out after 10 minutes'
        }

    except Exception as e:
        print(f"[ASYNC SCRAPE] Job {job_id} failed: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update job with failure
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = [str(e)]
            job.error_traceback = traceback.format_exc()
            job.save()
        except Exception as update_err:
            print(f"[ERROR] Failed to update job {job_id} status on error: {update_err}")

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


@shared_task(bind=True, max_retries=1, time_limit=600, soft_time_limit=580, acks_late=True)
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

    print(f"[ASYNC SCRAPE+SAVE] Starting scrape and save task for job {job_id}...")

    try:
        # Get the scraping job
        job = ScrapingJob.objects.get(id=job_id)

        # Check if job is already completed (idempotency)
        if job.status in ['success', 'partial', 'failed', 'cancelled']:
            print(f"[ASYNC SCRAPE+SAVE] Job {job_id} already has status '{job.status}', skipping")
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
        print(f"[ASYNC SCRAPE+SAVE] Scraping URL: {url}")

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
                print(f"[ASYNC SCRAPE+SAVE] Verification failed for company {company.id}: {e}")
                verification = {'status': 'error', 'message': str(e)}

            print(f"[ASYNC SCRAPE+SAVE] Job {job_id} completed successfully")
            print(f"  - Company: {company.name} (ID: {company.id})")
            print(f"  - Documents: {job.documents_found}")
            print(f"  - People: {job.people_found}")
            print(f"  - News scraping triggered")
            print(f"  - Verification: {verification.get('status', 'unknown')} (score: {verification.get('overall_score', 0)})")
            if verification.get('fixes_applied'):
                print(f"  - Auto-fixes applied: {verification['fixes_applied']}")

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
        print(f"[ASYNC SCRAPE+SAVE] Job {job_id} not found")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': f'ScrapingJob with ID {job_id} not found'
        }

    except SoftTimeLimitExceeded:
        print(f"[ASYNC SCRAPE+SAVE] Job {job_id} timed out")
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.error_messages = ['Task timed out - exceeded 10 minute limit']
            job.save()
        except Exception as e:
            print(f"[ERROR] Failed to update job {job_id} status on timeout: {e}")
        return {
            'status': 'error',
            'job_id': job_id,
            'error': 'Task timed out',
            'message': 'Scrape and save timed out after 10 minutes'
        }

    except Exception as e:
        print(f"[ASYNC SCRAPE+SAVE] Job {job_id} failed: {str(e)}")
        import traceback
        traceback.print_exc()

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
                existing = Company.objects.filter(website_url__icontains=domain).first()
                if existing:
                    print(f"[FALLBACK] Company already exists for {domain}: {existing.name} (ID: {existing.id})")
                    fallback_company = existing
                else:
                    # Create minimal company record - Claude verification will populate it
                    print(f"[FALLBACK] Creating minimal company record for {job.website_url}")
                    fallback_company = Company.objects.create(
                        name=f"{fallback_name} (pending verification)",
                        website_url=job.website_url,
                        country='Canada',  # Default for junior mining
                        description='Company data pending verification - scraped data incomplete.',
                        is_verified=False,
                    )
                    print(f"[FALLBACK] Created fallback company: {fallback_company.name} (ID: {fallback_company.id})")

                # Run Claude verification to populate the company with real data
                # This can extract: proper company name, description, projects from website
                if fallback_company:
                    print(f"[FALLBACK] Running Claude verification on company {fallback_company.id}...")
                    from core.claude_validator import verify_onboarded_company
                    verification = verify_onboarded_company(fallback_company.id)
                    print(f"[FALLBACK] Verification result: {verification.get('status', 'unknown')}")
                    if verification.get('fixes_applied'):
                        print(f"[FALLBACK] Auto-fixes applied: {verification['fixes_applied']}")

                    # Also trigger news scraping
                    scrape_company_news_task.delay(fallback_company.id)
                    print(f"[FALLBACK] News scraping triggered for company {fallback_company.id}")
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
            print(f"[FALLBACK] Failed to create fallback company: {fallback_error}")
            import traceback
            traceback.print_exc()

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


@shared_task(bind=True)
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

    print("[CLEANUP] Running stuck jobs cleanup task...")

    now = timezone.now()
    stuck_running_threshold = now - timedelta(minutes=15)
    stuck_pending_threshold = now - timedelta(minutes=30)

    # Cleanup stuck ScrapingJobs
    stuck_scraping_running = ScrapingJob.objects.filter(
        status='running',
        started_at__lt=stuck_running_threshold
    )

    stuck_scraping_pending = ScrapingJob.objects.filter(
        status='pending',
        started_at__isnull=True
    ).filter(
        # Filter by created_at being older than threshold
        # Note: Django auto-adds created_at if the model has it
    )

    scraping_fixed = 0
    for job in stuck_scraping_running:
        duration = (now - job.started_at).total_seconds() / 60
        print(f"[CLEANUP] Marking stuck ScrapingJob {job.id} as failed (running for {duration:.1f} minutes)")
        job.status = 'failed'
        job.completed_at = now
        job.error_messages = [f'Job stuck in running state for {duration:.1f} minutes. Likely worker crash or restart.']
        job.save()
        scraping_fixed += 1

    # Cleanup stuck DocumentProcessingJobs
    stuck_processing = DocumentProcessingJob.objects.filter(
        status='processing',
        started_at__lt=stuck_running_threshold
    )

    processing_fixed = 0
    for job in stuck_processing:
        duration = (now - job.started_at).total_seconds() / 60
        print(f"[CLEANUP] Marking stuck DocumentProcessingJob {job.id} as failed (processing for {duration:.1f} minutes)")
        job.status = 'failed'
        job.completed_at = now
        job.error_message = f'Job stuck in processing state for {duration:.1f} minutes. Likely worker crash or restart.'
        job.save()
        processing_fixed += 1

    total_fixed = scraping_fixed + processing_fixed
    print(f"[CLEANUP] Fixed {total_fixed} stuck jobs (ScrapingJobs: {scraping_fixed}, DocumentProcessingJobs: {processing_fixed})")

    return {
        'status': 'success',
        'scraping_jobs_fixed': scraping_fixed,
        'processing_jobs_fixed': processing_fixed,
        'total_fixed': total_fixed
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=60, time_limit=300, soft_time_limit=280)
def process_company_news_for_rag_task(self, company_id: int, limit: int = 20):
    """
    Background Celery task to process a company's news into the RAG knowledge base.

    This task:
    1. Fetches full content from news URLs
    2. Chunks the text into manageable pieces
    3. Generates embeddings using Voyage AI
    4. Stores chunks in PostgreSQL (NewsChunk) and ChromaDB

    Args:
        company_id: ID of the Company to process news for
        limit: Maximum number of news items to process (default 20)

    Returns:
        dict: Processing result with counts
    """
    from .models import Company, NewsChunk
    from mcp_servers.news_content_processor import NewsContentProcessor

    print(f"[RAG TASK] Starting news processing for company {company_id}...")

    try:
        company = Company.objects.get(id=company_id)

        # Check if already has chunks (avoid reprocessing)
        existing_chunks = NewsChunk.objects.filter(company=company).count()
        if existing_chunks > 0:
            print(f"[RAG TASK] Company {company.name} already has {existing_chunks} chunks, skipping")
            return {
                'status': 'skipped',
                'company': company.name,
                'existing_chunks': existing_chunks,
                'message': 'Company already has news chunks processed'
            }

        # Process news
        processor = NewsContentProcessor()
        result = processor._process_company_news(company.name, limit=limit)

        if result.get('success'):
            print(f"[RAG TASK] Processed {result.get('news_items_processed', 0)} news items, "
                  f"created {result.get('chunks_created', 0)} chunks for {company.name}")
            return {
                'status': 'success',
                'company': company.name,
                'news_items_processed': result.get('news_items_processed', 0),
                'chunks_created': result.get('chunks_created', 0),
                'errors': result.get('errors')
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"[RAG TASK] Processing failed for {company.name}: {error_msg}")
            return {
                'status': 'error',
                'company': company.name,
                'error': error_msg
            }

    except Company.DoesNotExist:
        print(f"[RAG TASK] Company {company_id} not found")
        return {
            'status': 'error',
            'company_id': company_id,
            'error': f'Company with ID {company_id} not found'
        }

    except Exception as e:
        print(f"[RAG TASK] Error processing company {company_id}: {str(e)}")
        import traceback
        traceback.print_exc()

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


@shared_task(bind=True, time_limit=600, soft_time_limit=580)
def store_company_profile_in_rag_task(self, company_id: int):
    """
    Background task to store a company's profile in the RAG knowledge base.

    Stores company overview, description, tagline, stock info, and project summaries
    in ChromaDB for semantic search.

    Args:
        company_id: ID of the Company to store profile for

    Returns:
        dict: Storage result
    """
    from .models import Company
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from pathlib import Path
    from django.conf import settings
    from mcp_servers.embeddings import get_embedding_function

    print(f"[RAG TASK] Storing profile for company {company_id}...")

    try:
        company = Company.objects.get(id=company_id)

        # Build company profile text
        profile_parts = []

        if company.description:
            profile_parts.append(f"Company Overview: {company.name}\n{company.description}")

        if company.tagline:
            profile_parts.append(f"Tagline: {company.tagline}")

        if company.ticker_symbol and company.exchange:
            profile_parts.append(f"Stock: {company.ticker_symbol} on {company.exchange.upper()}")

        # Projects summary
        projects = company.projects.all()
        if projects:
            project_texts = []
            for project in projects:
                project_text = f"Project: {project.name}"
                if project.description:
                    project_text += f"\n{project.description}"
                if project.country:
                    project_text += f"\nLocation: {project.country}"
                if project.primary_commodity:
                    project_text += f"\nCommodity: {project.primary_commodity}"
                project_texts.append(project_text)
            profile_parts.append("Projects:\n" + "\n\n".join(project_texts))

        if not profile_parts:
            return {'status': 'skipped', 'message': 'No profile data to store'}

        full_profile = "\n\n".join(profile_parts)

        # Store in ChromaDB
        chroma_path = Path(settings.BASE_DIR) / "chroma_db"
        chroma_path.mkdir(exist_ok=True)

        chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get embedding function
        embedding_function = get_embedding_function()

        collection = chroma_client.get_or_create_collection(
            name="company_profiles",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_function
        )

        # Delete existing profile
        try:
            collection.delete(ids=[f"company_{company.id}_profile"])
        except Exception:
            pass  # Profile may not exist yet

        # Add profile
        collection.add(
            ids=[f"company_{company.id}_profile"],
            documents=[full_profile],
            metadatas=[{
                "company_id": company.id,
                "company_name": company.name,
                "ticker": company.ticker_symbol or "",
                "exchange": company.exchange or "",
                "type": "company_profile"
            }]
        )

        print(f"[RAG TASK] Stored {len(full_profile)} chars of profile for {company.name}")
        return {
            'status': 'success',
            'company': company.name,
            'chars_stored': len(full_profile)
        }

    except Company.DoesNotExist:
        return {'status': 'error', 'error': f'Company {company_id} not found'}

    except Exception as e:
        print(f"[RAG TASK] Error storing profile for {company_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}
