"""
Thin wrapper around the GA4 Data API for the weekly industry report.

Activates only when GA4_PROPERTY_ID and GA4_CREDENTIALS_PATH env vars are
set. Returns top-viewed company pages over the given window, joined to
Company by slug or numeric id parsed from /companies/{id}-{slug}.

Install: `pip install google-analytics-data` (added to requirements.txt).
Server setup: drop the service-account JSON at GA4_CREDENTIALS_PATH and
grant the service-account "Viewer" on the GA4 property.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from typing import Any


logger = logging.getLogger(__name__)


COMPANY_PATH_RE = re.compile(r'^/companies/(\d+)(?:-([\w\-]+))?/?$')


def _enabled() -> bool:
    return bool(
        os.environ.get('GA4_PROPERTY_ID')
        and os.environ.get('GA4_CREDENTIALS_PATH')
    )


def fetch_top_company_pageviews(
    start: date,
    end: date,
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """
    Query GA4 for screen_page_views grouped by pagePath matching
    /companies/{id}-{slug}, return the top N joined to Company.

    Returns [] when GA4 is not configured or any error occurs — the report
    must always render even if engagement data is missing.
    """
    if not _enabled():
        return []

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Metric,
            RunReportRequest,
            FilterExpression,
            Filter,
        )
        from google.oauth2 import service_account
    except ImportError:
        logger.warning("google-analytics-data not installed — skipping GA4")
        return []

    try:
        creds = service_account.Credentials.from_service_account_file(
            os.environ['GA4_CREDENTIALS_PATH']
        )
        client = BetaAnalyticsDataClient(credentials=creds)

        request = RunReportRequest(
            property=f"properties/{os.environ['GA4_PROPERTY_ID']}",
            dimensions=[Dimension(name='pagePath')],
            metrics=[Metric(name='screenPageViews')],
            date_ranges=[DateRange(
                start_date=start.isoformat(),
                end_date=end.isoformat(),
            )],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name='pagePath',
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                        value='/companies/',
                    ),
                ),
            ),
            limit=200,
        )
        response = client.run_report(request)

    except Exception as e:
        logger.error("GA4 request failed: %s", e)
        return []

    # Parse /companies/{id}-{slug} rows and aggregate by company_id
    rows_by_company_id: dict[int, int] = {}
    for row in response.rows:
        path = row.dimension_values[0].value or ''
        views = int(row.metric_values[0].value or 0)
        m = COMPANY_PATH_RE.match(path)
        if not m:
            continue
        cid = int(m.group(1))
        rows_by_company_id[cid] = rows_by_company_id.get(cid, 0) + views

    if not rows_by_company_id:
        return []

    from core.models import Company
    companies = {
        c.id: c for c in Company.objects.filter(id__in=rows_by_company_id.keys())
    }

    out = []
    for cid, views in rows_by_company_id.items():
        company = companies.get(cid)
        if not company:
            continue
        out.append({
            'company_id': cid,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'pageviews': views,
        })

    out.sort(key=lambda r: r['pageviews'], reverse=True)
    return out[:top_n]
