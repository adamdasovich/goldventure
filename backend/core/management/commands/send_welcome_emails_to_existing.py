"""
One-off backfill: grant the early-access free month and send the welcome email
to existing users who haven't received it yet.

Idempotent — only targets users whose ``welcome_email_sent_at`` is null, and
stamps each on success, so it's safe to re-run (e.g. after a partial failure).

Scope: all active users with an email address, except superusers (already
treated as top tier). Users who already hold a paid Stripe subscription still
receive the welcome email, but the free-month grant is skipped for them so we
never clobber a paying customer.

Usage:
    python manage.py send_welcome_emails_to_existing --dry-run
    python manage.py send_welcome_emails_to_existing
    python manage.py send_welcome_emails_to_existing --limit 50
    python manage.py send_welcome_emails_to_existing --no-grant
"""

import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import User
from core.welcome_service import deliver_welcome


class Command(BaseCommand):
    help = 'Send the welcome email (and grant a free month) to existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List who would receive the email without sending or granting',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Only process the first N eligible users',
        )
        parser.add_argument(
            '--no-grant',
            action='store_true',
            help='Send the welcome email only; do NOT grant the free month',
        )
        parser.add_argument(
            '--sleep',
            type=float,
            default=0.6,
            help='Seconds to pause between sends (SendGrid rate limiting)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        grant = not options['no_grant']
        sleep_s = options['sleep']

        qs = (
            User.objects
            .filter(is_active=True, welcome_email_sent_at__isnull=True)
            .exclude(is_superuser=True)
            .exclude(Q(email__isnull=True) | Q(email__exact=''))
            .order_by('id')
        )
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(
            f"{total} eligible user(s) "
            f"(active, has email, not yet welcomed, non-superuser)."
        )
        if grant:
            self.stdout.write(
                "Each will be granted a 1-month comp Prospector subscription "
                "(users with an existing paid subscription are skipped)."
            )

        if dry_run:
            for u in qs:
                self.stdout.write(f"  [dry-run] {u.id}  {u.email}")
            self.stdout.write(self.style.WARNING("Dry run — nothing sent."))
            return

        sent = 0
        failed = 0
        for u in qs.iterator():
            try:
                ok = deliver_welcome(u, grant_free_month=grant)
            except Exception as e:  # noqa: BLE001 — keep the batch going
                ok = False
                self.stderr.write(f"  ERROR {u.id} {u.email}: {e}")

            if ok:
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"  sent -> {u.email}"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  FAILED -> {u.email}"))

            if sleep_s:
                time.sleep(sleep_s)

        self.stdout.write(
            self.style.SUCCESS(f"Done. Sent: {sent}, failed: {failed}.")
        )
