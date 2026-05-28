"""
Render the weekly industry report to HTML and PDF.

Presentation logic (formatting, conditionals, fallbacks) lives here in
Python — the Django template is intentionally flat (variable substitution
only) so it can't be broken by HTML auto-formatters splitting tags
across lines.
"""

from __future__ import annotations

import io
import logging
from typing import Any

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import escape


logger = logging.getLogger(__name__)


# Maximum bar width (in pt) used for the financings-by-commodity chart.
MAX_BAR_WIDTH_PT = 90


def _fmt_pct(value) -> str:
    if value is None:
        return ''
    return f'+{value}%' if value >= 0 else f'{value}%'


def _move_span(weekly_return_pct) -> str:
    if weekly_return_pct is None:
        return ''
    cls = 'move-pos' if weekly_return_pct >= 0 else 'move-neg'
    return f'<span class="{cls}">{escape(_fmt_pct(weekly_return_pct))}</span>'


def _ticker_html(ticker: str, exchange: str) -> str:
    if not ticker:
        return ''
    ex = f'.{escape(exchange.upper())}' if exchange else ''
    return f'<span class="ticker">({escape(ticker)}{ex})</span>'


def _zscore_meta(dev: dict) -> str:
    z = dev.get('sector_zscore')
    if z is None:
        return ''
    return (
        f'<span class="meta">&middot; z={escape(str(z))} vs '
        f'{escape(dev.get("primary_commodity", ""))} cohort</span>'
    )


def _gloss_text(dev: dict, gloss_by_rank: dict[int, str], rank: int) -> str:
    g = gloss_by_rank.get(rank)
    if g:
        return escape(g)
    cat = dev.get('catalyst') or {}
    if cat.get('title'):
        date_part = f' ({escape(cat["date"])})' if cat.get('date') else ''
        kind = escape((cat.get('kind') or '').replace('_', ' ').title())
        return f'{kind}: {escape(cat["title"])}{date_part}'
    return 'No material release in window — move appears technical.'


def _render_top_developments_html(
    top_developments: list[dict],
    gloss_by_rank: dict[int, str],
) -> str:
    if not top_developments:
        return '<p>No qualifying movers this week.</p>'

    parts = []
    for i, dev in enumerate(top_developments, start=1):
        parts.append(
            f'<div class="dev">'
            f'<span class="rank">{i}</span>'
            f'<span class="name">{escape(dev.get("company_name", ""))}</span> '
            f'{_ticker_html(dev.get("ticker", ""), dev.get("exchange", ""))} '
            f'{_move_span(dev.get("weekly_return_pct"))} '
            f'{_zscore_meta(dev)}'
            f'<div class="gloss">{_gloss_text(dev, gloss_by_rank, i)}</div>'
            f'</div>'
        )
    return ''.join(parts)


def _render_technical_reports_html(reports: list[dict]) -> str:
    if not reports:
        return ''

    parts = ['<h2>New Technical Reports</h2>']
    for r in reports:
        ticker_html = _ticker_html(r.get('ticker', ''), '')
        proj = r.get('project_name')
        proj_part = f' — {escape(proj)}' if proj else ''
        meta_parts = []
        econ = r.get('economics') or {}
        if econ.get('npv_5_usd_millions'):
            meta_parts.append(f'NPV5 ${econ["npv_5_usd_millions"]}M')
        if econ.get('irr_percent'):
            meta_parts.append(f'IRR {econ["irr_percent"]}%')
        if econ.get('aisc_per_oz'):
            meta_parts.append(f'AISC ${econ["aisc_per_oz"]}/oz')
        if econ.get('mine_life_years'):
            meta_parts.append(f'LOM {econ["mine_life_years"]}y')
        econ_html = (
            f'<div class="meta">{" &middot; ".join(escape(p) for p in meta_parts)}</div>'
            if meta_parts else ''
        )

        parts.append(
            f'<div class="dev">'
            f'<span class="name">{escape(r.get("company_name", ""))}</span> '
            f'{ticker_html} '
            f'<span class="meta">&middot; {escape(r.get("document_type", "").upper())} '
            f'&middot; {escape(r.get("document_date", ""))}</span>'
            f'<div class="gloss">{escape(r.get("title", ""))}{proj_part}</div>'
            f'{econ_html}'
            f'</div>'
        )
    return ''.join(parts)


