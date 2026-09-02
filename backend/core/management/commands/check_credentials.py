"""
Run the external-credential liveness checks by hand.

    python manage.py check_credentials
    python manage.py check_credentials --only stripe,digitalocean
    python manage.py check_credentials --json
    python manage.py check_credentials --notify     # actually send the email

The scheduled version is core.tasks.check_credentials_task (weekly). This
command exists so the same checks can be run on demand -- after rotating a
credential, or when something is behaving oddly -- without waiting a week or
triggering an email.

Exits 1 if any check FAILED, so it can gate a deploy script the way
check_counts does.
"""
import json

from django.core.management.base import BaseCommand

from core.credential_checks import FAIL, format_report, run_checks, send_alert


class Command(BaseCommand):
    help = 'Verify every external credential still works (Stripe, Anthropic, Voyage, SendGrid, AWS, DigitalOcean, DB).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            help='Comma-separated subset, e.g. "stripe,digitalocean". '
                 'Names are the check function names without the "check_" prefix.',
        )
        parser.add_argument('--json', action='store_true', help='Emit JSON instead of a table.')
        parser.add_argument(
            '--notify', action='store_true',
            help='Send the failure email as the scheduled task would. Off by default so '
                 'manual runs do not spam the inbox.',
        )

    def handle(self, *args, **options):
        only = None
        if options.get('only'):
            only = {n.strip() for n in options['only'].split(',') if n.strip()}

        results = run_checks(only=only)
        failed = [r for r in results if r.failed]

        if options['json']:
            self.stdout.write(json.dumps({
                'checked': len(results),
                'failed': len(failed),
                'results': [{'name': r.name, 'status': r.status, 'detail': r.detail}
                            for r in results],
            }, indent=2))
        else:
            width = max([len(r.name) for r in results] + [10])
            for r in results:
                style = self.style.ERROR if r.failed else (
                    self.style.SUCCESS if r.status != 'skipped' else self.style.WARNING)
                self.stdout.write(style('  %-8s' % r.status) + ' %-*s %s' % (width, r.name, r.detail))
            self.stdout.write('')
            if failed:
                self.stdout.write(self.style.ERROR(
                    '  %d of %d FAILING' % (len(failed), len(results))))
            else:
                self.stdout.write(self.style.SUCCESS(
                    '  all %d checks passed' % len(results)))

        if failed and options['notify']:
            sent = send_alert(results)
            self.stdout.write('  alert email sent: %s' % sent)

        if failed:
            raise SystemExit(1)
