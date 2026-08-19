"""
Extract structured resource and economic data from already-processed documents.

Why this exists
---------------
`gpu_worker.py` chunks and embeds documents for semantic search but performs no
structured extraction — across 2,286 completed jobs it produced 2 ResourceEstimate
rows and zero EconomicStudy rows. That is why Grade Ranker, Resource Growth,
EV/oz and P/NAV are hollow: they read `resource_estimates` and `economic_studies`,
which the GPU pipeline never writes.

The text those tables need is already in Postgres. 129 technical reports have
been chunked — roughly 62.7M characters — so extraction needs Claude over
existing rows, not another GPU run and not a re-download.

Cost control
------------
Sending whole reports would be enormous and mostly wasted: a 500-page NI 43-101
is overwhelmingly geology narrative, and the resource and economic figures sit in
a handful of sections. Chunks are scored against the vocabulary those sections
use and only the top-scoring ones are sent, which keeps a document to a few tens
of thousands of tokens instead of hundreds of thousands.

Usage
-----
    python manage.py extract_resources --dry-run --limit 3
    python manage.py extract_resources --limit 10
    python manage.py extract_resources
"""

import json
import re
import time
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Document, DocumentChunk, EconomicStudy, Project, ResourceEstimate,
)

# Sections that carry the numbers we want, in the words those sections use.
# Weighted: a chunk naming a resource category is far more likely to hold a
# resource table than one that merely mentions gold.
CHUNK_SIGNALS = [
    (10, re.compile(r'\b(measured|indicated|inferred)\s+(and\s+indicated\s+)?(mineral\s+)?resource', re.I)),
    (10, re.compile(r'\bmineral\s+resource\s+(estimate|statement|summary)', re.I)),
    (9, re.compile(r'\b(proven|probable)\s+(mineral\s+)?reserve', re.I)),
    (8, re.compile(r'\bcut-?off\s+grade', re.I)),
    (8, re.compile(r'\bcontained\s+(gold|silver|copper|metal|ounces)', re.I)),
    (7, re.compile(r'\bnet\s+present\s+value|\bNPV\b|\bafter-?tax\s+NPV', re.I)),
    (7, re.compile(r'\binternal\s+rate\s+of\s+return|\bIRR\b', re.I)),
    (6, re.compile(r'\ball-?in\s+sustaining\s+cost|\bAISC\b', re.I)),
    (6, re.compile(r'\binitial\s+capital|\bcapex\b|\bpayback\s+period', re.I)),
    (6, re.compile(r'\bmine\s+life|\bannual\s+production', re.I)),
    (5, re.compile(r'\b(gold|silver)\s+price\s+(assumption|of\s+US\$)', re.I)),
    (5, re.compile(r'\bg/t\b|\bgrams?\s+per\s+tonne\b', re.I)),
    (4, re.compile(r'\btonnes?\b|\bMt\b|\bmillion\s+tonnes', re.I)),
]

# Roughly 4 characters per token; enough headroom for the biggest reports
# without sending an entire document.
MAX_CONTEXT_CHARS = 120_000

EXTRACTION_PROMPT = """You are reading excerpts from a mining technical report (NI 43-101, PEA, or similar).

Extract ONLY figures that are explicitly stated in the text. Do not calculate,
infer, or estimate any value. If a field is not stated, use null. It is far
better to return null than a plausible-looking number that is not in the text.

Return ONLY a JSON object, no prose and no markdown fence, in exactly this shape:

{
  "project_name": "<the project this report covers, or null>",
  "country": "<country, or null>",
  "primary_commodity": "<gold|silver|copper|lithium|uranium|nickel|zinc|other, or null>",
  "report_date": "<YYYY-MM-DD of the report, or null>",
  "effective_date": "<YYYY-MM-DD effective date of the estimate, or null>",
  "qualified_person": "<lead QP name, or null>",
  "mineral_resources": [
    {
      "category": "<measured|indicated|mni|inferred|proven|probable>",
      "tonnes": <number of tonnes, not millions - convert Mt to tonnes>,
      "gold_grade_gpt": <number or null>,
      "gold_ounces": <number or null>,
      "silver_grade_gpt": <number or null>,
      "silver_ounces": <number or null>,
      "copper_grade_pct": <number or null>,
      "cutoff_grade": <number or null>
    }
  ],
  "economic_study": {
    "study_type": "<pea|pfs|fs, or null if this is not an economic study>",
    "release_date": "<YYYY-MM-DD or null>",
    "npv_5_usd_millions": <number or null>,
    "irr_percent": <number or null>,
    "payback_years": <number or null>,
    "mine_life_years": <number or null>,
    "annual_production_oz": <number or null>,
    "aisc_per_oz": <number or null>,
    "initial_capex_usd_millions": <number or null>,
    "gold_price_assumption": <number or null>
  }
}

Rules:
- "tonnes" must be in tonnes. If the report says "12.4 Mt", return 12400000.
- Use "mni" for a combined Measured & Indicated row.
- Return an empty mineral_resources list if the excerpts contain no resource table.
- Set economic_study.study_type to null if the excerpts contain no economic study.
- Never repeat a Measured & Indicated total as separate Measured and Indicated rows."""


