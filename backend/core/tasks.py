"""
Background Tasks for Document Processing
Processes document queue jobs sequentially
"""

from datetime import datetime
from .models import DocumentProcessingJob
from mcp_servers.document_processor_hybrid import HybridDocumentProcessor


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

        else:
            # For other document types, use basic processing
            job.progress_message = f"Processing {job.get_document_type_display()}..."
            job.save()

            # TODO: Add support for other document types
            raise NotImplementedError(f"Document type {job.document_type} not yet supported")

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

            print(f"✓ Job {job.id} completed successfully")
            print(f"  - Document ID: {job.document_id}")
            print(f"  - Resources created: {job.resources_created}")
            print(f"  - Chunks created: {job.chunks_created}")
            print(f"  - Processing time: {job.duration_display}")

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

            print(f"✗ Job {job.id} failed: {error_msg}")

    except Exception as e:
        # Handle unexpected errors
        job.status = 'failed'
        job.error_message = f"Unexpected error: {str(e)}"
        job.completed_at = datetime.now()

        if job.started_at:
            duration = (job.completed_at - job.started_at).total_seconds()
            job.processing_time_seconds = int(duration)

        job.save()

        print(f"✗ Job {job.id} failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
