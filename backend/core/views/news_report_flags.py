"""
ViewSet for technical-report flags (NI 43-101 / PEA / PFS / DFS / MRE).

Mirrors the financing-flag flow in news_flags.py but parallel:
 - list pending/processed/dismissed flags (superuser-only)
 - submit a report PDF URL -> creates a DocumentProcessingJob (docling/GPU
   orchestrator picks it up automatically) and links it on the flag
 - dismiss as false positive (scoped under reason='report_false_positive'
   so it doesn't suppress financing-flag detection on the same URL)
 - proxy the linked DocumentProcessingJob status so the page can show progress
"""

import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..security_utils import is_safe_url

logger = logging.getLogger(__name__)


class NewsReportFlagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Superuser-only ViewSet for news releases flagged as potential
    technical reports (NI 43-101 / PEA / PFS / DFS / MRE / etc.).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None
    queryset = None

    def get_queryset(self):
        from core.models import NewsReportFlag

        if not self.request.user.is_superuser:
            return NewsReportFlag.objects.none()

        qs = NewsReportFlag.objects.all().select_related(
            'news_release__company',
            'reviewed_by',
            'processing_job',
        )

        # status filter only applies to list; detail actions must reach any row
        if self.action == 'list':
            status_filter = self.request.query_params.get('status', 'pending')
            if status_filter:
                qs = qs.filter(status=status_filter)

        return qs

    def list(self, request, *args, **kwargs):
        flags = self.get_queryset()
        data = []
        for flag in flags:
            company = flag.news_release.company
            job = flag.processing_job
            data.append({
                'id': flag.id,
                'company_id': company.id,
                'company_name': company.name,
                'company_website': company.website or '',
                'news_release_id': flag.news_release.id,
                'news_title': flag.news_release.title,
                'news_url': flag.news_release.url,
                'news_date': flag.news_release.release_date,
                'detected_keywords': flag.detected_keywords,
                'status': flag.status,
                'flagged_at': flag.flagged_at,
                'reviewed_by': flag.reviewed_by.username if flag.reviewed_by else None,
                'reviewed_at': flag.reviewed_at,
                'review_notes': flag.review_notes,
                'report_url': flag.report_url,
                'report_type': flag.report_type,
                # Automated hunt for the actual report document. The flag points
                # at the announcement; these are the candidates found on the
                # company's site, ranked, so review is a click rather than a
                # manual search. See mcp_servers/report_hunter.py.
                'document_category': flag.document_category,
                'project_name': flag.project_name,
                'hunt_status': flag.hunt_status,
                'hunt_attempts': flag.hunt_attempts,
                'last_hunt_at': flag.last_hunt_at,
                'next_hunt_at': flag.next_hunt_at,
                'expected_filing_by': flag.expected_filing_by,
                'candidates': flag.candidates or [],
                'processing_job': {
                    'id': job.id,
                    'status': job.status,
                    'document_type': job.document_type,
                    'progress_message': job.progress_message,
                    'error_message': job.error_message,
                    'chunks_created': job.chunks_created,
                    'created_at': job.created_at,
                    'completed_at': job.completed_at,
                } if job else None,
            })
        return Response(data)

    @action(detail=True, methods=['post'], url_path='process-report')
    def process_report(self, request, pk=None):
        """
        Body: { report_url: str, report_type: 'ni43101'|'pea'|'pfs'|'dfs'|'mre'|'other',
                notes?: str }

        Creates a DocumentProcessingJob (picked up by the GPU orchestrator on its
        next poll) and links it to the flag. NI 43-101 / PEA / PFS / DFS map to
        the heavy-job types the orchestrator already handles; MRE / other map to
        'ni43101' so they go through the same docling pipeline.
        """
        from core.models import NewsReportFlag, DocumentProcessingJob

        flag = self.get_object()
        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from mcp_servers.report_hunter import canonical_document_url
        # Canonical identity — cache-buster params (?v=...) change per page
        # render; keying jobs on the raw URL ingested the same PDF repeatedly.
        report_url = canonical_document_url((request.data.get('report_url') or '').strip())
        report_type = (request.data.get('report_type') or '').strip()
        notes = request.data.get('notes', 'Submitted for docling processing from news flag')

        if not report_url:
            return Response({'error': 'report_url is required'}, status=status.HTTP_400_BAD_REQUEST)
        safe, safe_reason = is_safe_url(report_url)
        if not safe:
            return Response(
                {'error': f'report_url rejected by SSRF check: {safe_reason}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_report_types = {choice[0] for choice in NewsReportFlag.REPORT_TYPE_CHOICES}
        if report_type not in valid_report_types:
            return Response(
                {'error': f'report_type must be one of {sorted(valid_report_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Map our report_type -> DocumentProcessingJob.document_type. The GPU
        # orchestrator's HEAVY_JOB_TYPES already covers 'ni43101' and 'pea'; the
        # remaining types fall back to 'ni43101' so they share the same docling
        # pipeline (it's a generic technical-report processor).
        doc_type_map = {
            'ni43101': 'ni43101',
            'pea': 'pea',
            'pfs': 'ni43101',
            'dfs': 'ni43101',
            'mre': 'ni43101',
            'other': 'ni43101',
        }
        document_type = doc_type_map[report_type]

        try:
            # Reuse an existing pending/processing/completed job for the same
            # URL — avoids duplicate GPU work when the same report is submitted
            # twice.
            job, created = DocumentProcessingJob.objects.get_or_create(
                url=report_url,
                defaults={
                    'document_type': document_type,
                    'company_name': flag.news_release.company.name,
                    'status': 'pending',
                    'created_by': request.user,
                },
            )
            # A failed or cancelled job for this URL is dead: nothing retries a
            # terminal failure, and linking the flag to it would mark the flag
            # processed while no document ever arrives. The reviewer just
            # explicitly asked for this URL, so revive the job rather than
            # silently attaching a corpse.
            if not created and job.status in ('failed', 'cancelled'):
                previous_status = job.status
                job.status = 'pending'
                job.document_type = document_type
                job.error_message = ''
                job.retry_count = 0
                job.progress_message = (
                    f'Resubmitted by {request.user.username} from flag review '
                    f'(was {previous_status})'
                )
                job.started_at = None
                job.completed_at = None
                job.save(update_fields=[
                    'status', 'document_type', 'error_message', 'retry_count',
                    'progress_message', 'started_at', 'completed_at',
                ])

            flag.mark_as_processed(
                reviewer=request.user,
                job=job,
                report_url=report_url,
                report_type=report_type,
                notes=notes,
            )

            return Response({
                'message': 'Report submitted for processing',
                'flag_id': flag.id,
                'processing_job_id': job.id,
                'job_status': job.status,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error submitting report for flag {flag.id}: {e}")
            return Response(
                {'error': 'Failed to submit report. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss_flag(self, request, pk=None):
        from core.models import NewsReportFlag  # noqa: F401

        flag = self.get_object()
        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', 'Dismissed as false positive (report)')

        try:
            flag.dismiss_as_false_positive(reviewer=request.user, notes=notes)
            return Response(
                {'message': 'Flag dismissed successfully', 'flag_id': flag.id},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error dismissing report-flag {flag.id}: {e}")
            return Response(
                {'error': 'Failed to dismiss flag. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='job-status')
    def job_status(self, request, pk=None):
        """
        Lightweight proxy for the linked DocumentProcessingJob so the admin page
        can poll progress without hitting a separate endpoint.
        """
        flag = self.get_object()
        job = flag.processing_job
        if not job:
            return Response({'status': None, 'detail': 'No processing job linked yet'})
        return Response({
            'id': job.id,
            'status': job.status,
            'progress_message': job.progress_message,
            'error_message': job.error_message,
            'chunks_created': job.chunks_created,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
        })
