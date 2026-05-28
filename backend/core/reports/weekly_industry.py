"""
Pure data-collection queries for the Friday weekly industry report.

No side effects. Each function takes a `week_ending` date (the Friday whose
close anchors the report) and returns JSON-serializable Python primitives so
the entire result can be frozen into `WeeklyIndustryReport.data_snapshot`.

Window convention: trailing 7 calendar days, (week_ending - 7d, week_ending],
inclusive of the anchor Friday.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, pstdev
from typing import Any

from django.db.models import Avg, Sum, Q

from core.models import (
    Company,
    CommodityPrice,
    Document,
    Financing,
    MetalPrice,
    NewsArticle,
    NewsRelease,
    Project,
    StockPrice,
)


WEEK_DAYS = 7
WINDOW_TOLERANCE_DAYS = 4  # accept latest StockPrice within this many days of anchor

# Filter knobs for stock movers — recommended defaults from the design doc.
MIN_ABS_RETURN_PCT = 5.0
MIN_AVG_WEEKLY_DOLLAR_VOLUME_CAD = 50_000

# Document types treated as "new technical reports" in the report.
TECHNICAL_REPORT_TYPES = ('ni43101',)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def get_week_window(week_ending: date) -> tuple[date, date]:
    """Return (start, end) inclusive dates for the report window."""
    return week_ending - timedelta(days=WEEK_DAYS), week_ending


def _d(value) -> float | None:
    """Decimal/None -> float/None, JSON-safe."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _pct_change(start: Decimal | float | None, end: Decimal | float | None) -> float | None:
    if start in (None, 0) or end is None:
        return None
    start_f, end_f = float(start), float(end)
    if start_f == 0:
        return None
    return (end_f - start_f) / start_f * 100.0


def _zscore(value: float, population: list[float]) -> float | None:
    """Population Z-score; returns None if cohort too small or zero stdev."""
    if len(population) < 3:
        return None
    sd = pstdev(population)
    if sd == 0:
        return None
    return (value - mean(population)) / sd


# ---------------------------------------------------------------------------
# stock movers
# ---------------------------------------------------------------------------

def _latest_price_on_or_before(company_id: int, anchor: date) -> StockPrice | None:
    """Most recent StockPrice for company on or before anchor, within tolerance."""
    cutoff = anchor - timedelta(days=WINDOW_TOLERANCE_DAYS)
    return (
        StockPrice.objects
        .filter(company_id=company_id, date__lte=anchor, date__gte=cutoff)
        .order_by('-date')
        .first()
    )


def _avg_weekly_dollar_volume(company_id: int, week_ending: date) -> float:
    """Average daily $-volume * 5 over the trailing week."""
    start, end = get_week_window(week_ending)
    rows = StockPrice.objects.filter(
        company_id=company_id, date__gt=start, date__lte=end,
    ).values_list('close_price', 'volume')
    if not rows:
        return 0.0
    daily = [float(p) * int(v or 0) for p, v in rows if p is not None]
    if not daily:
        return 0.0
    return mean(daily) * 5


