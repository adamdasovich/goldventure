"""
Open Financings API — public-facing list with tier-based gating.

Free / Explorer users see the first 5 financings in full; rows past that are
returned with sensitive fields redacted (`is_locked: true`). Prospector/Miner
users see every row in full. The redaction happens server-side so $ amounts
and closing dates never leave the server for free users.
"""

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import Financing, PlatformSubscription


logger = logging.getLogger(__name__)


FREE_PREVIEW_COUNT = 5
PAID_TIERS = ('prospector', 'miner')


def _resolve_effective_tier(user) -> str:
    """Return the effective tier for `user` ('explorer' if anon or no sub)."""
    if not user or not user.is_authenticated:
        return 'explorer'
    try:
        return user.platform_subscription.effective_tier
    except PlatformSubscription.DoesNotExist:
        return 'explorer'


def _full_row(financing) -> dict:
    return {
        'id': financing.id,
        'company_id': financing.company.id,
        'company_name': financing.company.name,
        'company_ticker': financing.company.ticker_symbol,
        'company_exchange': financing.company.exchange,
        'financing_type': financing.financing_type,
        'financing_type_display': dict(Financing.FINANCING_TYPES).get(
            financing.financing_type, financing.financing_type
        ),
        'status': financing.status,
        'amount_raised_usd': str(financing.amount_raised_usd) if financing.amount_raised_usd else None,
        'price_per_share': str(financing.price_per_share) if financing.price_per_share else None,
        'shares_issued': financing.shares_issued,
        'has_warrants': financing.has_warrants,
        'warrant_strike_price': str(financing.warrant_strike_price) if financing.warrant_strike_price else None,
        'warrant_expiry_date': financing.warrant_expiry_date.isoformat() if financing.warrant_expiry_date else None,
        'announced_date': financing.announced_date.isoformat() if financing.announced_date else None,
        'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
        'lead_agent': financing.lead_agent,
        'use_of_proceeds': financing.use_of_proceeds,
        'press_release_url': financing.press_release_url,
        'notes': financing.notes,
        'is_locked': False,
    }


def _locked_row(financing) -> dict:
    """A redacted row for free users — only company identity + type leaks."""
    return {
        'id': financing.id,
        'company_id': financing.company.id,
        'company_name': financing.company.name,
        'company_ticker': financing.company.ticker_symbol,
        'company_exchange': financing.company.exchange,
        'financing_type': financing.financing_type,
        'financing_type_display': dict(Financing.FINANCING_TYPES).get(
            financing.financing_type, financing.financing_type
        ),
        'status': None,
        'amount_raised_usd': None,
        'price_per_share': None,
        'shares_issued': None,
        'has_warrants': None,
        'warrant_strike_price': None,
        'warrant_expiry_date': None,
        'announced_date': None,
        'closing_date': None,
        'lead_agent': None,
        'use_of_proceeds': None,
        'press_release_url': None,
        'notes': None,
        'is_locked': True,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def open_financings_list(request):
    """
    GET /api/open-financings/

    Public endpoint. Lists all open (non-closed) financings. Free users get
    the first 5 in full, plus locked stubs for the rest. Paid users get
    everything.

    Query params (only honored for paid users; ignored for explorers so the
    upgrade teaser stays consistent):
      - financing_type
      - sort_by    : announced_date | closing_date | amount | company
      - sort_order : asc | desc (default desc)
    """
    tier = _resolve_effective_tier(request.user)
    is_paid = tier in PAID_TIERS

    queryset = Financing.objects.filter(is_closed=False).select_related('company')

    # Filters are paid-only. For free users we want a stable, predictable
    # preview ordered by recency so the teaser composition doesn't shift.
    if is_paid:
        financing_type_filter = request.query_params.get('financing_type')
        if financing_type_filter:
            queryset = queryset.filter(financing_type=financing_type_filter)

        sort_by = request.query_params.get('sort_by', 'announced_date')
        sort_order = request.query_params.get('sort_order', 'desc')
        sort_mapping = {
            'announced_date': 'announced_date',
            'closing_date': 'closing_date',
            'amount': 'amount_raised_usd',
            'company': 'company__name',
        }
        sort_field = sort_mapping.get(sort_by, 'announced_date')
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        queryset = queryset.order_by(sort_field)
    else:
        queryset = queryset.order_by('-announced_date')

    total_count = queryset.count()

    if is_paid:
        rows = [_full_row(f) for f in queryset]
    else:
        # Materialize once, then split into preview + locked stubs.
        all_financings = list(queryset)
        preview = all_financings[:FREE_PREVIEW_COUNT]
        locked = all_financings[FREE_PREVIEW_COUNT:]
        rows = [_full_row(f) for f in preview] + [_locked_row(f) for f in locked]

    financing_types = [
        {'value': ft[0], 'label': ft[1]}
        for ft in Financing.FINANCING_TYPES
    ]

    return Response({
        'count': len(rows),
        'total_count': total_count,
        'locked_count': max(0, total_count - FREE_PREVIEW_COUNT) if not is_paid else 0,
        'user_tier': tier,
        'is_paid': is_paid,
        'preview_count': FREE_PREVIEW_COUNT,
        'results': rows,
        'financing_types': financing_types,
    })
