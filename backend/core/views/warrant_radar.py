"""
Warrant Overhang Radar.

Every junior placement issues warrants, and the terms sit buried in individual
press releases, so nobody tracks the resulting overhang in aggregate. The
Financing table already carries the strike, the expiry and the units issued for
151 live tranches across 115 companies — enough to answer the questions an
investor actually has:

  * How much cash lands in treasury if these warrants get exercised?
  * How many shares hit the market when they do?
  * What does the stock have to reach before any of that happens?
  * When does the overhang expire, and how much of it at once?

Caveat that shapes the whole endpoint: placements are sold as units of one
share plus a *fraction* of a warrant, and that fraction is stated in the press
release but is not a field on Financing. Warrant counts are therefore estimates
derived from an assumed coverage ratio, which the caller can override. Every
warrant-derived figure is labelled as an estimate in the response rather than
presented as fact.
"""

from django.core.cache import cache
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import Financing, StockPrice

# Half a warrant per unit is the sector norm.
DEFAULT_WARRANT_COVERAGE = 0.5

# Cap the tranche list on the sector-wide view so the payload stays sane.
SECTOR_TRANCHE_LIMIT = 200


def _latest_prices(company_ids):
    """Most recent close per company, as {company_id: row}."""
    prices = {}
    for row in (
        StockPrice.objects
        .filter(company_id__in=company_ids)
        .order_by('company_id', '-date')
        .values('company_id', 'close_price', 'currency', 'date')
    ):
        prices.setdefault(row['company_id'], row)
    return prices


def _build_tranches(financings, coverage, today):
    """Expand financings into priced warrant tranches against the latest close."""
    prices = _latest_prices([f.company_id for f in financings])
    tranches = []

    for fin in financings:
        strike = float(fin.warrant_strike_price)
        units = int(fin.shares_issued or 0)
        warrants = int(units * coverage)

        price_row = prices.get(fin.company_id)
        price = float(price_row['close_price']) if price_row else None
        in_the_money = bool(price and price > strike)

        shares_out = fin.company.shares_outstanding

        tranches.append({
            'financing_id': fin.id,
            'company_id': fin.company_id,
            'company_name': fin.company.name,
            'ticker': fin.company.ticker_symbol,
            'exchange': fin.company.exchange,
            'financing_type': fin.financing_type,
            'announced_date': fin.announced_date.isoformat(),
            'expiry_date': fin.warrant_expiry_date.isoformat(),
            'days_to_expiry': (fin.warrant_expiry_date - today).days,
            'strike_price': round(strike, 4),
            'current_price': round(price, 4) if price else None,
            'price_currency': price_row['currency'] if price_row else None,
            'in_the_money': in_the_money,
            # How far the stock still has to travel to make this exercisable.
            'pct_to_strike': (
                round((strike - price) / price * 100, 1)
                if price and price > 0 and not in_the_money else None
            ),
            'units_issued': units,
            'est_warrants': warrants,
            # Cash to treasury on exercise, in the strike's own currency.
            'est_proceeds': round(warrants * strike, 2),
            'est_dilution_pct': (
                round(warrants / shares_out * 100, 2)
                if shares_out and warrants else None
            ),
        })

    return tranches


def _expiry_wall(tranches):
    """Group the overhang by the calendar quarter it expires in."""
    buckets = {}
    for t in tranches:
        year, month = int(t['expiry_date'][:4]), int(t['expiry_date'][5:7])
        key = f"{year}-Q{(month - 1) // 3 + 1}"
        bucket = buckets.setdefault(key, {
            'quarter': key,
            'tranches': 0,
            'company_ids': set(),
            'est_warrants': 0,
            'est_proceeds': 0.0,
            'in_the_money': 0,
        })
        bucket['tranches'] += 1
        bucket['company_ids'].add(t['company_id'])
        bucket['est_warrants'] += t['est_warrants']
        bucket['est_proceeds'] += t['est_proceeds']
        if t['in_the_money']:
            bucket['in_the_money'] += 1

    wall = []
    for bucket in buckets.values():
        bucket['companies'] = len(bucket.pop('company_ids'))
        bucket['est_proceeds'] = round(bucket['est_proceeds'], 2)
        wall.append(bucket)
    return sorted(wall, key=lambda b: b['quarter'])