def get_stock_movers(
    week_ending: date,
    min_abs_return_pct: float = MIN_ABS_RETURN_PCT,
    min_avg_weekly_dollar_volume: float = MIN_AVG_WEEKLY_DOLLAR_VOLUME_CAD,
) -> list[dict[str, Any]]:
    """
    Compute weekly returns for every company with StockPrice in the window,
    apply liquidity + absolute-move floors, then annotate each row with a
    sector-relative Z-score (within the company's primary_commodity cohort).

    Cohort is taken from the company's flagship project (or first active
    project) primary_commodity. Companies with no project commodity fall into
    cohort 'other' and skip Z-scoring.
    """
    start, end = get_week_window(week_ending)

    candidate_company_ids = set(
        StockPrice.objects
        .filter(date__gt=start, date__lte=end)
        .values_list('company_id', flat=True)
        .distinct()
    )

    # Pre-load primary commodities per company (flagship preferred, then first active).
    commodity_by_company: dict[int, str] = {}
    proj_qs = Project.objects.filter(
        company_id__in=candidate_company_ids, is_active=True,
    ).order_by('company_id', '-is_flagship', 'id').values_list(
        'company_id', 'primary_commodity',
    )
    for company_id, commodity in proj_qs:
        commodity_by_company.setdefault(company_id, commodity or 'other')

    companies = {
        c.id: c for c in Company.objects.filter(id__in=candidate_company_ids)
    }

    raw: list[dict[str, Any]] = []
    for company_id in candidate_company_ids:
        company = companies.get(company_id)
        if not company:
            continue

        start_price = _latest_price_on_or_before(company_id, start)
        end_price = _latest_price_on_or_before(company_id, end)
        if not start_price or not end_price:
            continue

        ret_pct = _pct_change(start_price.close_price, end_price.close_price)
        if ret_pct is None or abs(ret_pct) < min_abs_return_pct:
            continue

        avg_dvol = _avg_weekly_dollar_volume(company_id, week_ending)
        if avg_dvol < min_avg_weekly_dollar_volume:
            continue

        raw.append({
            'company_id': company.id,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'primary_commodity': commodity_by_company.get(company_id, 'other'),
            'start_date': start_price.date.isoformat(),
            'start_close': _d(start_price.close_price),
            'end_date': end_price.date.isoformat(),
            'end_close': _d(end_price.close_price),
            'weekly_return_pct': round(ret_pct, 2),
            'avg_weekly_dollar_volume_cad': round(avg_dvol, 2),
            'market_cap_usd': _d(company.market_cap_usd),
            'currency': end_price.currency,
        })

    # Sector-relative Z-scores
    by_cohort: dict[str, list[float]] = defaultdict(list)
    for row in raw:
        by_cohort[row['primary_commodity']].append(row['weekly_return_pct'])

    for row in raw:
        cohort_returns = by_cohort[row['primary_commodity']]
        z = _zscore(row['weekly_return_pct'], cohort_returns)
        row['sector_zscore'] = round(z, 2) if z is not None else None

    raw.sort(key=lambda r: abs(r['weekly_return_pct']), reverse=True)
    return raw


# ---------------------------------------------------------------------------
# metal prices
# ---------------------------------------------------------------------------

def get_metal_changes(week_ending: date) -> list[dict[str, Any]]:
    """
    For each tracked metal: latest price, WoW change, and a 4-week trend
    direction ('up', 'down', 'flat') based on linear sign of the daily series.
    """
    out: list[dict[str, Any]] = []
    for metal_code, metal_label in MetalPrice.METAL_CHOICES:
        daily = MetalPrice.get_daily_series(metal_code, days=35)
        if not daily:
            continue

        # Anchor: last quote on/before week_ending
        in_window = [p for p in daily if p.day <= week_ending]
        if not in_window:
            continue
        end_q = in_window[-1]

        # Prior week: last quote on/before week_ending - 7d
        prior_cutoff = week_ending - timedelta(days=WEEK_DAYS)
        prior = [p for p in in_window if p.day <= prior_cutoff]
        start_q = prior[-1] if prior else None

        wow_pct = (
            _pct_change(start_q.bid_price, end_q.bid_price) if start_q else None
        )

        # 4-week trend: compare first vs last in last 28 days
        four_weeks = [p for p in in_window if p.day >= week_ending - timedelta(days=28)]
        if len(four_weeks) >= 2:
            trend_pct = _pct_change(four_weeks[0].bid_price, four_weeks[-1].bid_price) or 0
        else:
            trend_pct = 0
        if trend_pct > 1.0:
            trend = 'up'
        elif trend_pct < -1.0:
            trend = 'down'
        else:
            trend = 'flat'

        out.append({
            'metal': metal_code,
            'label': metal_label,
            'unit': end_q.unit,
            'end_price': _d(end_q.bid_price),
            'end_date': end_q.day.isoformat(),
            'start_price': _d(start_q.bid_price) if start_q else None,
            'wow_change_pct': round(wow_pct, 2) if wow_pct is not None else None,
            'trend_4w': trend,
            'trend_4w_pct': round(trend_pct, 2),
        })
    return out


# ---------------------------------------------------------------------------
# financings
# ---------------------------------------------------------------------------