class Command(BaseCommand):
    help = "Extract resource estimates and economic studies from processed document text."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0,
                            help="Stop after this many documents. 0 = all.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Extract and report without writing to the database.")
        parser.add_argument('--model', default='claude-opus-5',
                            help="Claude model id (default: claude-opus-5).")
        parser.add_argument('--document-id', type=int,
                            help="Process a single document, for debugging.")
        parser.add_argument('--redo', action='store_true',
                            help="Re-extract documents that already produced a resource estimate.")

    # ------------------------------------------------------------------

    def handle(self, *args, **opts):
        import anthropic
        from django.conf import settings

        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = opts['model']
        self.dry_run = opts['dry_run']

        documents = self._target_documents(opts)
        total = len(documents)
        self.stdout.write(f"{total} document(s) to extract with {self.model}\n")
        if not total:
            return

        stats = {'resources': 0, 'studies': 0, 'empty': 0, 'failed': 0,
                 'in_tokens': 0, 'out_tokens': 0}
        started = time.time()

        for i, document in enumerate(documents, 1):
            label = f"[{i}/{total}] {document.company.name[:26]:26s}"
            try:
                self._extract_one(document, label, stats)
            except Exception as exc:
                stats['failed'] += 1
                self.stderr.write(self.style.ERROR(f"{label} FAILED: {type(exc).__name__}: {exc}"))

        elapsed = time.time() - started
        self.stdout.write(self.style.SUCCESS(
            f"\nDone in {elapsed:.0f}s — {stats['resources']} resource estimates, "
            f"{stats['studies']} economic studies, {stats['empty']} with nothing to extract, "
            f"{stats['failed']} failed"
        ))
        # Priced at claude-opus-5 list rates so the run reports its own cost.
        cost = stats['in_tokens'] / 1e6 * 5 + stats['out_tokens'] / 1e6 * 25
        self.stdout.write(
            f"Tokens: {stats['in_tokens']:,} in / {stats['out_tokens']:,} out "
            f"(~${cost:.2f} at Opus 5 list rates)"
        )
        if self.dry_run:
            self.stdout.write(self.style.NOTICE("Dry run — nothing written."))

    # ------------------------------------------------------------------

    def _target_documents(self, opts):
        qs = Document.objects.filter(
            document_type__in=('ni43101', 'pea', 'technical_report')
        ).select_related('company').order_by('id')

        if opts.get('document_id'):
            return list(qs.filter(id=opts['document_id']))

        # Only documents whose text we actually hold.
        with_chunks = DocumentChunk.objects.values_list('document_id', flat=True).distinct()
        qs = qs.filter(id__in=with_chunks)

        if not opts['redo']:
            done = ResourceEstimate.objects.filter(
                report_url__startswith='doc:'
            ).values_list('report_url', flat=True)
            already = {int(u.split(':', 1)[1]) for u in done if u.split(':', 1)[1].isdigit()}
            qs = qs.exclude(id__in=already)

        documents = list(qs)
        if opts['limit']:
            documents = documents[:opts['limit']]
        return documents

    def _select_context(self, document):
        """Pick the chunks most likely to contain resource and economic tables."""
        chunks = list(
            DocumentChunk.objects.filter(document=document)
            .order_by('chunk_index')
            .values('chunk_index', 'text')
        )
        scored = []
        for chunk in chunks:
            text = chunk['text'] or ''
            score = sum(weight for weight, pattern in CHUNK_SIGNALS if pattern.search(text))
            if score:
                scored.append((score, chunk['chunk_index'], text))

        scored.sort(key=lambda row: (-row[0], row[1]))

        selected, size = [], 0
        for score, index, text in scored:
            if size + len(text) > MAX_CONTEXT_CHARS:
                continue
            selected.append((index, text))
            size += len(text)

        # Restore document order so tables read the way they were written.
        selected.sort(key=lambda row: row[0])
        return "\n\n---\n\n".join(text for _, text in selected), len(selected), len(chunks)

    def _ask_claude(self, context):
        """Call Claude and return parsed JSON, or None."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            system=EXTRACTION_PROMPT,
            messages=[{"role": "user", "content": f"Report excerpts:\n\n{context}"}],
        )

        # Claude Opus 5 thinks by default, so content[0] is a thinking block —
        # take the first text block rather than indexing blindly.
        text = next(
            (block.text for block in message.content if block.type == 'text'), ''
        )
        usage = (message.usage.input_tokens, message.usage.output_tokens)

        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned)
        try:
            return json.loads(cleaned), usage
        except json.JSONDecodeError:
            start, end = cleaned.find('{'), cleaned.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(cleaned[start:end]), usage
            raise ValueError(f"Claude did not return JSON: {cleaned[:160]}")

    def _extract_one(self, document, label, stats):
        context, used, available = self._select_context(document)
        if not context:
            stats['empty'] += 1
            self.stdout.write(f"{label} no resource/economic text in {available} chunks")
            return

        data, (tokens_in, tokens_out) = self._ask_claude(context)
        stats['in_tokens'] += tokens_in
        stats['out_tokens'] += tokens_out

        resources = data.get('mineral_resources') or []
        study = data.get('economic_study') or {}
        has_study = bool(study.get('study_type'))

        self.stdout.write(
            f"{label} {used}/{available} chunks -> "
            f"{len(resources)} resource rows, study={'yes' if has_study else 'no'} "
            f"({data.get('project_name') or 'unnamed project'})"
        )

        if self.dry_run or (not resources and not has_study):
            if not resources and not has_study:
                stats['empty'] += 1
            return

        with transaction.atomic():
            project = self._resolve_project(document, data)
            if not project:
                self.stderr.write(f"{label} could not resolve a project — skipped")
                return
            stats['resources'] += self._save_resources(document, project, data, resources)
            if has_study:
                stats['studies'] += self._save_study(document, project, study)

    # ------------------------------------------------------------------

    def _resolve_project(self, document, data):
        """Find or create the project this report covers."""
        if document.project_id:
            return document.project

        name = (data.get('project_name') or '').strip()
        company = document.company

        if name:
            existing = Project.objects.filter(
                company=company, name__iexact=name
            ).first()
            if existing:
                return existing

        # Fall back to the company's flagship before inventing a project —
        # a duplicate project would split its resource history in two.
        flagship = Project.objects.filter(company=company, is_flagship=True).first()
        if flagship and not name:
            return flagship

        if not name:
            return Project.objects.filter(company=company, is_active=True).first()

        return Project.objects.create(
            company=company,
            name=name[:200],
            country=(data.get('country') or '')[:100],
            primary_commodity=(data.get('primary_commodity') or 'gold')[:20],
            project_stage='resource',
        )

    @staticmethod
    def _decimal(value, places='0.001'):
        if value in (None, '', False):
            return None
        try:
            return Decimal(str(value)).quantize(Decimal(places))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def _date(value, fallback):
        if not value:
            return fallback
        try:
            return timezone.datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return fallback

    def _save_resources(self, document, project, data, resources):
        report_date = self._date(data.get('report_date'), document.document_date)
        effective = self._date(data.get('effective_date'), report_date)
        saved = 0

        for row in resources:
            tonnes = self._decimal(row.get('tonnes'), '0.01')
            if not tonnes or tonnes <= 0:
                # tonnes is non-nullable and a resource row without it is not
                # a usable estimate.
                continue
            category = (row.get('category') or '').lower().strip()
            if category not in dict(ResourceEstimate.RESOURCE_CATEGORIES):
                continue

            ResourceEstimate.objects.update_or_create(
                project=project,
                category=category,
                report_date=report_date,
                defaults={
                    'standard': 'ni43101',
                    'tonnes': tonnes,
                    'gold_grade_gpt': self._decimal(row.get('gold_grade_gpt')),
                    'gold_ounces': self._decimal(row.get('gold_ounces'), '0.01'),
                    'silver_grade_gpt': self._decimal(row.get('silver_grade_gpt')),
                    'silver_ounces': self._decimal(row.get('silver_ounces'), '0.01'),
                    'copper_grade_pct': self._decimal(row.get('copper_grade_pct')),
                    'cutoff_grade': self._decimal(row.get('cutoff_grade')),
                    'effective_date': effective,
                    'qualified_person': (data.get('qualified_person') or '')[:200],
                    # Marks provenance and makes reruns idempotent.
                    'report_url': f"doc:{document.id}",
                },
            )
            saved += 1
        return saved

    def _save_study(self, document, project, study):
        study_type = (study.get('study_type') or '').lower().strip()
        if study_type not in dict(EconomicStudy.STUDY_TYPES):
            return 0

        release = self._date(study.get('release_date'), document.document_date)
        EconomicStudy.objects.update_or_create(
            project=project,
            study_type=study_type,
            release_date=release,
            defaults={
                'npv_5_usd': self._decimal(study.get('npv_5_usd_millions'), '0.01'),
                'irr_percent': self._decimal(study.get('irr_percent'), '0.01'),
                'payback_years': self._decimal(study.get('payback_years'), '0.1'),
                'mine_life_years': self._decimal(study.get('mine_life_years'), '0.1'),
                'annual_production_oz': (
                    int(study['annual_production_oz'])
                    if study.get('annual_production_oz') else None
                ),
                'aisc_per_oz': self._decimal(study.get('aisc_per_oz'), '0.01'),
                'initial_capex_usd': self._decimal(
                    study.get('initial_capex_usd_millions'), '0.01'
                ),
                'gold_price_assumption': self._decimal(
                    study.get('gold_price_assumption'), '0.01'
                ),
                'report_url': f"doc:{document.id}",
            },
        )
        return 1
