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

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q

from core.document_dates import parse_date_from_body, parse_date_from_text
from core.models import Document, EconomicStudy, ResourceEstimate


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
        if sources:
            self.stdout.write('Recovered by source:')
            for how, n in sorted(sources.items(), key=lambda kv: -kv[1]):
                self.stdout.write(f'  {how:<12s} {n}')
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
