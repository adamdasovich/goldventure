"""
Django Management Command: Process Documents with Recursive Language Model (RLM)

Based on: "Recursive Language Models" (Zhang, Kraska, Khattab - arXiv:2512.24601)

This command processes NI 43-101 reports using the RLM framework, which enables
processing documents much longer than the LLM's context window by:
1. Decomposing the document into logical chunks
2. Recursively processing each chunk
3. Aggregating results with conflict resolution
4. Validating extracted data

Usage:
    # Process a single document URL
    python manage.py process_document_rlm --url "https://example.com/report.pdf" --company "1911 Gold"

    # Process with specific decomposition strategy
    python manage.py process_document_rlm --url "..." --company "..." --strategy section

    # Process pending DocumentProcessingJobs with RLM
    python manage.py process_document_rlm --process-queue --use-rlm-threshold 50

    # Force RLM processing for all documents (regardless of page count)
    python manage.py process_document_rlm --url "..." --company "..." --force-rlm
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from core.models import Company, Document, DocumentProcessingJob
from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from mcp_servers.rlm_processor import RLMProcessor, DecompositionStrategy
import json


class Command(BaseCommand):
    help = 'Process NI 43-101 documents using Recursive Language Model (RLM) approach'

    def add_arguments(self, parser):
        # Single document processing
        parser.add_argument(
            '--url',
            type=str,
            help='URL of the PDF document to process'
        )
        parser.add_argument(
            '--company',
            type=str,
            help='Company name or ticker symbol'
        )
        parser.add_argument(
            '--project',
            type=str,
            help='Project name (optional)'
        )

        # RLM options
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['hybrid', 'section', 'page', 'semantic'],
            default='hybrid',
            help='Decomposition strategy (default: hybrid)'
        )
        parser.add_argument(
            '--no-validate',
            action='store_true',
            help='Skip validation pass'
        )
        parser.add_argument(
            '--force-rlm',
            action='store_true',
            help='Force RLM processing regardless of document length'
        )

        # Queue processing
        parser.add_argument(
            '--process-queue',
            action='store_true',
            help='Process pending DocumentProcessingJobs with RLM'
        )
        parser.add_argument(
            '--use-rlm-threshold',
            type=int,
            default=50,
            help='Use RLM for documents with more than N pages (default: 50)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of jobs to process'
        )

        # Output options
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing logs'
        )

    def handle(self, *args, **options):
        """Main command handler"""

        if options['process_queue']:
            self._process_queue(options)
        elif options['url'] and options['company']:
            self._process_single_document(options)
        else:
            raise CommandError('Must specify either --url and --company, or --process-queue')

    def _process_single_document(self, options):
        """Process a single document with RLM"""

        url = options['url']
        company_name = options['company']
        project_name = options.get('project')
        strategy = options['strategy']
        validate = not options['no_validate']

        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*80}'))
        self.stdout.write(self.style.HTTP_INFO('RLM Document Processing'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*80}'))
        self.stdout.write(f'URL: {url}')
        self.stdout.write(f'Company: {company_name}')
        self.stdout.write(f'Strategy: {strategy}')
        self.stdout.write(f'Validation: {"enabled" if validate else "disabled"}')
        self.stdout.write('')

        # Process with RLM
        processor = HybridDocumentProcessor()

        if options['force_rlm']:
            # Force RLM processing
            result = processor._process_ni43101_rlm(
                document_url=url,
                company_name=company_name,
                project_name=project_name,
                decomposition_strategy=strategy,
                validate=validate
            )
        else:
            # Let the hybrid processor decide (will use RLM for long docs)
            result = processor._process_ni43101_hybrid(
                document_url=url,
                company_name=company_name,
                project_name=project_name
            )

        # Output results
        if options['json']:
            self.stdout.write(json.dumps(result, indent=2, default=str))
        else:
            self._display_result(result)

    def _process_queue(self, options):
        """Process pending jobs with RLM"""

        threshold = options['use_rlm_threshold']
        limit = options.get('limit')

        pending_jobs = DocumentProcessingJob.objects.filter(
            status='pending',
            document_type='ni43101'
        ).order_by('created_at')

        if limit:
            pending_jobs = pending_jobs[:limit]

        total = pending_jobs.count()
        self.stdout.write(self.style.HTTP_INFO(f'\nFound {total} pending NI 43-101 jobs'))

        if total == 0:
            return

        processor = HybridDocumentProcessor()
        processed = 0
        succeeded = 0
        failed = 0

        for job in pending_jobs:
            self.stdout.write(self.style.HTTP_INFO(f'\n{"="*80}'))
            self.stdout.write(f'Processing job {processed + 1}/{total}: {job.company_name}')
            self.stdout.write(f'URL: {job.url[:60]}...')

            try:
                # Update job status
                job.status = 'processing'
                job.started_at = datetime.now()
                job.save()

                # Process with RLM (threshold is handled in hybrid processor)
                result = processor._process_ni43101_rlm(
                    document_url=job.url,
                    company_name=job.company_name,
                    project_name=job.project_name,
                    decomposition_strategy=options['strategy'],
                    validate=not options['no_validate']
                )

                if result.get('success'):
                    job.status = 'completed'
                    job.document_id = result.get('document_id')
                    job.resources_created = result.get('processing_stats', {}).get('resources_stored', 0)
                    job.chunks_created = result.get('processing_stats', {}).get('document_chunks_stored', 0)
                    succeeded += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Success: {result.get("message")}'))
                else:
                    job.status = 'failed'
                    job.error_message = result.get('error', 'Unknown error')
                    failed += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: {result.get("error")}'))

            except Exception as e:
                job.status = 'failed'
                job.error_message = str(e)
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Exception: {str(e)}'))

            finally:
                job.completed_at = datetime.now()
                if job.started_at:
                    job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
                job.save()
                processed += 1

        # Summary
        self.stdout.write(self.style.HTTP_INFO(f'\n{"="*80}'))
        self.stdout.write(self.style.HTTP_INFO('PROCESSING COMPLETE'))
        self.stdout.write(self.style.HTTP_INFO(f'{"="*80}'))
        self.stdout.write(f'Total processed: {processed}')
        self.stdout.write(self.style.SUCCESS(f'Succeeded: {succeeded}'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed}'))

    def _display_result(self, result):
        """Display processing result in human-readable format"""

        if result.get('error'):
            self.stdout.write(self.style.ERROR(f'\n✗ Processing failed: {result["error"]}'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n✓ {result.get("message", "Processing complete")}'))
        self.stdout.write('')

        # Document info
        self.stdout.write(self.style.HTTP_INFO('Document Info:'))
        self.stdout.write(f'  Document ID: {result.get("document_id")}')
        self.stdout.write(f'  Company: {result.get("company")}')
        self.stdout.write(f'  Project: {result.get("project") or "N/A"}')
        self.stdout.write(f'  Method: {result.get("method")}')

        # RLM stats
        rlm_stats = result.get('rlm_stats', {})
        if rlm_stats:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('RLM Processing Stats:'))
            self.stdout.write(f'  Chunks processed: {rlm_stats.get("chunks_processed", "N/A")}')
            self.stdout.write(f'  Successful extractions: {rlm_stats.get("successful_extractions", "N/A")}')
            self.stdout.write(f'  Processing time: {rlm_stats.get("processing_time_seconds", 0):.1f}s')
            self.stdout.write(f'  Validation passed: {rlm_stats.get("validation_passed", "N/A")}')
            self.stdout.write(f'  Strategy: {rlm_stats.get("decomposition_strategy", "N/A")}')

        # Processing stats
        stats = result.get('processing_stats', {})
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Processing Stats:'))
        self.stdout.write(f'  Pages processed: {stats.get("pages_processed", "N/A")}')
        self.stdout.write(f'  Tables extracted: {stats.get("tables_extracted", "N/A")}')
        self.stdout.write(f'  Resources stored: {stats.get("resources_stored", 0)}')
        self.stdout.write(f'  Economic study: {"Yes" if stats.get("economic_study_stored") else "No"}')
        self.stdout.write(f'  RAG chunks: {stats.get("document_chunks_stored", 0)}')

        # Key findings
        extracted = result.get('extracted_data', {})
        findings = extracted.get('key_findings', {})
        if findings.get('highlights'):
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('Key Highlights:'))
            for highlight in findings['highlights'][:5]:
                self.stdout.write(f'  • {highlight[:100]}...' if len(highlight) > 100 else f'  • {highlight}')

        # Resources summary
        if extracted.get('resources_summary'):
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('Resources:'))
            self.stdout.write(f'  {extracted["resources_summary"]}')


# Import datetime for queue processing
from datetime import datetime
