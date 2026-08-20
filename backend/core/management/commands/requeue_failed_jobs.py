"""
Requeue document jobs whose failure cause has since been fixed.

Of 1,036 failed DocumentProcessingJob rows, 934 failed for reasons that no
longer exist:

  646  "not in allowlist"        — api.investi.com.au and regional S3/CloudFront
                                   hosts were missing from the GPU worker's
                                   allowlist.
  165  "private IP address"      — is_private_ip() swallowed a ValueError and
                                   returned True, so every hostname it could
                                   not resolve was reported as private.
   98  "stuck in processing"     — the stuck-job threshold was 15 minutes,
                                   which killed 300-page NI 43-101s mid-convert.
                                   It is now 90.
   25  "value too long"          — documents.file_url was varchar(200) and SEDAR
                                   links routinely exceed it. It is now 500.

The rest failed on HTTP 4xx/5xx, Docling errors or download timeouts, which are
properties of the source rather than bugs here, so they are left alone.

Requeue in batches. The queue drives on-demand GPU droplets at $1.57/h, and a
worker fault discovered after 900 jobs is expensive.

Usage:
    python manage.py requeue_failed_jobs --dry-run
    python manage.py requeue_failed_jobs --limit 20
    python manage.py requeue_failed_jobs
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import DocumentProcessingJob

FIXED_CAUSES = re.compile(
    r'not in allowlist'
    r'|private IP address'
    r'|stuck in processing'
    r'|value too long for type',
    re.I,
)


class Command(BaseCommand):
    help = "Reset failed document jobs whose cause has been fixed back to pending."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0,
                            help="Requeue at most this many. 0 = all.")

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']

        failed = DocumentProcessingJob.objects.filter(status='failed').order_by('id')
        targets = [j for j in failed if FIXED_CAUSES.search(j.error_message or '')]

        if opts['limit']:
            targets = targets[:opts['limit']]

        by_type = {}
        for job in targets:
            by_type[job.document_type or '?'] = by_type.get(job.document_type or '?', 0) + 1

        self.stdout.write(f"{len(targets)} job(s) to requeue")
        for doc_type, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
            self.stdout.write(f"  {doc_type:<18s} {n}")

        already_pending = DocumentProcessingJob.objects.filter(
            status__in=['pending', 'processing']).count()
        if already_pending:
            self.stdout.write(self.style.WARNING(
                f"\n{already_pending} job(s) already pending/processing — "
                f"a droplet may be running"))

        if dry_run:
            self.stdout.write(self.style.NOTICE('\nDry run — nothing written.'))
            return

        with transaction.atomic():
            DocumentProcessingJob.objects.filter(id__in=[j.id for j in targets]).update(
                status='pending',
                error_message='',
                progress_message='Requeued after upstream fixes',
                started_at=None,
                completed_at=None,
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n{len(targets)} job(s) requeued. The orchestrator polls every 60s "
            f"and will create a GPU droplet at $1.57/h."
        ))
