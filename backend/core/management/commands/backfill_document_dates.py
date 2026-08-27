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
# Digit guards, not word boundaries: \b does not fire between a digit and a
# letter or after an underscore, so "Oct 2019a" and "report_20191015_final"
# both went unmatched.
#
# Digit guards rather than \b: word boundaries do not fire between a digit and
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


# A publication date sits at the very top — a news-release dateline, a cover
# page, a title slide. Everything past that is other dates: prior studies,
# drill campaigns, "dated September 24, 2019" references to earlier filings.
# Scanning wide finds those instead, so the window is deliberately narrow.
HEAD_SCAN_CHARS = 800

# Technical reports put a labelled date on a verbose cover page, so a labelled
# date is allowed a wider window — but only when the narrow scan found nothing.
LABEL_SCAN_CHARS = 3000

_D = r'(?P<d>\d{1,2})'
_Y = r'(?P<y>(?:19|20)\d{2})'
_M = r'(?P<m>' + MONTH_RE + r')'

FULL_DATE_PATTERNS = [
    re.compile(_M + r'\s+' + _D + r'(?:st|nd|rd|th)?,?\s+' + _Y, re.I),
    re.compile(_D + r'(?:st|nd|rd|th)?\s+' + _M + r',?\s+' + _Y, re.I),
    re.compile(r'(?P<y>(?:19|20)\d{2})-(?P<m>\d{2})-(?P<d>\d{2})'),
]

DATE_LABEL = re.compile(
    r'(?:report\s+date|date\s+of\s+report|date\s+of\s+this\s+announcement'
    r'|issue\s+date|dated|effective\s+date)\s*:?\s*'
    # ASX filings write "Date of this announcement Friday July 12, 2024", so a
    # weekday may sit between the label and the date.
    r'(?:mon|tues|wednes|thurs|fri|satur|sun)?(?:day)?\s*,?\s*$', re.I)

# Dates a document looks BACK to rather than is published on: "as at December
# 31, 2024" on a presentation is the balance-sheet date, not the deck's date.
BACKWARD_LOOKING = re.compile(
    r'(?:as\s+at|as\s+of|year\s+ended|quarter\s+ended|period\s+ended|ended'
    r'|since|prior\s+to|before|until|through)\s*$', re.I)

MONTH_YEAR = re.compile(r'\b' + _M + r'\s+' + _Y, re.I)


def _build(match):
    """Turn a regex match into a plausible date, or None."""
    parts = match.groupdict()
    try:
        year = int(parts['y'])
        raw_month = parts['m']
        month = MONTHS[raw_month.lower()] if not raw_month.isdigit() else int(raw_month)
        day = int(parts.get('d') or 1)
        parsed = date(year, month, day)
    except (ValueError, KeyError, TypeError):
        return None
    if not (1990 <= year <= date.today().year) or parsed > date.today():
        return None
    return parsed


def _dates_in(text, limit):
    """Every plausible full date in the first `limit` chars, in position order."""
    head = text[:limit]
    found = []
    for pattern in FULL_DATE_PATTERNS:
        for match in pattern.finditer(head):
            parsed = _build(match)
            if not parsed:
                continue
            # 48 chars so a full label fits ("Date of this announcement Friday "),
            # but the backward-looking test only reads the last 30 — a wider
            # window there would suppress dates over unrelated earlier prose.
            preceding = head[max(0, match.start() - 48):match.start()]
            if BACKWARD_LOOKING.search(preceding[-30:].rstrip()):
                continue
            found.append((match.start(), parsed, preceding))
    found.sort(key=lambda t: t[0])
    return found


def parse_date_from_body(text):
    """Read a document's own publication date out of its opening text.

    Position is the strongest signal, so the first qualifying date in a narrow
    head window wins. An earlier version preferred any labelled date anywhere
    in 3000 characters, which made a LAURION release read 2019-09-24 from a
    "dated September 24, 2019" reference to a prior filing while its own
    dateline said October 28 — the label rule now only applies when the head
    window is empty.

    Returns (date, how), or (None, None).
    """
    if not text:
        return None, None

    head = _dates_in(text, HEAD_SCAN_CHARS)
    if head:
        position, parsed, preceding = head[0]
        return parsed, 'labelled' if DATE_LABEL.search(preceding.rstrip()) else 'head'

    for position, parsed, preceding in _dates_in(text, LABEL_SCAN_CHARS):
        if DATE_LABEL.search(preceding.rstrip()):
            return parsed, 'labelled'

    for match in MONTH_YEAR.finditer(text[:HEAD_SCAN_CHARS]):
        preceding = text[max(0, match.start() - 30):match.start()]
        if BACKWARD_LOOKING.search(preceding.rstrip()):
            continue
        parsed = _build(match)
        if parsed:
            return parsed, 'month-year'
    return None, None


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
        sources = {}
        unparsed = []
        for doc in candidates.iterator():
            parsed, how = self._resolve_date(doc)
            if not parsed or parsed == doc.document_date:
                unparsed.append(doc)
                continue
            sources[how] = sources.get(how, 0) + 1

            old = doc.document_date
            fixed += 1
            if fixed <= 25:
                self.stdout.write(
                    f"  #{doc.id:<5d} {old} -> {parsed}  [{how}]  {doc.title[:44]}")

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

    def _resolve_date(self, doc):
        """Find a document's date, most authoritative source first.

        The document's own text beats its filename: a news release states
        "Melbourne, Australia and Vancouver, Canada - January 30, 2026" in its
        dateline while its URL is an opaque UUID, and a presentation's title
        slide carries the month the filename may omit. Filename parsing stays
        as the fallback for documents whose text was never chunked.
        """
        chunk = doc.chunks.order_by('chunk_index').first()
        if chunk:
            parsed, how = parse_date_from_body(chunk.text)
            # A bare month/year off a title slide is weaker than an explicit
            # date in the filename, so let the filename try first.
            if parsed and how != 'month-year':
                return parsed, how
            fallback = parse_date_from_text(doc.title) or parse_date_from_text(doc.file_url)
            if fallback:
                return fallback, 'filename'
            if parsed:
                return parsed, how

        parsed = parse_date_from_text(doc.title) or parse_date_from_text(doc.file_url)
        return (parsed, 'filename') if parsed else (None, None)

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