def _render_metals_rows_html(metals: list[dict]) -> str:
    if not metals:
        return '<tr><td colspan="4">No metal price data this week.</td></tr>'

    rows = []
    for m in metals:
        change = m.get('wow_change_pct')
        if change is None:
            change_html = '<span class="flat">—</span>'
        elif change > 0:
            change_html = f'<span class="pos">+{change}%</span>'
        elif change < 0:
            change_html = f'<span class="neg">{change}%</span>'
        else:
            change_html = '<span class="flat">flat</span>'

        rows.append(
            f'<tr>'
            f'<td class="name">{escape(m.get("label", ""))}</td>'
            f'<td>${m.get("end_price")}/{escape(m.get("unit", ""))}</td>'
            f'<td>{change_html}</td>'
            f'<td class="meta">{escape(m.get("trend_4w", ""))} 4w</td>'
            f'</tr>'
        )
    return ''.join(rows)


def _render_financings_html(financings: dict) -> str:
    total_m = round((financings.get('total_amount_usd') or 0) / 1e6, 1)
    count = financings.get('count', 0)
    pending = financings.get('pending_review_flag_count') or 0
    suffix = '' if count == 1 else 's'

    parts = [
        f'<div class="fin-summary">'
        f'<strong>${total_m}M</strong> across {count} deal{suffix}.'
        f'</div>'
    ]

    by_commodity = sorted(
        financings.get('by_commodity') or [],
        key=lambda b: b.get('amount_usd', 0),
        reverse=True,
    )
    if by_commodity:
        max_amt = max((b.get('amount_usd', 0) for b in by_commodity), default=0)
        rows = []
        for b in by_commodity:
            amt = b.get('amount_usd', 0) or 0
            amt_m = round(amt / 1e6, 1)
            bar_w = round((amt / max_amt) * MAX_BAR_WIDTH_PT, 1) if max_amt else 0
            rows.append(
                f'<tr>'
                f'<td class="label">{escape((b.get("commodity") or "").title())}</td>'
                f'<td><span class="bar" style="width: {bar_w}pt;">&nbsp;</span></td>'
                f'<td class="amt">${amt_m}M</td>'
                f'</tr>'
            )
        parts.append(f'<table class="fin-bars">{"".join(rows)}</table>')

    if pending:
        suffix_p = '' if pending == 1 else 's'
        parts.append(
            f'<div class="pending-note">'
            f'+{pending} flag{suffix_p} awaiting review (totals may be understated).'
            f'</div>'
        )

    return ''.join(parts)


def _prepare_template_context(data: dict[str, Any]) -> dict[str, Any]:
    """Precompute every dynamic HTML fragment for the template."""
    narrative = data.get('narrative') or {}
    gloss_by_rank = {
        int(g.get('rank', 0)): g.get('gloss', '')
        for g in narrative.get('development_glosses', [])
    }
    top_devs = data.get('top_developments', []) or []

    exec_summary = narrative.get('executive_summary') or ''
    theme_note = narrative.get('theme_note')

    return {
        'week_ending': data.get('week_ending'),
        'window_start': data.get('window_start'),
        'window_end': data.get('window_end'),
        'generated_at': timezone.localtime().strftime('%Y-%m-%d %H:%M %Z'),
        'executive_summary_html': escape(exec_summary),
        'top_developments_html': _render_top_developments_html(top_devs, gloss_by_rank),
        'technical_reports_html': _render_technical_reports_html(
            data.get('technical_reports', []) or []
        ),
        'metals_rows_html': _render_metals_rows_html(data.get('metals', []) or []),
        'financings_html': _render_financings_html(data.get('financings', {}) or {}),
        'theme_html': (
            f'<div class="theme">{escape(theme_note)}</div>' if theme_note else ''
        ),
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
    """Returns (html, pdf_bytes)."""
    html = render_html(data)
    pdf_bytes = render_pdf(html)
    return html, pdf_bytes
