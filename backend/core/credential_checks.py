"""
Liveness checks for every external credential the platform depends on.

WHY THIS EXISTS
---------------
Every credential here fails *silently*. Nothing 500s, no page breaks, and no
user complains -- the platform just quietly stops doing one of its jobs:

  * DO_API_TOKEN expires   -> the GPU orchestrator polls, gets 401s into a log
                              nobody reads, and document processing simply never
                              produces a droplet.
  * ANTHROPIC_API_KEY dies -> _generate_ai_briefing() catches every exception and
                              returns None, so paying subscribers silently drop
                              to the templated briefing forever.
  * the SendGrid key dies  -> EmailService.is_configured() only checks the 'SG.'
                              prefix, so it keeps reporting healthy while no mail
                              is delivered.
  * a Stripe webhook       -> Stripe logs delivery failures on its side; the app
    endpoint goes missing     sees nothing at all. On 2026-09-01 the store
                              endpoint was found unregistered: a customer could
                              be charged and no order was ever created.

Each check is cheap enough to run weekly and deliberately isolated: one broken
credential must not stop the others being tested. A credential that is not
configured at all reports 'skipped', not 'FAIL' -- absence is a deployment
choice, a dead value is a fault.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger('celery.credential_checks')

OK, FAIL, SKIP = 'ok', 'FAIL', 'skipped'
TIMEOUT = 20


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == FAIL


def _get(url, headers):
    """GET returning (status_code, body_bytes) without raising on 4xx/5xx."""
    req = urllib.request.Request(url, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=TIMEOUT)
        return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# --------------------------------------------------------------------------
# individual checks -- each returns a CheckResult and never raises
# --------------------------------------------------------------------------

def check_stripe():
    from core.api_utils import get_stripe_api_key
    key = get_stripe_api_key()
    if not key:
        return CheckResult('stripe', SKIP, 'not configured')
    try:
        import stripe
        stripe.api_key = key
        acct = stripe.Account.retrieve()
        if not acct.charges_enabled:
            return CheckResult('stripe', FAIL,
                               'authenticates but charges_enabled is False on %s' % acct.id)
        return CheckResult('stripe', OK, 'account %s, charges enabled' % acct.id)
    except Exception as e:
        return CheckResult('stripe', FAIL, '%s: %s' % (type(e).__name__, str(e)[:160]))


# Each configured signing secret needs a live endpoint in Stripe, or the events
# it guards are never delivered. This pairing is exactly what was missing for
# the store on 2026-09-01.
WEBHOOK_ENDPOINTS = (
    ('STRIPE_PLATFORM_WEBHOOK_SECRET', '/api/platform/webhooks/stripe/'),
    ('STRIPE_COMPANY_WEBHOOK_SECRET', '/api/company/webhooks/stripe/'),
    ('STRIPE_STORE_WEBHOOK_SECRET', '/api/store/webhook/'),
)


def check_stripe_webhooks():
    from core.api_utils import get_stripe_api_key
    if not get_stripe_api_key():
        return CheckResult('stripe_webhooks', SKIP, 'stripe not configured')
    try:
        import stripe
        stripe.api_key = get_stripe_api_key()
        live = {e.url: e.status
                for e in stripe.WebhookEndpoint.list(limit=100).auto_paging_iter()}
    except Exception as e:
        return CheckResult('stripe_webhooks', FAIL,
                           'could not list endpoints: %s' % str(e)[:140])

    problems = []
    checked = 0
    for setting_name, path in WEBHOOK_ENDPOINTS:
        if not getattr(settings, setting_name, ''):
            continue
        checked += 1
        matches = [(u, s) for u, s in live.items() if u.endswith(path)]
        if not matches:
            problems.append('%s is set but NO endpoint is registered for %s'
                            % (setting_name, path))
        elif not any(s == 'enabled' for _, s in matches):
            problems.append('%s endpoint exists but is disabled (%s)'
                            % (setting_name, path))

    if problems:
        return CheckResult('stripe_webhooks', FAIL, '; '.join(problems))
    return CheckResult('stripe_webhooks', OK,
                       '%d configured secret(s) each have an enabled endpoint' % checked)


def check_anthropic():
    key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not key:
        return CheckResult('anthropic', SKIP, 'not configured')
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        # max_tokens=1 keeps this to a fraction of a cent per week.
        client.messages.create(model='claude-haiku-4-5', max_tokens=1,
                               messages=[{'role': 'user', 'content': 'hi'}])
        return CheckResult('anthropic', OK, 'completion returned')
    except Exception as e:
        return CheckResult('anthropic', FAIL, '%s: %s' % (type(e).__name__, str(e)[:160]))


def check_voyage():
    try:
        from mcp_servers.embeddings import _voyage_api_key, VoyageEmbeddingFunction
    except Exception as e:
        return CheckResult('voyage', SKIP, 'embeddings module unavailable: %s' % str(e)[:100])
    if not _voyage_api_key():
        return CheckResult('voyage', SKIP, 'not configured')
    try:
        vec = VoyageEmbeddingFunction()(['credential check'])
        first = vec[0] if isinstance(vec, list) else vec
        return CheckResult('voyage', OK, '%d-dim embedding returned' % len(first))
    except Exception as e:
        return CheckResult('voyage', FAIL, '%s: %s' % (type(e).__name__, str(e)[:160]))


def check_sendgrid():
    """
    Authenticate against SendGrid rather than trusting is_configured(), which
    only checks that the value starts with 'SG.' and therefore keeps reporting
    healthy for a revoked key.
    """
    from core.email_service import _get_sendgrid_api_key
    key = _get_sendgrid_api_key()
    if not key:
        return CheckResult('sendgrid', SKIP, 'not configured')
    code, body = _get('https://api.sendgrid.com/v3/scopes',
                      {'Authorization': 'Bearer ' + key})
    if code != 200:
        return CheckResult('sendgrid', FAIL, 'HTTP %s from /v3/scopes' % code)
    try:
        scopes = json.loads(body).get('scopes', [])
    except Exception:
        return CheckResult('sendgrid', FAIL, 'unparseable /v3/scopes response')
    if 'mail.send' not in scopes:
        return CheckResult('sendgrid', FAIL,
                           'authenticates but lacks mail.send -- no email can be delivered')
    return CheckResult('sendgrid', OK, 'mail.send granted (%d scopes)' % len(scopes))


def check_aws():
    kid = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
    sec = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
    if not (kid and sec):
        return CheckResult('aws', SKIP, 'not configured')
    try:
        import boto3
        region = getattr(settings, 'AWS_S3_REGION_NAME', '') or 'us-east-1'
        who = boto3.client('sts', aws_access_key_id=kid, aws_secret_access_key=sec,
                           region_name=region).get_caller_identity()
        return CheckResult('aws', OK, who['Arn'].split('/')[-1])
    except Exception as e:
        return CheckResult('aws', FAIL, '%s: %s' % (type(e).__name__, str(e)[:160]))


def _read_do_token():
    """
    DO_API_TOKEN is read from os.environ by gpu_orchestrator.py, a standalone
    service -- it is NOT a Django setting. config/celery.py also scrubs it from
    the worker environment so browser subprocesses cannot inherit it, so inside
    a Celery worker os.environ will not have it either. Fall back to the files.
    """
    token = os.environ.get('DO_API_TOKEN', '')
    if token:
        return token
    for path in ('/var/www/goldventure/backend/gpu_orchestrator.env',
                 '/var/www/goldventure/backend/.env'):
        try:
            with open(path, encoding='utf-8') as fh:
                for line in fh:
                    if line.startswith('DO_API_TOKEN='):
                        token = line.split('=', 1)[1].strip()
        except OSError:
            continue
        if token:
            return token
    return ''


def check_digitalocean():
    """
    /v2/droplets is deliberate: it sits inside the token's custom scopes.
    /v2/account does NOT, and returns 403 on a perfectly healthy token.
    """
    token = _read_do_token()
    if not token:
        return CheckResult('digitalocean', SKIP, 'not configured')
    code, body = _get('https://api.digitalocean.com/v2/droplets?per_page=1',
                      {'Authorization': 'Bearer ' + token})
    if code == 401:
        return CheckResult('digitalocean', FAIL,
                           'HTTP 401 -- token expired or revoked. GPU document '
                           'processing will not run until it is replaced.')
    if code != 200:
        return CheckResult('digitalocean', FAIL, 'HTTP %s from /v2/droplets' % code)
    try:
        total = json.loads(body).get('meta', {}).get('total', '?')
    except Exception:
        total = '?'
    return CheckResult('digitalocean', OK, 'droplets readable (total=%s)' % total)


def check_database():
    try:
        from django.db import connection
        from core.models import Company
        connection.close()   # force a fresh connect, so a stale password shows up
        n = Company.objects.filter(is_deleted=False).count()
        return CheckResult('database', OK, '%d companies on a fresh connection' % n)
    except Exception as e:
        return CheckResult('database', FAIL, '%s: %s' % (type(e).__name__, str(e)[:160]))


CHECKS = (
    check_database,
    check_stripe,
    check_stripe_webhooks,
    check_anthropic,
    check_voyage,
    check_sendgrid,
    check_aws,
    check_digitalocean,
)


def run_checks(only=None):
    results = []
    for fn in CHECKS:
        name = fn.__name__.replace('check_', '')
        if only and name not in only:
            continue
        try:
            results.append(fn())
        except Exception as e:
            # A check itself blowing up is a fault worth reporting, not a crash.
            results.append(CheckResult(
                name, FAIL, 'check raised %s: %s' % (type(e).__name__, str(e)[:140])))
    return results


def format_report(results):
    failed = [r for r in results if r.failed]
    subject = ('[JMI] %d credential check(s) FAILING' % len(failed)) if failed \
        else '[JMI] all credential checks passed'
    width = max([len(r.name) for r in results] + [10])
    lines = ['%-8s %-*s %s' % (r.status, width, r.name, r.detail) for r in results]
    body = '\n'.join(lines)
    if failed:
        body += ('\n\nThese fail silently in normal operation -- nothing errors and no '
                 'user reports it, which is why this check exists. Rotate or '
                 're-register the affected credential with '
                 'backend/scripts/rotate_env_secret.sh.')
    return subject, body


def alert_recipient():
    """
    ADMIN_EMAIL defaults to the placeholder 'admin@example.com' and has never
    been set in production, so anything addressed there is silently discarded.
    Prefer an explicitly configured address and skip placeholder domains.
    """
    for name in ('CREDENTIAL_ALERT_EMAIL', 'ADMIN_EMAIL', 'EDITOR_NOTIFICATION_EMAIL'):
        value = (getattr(settings, name, '') or '').strip()
        if value and not value.lower().endswith(('@example.com', '@example.org')):
            return value
    return ''


def send_alert(results):
    """
    Email the failures. Returns False if it could not send -- including the case
    where SendGrid itself is the broken credential, which is logged loudly,
    because no email can report that email is down.
    """
    failed = [r for r in results if r.failed]
    if not failed:
        return False
    subject, body = format_report(results)
    to = alert_recipient()
    summary = '; '.join('%s: %s' % (r.name, r.detail) for r in failed)
    if not to:
        logger.error('Credential checks FAILING but no alert recipient is '
                     'configured: %s', summary)
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        from core.email_service import _get_sendgrid_api_key
        key = _get_sendgrid_api_key()
        if not key:
            raise RuntimeError('no SendGrid key configured')
        message = Mail(
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL',
                               'info@juniorminingintelligence.com'),
            to_emails=to,
            subject=subject,
            plain_text_content=body,
        )
        SendGridAPIClient(key).send(message)
        logger.warning('Credential check alert sent to %s: %s', to, subject)
        return True
    except Exception as e:
        logger.error('Credential checks FAILING and the alert could not be sent '
                     '(%s: %s). Failures: %s',
                     type(e).__name__, str(e)[:120], summary)
        return False
