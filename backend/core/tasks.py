"""
Background Tasks for Document Processing and News Scraping
Processes document queue jobs sequentially
"""

from celery import shared_task
from django.utils import timezone
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
                except:
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
                existing_job = DocumentProcessingJob.objects.filter(url=url).exists()
                if not existing_job:
                    job = DocumentProcessingJob.objects.create(
                        url=url,
                        document_type='news_release',
                        company_name=company.name,
                        status='pending'
                    )
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
                if detected_keywords:
                    from core.models import NewsReleaseFlag, DismissedNewsURL

                    # Check if URL was dismissed
                    if DismissedNewsURL.objects.filter(url=url).exists():
                        print(f"  [SKIP] Previously dismissed URL")
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
        if created_count > 0:
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
                
                print(f"  Discovered {len(documents)} documents")
                total_discovered += len(documents)
                
                # Create processing jobs (skip existing)
                jobs_created = 0
                for doc in documents:
                    # Check if document already exists or job pending
                    existing = Document.objects.filter(
                        company=company,
                        file_url=doc['url']
                    ).exists()
                    
                    existing_job = DocumentProcessingJob.objects.filter(
                        url=doc['url'],
                        status__in=['completed', 'processing']
                    ).exists()
                    
                    if existing or existing_job:
                        continue
                    
                    # Create processing job
                    DocumentProcessingJob.objects.create(
                        url=doc['url'],
                        document_type=doc['document_type'],
                        company_name=company.name,
                        status='pending'
                    )
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
                except:
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
                financing_keywords = [
                    'private placement', 'financing', 'funding round',
                    'capital raise', 'bought deal', 'equity financing',
                    'flow-through', 'warrant', 'subscription', 'offering',
                    'strategic investment', 'strategic partner'
                ]

                title_lower = title.lower()
                detected_keywords = [kw for kw in financing_keywords if kw in title_lower]

                if detected_keywords:
                    from core.models import NewsReleaseFlag, DismissedNewsURL
                    # Check if this URL was previously dismissed - never re-flag dismissed news
                    if DismissedNewsURL.objects.filter(url=url).exists():
                        print(f"  [SKIP] Previously dismissed: {title[:50]}...")
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


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
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
    """
    from mcp_servers.company_scraper import scrape_company_website
    from .models import ScrapingJob

    print(f"[ASYNC SCRAPE] Starting company scrape task for job {job_id}...")

    try:
        # Get the scraping job
        job = ScrapingJob.objects.get(id=job_id)
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
        except:
            pass

        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'job_id': job_id,
                'error': str(e),
                'message': f'Company scrape failed after retries: {str(e)}'
            }
