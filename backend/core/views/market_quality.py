"""
Tools that measure the *quality* of a listing rather than its prospects.

Two endpoints:

  liquidity_screener — how tradeable a stock actually is. 71% of the companies
      tracked here have a median daily dollar volume under $5,000, which means
      an ordinary retail position cannot be exited in any reasonable time. That
      fact is invisible on every other screener, including this platform's own.

  signal_to_noise — how much of a company's news is results rather than
      corporate filler. Releases are already classified, so the ratio is
      directly measurable: sector-wide only about a quarter of junior mining
      news is drill, resource or study results.
"""

from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..entitlements import tier_gated
from ..models import Company, MarketData, NewsRelease

# Trailing sessions used for the liquidity median. Long enough to survive a
# quiet fortnight, short enough to reflect a stock that has recently woken up.
LIQUIDITY_LOOKBACK = 60

# Share of a session's volume a buyer can realistically take without moving the
# price. 20% is the conventional planning figure for thin listings.
PARTICIPATION_RATE = 0.20

# Releases that report an actual result, as opposed to corporate housekeeping.
HARD_NEWS_TYPES = ('drill_results', 'resource_update', 'study_results')

LIQUIDITY_BANDS = (
    # (label, upper bound of median daily dollar volume)
    ('untradeable', 1_000),
    ('very_thin', 5_000),
    ('thin', 25_000),
    ('moderate', 100_000),
    ('liquid', None),
)


def _band(dollar_volume):
    for label, upper in LIQUIDITY_BANDS:
        if upper is None or dollar_volume < upper:
            return label
    return 'liquid'


def _median(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (float(ordered[mid - 1]) + float(ordered[mid])) / 2


@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('results',))
def liquidity_screener(request):
    """
    How long it takes to exit a position, per company.

    GET /api/tools/liquidity-screener/?position=25000&participation=0.2&band=
    """
    try:
        position = float(request.GET.get('position', 25_000))
    except (TypeError, ValueError):
        position = 25_000.0
    position = min(max(position, 100.0), 100_000_000.0)

    try:
        participation = float(request.GET.get('participation', PARTICIPATION_RATE))
    except (TypeError, ValueError):
        participation = PARTICIPATION_RATE
    participation = min(max(participation, 0.01), 1.0)

    band_filter = request.GET.get('band', '').strip()

    cache_key = f"liquidity_screener_{request.GET.urlencode()}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    cutoff = timezone.now().date() - timedelta(days=LIQUIDITY_LOOKBACK * 2)

    # Pull recent bars for every company in one query, then reduce in Python.
    # Per-company percentile in SQL needs a window function per row and this
    # dataset is small enough that it is not worth the complexity.
    bars = (
        MarketData.objects
        .filter(date__gte=cutoff, volume__gt=0, company__is_active=True)
        .values_list('company_id', 'date', 'close_price', 'volume')
        .order_by('company_id', '-date')
    )

    per_company = {}
    for company_id, _date, close, volume in bars:
        series = per_company.setdefault(company_id, [])
        if len(series) < LIQUIDITY_LOOKBACK:
            series.append(float(close) * float(volume))

    companies = {
        c.id: c for c in Company.objects.filter(
            id__in=per_company.keys(), is_active=True, is_deleted=False
        )
    }

    results = []
    for company_id, dollar_volumes in per_company.items():
        company = companies.get(company_id)
        if not company or len(dollar_volumes) < 5:
            # Too few sessions to characterise; reporting one would be noise.
            continue

        median_dv = _median(dollar_volumes)
        tradeable_per_day = median_dv * participation
        days_to_exit = (
            round(position / tradeable_per_day, 1) if tradeable_per_day > 0 else None
        )

        results.append({
            'company_id': company.id,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'median_daily_dollar_volume': round(median_dv, 2),
            'sessions_sampled': len(dollar_volumes),
            'tradeable_per_day': round(tradeable_per_day, 2),
            'days_to_exit': days_to_exit,
            'band': _band(median_dv),
            'market_cap_usd': (
                float(company.market_cap_usd) if company.market_cap_usd else None
            ),
            'current_price': (
                float(company.current_price) if company.current_price else None
            ),
        })

    if band_filter:
        results = [r for r in results if r['band'] == band_filter]

    results.sort(key=lambda r: r['median_daily_dollar_volume'])

    distribution = {label: 0 for label, _ in LIQUIDITY_BANDS}
    for row in results:
        distribution[row['band']] += 1

    data = {
        'results': results,
        'count': len(results),
        'distribution': distribution,
        'summary': {
            'companies': len(results),
            'median_daily_dollar_volume': round(
                _median([r['median_daily_dollar_volume'] for r in results]), 2
            ),
            'under_5k': sum(
                1 for r in results if r['median_daily_dollar_volume'] < 5_000
            ),
            'position_size': position,
            'participation_rate': participation,
        },
        'assumptions': {
            'lookback_sessions': LIQUIDITY_LOOKBACK,
            'method': (
                f"Median daily dollar volume over the last {LIQUIDITY_LOOKBACK} "
                "sessions with any trading. Days to exit assumes you can be "
                f"{participation:.0%} of a session's volume without moving the "
                "price — optimistic for the thinnest names, where your own "
                "selling is the market."
            ),
            'currency': (
                "Dollar volume is in the currency the stock trades in, usually "
                "CAD. It is not converted to USD."
            ),
        },
        'bands': [label for label, _ in LIQUIDITY_BANDS],
    }

    cache.set(cache_key, data, 1800)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('results',))
