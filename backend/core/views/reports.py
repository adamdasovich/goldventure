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
from django.views.decorators.http import require_GET

from core.models import WeeklyIndustryReport


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


@require_GET
def weekly_report_detail(request, week_ending: str):
    """Render the report HTML for a given week_ending date (YYYY-MM-DD)."""
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
