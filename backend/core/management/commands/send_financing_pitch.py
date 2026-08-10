"""
Send the Weekly Financing Roundup outreach pitch via SendGrid.

Reusable digital-PR tool: the "this week" line is pulled automatically from the
latest completed WeeklyIndustryReport, so you can re-run it each week with a
fresh figure and no editing. Plain-text (reads personal, best deliverability),
Reply-To set to a monitored inbox, each recipient sent separately.

Examples:
    # Dry run against a recipients file (prints, sends nothing)
    python manage.py send_financing_pitch --recipients-file outreach.json --dry-run

    # Send to a couple of inboxes with a generic greeting
    python manage.py send_financing_pitch --to tips@example.com,news@example.com

recipients-file format (JSON):
    [
      {"email": "tnm@northernminer.com", "greeting": "Hi Northern Miner team",
       "outlet": "the Northern Miner desk"}
    ]
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

FROM_ADDRESS = "noreply@juniorminingintelligence.com"
FROM_NAME = "Adam Dasovich · Junior Mining Intelligence"
REPLY_TO = "info@juniorminingintelligence.com"
SUBJECT = "Weekly junior-mining financing data — free to use"
ROUNDUP_URL = "https://juniorminingintelligence.com/reports/financings"


def _format_usd(total: float) -> str:
    if total >= 1_000_000:
        return f"${total / 1_000_000:.1f}M"
    if total >= 1_000:
        return f"${total / 1_000:.0f}K"
    return f"${total:.0f}"


def _this_week_line() -> str:
    """Build the '13 financings totalling $72.9M, gold-led' line from the most
    recent completed weekly report. Falls back to a generic phrase."""
    from core.models import WeeklyIndustryReport

    report = (
        WeeklyIndustryReport.objects
        .filter(status="completed")
        .order_by("-week_ending")
        .first()
    )
    if not report:
        return "dozens of financings each week"
    fin = (report.data_snapshot or {}).get("financings") or {}
    count = fin.get("count", 0) or 0
    total = fin.get("total_amount_usd", 0) or 0
    by_commodity = fin.get("by_commodity") or []
    top = max(by_commodity, key=lambda c: c.get("amount_usd", 0), default=None)
    if not count:
        return "dozens of financings each week"
    led = f", {top['commodity']}-led" if top and top.get("commodity") else ""
    return f"{count} financings totalling {_format_usd(total)}{led}"


def _body(greeting: str, outlet: str, week_line: str) -> str:
    return f"""{greeting},

I run Junior Mining Intelligence, a platform that tracks junior mining companies and their financings. Each week we compile every private placement, bought deal, and flow-through raise announced across gold, silver, copper, lithium and critical minerals — with amounts, structures, and warrant terms.

I publish it as a free weekly roundup: {ROUNDUP_URL}

This week, for example: {week_line}.

If it's useful for your coverage, you're welcome to cite the figures or the roundup directly — no permission needed. And if you ever want the underlying data (by commodity, exchange, or date range) for a story, I'm glad to pull it for you.

Either way, thought it might be a handy reference for {outlet}.

Best,
Adam Dasovich
Junior Mining Intelligence
{REPLY_TO}
"""


def _get_api_key():
    key = getattr(settings, "EMAIL_HOST_PASSWORD", None)
    if not key:
        key = os.getenv("SENDGRID_API_KEY") or os.getenv("EMAIL_HOST_PASSWORD")
    return key


class Command(BaseCommand):
    help = "Send the Weekly Financing Roundup outreach pitch via SendGrid."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipients-file",
            type=str,
            help='Path to a JSON list of {"email","greeting","outlet"} objects.',
        )
        parser.add_argument(
            "--to",
            type=str,
            help="Comma-separated emails (generic greeting/outlet).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be sent without sending.",
        )

    def _load_recipients(self, opts):
        recipients = []
        if opts.get("recipients_file"):
            with open(opts["recipients_file"], "r", encoding="utf-8") as fh:
                for r in json.load(fh):
                    recipients.append(
                        {
                            "email": r["email"],
                            "greeting": r.get("greeting", "Hi there"),
                            "outlet": r.get("outlet", "your desk"),
                        }
                    )
        if opts.get("to"):
            for email in [e.strip() for e in opts["to"].split(",") if e.strip()]:
                recipients.append(
                    {"email": email, "greeting": "Hi there", "outlet": "your desk"}
                )
        return recipients

    def handle(self, *args, **opts):
        recipients = self._load_recipients(opts)
        if not recipients:
            self.stderr.write("No recipients. Use --recipients-file or --to.")
            return

        week_line = _this_week_line()
        dry = opts["dry_run"]

        self.stdout.write(f"From:     {FROM_NAME} <{FROM_ADDRESS}>")
        self.stdout.write(f"Reply-To: {REPLY_TO}")
        self.stdout.write(f"Subject:  {SUBJECT}")
        self.stdout.write(f"Week:     {week_line}")
        self.stdout.write("DRY RUN — nothing sent\n" if dry else "SENDING\n")

        if not dry:
            key = _get_api_key()
            if not key or not key.startswith("SG."):
                self.stderr.write("SendGrid API key missing/invalid. Aborting.")
                return
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo

            sg = SendGridAPIClient(key)

        for r in recipients:
            body = _body(r["greeting"], r["outlet"], week_line)
            if dry:
                self.stdout.write(f"--- would send to {r['email']} ---")
                self.stdout.write(body)
                continue
            try:
                message = Mail(
                    from_email=Email(FROM_ADDRESS, FROM_NAME),
                    to_emails=To(r["email"]),
                    subject=SUBJECT,
                    plain_text_content=Content("text/plain", body),
                )
                message.reply_to = ReplyTo(REPLY_TO)
                resp = sg.send(message)
                self.stdout.write(f"SENT  -> {r['email']}  status={resp.status_code}")
            except Exception as e:  # noqa: BLE001
                self.stderr.write(f"FAIL  -> {r['email']}  error={e}")