def signal_to_noise(request):
    """
    Share of a company's news that reports a result rather than corporate news.

    GET /api/tools/signal-to-noise/?min_releases=10&months=0
    """
    try:
        min_releases = int(request.GET.get('min_releases', 10))
    except (TypeError, ValueError):
        min_releases = 10
    min_releases = min(max(min_releases, 1), 500)

    try:
        months = int(request.GET.get('months', 0))
    except (TypeError, ValueError):
        months = 0

    cache_key = f"signal_to_noise_{request.GET.urlencode()}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    releases = NewsRelease.objects.filter(company__is_active=True)
    if months > 0:
        releases = releases.filter(
            release_date__gte=timezone.now().date() - timedelta(days=months * 30)
        )
    # Future-dated rows would inflate recent counts; they are a known data
    # defect rather than real releases.
    releases = releases.filter(release_date__lte=timezone.now().date())

    rows = (
        releases
        .values('company_id', 'company__name', 'company__ticker_symbol',
                'company__exchange')
        .annotate(
            total=Count('id'),
            hard=Count('id', filter=Q(release_type__in=HARD_NEWS_TYPES)),
            drill=Count('id', filter=Q(release_type='drill_results')),
            financing=Count('id', filter=Q(release_type='financing')),
        )
        .filter(total__gte=min_releases)
    )

    results = []
    sector_total = sector_hard = 0
    for row in rows:
        total, hard = row['total'], row['hard']
        sector_total += total
        sector_hard += hard
        results.append({
            'company_id': row['company_id'],
            'company_name': row['company__name'],
            'ticker': row['company__ticker_symbol'],
            'exchange': row['company__exchange'],
            'total_releases': total,
            'hard_releases': hard,
            'drill_releases': row['drill'],
            'financing_releases': row['financing'],
            'signal_pct': round(100.0 * hard / total, 1) if total else 0.0,
            'financing_pct': (
                round(100.0 * row['financing'] / total, 1) if total else 0.0
            ),
        })

    results.sort(key=lambda r: r['signal_pct'], reverse=True)

    data = {
        'results': results,
        'count': len(results),
        'summary': {
            'companies': len(results),
            'sector_signal_pct': (
                round(100.0 * sector_hard / sector_total, 1) if sector_total else 0.0
            ),
            'total_releases': sector_total,
            'hard_releases': sector_hard,
            'min_releases': min_releases,
            'months': months,
        },
        'assumptions': {
            'hard_news_types': list(HARD_NEWS_TYPES),
            'method': (
                "Signal is the share of a company's press releases classified as "
                "drill results, resource updates or study results. Everything "
                "else — financings, management changes, corporate updates — is "
                "counted as noise. Classification comes from the release "
                "classifier, so a misfiled release is misfiled here too."
            ),
            'caveat': (
                "A low ratio is not automatically bad: a company in permitting "
                "or financing has little to report. Read it alongside stage."
            ),
        },
    }

    cache.set(cache_key, data, 1800)
    return Response(data)
