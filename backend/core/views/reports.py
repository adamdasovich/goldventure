"""
Public archive endpoints for the Friday weekly industry report.

Routes (mounted under /api/reports/weekly/):
- GET /api/reports/weekly/             -> list (week_ending, generated_at, urls)
- GET /api/reports/weekly/<YYYY-MM-DD>/      -> rendered HTML
- GET /api/reports/weekly/<YYYY-MM-DD>/pdf/  -> PDF download
- GET /api/reports/weekly/latest/      -> HTML for the most recent completed report
"""

from __future__ import annotations

from datetime import date

from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET

from core.models import Company, WeeklyIndustryReport


def _serialize(report: WeeklyIndustryReport, request) -> dict:
    week = report.week_ending.isoformat()
    base = request.build_absolute_uri('/api/reports/weekly/')
    return {
        'week_ending': week,
        'status': report.status,
        'generated_at': report.generated_at.isoformat() if report.generated_at else None,
        'has_pdf': bool(report.pdf_file),
        'html_url': f'{base}{week}/',
        'pdf_url': f'{base}{week}/pdf/' if report.pdf_file else None,
    }


@require_GET
def weekly_report_list(request):
    """Index of completed weekly reports, newest first."""
    qs = WeeklyIndustryReport.objects.filter(status='completed').order_by('-week_ending')
    return JsonResponse({
        'count': qs.count(),
        'reports': [_serialize(r, request) for r in qs[:52]],  # one year
    })


@xframe_options_sameorigin
@require_GET
def weekly_report_detail(request, week_ending: str):
    """Render the report HTML for a given week_ending date (YYYY-MM-DD).

    `xframe_options_sameorigin` overrides the project-wide DENY default so
    the frontend's /reports/weekly/<date>/ page can iframe-embed the report.
    nginx also adds X-Frame-Options: SAMEORIGIN — without this override,
    Django emits DENY and Chrome refuses the iframe due to conflicting
    values.
    """
    try:
        wk = date.fromisoformat(week_ending)
    except ValueError:
        return HttpResponse('Invalid date — expected YYYY-MM-DD', status=400)

    report = get_object_or_404(
        WeeklyIndustryReport, week_ending=wk, status='completed',
    )
    return HttpResponse(report.html or '<h1>Report not yet rendered</h1>',
                        content_type='text/html; charset=utf-8')


@require_GET
def weekly_report_pdf(request, week_ending: str):
    """Stream the report PDF for a given week_ending date."""
    try:
        wk = date.fromisoformat(week_ending)
    except ValueError:
        return HttpResponse('Invalid date — expected YYYY-MM-DD', status=400)

    report = get_object_or_404(
        WeeklyIndustryReport, week_ending=wk, status='completed',
    )
    if not report.pdf_file:
        return HttpResponse('PDF not available for this week', status=404)

    return FileResponse(
        report.pdf_file.open('rb'),
        content_type='application/pdf',
        as_attachment=False,
        filename=f'goldventure-weekly-{wk.isoformat()}.pdf',
    )


# ---------------------------------------------------------------------------
# Weekly Financing Roundup — native, crawlable JSON for the Next.js pages.
#
# Reuses the financings slice already frozen into each report's data_snapshot
# by the Friday generator (core.reports.weekly_industry.get_financings_in_window),
# so there is no new job — this only *exposes* existing data as SEO-native pages
# instead of the iframe'd HTML report.
# ---------------------------------------------------------------------------

def _financings_summary(snapshot: dict | None) -> dict:
    """Lightweight per-week summary for the roundup index."""
    fin = (snapshot or {}).get('financings') or {}
    by_commodity = fin.get('by_commodity') or []
    top = max(by_commodity, key=lambda c: c.get('amount_usd', 0), default=None)
    return {
        'count': fin.get('count', 0) or 0,
        'total_amount_usd': fin.get('total_amount_usd', 0) or 0,
        'top_commodity': (top or {}).get('commodity'),
    }


def _enrich_items_with_slug(items: list[dict]) -> list[dict]:
    """Add company_slug to each item so the frontend can build canonical
    /companies/{id}-{slug} links. Done at serve time so it works for older
    snapshots frozen before slug was tracked."""
    ids = {i.get('company_id') for i in items if i.get('company_id')}
    slugs = dict(Company.objects.filter(id__in=ids).values_list('id', 'slug'))
    for i in items:
        i['company_slug'] = slugs.get(i.get('company_id'))
    return items


@require_GET
def weekly_financings_list(request):
    """Index of weeks that had financings, newest first — for the roundup hub.

    Weeks with zero financings are omitted so we never link to a thin page.
    """
    qs = (
        WeeklyIndustryReport.objects
        .filter(status='completed')
        .defer('html')
        .order_by('-week_ending')
    )
    weeks = []
    for report in qs[:52]:  # one year
        summary = _financings_summary(report.data_snapshot)
        if summary['count'] == 0:
            continue
        weeks.append({
            'week_ending': report.week_ending.isoformat(),
            'generated_at': report.generated_at.isoformat() if report.generated_at else None,
            **summary,
        })
    return JsonResponse({'count': len(weeks), 'weeks': weeks})


@require_GET
def weekly_financings_detail(request, week_ending: str):
    """Full financings breakdown for one week — items, totals, and the
    by-type / by-commodity aggregations, with company slugs enriched in."""
    try:
        wk = date.fromisoformat(week_ending)
    except ValueError:
        return JsonResponse({'error': 'Invalid date — expected YYYY-MM-DD'}, status=400)

    report = get_object_or_404(
        WeeklyIndustryReport, week_ending=wk, status='completed',
    )
    snapshot = report.data_snapshot or {}
    fin = snapshot.get('financings') or {}
    items = _enrich_items_with_slug(list(fin.get('items') or []))

    return JsonResponse({
        'week_ending': wk.isoformat(),
        'window_start': snapshot.get('window_start'),
        'window_end': snapshot.get('window_end'),
        'count': fin.get('count', 0) or 0,
        'total_amount_usd': fin.get('total_amount_usd', 0) or 0,
        'by_type': fin.get('by_type') or [],
        'by_commodity': fin.get('by_commodity') or [],
        'items': items,
    })


@xframe_options_sameorigin
@require_GET
def weekly_report_latest(request):
    """Convenience: render the most recent completed report."""
    report = (
        WeeklyIndustryReport.objects
        .filter(status='completed')
        .order_by('-week_ending')
        .first()
    )
    if not report:
        return HttpResponse('No weekly reports yet', status=404)
    return HttpResponse(report.html or '<h1>Report not yet rendered</h1>',
                        content_type='text/html; charset=utf-8')
