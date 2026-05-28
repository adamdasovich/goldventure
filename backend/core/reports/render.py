"""
Render the weekly industry report to HTML and PDF.

Template lives at core/templates/reports/weekly_industry.html. PDF rendering
uses xhtml2pdf (pure Python, no system deps). For a single-page report the
limited CSS support is acceptable; if richer styling is needed later, swap
to WeasyPrint.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, date
from typing import Any

from django.template.loader import render_to_string
from django.utils import timezone


logger = logging.getLogger(__name__)


# Maximum bar width (in pt) used for the financings-by-commodity chart.
# Sized so even a single bar reading 100% of the row stays inside the
# narrow right column.
MAX_BAR_WIDTH_PT = 90


def _prepare_template_context(data: dict[str, Any]) -> dict[str, Any]:
    """
    Reshape `data_snapshot` (with narrative + top_developments attached) into
    the dict the template expects. Adds the per-development glosses, bar
    widths for the financings chart, and a few convenience numbers.
    """
    narrative = data.get('narrative') or {}
    gloss_by_rank = {
        g['rank']: g['gloss'] for g in narrative.get('development_glosses', [])
    }

    top = []
    for i, dev in enumerate(data.get('top_developments', [])):
        top.append({**dev, 'gloss': gloss_by_rank.get(i + 1, '')})

    fin = dict(data.get('financings', {}))
    fin['total_amount_usd_millions'] = round((fin.get('total_amount_usd') or 0) / 1e6, 1)

    by_commodity_raw = fin.get('by_commodity') or []
    max_amt = max((b.get('amount_usd', 0) for b in by_commodity_raw), default=0)
    fin['by_commodity'] = [
        {
            'commodity': b['commodity'],
            'count': b['count'],
            'amount_usd_millions': round((b['amount_usd'] or 0) / 1e6, 1),
            'bar_width': (
                round((b['amount_usd'] / max_amt) * MAX_BAR_WIDTH_PT, 1)
                if max_amt else 0
            ),
        }
        for b in sorted(by_commodity_raw, key=lambda x: x.get('amount_usd', 0), reverse=True)
    ]

    return {
        'week_ending': data.get('week_ending'),
        'window_start': data.get('window_start'),
        'window_end': data.get('window_end'),
        'generated_at': timezone.localtime().strftime('%Y-%m-%d %H:%M %Z'),
        'top_developments': top,
        'metals': data.get('metals', []),
        'financings': fin,
        'technical_reports': data.get('technical_reports', []),
        'emerging_themes': data.get('emerging_themes', []),
        'narrative': narrative,
    }


def render_html(data: dict[str, Any]) -> str:
    """Render the report template to an HTML string."""
    context = _prepare_template_context(data)
    return render_to_string('reports/weekly_industry.html', context)


def render_pdf(html: str) -> bytes:
    """
    Convert HTML to PDF bytes via xhtml2pdf. Returns b'' on failure so the
    caller can persist the HTML even if PDF rendering breaks.
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        logger.error("xhtml2pdf not installed — skipping PDF render")
        return b''

    buf = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buf, encoding='utf-8')
    if result.err:
        logger.error("xhtml2pdf reported %d errors during render", result.err)
        return b''
    return buf.getvalue()


def render_report(data: dict[str, Any]) -> tuple[str, bytes]:
    """
    Convenience: returns (html, pdf_bytes). Used by the Celery task in
    commit 3 to populate WeeklyIndustryReport.html and .pdf_file.
    """
    html = render_html(data)
    pdf_bytes = render_pdf(html)
    return html, pdf_bytes