def _roll_up_companies(tranches):
    """One row per company, so the sector view is scannable."""
    by_company = {}

    for t in tranches:
        entry = by_company.get(t['company_id'])
        if entry is None:
            entry = by_company[t['company_id']] = {
                'company_id': t['company_id'],
                'company_name': t['company_name'],
                'ticker': t['ticker'],
                'exchange': t['exchange'],
                'current_price': t['current_price'],
                'price_currency': t['price_currency'],
                'tranches': 0,
                'in_the_money_tranches': 0,
                'est_warrants': 0,
                'est_proceeds_if_all_exercised': 0.0,
                'est_proceeds_in_the_money': 0.0,
                'est_dilution_pct': 0.0,
                'next_expiry': t['expiry_date'],
                'lowest_strike': t['strike_price'],
                'highest_strike': t['strike_price'],
            }

        entry['tranches'] += 1
        entry['est_warrants'] += t['est_warrants']
        entry['est_proceeds_if_all_exercised'] += t['est_proceeds']
        if t['in_the_money']:
            entry['in_the_money_tranches'] += 1
            entry['est_proceeds_in_the_money'] += t['est_proceeds']
        if t['est_dilution_pct']:
            entry['est_dilution_pct'] += t['est_dilution_pct']
        entry['next_expiry'] = min(entry['next_expiry'], t['expiry_date'])
        entry['lowest_strike'] = min(entry['lowest_strike'], t['strike_price'])
        entry['highest_strike'] = max(entry['highest_strike'], t['strike_price'])

    companies = []
    for entry in by_company.values():
        entry['est_proceeds_if_all_exercised'] = round(entry['est_proceeds_if_all_exercised'], 2)
        entry['est_proceeds_in_the_money'] = round(entry['est_proceeds_in_the_money'], 2)
        entry['est_dilution_pct'] = round(entry['est_dilution_pct'], 2) or None
        # What the stock must reach for this company's entire live warrant book
        # to be exercisable — i.e. fully funded without another placement.
        entry['fully_funded_price'] = entry['highest_strike']
        entry['pct_to_fully_funded'] = (
            round((entry['highest_strike'] - entry['current_price'])
                  / entry['current_price'] * 100, 1)
            if entry['current_price'] else None
        )
        companies.append(entry)

    companies.sort(key=lambda c: c['est_proceeds_if_all_exercised'], reverse=True)
    return companies


@api_view(['GET'])
@permission_classes([AllowAny])
def warrant_radar(request):
    """
    Live warrant overhang, sector-wide or for one company.

    GET /api/tools/warrant-radar/?company_id=&coverage=0.5
    """
    try:
        coverage = float(request.GET.get('coverage', DEFAULT_WARRANT_COVERAGE))
    except (TypeError, ValueError):
        coverage = DEFAULT_WARRANT_COVERAGE
    coverage = min(max(coverage, 0.0), 1.0)

    company_id = request.GET.get('company_id', '').strip()

    cache_key = f"warrant_radar_{request.GET.urlencode()}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    today = timezone.now().date()
    queryset = Financing.objects.filter(
        has_warrants=True,
        warrant_strike_price__isnull=False,
        warrant_expiry_date__gte=today,
        shares_issued__isnull=False,
        is_deleted=False,
        company__is_active=True,
    ).select_related('company')

    if company_id.isdigit():
        queryset = queryset.filter(company_id=int(company_id))

    financings = list(queryset)
    tranches = _build_tranches(financings, coverage, today)
    tranches.sort(key=lambda t: t['expiry_date'])

    in_the_money = [t for t in tranches if t['in_the_money']]

    data = {
        'summary': {
            'live_tranches': len(tranches),
            'companies': len({t['company_id'] for t in tranches}),
            'est_warrants': sum(t['est_warrants'] for t in tranches),
            'in_the_money_tranches': len(in_the_money),
            'out_of_money_tranches': len(tranches) - len(in_the_money),
            'est_proceeds_if_all_exercised': round(sum(t['est_proceeds'] for t in tranches), 2),
            'est_proceeds_in_the_money': round(sum(t['est_proceeds'] for t in in_the_money), 2),
            'next_expiry': tranches[0]['expiry_date'] if tranches else None,
        },
        'expiry_wall': _expiry_wall(tranches),
        'companies': _roll_up_companies(tranches),
        'tranches': tranches if company_id.isdigit() else tranches[:SECTOR_TRANCHE_LIMIT],
        'tranches_truncated': (
            not company_id.isdigit() and len(tranches) > SECTOR_TRANCHE_LIMIT
        ),
        'assumptions': {
            'warrant_coverage': coverage,
            'warrants': (
                f"Warrant counts assume {coverage:g} warrant per unit issued. "
                "Financing records store units issued and the strike price, but "
                "not the warrant ratio, so warrant counts, proceeds and dilution "
                "are estimates. Adjust coverage to match a specific deal."
            ),
            'currency': (
                "Strikes and proceeds are in the currency of the original "
                "financing — usually CAD — and are compared against a close "
                "from the same exchange. They are not converted to USD."
            ),
        },
    }

    cache.set(cache_key, data, 900)
    return Response(data)
