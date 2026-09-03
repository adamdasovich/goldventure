"""
Superuser view of the GPU document-processing queue.

Documents reach this queue from three places: the technical-report hunter
(which can auto-queue a high-confidence match), the flag-review page, and the
weekly auto-discovery crawl. Everything in it is destined for a GPU droplet at
roughly $1.57/hr, and a large NI 43-101 runs about half an hour, so a wrong
document is both a cost and a pollutant — its chunks land in ChromaDB and the
mining assistant answers from them.

This gives a superuser the queue, what put each job there, and a way to reject
anything that does not belong before the GPU picks it up. Both the orchestrator
and the worker select strictly on status='pending', so cancelling is enough to
keep a job from ever being claimed.
"""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Jobs that have not been touched by the GPU yet. Only these can be cancelled —
# once the worker has claimed a job it is already burning GPU time, and marking
# the row would not call it back.
CANCELLABLE_STATUSES = {'pending'}

# Job types that are technical reports. The queue defaults to these because the
# table also holds every news-release PDF and corporate presentation the
# platform has ever processed — 2,449 and 506 completed rows respectively — and
# those swamp the handful of technical reports this review exists for.
TECHNICAL_JOB_TYPES = ['ni43101', 'pea', 'technical_report']

SOURCE_CHOICES = ('technical', 'flags', 'all')


def apply_source(qs, source):
    """
    Narrow a job queryset to what the reviewer means by "the queue".

    'technical' (default) — NI 43-101 / PEA / technical report jobs, whatever
        queued them. Stable regardless of how a job got here.
    'flags' — only jobs still linked to a technical-report flag. Narrower, and
        deliberately not the default: a flag reopened after review clears its
        processing_job link, so its job drops out of this view even though the
        document is still queued and still valid.
    'all' — the entire processing table, including news releases and
        presentations.
    """
    if source == 'flags':
        return qs.filter(source_report_flags__isnull=False).distinct()
    if source == 'all':
        return qs
    return qs.filter(document_type__in=TECHNICAL_JOB_TYPES)


class DocumentQueueViewSet(viewsets.ViewSet):
    """Superuser-only queue management for DocumentProcessingJob."""

    permission_classes = [IsAuthenticated]

    def _denied(self):
        return Response(
            {'error': 'Superuser access required'},
            status=status.HTTP_403_FORBIDDEN,
        )

    def _serialize(self, job):
        """One job plus the provenance a reviewer needs to judge it."""
        # A job auto-queued by the hunter carries its score and reasoning in the
        # originating flag's review notes. Showing that is the difference
        # between "cancel this?" and "cancel this, it scored 72 on a partial
        # project match".
        source = job.source_report_flags.first()
        source_info = None
        if source:
            news = source.news_release
            source_info = {
                'flag_id': source.id,
                'news_title': news.title,
                'news_url': news.url,
                'news_date': news.release_date,
                'project_name': source.project_name,
                'document_category': source.document_category,
                'hunt_status': source.hunt_status,
                'review_notes': source.review_notes,
                'auto_queued': source.reviewed_by_id is None and source.hunt_status == 'auto_queued',
            }

        document = None
        if job.document_id:
            doc = getattr(job, 'document', None)
            if doc:
                document = {'id': doc.id, 'title': doc.title,
                            'document_type': doc.document_type}

        return {
            'id': job.id,
            'url': job.url,
            'document_type': job.document_type,
            'company_name': job.company_name,
            'project_name': job.project_name,
            'status': job.status,
            'progress_message': job.progress_message,
            'error_message': job.error_message,
            'chunks_created': job.chunks_created,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'created_by': job.created_by.username if job.created_by_id else None,
            'source_flag': source_info,
            'document': document,
        }

    def list(self, request):
        """
        Queue listing. `status` filters (default 'pending'); `limit` caps rows.

        Pending is the default because it is the only actionable state — those
        are the jobs a superuser can still stop.
        """
        if not request.user.is_superuser:
            return self._denied()

        from core.models import DocumentProcessingJob

        qs = DocumentProcessingJob.objects.all().select_related(
            'document', 'created_by'
        ).prefetch_related('source_report_flags__news_release')

        source = request.query_params.get('source', 'technical')
        if source not in SOURCE_CHOICES:
            source = 'technical'
        qs = apply_source(qs, source)

        status_filter = request.query_params.get('status', 'pending')
        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)

        try:
            limit = min(int(request.query_params.get('limit', 100)), 500)
        except (TypeError, ValueError):
            limit = 100

        # Pending ascending: oldest first is the order the worker will claim
        # them, so the reviewer sees what is about to run next. Everything else
        # newest first, which is how completed and failed work get reviewed.
        qs = qs.order_by('created_at' if status_filter == 'pending' else '-created_at')

        return Response([self._serialize(j) for j in qs[:limit]])

    @action(detail=False, methods=['get'], url_path='counts')
    def counts(self, request):
        """Job counts per status, for the queue header."""
        if not request.user.is_superuser:
            return self._denied()

        from django.db.models import Count

        from core.models import DocumentProcessingJob

        source = request.query_params.get('source', 'technical')
        if source not in SOURCE_CHOICES:
            source = 'technical'

        rows = apply_source(
            DocumentProcessingJob.objects.all(), source
        ).values('status').annotate(n=Count('id'))
        counts = {r['status']: r['n'] for r in rows}
        counts['total'] = sum(counts.values())
        counts['source'] = source
        return Response(counts)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Reject a queued job before the GPU claims it.

        If the job was auto-queued from a technical-report flag, the flag is
        returned to the review queue rather than left marked as processed —
        otherwise cancelling a wrong document would silently discard the flag
        and the report would never be found. The ranked candidates stay on the
        flag so the right one can be picked by hand.
        """
        if not request.user.is_superuser:
            return self._denied()

        from core.models import DocumentProcessingJob

        try:
            job = DocumentProcessingJob.objects.get(pk=pk)
        except DocumentProcessingJob.DoesNotExist:
            return Response({'error': 'Job not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if job.status not in CANCELLABLE_STATUSES:
            return Response(
                {'error': f"Cannot cancel a job with status '{job.status}'. "
                          "Only pending jobs can be cancelled — once the worker "
                          "has claimed a job it is already processing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = (request.data.get('reason') or '').strip()

        try:
            job.status = 'cancelled'
            job.error_message = (
                f"Cancelled by {request.user.username}"
                + (f": {reason}" if reason else '')
            )
            job.save(update_fields=['status', 'error_message'])

            released = []
            for flag in job.source_report_flags.all():
                flag.status = 'pending'
                flag.hunt_status = 'found' if flag.candidates else 'not_found'
                flag.processing_job = None
                flag.report_url = ''
                flag.report_type = ''
                flag.reviewed_by = None
                flag.reviewed_at = None
                flag.review_notes = (
                    f"Auto-queued document rejected by {request.user.username}"
                    + (f": {reason}" if reason else '')
                    + ". Returned to review with candidates intact."
                )
                flag.save(update_fields=[
                    'status', 'hunt_status', 'processing_job', 'report_url',
                    'report_type', 'reviewed_by', 'reviewed_at', 'review_notes',
                ])
                released.append(flag.id)

            logger.info(
                f"[QUEUE] Job {job.id} cancelled by {request.user.username}; "
                f"released flags: {released or 'none'}"
            )
            return Response({
                'message': 'Job cancelled',
                'job_id': job.id,
                'released_flag_ids': released,
            })
        except Exception as e:
            logger.error(f"[QUEUE] Failed to cancel job {pk}: {e}")
            return Response(
                {'error': 'Failed to cancel job. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
