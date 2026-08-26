"""
CSV exports of the company database.

Paid-tier only, and deliberately so: the directory itself is public and
indexable — that is what earns the organic traffic — but taking the whole
dataset away in one file is a different thing from reading a profile, and it is
the kind of concrete deliverable a subscription can be justified by.

Streams rather than building a list in memory: the export is ~500 rows today
but grows with the database, and a request that materialises every company plus
its related counts is exactly the sort of thing that OOMs a 8 GB box during the
morning scrape.
"""

import csv
import logging

from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..entitlements import requires_tier
from ..models import Company

logger = logging.getLogger(__name__)


# Deliberately excludes ir_contact_email / ir_contact_phone. Those are personal
# contact details, and shipping them as a downloadable list turns the directory
# into a mailing list. They stay on the profile page where they are shown in
# context.
COLUMNS = [
    ('name', 'Company'),
    ('ticker_symbol', 'Ticker'),
    ('exchange', 'Exchange'),
    ('status', 'Status'),
    ('jurisdiction', 'Jurisdiction'),
    ('headquarters_city', 'HQ City'),
    ('headquarters_country', 'HQ Country'),
    ('ceo_name', 'CEO'),
    ('market_cap_usd', 'Market Cap (USD)'),
    ('shares_outstanding', 'Shares Outstanding'),
    ('current_price', 'Last Price'),
    ('website', 'Website'),
]

COUNT_COLUMNS = [
    ('project_count', 'Projects'),
    ('open_financing_count', 'Open Financings'),
    ('closed_financing_count', 'Closed Financings'),
]


class _Echo:
    """File-like object whose write() returns the value, for csv + streaming."""

    def write(self, value):
        return value


def _rows(queryset):
    writer = csv.writer(_Echo())
    header = [label for _, label in COLUMNS] + [label for _, label in COUNT_COLUMNS]
    yield writer.writerow(header)

    for company in queryset.iterator(chunk_size=200):
        row = []
        for field, _ in COLUMNS:
            value = getattr(company, field, '')
            row.append('' if value is None else value)
        for field, _ in COUNT_COLUMNS:
            row.append(getattr(company, field, 0))
        yield writer.writerow(row)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requires_tier('prospector')
def export_companies_csv(request):
    """
    GET /api/companies/export/csv/

    The full company directory as CSV. Prospector and above.

    Annotated counts come from the same query rather than per-row lookups —
    500 companies each doing three COUNT queries is 1,500 round trips, which is
    slow enough to hold a gunicorn worker for the whole export.
    """
    queryset = (
        Company.objects.filter(is_deleted=False)
        .annotate(
            project_count=Count('projects', distinct=True),
            open_financing_count=Count(
                'financings', filter=Q(financings__is_closed=False), distinct=True,
            ),
            closed_financing_count=Count(
                'financings', filter=Q(financings__is_closed=True), distinct=True,
            ),
        )
        .order_by('name')
    )

    stamp = timezone.localtime().strftime('%Y-%m-%d')
    filename = f'junior-mining-companies-{stamp}.csv'

    response = StreamingHttpResponse(_rows(queryset), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    logger.info(
        "CSV export requested by user %s (%s companies)",
        request.user.id, queryset.count(),
    )
    return response