def get_financings_in_window(week_ending: date) -> dict[str, Any]:
    """
    Financings announced in the window. Aggregates by financing_type and by
    primary_commodity (joined through the company's flagship project).
    Excludes soft-deleted records.
    """
    start, end = get_week_window(week_ending)
    qs = (
        Financing.objects
        .filter(announced_date__gt=start, announced_date__lte=end, is_deleted=False)
        .select_related('company')
        .order_by('-amount_raised_usd')
    )

    company_ids = {f.company_id for f in qs}
    commodity_by_company: dict[int, str] = {}
    if company_ids:
        proj_qs = Project.objects.filter(
            company_id__in=company_ids, is_active=True,
        ).order_by('company_id', '-is_flagship', 'id').values_list(
            'company_id', 'primary_commodity',
        )
        for company_id, commodity in proj_qs:
            commodity_by_company.setdefault(company_id, commodity or 'other')

    items: list[dict[str, Any]] = []
    by_type: Counter = Counter()
    by_type_amount: defaultdict = defaultdict(float)
    by_commodity: Counter = Counter()
    by_commodity_amount: defaultdict = defaultdict(float)
    total = 0.0

    for f in qs:
        amount = float(f.amount_raised_usd or 0)
        commodity = commodity_by_company.get(f.company_id, 'other')
        items.append({
            'financing_id': f.id,
            'company_id': f.company_id,
            'company_name': f.company.name if f.company else '',
            'ticker': f.company.ticker_symbol if f.company else '',
            'financing_type': f.financing_type,
            'status': f.status,
            'announced_date': f.announced_date.isoformat(),
            'amount_raised_usd': amount,
            'lead_agent': f.lead_agent,
            'press_release_url': f.press_release_url,
            'primary_commodity': commodity,
        })
        total += amount
        by_type[f.financing_type] += 1
        by_type_amount[f.financing_type] += amount
        by_commodity[commodity] += 1
        by_commodity_amount[commodity] += amount

    # Pending-review count: NewsReleaseFlags awaiting review in the window
    # (proxy for financings likely undercounted because superuser is behind).
    from core.models import NewsReleaseFlag  # local import avoids circular
    pending_review = NewsReleaseFlag.objects.filter(
        status='pending',
        news_release__release_date__gt=start,
        news_release__release_date__lte=end,
    ).count()

    return {
        'count': len(items),
        'total_amount_usd': round(total, 2),
        'pending_review_flag_count': pending_review,
        'items': items,
        'by_type': [
            {'type': t, 'count': by_type[t], 'amount_usd': round(by_type_amount[t], 2)}
            for t in by_type
        ],
        'by_commodity': [
            {'commodity': c, 'count': by_commodity[c], 'amount_usd': round(by_commodity_amount[c], 2)}
            for c in by_commodity
        ],
    }


# ---------------------------------------------------------------------------
# new technical reports (43-101, PEA, PFS, DFS)
# ---------------------------------------------------------------------------

def get_new_technical_reports(week_ending: date) -> list[dict[str, Any]]:
    """
    Documents of technical-report type with document_date in the window.
    Annotates each with company, project, and any linked EconomicStudy economics
    (NPV5, IRR, AISC, mine life) if a study was created for the same project.
    """
    start, end = get_week_window(week_ending)
    docs = (
        Document.objects
        .filter(document_type__in=TECHNICAL_REPORT_TYPES,
                document_date__gt=start, document_date__lte=end)
        .select_related('company', 'project')
        .order_by('-document_date')
    )

    out: list[dict[str, Any]] = []
    for doc in docs:
        economics = None
        if doc.project_id:
            study = (
                doc.project.economic_studies
                .filter(release_date__gte=start - timedelta(days=14))
                .order_by('-release_date')
                .first()
            )
            if study:
                economics = {
                    'study_type': study.study_type,
                    'npv_5_usd_millions': _d(study.npv_5_usd),
                    'irr_percent': _d(study.irr_percent),
                    'aisc_per_oz': _d(study.aisc_per_oz),
                    'mine_life_years': _d(study.mine_life_years),
                    'initial_capex_usd_millions': _d(study.initial_capex_usd),
                    'gold_price_assumption': _d(study.gold_price_assumption),
                }
        out.append({
            'document_id': doc.id,
            'company_id': doc.company_id,
            'company_name': doc.company.name if doc.company else '',
            'ticker': doc.company.ticker_symbol if doc.company else '',
            'project_id': doc.project_id,
            'project_name': doc.project.name if doc.project else '',
            'title': doc.title,
            'document_type': doc.document_type,
            'document_date': doc.document_date.isoformat(),
            'file_url': doc.file_url,
            'economics': economics,
        })
    return out


# ---------------------------------------------------------------------------
# material press releases
# ---------------------------------------------------------------------------

