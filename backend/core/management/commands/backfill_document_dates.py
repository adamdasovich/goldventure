"""
Recover real publication dates for documents stamped with their ingest date.

`ensure_document_record` in gpu_worker.py had no publication date to work from
and defaulted `document_date` to today, so 2,111 of 2,375 documents carry the
day they were scraped rather than the day they were published. That lie
propagates: extract_resources falls back to `document.document_date` for
`report_date`, so Almaden's 2015 PEA, 2017 PFS and 2019 FS all landed on the
same date. Grade Ranker cannot then tell which estimate supersedes which and
sums all three — 3.2 Moz against a real ~1.4 Moz — and Resource Growth, whose
entire purpose is plotting a resource through time, collapses to a single point.

The real dates are sitting in the titles: "NI43 101 IxtacaFS Oct 2019a",
"N43 101 Ixtaca PFS 17May2017", "Amended PEA November 9 2015 op". This parses
them out of the title, then the file URL, and only touches rows whose current
date equals their ingest date — a document with a genuine date is never
overwritten.

Month-only matches ("Oct 2019") are stored as the first of the month. That is
an approximation, but ordering reports correctly is the whole point and a
month is ample resolution for it; year-only matches are rejected as too coarse
to be worth asserting.

Usage:
    python manage.py backfill_document_dates --dry-run
    python manage.py backfill_document_dates
"""

import re
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q

from core.models import Document, EconomicStudy, ResourceEstimate

MONTHS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}
MONTH_RE = '|'.join(sorted(MONTHS, key=len, reverse=True))

# Ordered most-specific first: a title carrying a full date should never be
# read as the weaker month-only form.
#
# Digit guards, not word boundaries:  does not fire between a digit and a
# letter or after an underscore, so "Oct 2019a" and "report_20191015_final"
# both went unmatched.
#
# Digit guards rather than : word boundaries do not fire between a digit and
# a letter, so "Oct 2019a" and "report_20191015_final" both slipped through.
PATTERNS = [
    # 2019-10-15 / 2019_10_15 / 20191015
    (re.compile(r'(?<!\d)(19|20)(\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?!\d)'),
     lambda m: (int(m.group(1) + m.group(2)), int(m.group(3)), int(m.group(4)))),
    # 17May2017 / 17 May 2017 / 9 November, 2015
    (re.compile(r'(?<!\d)(\d{1,2})[\s\-_]*(' + MONTH_RE + r')[\s\-_,]*((?:19|20)\d{2})(?!\d)', re.I),
     lambda m: (int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))),
    # November 9 2015 / Oct 15, 2019
    (re.compile(r'\b(' + MONTH_RE + r')[\s\-_]*(\d{1,2})[\s\-_,]+((?:19|20)\d{2})(?!\d)', re.I),
     lambda m: (int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))),
    # Oct 2019 / October2019 — day unknown, take the first
    (re.compile(r'\b(' + MONTH_RE + r')[\s\-_]*((?:19|20)\d{2})(?!\d)', re.I),
     lambda m: (int(m.group(2)), MONTHS[m.group(1).lower()], 1)),
]


def parse_date_from_text(text):
    """Pull a publication date out of a title or filename, or return None."""
    if not text:
        return None
    # "NI 43-101" and "43101" are not dates; drop the standard's number first so
    # it cannot be read as one.
    text = re.sub(r'(?<!\d)43[\s\-_]?101(?!\d)', ' ', text, flags=re.I)

    for pattern, build in PATTERNS:
        for m in pattern.finditer(text):
            try:
                y, mo, d = build(m)
                if not (1990 <= y <= date.today().year and 1 <= mo <= 12 and 1 <= d <= 31):
                    continue
                parsed = date(y, mo, d)
            except ValueError:
                continue
            if parsed <= date.today():
                return parsed
    return None


class Command(BaseCommand):
    help = "Backfill document_date from titles for documents stamped with their ingest date."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']

        # Only rows whose date equals the day they were created — the signature
        # of the fallback. Anything else was set deliberately.
        # Two populations: rows stamped with their ingest date by the old
        # worker, and rows the current worker correctly leaves null.
        candidates = (Document.objects
                      .filter(Q(document_date=F('created_at__date'))
                              | Q(document_date__isnull=True))
                      .order_by('id'))
        if opts['limit']:
            candidates = candidates[:opts['limit']]

        total = candidates.count()
        self.stdout.write(f"{total} document(s) carrying their ingest date\n")

        fixed = cascaded = 0
        unparsed = []
        for doc in candidates.iterator():
            parsed = parse_date_from_text(doc.title) or parse_date_from_text(doc.file_url)
            if not parsed or parsed == doc.document_date:
                unparsed.append(doc)
                continue

            old = doc.document_date
            fixed += 1
            if fixed <= 25:
                self.stdout.write(f"  #{doc.id:<5d} {old} -> {parsed}  {doc.title[:52]}")

            if dry_run:
                cascaded += self._cascade(doc, old, parsed, dry_run=True)
                continue

            with transaction.atomic():
                doc.document_date = parsed
                doc.save(update_fields=['document_date', 'updated_at'])
                cascaded += self._cascade(doc, old, parsed, dry_run=False)

        if fixed > 25:
            self.stdout.write(f"  ... and {fixed - 25} more")

        self.stdout.write(self.style.SUCCESS(
            f"\n{fixed} document date(s) recovered, {cascaded} estimate/study row(s) "
            f"re-dated, {len(unparsed)} with no parseable date"
        ))
        if unparsed[:8]:
            self.stdout.write("\nExamples with no parseable date:")
            for doc in unparsed[:8]:
                self.stdout.write(f"  #{doc.id:<5d} {doc.title[:66]}")
        if dry_run:
            self.stdout.write(self.style.NOTICE('\nDry run — nothing written.'))

    def _cascade(self, doc, old_date, new_date, dry_run):
        """Re-date estimates/studies that inherited this document's fallback date."""
        marker = f'doc:{doc.id}'
        n = 0
        for model, field in ((ResourceEstimate, 'report_date'), (EconomicStudy, 'release_date')):
            qs = model.objects.filter(report_url__contains=marker, **{field: old_date})
            n += qs.count()
            if not dry_run:
                qs.update(**{field: new_date})
        return n