def get_material_releases(week_ending: date) -> list[dict[str, Any]]:
    """All NewsRelease rows with is_material=True in the window."""
    start, end = get_week_window(week_ending)
    releases = (
        NewsRelease.objects
        .filter(release_date__gt=start, release_date__lte=end, is_material=True)
        .select_related('company', 'project')
        .order_by('-release_date')
    )
    return [
        {
            'release_id': r.id,
            'company_id': r.company_id,
            'company_name': r.company.name if r.company else '',
            'ticker': r.company.ticker_symbol if r.company else '',
            'project_name': r.project.name if r.project else '',
            'title': r.title,
            'release_type': r.release_type,
            'release_date': r.release_date.isoformat(),
            'url': r.url,
            'summary': r.summary,
        }
        for r in releases
    ]


# ---------------------------------------------------------------------------
# emerging themes from industry news
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset("""
a an and are as at be by for from has have he her his i in is it its of on or
that the this to was we were will with you your they them their not but if so
about into over after before more most some all any new news update report
results says said per via vs amid amid amid year week day month
""".split())

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{2,}")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or '') if t.lower() not in _STOPWORDS]


def get_emerging_themes(week_ending: date, top_n: int = 10) -> list[dict[str, Any]]:
    """
    Token frequency in this week's NewsArticle titles+summaries vs the prior
    4 weeks. Returns tokens whose ratio is >= 1.5x (and appear at least 3
    times this week). Rough but effective signal for emerging themes.
    """
    start, end = get_week_window(week_ending)
    prior_start = end - timedelta(days=WEEK_DAYS + 28)
    prior_end = start  # exclusive of current window start

    this_week = NewsArticle.objects.filter(
        published_at__gt=start, published_at__lte=end,
    ).values_list('title', 'summary')

    prior = NewsArticle.objects.filter(
        published_at__gt=prior_start, published_at__lte=prior_end,
    ).values_list('title', 'summary')

    cur_counts: Counter = Counter()
    for title, summary in this_week:
        cur_counts.update(_tokens(f"{title} {summary or ''}"))

    prior_counts: Counter = Counter()
    for title, summary in prior:
        prior_counts.update(_tokens(f"{title} {summary or ''}"))

    # Per-week rate baseline (prior covers 4 weeks)
    candidates = []
    for token, n in cur_counts.most_common(200):
        if n < 3:
            continue
        prior_rate = prior_counts.get(token, 0) / 4.0
        if prior_rate == 0:
            ratio = float('inf') if n >= 3 else 0
        else:
            ratio = n / prior_rate
        if ratio >= 1.5:
            candidates.append({
                'token': token,
                'count_this_week': n,
                'avg_count_prior_4w': round(prior_rate, 2),
                'ratio': round(ratio, 2) if ratio != float('inf') else None,
                'is_new': prior_counts.get(token, 0) == 0,
            })

    candidates.sort(
        key=lambda r: (r['is_new'], r['count_this_week']),
        reverse=True,
    )
    return candidates[:top_n]


# ---------------------------------------------------------------------------
# GA4 engagement — stub
# ---------------------------------------------------------------------------

def get_ga4_top_companies(week_ending: date, top_n: int = 20) -> list[dict[str, Any]]:
    """
    Placeholder. Wired in commit 3 (GA4 client). Returns empty list when
    GA4_PROPERTY_ID / GA4_CREDENTIALS_PATH env vars are not set so the rest
    of the report still renders cleanly.
    """
    import os
    if not (os.environ.get('GA4_PROPERTY_ID') and os.environ.get('GA4_CREDENTIALS_PATH')):
        return []
    # Real implementation lives in core/reports/ga4.py once added.
    return []


# ---------------------------------------------------------------------------
# top-level collector
# ---------------------------------------------------------------------------

def collect_weekly_data(week_ending: date) -> dict[str, Any]:
    """
    One-shot collector used by the Celery task. Returns a single
    JSON-serializable dict suitable for `WeeklyIndustryReport.data_snapshot`.
    """
    start, end = get_week_window(week_ending)
    return {
        'week_ending': week_ending.isoformat(),
        'window_start': start.isoformat(),
        'window_end': end.isoformat(),
        'stock_movers': get_stock_movers(week_ending),
        'metals': get_metal_changes(week_ending),
        'financings': get_financings_in_window(week_ending),
        'technical_reports': get_new_technical_reports(week_ending),
        'material_releases': get_material_releases(week_ending),
        'emerging_themes': get_emerging_themes(week_ending),
        'ga4_top_companies': get_ga4_top_companies(week_ending),
    }
