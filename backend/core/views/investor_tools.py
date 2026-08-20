"""
Investor Tools API endpoints.
Provides data for grade ranking, peer comparison, financing flow, and sector pulse.
"""
import logging
import statistics
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum, Count, Avg, Q, F, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..entitlements import tier_gated

from ..models import (
    Company, Project, ResourceEstimate, EconomicStudy,
    Financing, MarketData, StockPrice, MetalPrice,
    NewsRelease, NewsArticle, PropertyListing,
)

logger = logging.getLogger(__name__)


def _clean_doc_title(title):
    """
    Strip scraped URL query-string cruft (e.g. '?v=011202', '?2kjnty') that
    some Document titles carry, for cleaner display. Document titles never
    legitimately contain a '?', so everything from the first one is dropped.
    """
    if not title or '?' not in title:
        return title
    return title.split('?', 1)[0].strip()


# ============================================================================
# RESOURCE GRADE RANKER
# ============================================================================

# Resource categories, per CIM definitions as used by NI 43-101.
#
# These do NOT simply add up, which is what made the old Sum() over every row
# wrong. Measured and Indicated are often restated as a single combined "M&I"
# row, so a report carrying all three has the same tonnes twice. Reserves
# (Proven/Probable) are the economically mineable part of Measured/Indicated —
# a subset, never an addition. And CIM forbids adding Inferred to M&I at all,
# because Inferred has too little geological confidence to be treated as
# equivalent, so it is carried separately rather than folded into the total.
MEASURED_INDICATED = ('measured', 'indicated')
COMBINED_MI = 'mni'
INFERRED = 'inferred'
RESERVES = ('proven', 'probable')

GRAMS_PER_TROY_OZ = 31.1035


def summarize_resources(resources, commodity):
    """Collapse one project's estimates into a category-aware summary.

    `resources` must already be narrowed to a single report vintage.
    Returns None when the rows carry nothing usable for this commodity.
    """
    def bucket(rows):
        tonnes = sum(float(r.tonnes or 0) for r in rows)
        gold = sum(float(r.gold_ounces or 0) for r in rows)
        silver = sum(float(r.silver_ounces or 0) for r in rows)
        return tonnes, gold, silver

    by_cat = {}
    for r in resources:
        by_cat.setdefault((r.category or '').lower(), []).append(r)

    # Prefer the combined M&I row when the report provides one; falling back to
    # separate Measured + Indicated only when it does not.
    if by_cat.get(COMBINED_MI):
        mi_rows = by_cat[COMBINED_MI]
    else:
        mi_rows = [r for c in MEASURED_INDICATED for r in by_cat.get(c, [])]

    inferred_rows = by_cat.get(INFERRED, [])
    reserve_rows = [r for c in RESERVES for r in by_cat.get(c, [])]

    mi_t, mi_au, mi_ag = bucket(mi_rows)
    inf_t, inf_au, inf_ag = bucket(inferred_rows)
    _, res_au, _ = bucket(reserve_rows)

    # Headline totals are M&I + Inferred, reported separately in the payload so
    # the split stays visible. Reserves are deliberately excluded from the
    # total to avoid counting the same ore twice.
    tonnes = mi_t + inf_t
    gold_oz = mi_au + inf_au
    silver_oz = mi_ag + inf_ag

    counted = mi_rows + inferred_rows
    if not counted:
        return None

    def weighted(field):
        """Tonnage-weighted grade. A plain Avg let a 140kt row outrank a 5Mt one."""
        num = den = 0.0
        for r in counted:
            g, t = getattr(r, field, None), float(r.tonnes or 0)
            if g and t:
                num += float(g) * t
                den += t
        return (num / den) if den else 0.0

    if commodity == 'silver':
        grade, ounces, unit = weighted('silver_grade_gpt'), silver_oz, 'g/t Ag'
    elif commodity == 'copper':
        grade, ounces, unit = weighted('copper_grade_pct'), tonnes, '% Cu'
    else:
        grade, ounces, unit = weighted('gold_grade_gpt'), gold_oz, 'g/t Au'

    if not grade and not ounces:
        return None

    dates = [r.report_date for r in counted if r.report_date]
    return {
        'grade': grade,
        'ounces': ounces,
        'tonnes': tonnes,
        'gold_oz': gold_oz,
        'silver_oz': silver_oz,
        'mi_oz': mi_au if commodity != 'silver' else mi_ag,
        'inferred_oz': inf_au if commodity != 'silver' else inf_ag,
        'reserve_oz': res_au,
        'grade_unit': unit,
        'categories': sorted({(r.category or '').lower() for r in counted}),
        'report_date': max(dates) if dates else None,
    }



@api_view(['GET'])
@permission_classes([AllowAny])
def grade_ranker(request):
    """
    Rank companies by resource grade and size.
    GET /api/tools/grade-ranker/?commodity=gold&sort=grade&min_ounces=0&stage=
    """
    cached_key = f"grade_ranker_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    commodity = request.GET.get('commodity', 'gold')
    sort_by = request.GET.get('sort', 'grade')
    min_ounces = float(request.GET.get('min_ounces', 0))
    stage_filter = request.GET.get('stage', '')

    projects_qs = Project.objects.filter(
        is_active=True,
        company__is_active=True,
    ).select_related('company')

    if commodity:
        projects_qs = projects_qs.filter(primary_commodity=commodity)
    if stage_filter:
        projects_qs = projects_qs.filter(project_stage=stage_filter)

    results = []
    for project in projects_qs:
        resources = list(ResourceEstimate.objects.filter(project=project))
        if not resources:
            continue

        # Only the newest estimate counts. A project restated in 2024 still has
        # its 2016 rows on file, and summing across vintages counted the same
        # deposit twice — True North read 4.2 Moz against a real ~2 Moz.
        dated = [r for r in resources if r.report_date]
        if dated:
            newest = max(r.report_date for r in dated)
            resources = [r for r in dated if r.report_date == newest]

        summary = summarize_resources(resources, commodity)
        if summary is None:
            continue

        grade = summary['grade']
        ounces = summary['ounces']
        tonnes = summary['tonnes']
        gold_oz = summary['gold_oz']
        silver_oz = summary['silver_oz']
        grade_unit = summary['grade_unit']

        if min_ounces and ounces < min_ounces:
            continue

        # Get economic study if available
        econ = EconomicStudy.objects.filter(project=project).order_by('-release_date').first()

        # Get latest stock price
        latest_price = StockPrice.objects.filter(
            company=project.company
        ).order_by('-date').first()

        results.append({
            'company_id': project.company.id,
            'company_name': project.company.name,
            'ticker': project.company.ticker_symbol,
            'exchange': project.company.exchange,
            'project_name': project.name,
            'project_stage': project.project_stage,
            'country': project.country,
            'commodity': project.primary_commodity,
            'grade': round(grade, 3),
            'grade_unit': grade_unit,
            'ounces': round(ounces, 0),
            'tonnes': round(tonnes, 0),
            'gold_oz': round(gold_oz, 0),
            'silver_oz': round(silver_oz, 0),
            'measured_indicated_oz': round(summary['mi_oz'], 0),
            'inferred_oz': round(summary['inferred_oz'], 0),
            'reserves_oz': round(summary['reserve_oz'], 0),
            'resource_categories': summary['categories'],
            'report_date': summary['report_date'].isoformat() if summary['report_date'] else None,
            'npv_usd_m': float(econ.npv_5_usd) if econ and econ.npv_5_usd else None,
            'irr_pct': float(econ.irr_percent) if econ and econ.irr_percent else None,
            'aisc': float(econ.aisc_per_oz) if econ and econ.aisc_per_oz else None,
            'stock_price': float(latest_price.close_price) if latest_price else None,
            'currency': latest_price.currency if latest_price else None,
        })

    # Sort
    if sort_by == 'grade':
        results.sort(key=lambda x: x['grade'], reverse=True)
    elif sort_by == 'ounces':
        results.sort(key=lambda x: x['ounces'], reverse=True)
    elif sort_by == 'npv':
        results.sort(key=lambda x: x['npv_usd_m'] or 0, reverse=True)
    elif sort_by == 'aisc':
        results.sort(key=lambda x: x['aisc'] or 9999)

    data = {
        'results': results,
        'count': len(results),
        'filters': {
            'commodity': commodity,
            'sort': sort_by,
            'min_ounces': min_ounces,
            'stage': stage_filter,
        },
        'commodities': [c[0] for c in Project.COMMODITY_TYPES],
        'stages': [s[0] for s in Project.PROJECT_STAGES],
    }

    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# PEER COMPARISON ENGINE
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('peers',))
def peer_comparison(request):
    """
    Compare a company against auto-detected or manual peer group.
    GET /api/tools/peer-comparison/?company_id=123
    GET /api/tools/peer-comparison/?company_ids=1,2,3,4,5
    """
    company_id = request.GET.get('company_id', '').strip()
    company_ids_raw = request.GET.get('company_ids', '')

    if company_ids_raw:
        company_ids = [int(x) for x in company_ids_raw.split(',') if x.strip().isdigit()]
    elif company_id:
        # Support both numeric ID and name/ticker search
        target = None
        if company_id.isdigit():
            target = Company.objects.filter(id=int(company_id), is_active=True).first()
        if not target:
            target = Company.objects.filter(
                Q(name__icontains=company_id) | Q(ticker_symbol__iexact=company_id),
                is_active=True,
            ).first()
        # Fuzzy fallback: try each word (stripped of punctuation) for partial match
        if not target:
            import re
            words = [re.sub(r'[^\w]', '', w) for w in company_id.split()]
            words = [w for w in words if len(w) > 2]
            if words:
                q = Q(is_active=True)
                for w in words:
                    q &= Q(name__icontains=w)
                target = Company.objects.filter(q).first()
        if not target:
            return Response({'error': f'Company not found: {company_id}'}, status=404)
        company_id = str(target.id)

        # Find peers: same primary commodity, same exchange
        flagship = Project.objects.filter(company=target, is_flagship=True).first()
        if not flagship:
            flagship = Project.objects.filter(company=target, is_active=True).first()

        if flagship:
            peer_projects = Project.objects.filter(
                primary_commodity=flagship.primary_commodity,
                is_active=True,
                company__is_active=True,
            ).exclude(company=target).values_list('company_id', flat=True).distinct()
            company_ids = [target.id] + list(peer_projects[:9])
        else:
            company_ids = [target.id]
    else:
        return Response({'error': 'Provide company_id or company_ids'}, status=400)

    companies = Company.objects.filter(id__in=company_ids, is_active=True)
    results = []

    for company in companies:
        # Resources
        resources = ResourceEstimate.objects.filter(
            project__company=company, project__is_active=True
        ).aggregate(
            total_gold_oz=Sum('gold_ounces'),
            total_silver_oz=Sum('silver_ounces'),
            avg_grade=Avg('gold_grade_gpt'),
            total_tonnes=Sum('tonnes'),
        )

        # Best economic study
        econ = EconomicStudy.objects.filter(
            project__company=company
        ).order_by('-release_date').first()

        # Latest market data
        latest_price = StockPrice.objects.filter(company=company).order_by('-date').first()
        market = MarketData.objects.filter(company=company).order_by('-date').first()

        # Financing totals
        financing_total = Financing.objects.filter(
            company=company, status='closed'
        ).aggregate(total=Sum('amount_raised_usd'))['total'] or 0

        # Project count and stage
        projects = Project.objects.filter(company=company, is_active=True)

        market_cap = float(market.market_cap_usd) if market and market.market_cap_usd else None
        gold_oz = float(resources['total_gold_oz'] or 0)

        results.append({
            'company_id': company.id,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'stock_price': float(latest_price.close_price) if latest_price else None,
            'currency': latest_price.currency if latest_price else None,
            'market_cap_usd': market_cap,
            'total_gold_oz': gold_oz,
            'total_silver_oz': float(resources['total_silver_oz'] or 0),
            'avg_grade_gpt': round(float(resources['avg_grade'] or 0), 3),
            'total_tonnes': float(resources['total_tonnes'] or 0),
            'ev_per_oz': round(market_cap / gold_oz, 2) if market_cap and gold_oz > 0 else None,
            'npv_usd_m': float(econ.npv_5_usd) if econ and econ.npv_5_usd else None,
            'p_nav': round(market_cap / (float(econ.npv_5_usd) * 1_000_000), 2) if market_cap and econ and econ.npv_5_usd and float(econ.npv_5_usd) > 0 else None,
            'irr_pct': float(econ.irr_percent) if econ and econ.irr_percent else None,
            'aisc': float(econ.aisc_per_oz) if econ and econ.aisc_per_oz else None,
            'total_financing_usd': float(financing_total),
            'project_count': projects.count(),
            'flagship_stage': projects.filter(is_flagship=True).values_list('project_stage', flat=True).first(),
        })

    # Sort by market cap descending
    results.sort(key=lambda x: x['market_cap_usd'] or 0, reverse=True)

    return Response({
        'peers': results,
        'count': len(results),
        'target_id': int(company_id) if company_id else None,
    })


# ============================================================================
# FINANCING FLOW TRACKER
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('top_companies', 'recent'))
def financing_flow(request):
    """
    Track financing activity trends across the sector.
    GET /api/tools/financing-flow/?months=6&commodity=&type=
    """
    cached_key = f"financing_flow_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    months = int(request.GET.get('months', 6))
    commodity_filter = request.GET.get('commodity', '')
    type_filter = request.GET.get('type', '')

    start_date = timezone.now().date() - timedelta(days=months * 30)

    financings = Financing.objects.filter(
        announced_date__gte=start_date,
    ).select_related('company')

    if commodity_filter:
        company_ids = Project.objects.filter(
            primary_commodity=commodity_filter, is_active=True
        ).values_list('company_id', flat=True)
        financings = financings.filter(company_id__in=company_ids)

    if type_filter:
        financings = financings.filter(financing_type=type_filter)

    # Monthly volume trend
    monthly = financings.annotate(
        month=TruncMonth('announced_date')
    ).values('month').annotate(
        count=Count('id'),
        total_usd=Sum('amount_raised_usd'),
    ).order_by('month')

    # By financing type
    by_type = financings.values('financing_type').annotate(
        count=Count('id'),
        total_usd=Sum('amount_raised_usd'),
        avg_usd=Avg('amount_raised_usd'),
    ).order_by('-total_usd')

    # Top companies by amount raised
    top_companies = financings.values(
        'company__id', 'company__name', 'company__ticker_symbol'
    ).annotate(
        count=Count('id'),
        total_usd=Sum('amount_raised_usd'),
    ).order_by('-total_usd')[:10]

    # By commodity (via projects)
    by_commodity = []
    commodity_ids = {}
    for f in financings:
        flagship = Project.objects.filter(
            company=f.company, is_active=True
        ).order_by('-is_flagship').first()
        if flagship:
            comm = flagship.primary_commodity
            if comm not in commodity_ids:
                commodity_ids[comm] = {'commodity': comm, 'count': 0, 'total_usd': 0}
            commodity_ids[comm]['count'] += 1
            commodity_ids[comm]['total_usd'] += float(f.amount_raised_usd or 0)

    by_commodity = sorted(commodity_ids.values(), key=lambda x: x['total_usd'], reverse=True)

    # Recent notable financings
    recent = financings.order_by('-amount_raised_usd')[:15]
    recent_list = [{
        'id': f.id,
        'company_id': f.company.id,
        'company_name': f.company.name,
        'ticker': f.company.ticker_symbol,
        'type': f.financing_type,
        'amount_usd': float(f.amount_raised_usd or 0),
        'price_per_share': float(f.price_per_share) if f.price_per_share else None,
        'announced_date': f.announced_date.isoformat(),
        'status': f.status,
        'has_warrants': f.has_warrants,
    } for f in recent]

    data = {
        'monthly_trend': [
            {'month': m['month'].isoformat(), 'count': m['count'], 'total_usd': float(m['total_usd'] or 0)}
            for m in monthly
        ],
        'by_type': [
            {'type': t['financing_type'], 'count': t['count'], 'total_usd': float(t['total_usd'] or 0), 'avg_usd': float(t['avg_usd'] or 0)}
            for t in by_type
        ],
        'by_commodity': by_commodity,
        'top_companies': [
            {'company_id': c['company__id'], 'company_name': c['company__name'], 'ticker': c['company__ticker_symbol'], 'count': c['count'], 'total_usd': float(c['total_usd'] or 0)}
            for c in top_companies
        ],
        'recent': recent_list,
        'summary': {
            'total_count': financings.count(),
            'total_usd': float(financings.aggregate(t=Sum('amount_raised_usd'))['t'] or 0),
            'period_months': months,
        },
        'financing_types': [t[0] for t in Financing.FINANCING_TYPES],
        # Financing.amount_raised_usd is a misnomer — it stores the raise in the
        # deal's own currency, which for this universe is overwhelmingly CAD.
        # Reporting these totals as USD overstated them by the CAD/USD spread,
        # so the currency is declared rather than assumed. The `*_usd` keys keep
        # their names to avoid breaking existing callers.
        'currency': 'CAD',
        'currency_note': (
            "Amounts are in each financing's own currency, which for the "
            "TSX/TSXV/CSE listings that dominate this data is Canadian dollars. "
            "They are not converted to USD."
        ),
    }

    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# SECTOR PULSE DASHBOARD
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def sector_pulse(request):
    """
    Real-time sector overview with metals, market breadth, and news.
    GET /api/tools/sector-pulse/
    """
    cached = cache.get('sector_pulse')
    if cached:
        return Response(cached)

    today = timezone.now().date()

    # 1. Latest metals prices
    metals_list = []
    for symbol in ['XAU', 'XAG', 'XPT', 'XPD']:
        mp = MetalPrice.objects.filter(metal=symbol).order_by('-scraped_at').first()
        if mp:
            metals_list.append({
                'symbol': symbol,
                'name': mp.get_metal_display(),
                'price': float(mp.bid_price),
                'change_pct': float(mp.change_percent),
                'updated': mp.scraped_at.isoformat(),
            })

    # 2. Market breadth - % of stocks up/down in last trading day
    latest_date = StockPrice.objects.aggregate(d=Max('date'))['d']
    if latest_date:
        day_prices = StockPrice.objects.filter(date=latest_date)
        total = day_prices.count()
        up = day_prices.filter(change_percent__gt=0).count()
        down = day_prices.filter(change_percent__lt=0).count()
        flat = total - up - down
        avg_change = day_prices.aggregate(a=Avg('change_percent'))['a'] or 0
    else:
        total = up = down = flat = 0
        avg_change = 0

    breadth = {
        'date': latest_date.isoformat() if latest_date else None,
        'total_stocks': total,
        'up': up,
        'down': down,
        'flat': flat,
        'up_pct': round(up / total * 100, 1) if total else 0,
        'avg_change_pct': round(float(avg_change), 2),
    }

    # 3. Top gainers/losers
    gainers = []
    losers = []
    if latest_date:
        top_g = StockPrice.objects.filter(date=latest_date).order_by('-change_percent')[:5]
        top_l = StockPrice.objects.filter(date=latest_date, change_percent__lt=0).order_by('change_percent')[:5]
        for sp in top_g:
            gainers.append({
                'company_id': sp.company_id,
                'company_name': sp.company.name,
                'ticker': sp.company.ticker_symbol,
                'price': float(sp.close_price),
                'change_pct': float(sp.change_percent),
            })
        for sp in top_l:
            losers.append({
                'company_id': sp.company_id,
                'company_name': sp.company.name,
                'ticker': sp.company.ticker_symbol,
                'price': float(sp.close_price),
                'change_pct': float(sp.change_percent),
            })

    # 4. Financing activity summary (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent_financings = Financing.objects.filter(announced_date__gte=thirty_days_ago)
    financing_summary = {
        'count_30d': recent_financings.count(),
        'total_usd_30d': float(recent_financings.aggregate(t=Sum('amount_raised_usd'))['t'] or 0),
    }

    # 5. News activity
    recent_news_count = NewsRelease.objects.filter(
        release_date__gte=today - timedelta(days=7)
    ).count()
    recent_articles_count = NewsArticle.objects.filter(
        published_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    data = {
        'metals': metals_list,
        'breadth': breadth,
        'gainers': gainers,
        'losers': losers,
        'financing': financing_summary,
        'news': {
            'press_releases_7d': recent_news_count,
            'articles_7d': recent_articles_count,
        },
        'timestamp': timezone.now().isoformat(),
    }

    cache.set('sector_pulse', data, 300)
    return Response(data)


# ============================================================================
# DRILL RESULT SCANNER
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('results',))
def drill_scanner(request):
    """
    Search news releases for drill results. Returns recent drill-related news.
    GET /api/tools/drill-scanner/?commodity=gold&days=30&company=
    """
    days = min(int(request.GET.get('days', 30)), 90)
    commodity = request.GET.get('commodity', '')
    company_search = request.GET.get('company', '').strip()

    start_date = timezone.now().date() - timedelta(days=days)

    DRILL_KEYWORDS = [
        'drill', 'assay', 'intercept', 'metres', 'meters', 'g/t', 'gpt',
        'mineralization', 'mineralized', 'hole', 'core', 'exploration results',
        'sampling', 'trench', 'channel sample',
    ]

    q_filter = Q(release_date__gte=start_date)
    keyword_q = Q()
    for kw in DRILL_KEYWORDS:
        keyword_q |= Q(title__icontains=kw)
    q_filter &= keyword_q

    if company_search:
        q_filter &= Q(company__name__icontains=company_search) | Q(company__ticker_symbol__iexact=company_search)

    if commodity:
        commodity_companies = Project.objects.filter(
            primary_commodity=commodity, is_active=True
        ).values_list('company_id', flat=True)
        q_filter &= Q(company_id__in=commodity_companies)

    releases = NewsRelease.objects.filter(q_filter).select_related('company').order_by('-release_date')[:50]

    results = [{
        'id': nr.id,
        'company_id': nr.company_id,
        'company_name': nr.company.name,
        'ticker': nr.company.ticker_symbol,
        'title': nr.title,
        'published_date': nr.release_date.isoformat() if nr.release_date else None,
        'url': nr.url,
    } for nr in releases]

    # Company counts
    company_counts = {}
    for r in results:
        cid = r['company_id']
        if cid not in company_counts:
            company_counts[cid] = {'company_name': r['company_name'], 'ticker': r['ticker'], 'count': 0}
        company_counts[cid]['count'] += 1

    most_active = sorted(company_counts.values(), key=lambda x: x['count'], reverse=True)[:10]

    return Response({
        'results': results,
        'count': len(results),
        'most_active_drillers': most_active,
        'period_days': days,
    })


# ============================================================================
# NEWS CATALYST CALENDAR
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('companies', 'quiet_companies'))
def catalyst_calendar(request):
    """
    Recent news releases grouped by company with activity frequency analysis.
    GET /api/tools/catalyst-calendar/?days=60&commodity=
    """
    days = min(int(request.GET.get('days', 60)), 180)
    commodity = request.GET.get('commodity', '')

    start_date = timezone.now().date() - timedelta(days=days)

    releases_qs = NewsRelease.objects.filter(
        release_date__gte=start_date,
        company__is_active=True,
    ).select_related('company')

    if commodity:
        commodity_companies = Project.objects.filter(
            primary_commodity=commodity, is_active=True
        ).values_list('company_id', flat=True)
        releases_qs = releases_qs.filter(company_id__in=commodity_companies)

    # Group by company with counts and last release date
    company_data = {}
    for nr in releases_qs.order_by('-release_date'):
        cid = nr.company_id
        if cid not in company_data:
            company_data[cid] = {
                'company_id': cid,
                'company_name': nr.company.name,
                'ticker': nr.company.ticker_symbol,
                'releases': [],
                'count': 0,
                'latest_date': None,
                'earliest_date': None,
            }
        cd = company_data[cid]
        cd['count'] += 1
        pub = nr.release_date.isoformat() if nr.release_date else None
        if pub:
            if not cd['latest_date'] or pub > cd['latest_date']:
                cd['latest_date'] = pub
            if not cd['earliest_date'] or pub < cd['earliest_date']:
                cd['earliest_date'] = pub
        if len(cd['releases']) < 5:
            cd['releases'].append({
                'id': nr.id,
                'title': nr.title,
                'date': pub,
                'url': nr.url,
            })

    # Calculate days since last release and avg frequency
    for cd in company_data.values():
        if cd['latest_date']:
            from datetime import date as dt_date
            latest = dt_date.fromisoformat(cd['latest_date'])
            cd['days_since_last'] = (timezone.now().date() - latest).days
        else:
            cd['days_since_last'] = None
        if cd['count'] > 1 and cd['earliest_date'] and cd['latest_date']:
            earliest = dt_date.fromisoformat(cd['earliest_date'])
            latest = dt_date.fromisoformat(cd['latest_date'])
            span = (latest - earliest).days
            cd['avg_days_between'] = round(span / (cd['count'] - 1), 1) if span > 0 else None
        else:
            cd['avg_days_between'] = None

    companies_list = sorted(company_data.values(), key=lambda x: x['count'], reverse=True)

    # Quiet companies (no news in last 30 days but had news before)
    quiet = [c for c in companies_list if c['days_since_last'] and c['days_since_last'] > 30]

    # Weekly news volume
    weekly = releases_qs.annotate(
        week=TruncWeek('release_date')
    ).values('week').annotate(count=Count('id')).order_by('week')

    return Response({
        'companies': companies_list[:50],
        'quiet_companies': quiet[:20],
        'weekly_volume': [{'week': w['week'].isoformat(), 'count': w['count']} for w in weekly],
        'total_releases': releases_qs.count(),
        'period_days': days,
    })


# ============================================================================
# PORTFOLIO X-RAY
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('holdings',))
def portfolio_xray(request):
    """
    Analyze a set of companies for exposure, diversification, and risk.
    GET /api/tools/portfolio-xray/?company_ids=1,2,3,4,5
    """
    company_ids_raw = request.GET.get('company_ids', '')
    if not company_ids_raw:
        return Response({'error': 'Provide company_ids (comma-separated)'}, status=400)

    company_ids = [int(x) for x in company_ids_raw.split(',') if x.strip().isdigit()]
    if not company_ids:
        return Response({'error': 'No valid company IDs provided'}, status=400)

    companies = Company.objects.filter(id__in=company_ids, is_active=True)

    # Build portfolio analysis
    holdings = []
    commodity_exposure = {}
    country_exposure = {}
    stage_exposure = {}
    total_market_cap = 0

    for company in companies:
        projects = Project.objects.filter(company=company, is_active=True)
        latest_price = StockPrice.objects.filter(company=company).order_by('-date').first()
        market = MarketData.objects.filter(company=company).order_by('-date').first()
        resources = ResourceEstimate.objects.filter(
            project__company=company
        ).aggregate(gold_oz=Sum('gold_ounces'), silver_oz=Sum('silver_ounces'))

        mcap = float(market.market_cap_usd) if market and market.market_cap_usd else 0
        total_market_cap += mcap

        # Upcoming financing risk
        open_financings = Financing.objects.filter(
            company=company, status__in=['announced', 'closing']
        ).count()

        flagship = projects.filter(is_flagship=True).first() or projects.first()

        holdings.append({
            'company_id': company.id,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'stock_price': float(latest_price.close_price) if latest_price else None,
            'change_pct': float(latest_price.change_percent) if latest_price else None,
            'market_cap_usd': mcap,
            'gold_oz': float(resources['gold_oz'] or 0),
            'silver_oz': float(resources['silver_oz'] or 0),
            'project_count': projects.count(),
            'commodity': flagship.primary_commodity if flagship else None,
            'country': flagship.country if flagship else None,
            'stage': flagship.project_stage if flagship else None,
            'open_financings': open_financings,
        })

        # Exposure tracking
        if flagship:
            comm = flagship.primary_commodity
            commodity_exposure[comm] = commodity_exposure.get(comm, 0) + 1
            country = flagship.country
            country_exposure[country] = country_exposure.get(country, 0) + 1
            stage = flagship.project_stage
            stage_exposure[stage] = stage_exposure.get(stage, 0) + 1

    total_companies = len(holdings)

    def to_pct_list(d):
        return sorted([
            {'name': k, 'count': v, 'pct': round(v / total_companies * 100, 1) if total_companies else 0}
            for k, v in d.items()
        ], key=lambda x: x['count'], reverse=True)

    # Dilution risk: companies with open financings
    dilution_risks = [h for h in holdings if h['open_financings'] > 0]

    return Response({
        'holdings': holdings,
        'count': total_companies,
        'total_market_cap_usd': total_market_cap,
        'commodity_exposure': to_pct_list(commodity_exposure),
        'country_exposure': to_pct_list(country_exposure),
        'stage_exposure': to_pct_list(stage_exposure),
        'dilution_risks': dilution_risks,
    })


# ============================================================================
# PROPERTY VALUATION TOOL
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('listings',))
def property_valuation(request):
    """
    Property comparables and valuation benchmarks.
    GET /api/tools/property-valuation/?mineral=gold&country=Canada
    """
    mineral = request.GET.get('mineral', '')
    country = request.GET.get('country', '')

    listings = PropertyListing.objects.filter(
        status='active'
    ).select_related('prospector').order_by('-created_at')

    if mineral:
        listings = listings.filter(primary_mineral__iexact=mineral)
    if country:
        # `country` is stored as a short code (CA, US); accept either code or display name
        code = country.strip()
        for c_code, c_label in PropertyListing.COUNTRIES:
            if c_label.lower() == code.lower():
                code = c_code
                break
        listings = listings.filter(country__iexact=code)

    results = []
    for p in listings[:30]:
        hectares = float(p.total_hectares) if p.total_hectares else None
        price = float(p.asking_price) if p.asking_price else None
        price_per_ha = round(price / hectares, 2) if price and hectares and hectares > 0 else None

        # No single `location` column — compose one from the geographic fields.
        location = ', '.join(
            part for part in (p.nearest_town, p.region_district, p.province_state) if part
        )

        results.append({
            'id': p.id,
            'slug': p.slug,
            'title': p.title,
            'location': location,
            'country': p.get_country_display(),
            'primary_mineral': p.primary_mineral,
            'exploration_stage': p.exploration_stage,
            'total_hectares': hectares,
            'asking_price': price,
            'price_currency': p.price_currency,
            'price_per_hectare': price_per_ha,
            'listing_type': p.listing_type,
        })

    # Benchmarks
    priced = [r for r in results if r['price_per_hectare']]
    benchmarks = {}
    if priced:
        prices = [r['price_per_hectare'] for r in priced]
        benchmarks = {
            'avg_price_per_ha': round(sum(prices) / len(prices), 2),
            'min_price_per_ha': min(prices),
            'max_price_per_ha': max(prices),
            'median_price_per_ha': round(sorted(prices)[len(prices) // 2], 2),
            'sample_size': len(priced),
        }

    # Distinct values for filters
    active = PropertyListing.objects.filter(status='active')
    minerals = list(active.values_list('primary_mineral', flat=True).distinct().order_by('primary_mineral'))
    country_codes = active.values_list('country', flat=True).distinct().order_by('country')
    country_labels = dict(PropertyListing.COUNTRIES)
    countries = [country_labels.get(c, c) for c in country_codes]

    return Response({
        'listings': results,
        'count': len(results),
        'benchmarks': benchmarks,
        'filters': {
            'minerals': minerals,
            'countries': countries,
        },
        # Let the frontend distinguish "no match for your filters" from
        # "the marketplace has no active listings yet".
        'total_active_listings': active.count(),
    })


# ============================================================================
# STOCK PERFORMANCE COMPARATOR
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('series', 'summary'))
def stock_comparison(request):
    """
    Compare normalized share-price performance of up to 10 companies.
    GET /api/tools/stock-comparison/?company_ids=1,2,3&days=90

    With no company_ids, returns just the available-companies list (those
    that have price history) so the frontend can populate its picker.
    Each series is normalized to its first day = 0% so curves are comparable
    regardless of share price.
    """
    cached_key = f"stock_comparison_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    days = max(7, min(int(request.GET.get('days', 90)), 400))
    company_ids_raw = request.GET.get('company_ids', '')
    company_ids = [
        int(x) for x in company_ids_raw.split(',') if x.strip().isdigit()
    ][:10]

    # Companies that have price history - powers the frontend company picker.
    priced_ids = StockPrice.objects.values_list('company_id', flat=True).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=priced_ids, is_active=True
        ).order_by('name')
    ]

    series = []
    summary = []
    start_date = timezone.now().date() - timedelta(days=days)

    for cid in company_ids:
        company = Company.objects.filter(id=cid, is_active=True).first()
        if not company:
            continue
        prices = list(
            StockPrice.objects.filter(
                company=company, date__gte=start_date
            ).order_by('date')
        )
        if len(prices) < 2:
            summary.append({
                'company_id': cid,
                'company_name': company.name,
                'ticker': company.ticker_symbol,
                'error': 'Not enough price history in this window.',
            })
            continue

        base = float(prices[0].close_price)
        points = []
        daily_returns = []
        prev_close = None
        for p in prices:
            close = float(p.close_price)
            points.append({
                'date': p.date.isoformat(),
                'close': round(close, 4),
                'pct': round((close - base) / base * 100, 2) if base else 0,
            })
            if prev_close:
                daily_returns.append((close - prev_close) / prev_close)
            prev_close = close

        first, last = prices[0], prices[-1]
        end_close = float(last.close_price)
        volatility = (
            round(statistics.pstdev(daily_returns) * 100, 2)
            if len(daily_returns) >= 2 else None
        )

        series.append({
            'company_id': cid,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'currency': last.currency,
            'points': points,
        })
        summary.append({
            'company_id': cid,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'currency': last.currency,
            'start_date': first.date.isoformat(),
            'start_price': round(base, 4),
            'end_date': last.date.isoformat(),
            'end_price': round(end_close, 4),
            'pct_change': round((end_close - base) / base * 100, 2) if base else 0,
            'daily_volatility_pct': volatility,
            'data_points': len(prices),
        })

    # Rank best-to-worst by % change; rows with errors sink to the bottom.
    summary.sort(
        key=lambda s: s['pct_change'] if s.get('pct_change') is not None else -9e9,
        reverse=True,
    )

    data = {
        'available_companies': available_companies,
        'series': series,
        'summary': summary,
        'days': days,
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# RESOURCE GROWTH TRACKER
# ============================================================================

# Resource categories that can be summed without double-counting. 'mni'
# (Measured & Indicated combined) and reserve categories overlap these.
_ADDITIVE_RESOURCE_CATEGORIES = ['inferred', 'indicated', 'measured']
_RESERVE_CATEGORIES = ['proven', 'probable']


@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('projects',))
def resource_growth(request):
    """
    Show how a company's mineral resource estimates evolved over time.
    GET /api/tools/resource-growth/?company_id=1

    With no company_id, returns just the available-companies list (those that
    have resource estimates on record) for the frontend picker.
    """
    cached_key = f"resource_growth_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    # Companies that have resource estimates - powers the frontend picker.
    res_company_ids = ResourceEstimate.objects.values_list(
        'project__company_id', flat=True
    ).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=res_company_ids, is_active=True
        ).order_by('name')
    ]

    company_id_raw = request.GET.get('company_id', '').strip()
    if not company_id_raw.isdigit():
        return Response({'available_companies': available_companies, 'projects': []})

    company = Company.objects.filter(id=int(company_id_raw), is_active=True).first()
    if not company:
        return Response({'error': 'Company not found'}, status=404)

    cat_display = dict(ResourceEstimate.RESOURCE_CATEGORIES)
    projects_out = []

    for project in Project.objects.filter(company=company):
        estimates = ResourceEstimate.objects.filter(
            project=project
        ).order_by('report_date')

        # Group estimate rows by report date (one report lists several categories).
        by_date = {}
        for est in estimates:
            by_date.setdefault(est.report_date.isoformat(), []).append(est)
        if not by_date:
            continue

        timeline = []
        for report_date, rows in sorted(by_date.items()):
            categories = []
            additive_gold = 0.0
            additive_silver = 0.0
            additive_tonnes = 0.0
            reserve_gold = 0.0
            for r in rows:
                gold_oz = float(r.gold_ounces or 0)
                silver_oz = float(r.silver_ounces or 0)
                tonnes = float(r.tonnes or 0)
                if r.category in _ADDITIVE_RESOURCE_CATEGORIES:
                    additive_gold += gold_oz
                    additive_silver += silver_oz
                    additive_tonnes += tonnes
                elif r.category in _RESERVE_CATEGORIES:
                    reserve_gold += gold_oz
                categories.append({
                    'category': cat_display.get(r.category, r.category),
                    'tonnes': tonnes,
                    'gold_grade_gpt': float(r.gold_grade_gpt) if r.gold_grade_gpt else None,
                    'gold_ounces': float(r.gold_ounces) if r.gold_ounces else None,
                    'silver_ounces': float(r.silver_ounces) if r.silver_ounces else None,
                    'copper_grade_pct': (
                        float(r.copper_grade_pct) if r.copper_grade_pct else None
                    ),
                })
            timeline.append({
                'report_date': report_date,
                'standard': rows[0].get_standard_display(),
                'categories': categories,
                # Per-metric resource totals (Inferred + Indicated + Measured).
                # The frontend charts whichever metric suits the commodity.
                'resource_gold_oz': round(additive_gold, 0),
                'resource_silver_oz': round(additive_silver, 0),
                'resource_tonnes': round(additive_tonnes, 0),
                'reserve_gold_oz': round(reserve_gold, 0),
            })

        projects_out.append({
            'project_id': project.id,
            'project_name': project.name,
            'primary_commodity': project.primary_commodity,
            'estimate_count': len(timeline),
            'timeline': timeline,
        })

    data = {
        'available_companies': available_companies,
        'company': {
            'id': company.id,
            'name': company.name,
            'ticker': company.ticker_symbol,
        },
        'projects': projects_out,
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# DILUTION TRACKER
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('financings',))
def dilution_tracker(request):
    """
    Show a company's share-dilution history from its financing record.
    GET /api/tools/dilution-tracker/?company_id=1

    With no company_id, returns just the available-companies list (those that
    have financing records) for the frontend picker.
    """
    cached_key = f"dilution_tracker_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    # Companies that have financing records - powers the frontend picker.
    fin_company_ids = Financing.objects.filter(
        is_deleted=False
    ).values_list('company_id', flat=True).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=fin_company_ids, is_active=True
        ).order_by('name')
    ]

    company_id_raw = request.GET.get('company_id', '').strip()
    if not company_id_raw.isdigit():
        return Response({'available_companies': available_companies, 'financings': []})

    company = Company.objects.filter(id=int(company_id_raw), is_active=True).first()
    if not company:
        return Response({'error': 'Company not found'}, status=404)

    today = timezone.now().date()
    financings = Financing.objects.filter(
        company=company, is_deleted=False
    ).order_by('announced_date')

    rows = []
    cumulative_shares = 0
    total_shares = 0
    total_raised = 0.0
    active_warrant_tranches = 0

    for f in financings:
        shares = f.shares_issued or 0
        cumulative_shares += shares
        total_shares += shares
        total_raised += float(f.amount_raised_usd or 0)
        warrant_active = bool(
            f.has_warrants
            and f.warrant_expiry_date
            and f.warrant_expiry_date >= today
        )
        if warrant_active:
            active_warrant_tranches += 1
        rows.append({
            'id': f.id,
            'announced_date': f.announced_date.isoformat(),
            'financing_type': f.financing_type,
            'status': f.status,
            'amount_raised_usd': float(f.amount_raised_usd or 0),
            'shares_issued': f.shares_issued,
            'cumulative_shares': cumulative_shares,
            'price_per_share': float(f.price_per_share) if f.price_per_share else None,
            'has_warrants': f.has_warrants,
            'warrant_strike_price': (
                float(f.warrant_strike_price) if f.warrant_strike_price else None
            ),
            'warrant_expiry_date': (
                f.warrant_expiry_date.isoformat() if f.warrant_expiry_date else None
            ),
            'warrant_active': warrant_active,
        })

    shares_outstanding = company.shares_outstanding
    issued_pct = None
    if shares_outstanding and total_shares:
        issued_pct = round(total_shares / float(shares_outstanding) * 100, 1)

    data = {
        'available_companies': available_companies,
        'company': {
            'id': company.id,
            'name': company.name,
            'ticker': company.ticker_symbol,
        },
        'summary': {
            'current_shares_outstanding': shares_outstanding,
            'financing_count': len(rows),
            'total_shares_issued': total_shares or None,
            'total_capital_raised_usd': round(total_raised, 0),
            'issued_shares_pct_of_current': issued_pct,
            'active_warrant_tranches': active_warrant_tranches,
        },
        'financings': rows,
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# UNUSUAL ACTIVITY DETECTOR
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(window=('series',), truncate=('flagged_days',))
def unusual_activity(request):
    """
    Detect trading-volume spikes for a company and cross-reference news.
    GET /api/tools/unusual-activity/?company_id=1&days=90&volume_multiple=2.5

    With no company_id, returns just the available-companies list (those that
    have price history) for the frontend picker.
    """
    cached_key = f"unusual_activity_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    # Companies that have price history - powers the frontend picker.
    priced_ids = StockPrice.objects.values_list('company_id', flat=True).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=priced_ids, is_active=True
        ).order_by('name')
    ]

    company_id_raw = request.GET.get('company_id', '').strip()
    if not company_id_raw.isdigit():
        return Response({
            'available_companies': available_companies,
            'series': [],
            'flagged_days': [],
        })

    company = Company.objects.filter(id=int(company_id_raw), is_active=True).first()
    if not company:
        return Response({'error': 'Company not found'}, status=404)

    days = max(30, min(int(request.GET.get('days', 90)), 365))
    multiple = max(1.5, min(float(request.GET.get('volume_multiple', 2.5)), 10.0))
    trail = 20  # trailing trading days for the volume baseline

    # Over-fetch so the earliest days in the window still have a baseline.
    history = list(
        StockPrice.objects.filter(
            company=company,
            date__gte=timezone.now().date() - timedelta(days=days + 45),
        ).order_by('date')
    )

    base = {
        'available_companies': available_companies,
        'company': {
            'id': company.id,
            'name': company.name,
            'ticker': company.ticker_symbol,
        },
        'window_days': days,
        'volume_multiple': multiple,
    }

    if len(history) < trail + 5:
        data = {
            **base,
            'series': [],
            'flagged_days': [],
            'summary': {'trading_days': 0, 'unusual_days': 0, 'unexplained_days': 0},
            'message': 'Not enough price history to assess unusual volume.',
        }
        cache.set(cached_key, data, 600)
        return Response(data)

    news = list(
        NewsRelease.objects.filter(
            company=company, release_date__gte=history[0].date,
        ).order_by('release_date')
    )

    scan_start = timezone.now().date() - timedelta(days=days)
    series = []
    flagged_days = []

    for i in range(trail, len(history)):
        day = history[i]
        if day.date < scan_start or not day.volume:
            continue
        window = [h.volume for h in history[i - trail:i] if h.volume]
        if len(window) < 5:
            continue
        avg = sum(window) / len(window)
        if avg <= 0:
            continue
        ratio = day.volume / avg
        flagged = ratio >= multiple
        series.append({
            'date': day.date.isoformat(),
            'volume': day.volume,
            'trailing_avg_volume': int(avg),
            'volume_ratio': round(ratio, 2),
            'price_change_pct': float(day.change_percent or 0),
            'flagged': flagged,
        })
        if flagged:
            related = [
                n for n in news if abs((n.release_date - day.date).days) <= 2
            ]
            flagged_days.append({
                'date': day.date.isoformat(),
                'volume': day.volume,
                'trailing_avg_volume': int(avg),
                'volume_ratio': round(ratio, 1),
                'price_change_pct': float(day.change_percent or 0),
                'explained': bool(related),
                'related_news': [
                    {
                        'title': n.title,
                        'date': n.release_date.isoformat(),
                        'type': n.get_release_type_display(),
                        'url': n.url,
                    }
                    for n in related[:3]
                ],
            })

    flagged_days.sort(key=lambda d: d['volume_ratio'], reverse=True)

    data = {
        **base,
        'series': series,
        'flagged_days': flagged_days,
        'summary': {
            'trading_days': len(series),
            'unusual_days': len(flagged_days),
            'unexplained_days': sum(1 for d in flagged_days if not d['explained']),
        },
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# CATALYST IMPACT ANALYZER
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('events',))
def catalyst_impact(request):
    """
    Event study: how a company's share price historically reacted to each
    TYPE of news, measured at 1, 5 and 20 trading days after the release.
    GET /api/tools/catalyst-impact/?company_id=1&days=365

    With no company_id, returns just the available-companies list (those with
    price history) for the frontend picker.
    """
    cached_key = f"catalyst_impact_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    # Companies that have price history - powers the frontend picker.
    priced_ids = StockPrice.objects.values_list('company_id', flat=True).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=priced_ids, is_active=True
        ).order_by('name')
    ]

    company_id_raw = request.GET.get('company_id', '').strip()
    if not company_id_raw.isdigit():
        return Response({
            'available_companies': available_companies,
            'by_catalyst_type': [],
            'events': [],
        })

    company = Company.objects.filter(id=int(company_id_raw), is_active=True).first()
    if not company:
        return Response({'error': 'Company not found'}, status=404)

    days = max(90, min(int(request.GET.get('days', 365)), 1095))

    # Full price history as an ordered list so we can step trading days.
    prices = list(
        StockPrice.objects.filter(company=company).order_by('date')
    )
    base = {
        'available_companies': available_companies,
        'company': {
            'id': company.id,
            'name': company.name,
            'ticker': company.ticker_symbol,
        },
        'window_days': days,
    }

    if len(prices) < 22:
        data = {
            **base,
            'total_events': 0,
            'by_catalyst_type': [],
            'events': [],
            'message': (
                'Not enough price history for an event study '
                '(need 20+ trading days).'
            ),
        }
        cache.set(cached_key, data, 600)
        return Response(data)

    price_dates = [p.date for p in prices]
    cutoff = timezone.now().date() - timedelta(days=days)
    news = NewsRelease.objects.filter(
        company=company, release_date__gte=cutoff,
    ).order_by('release_date')

    horizons = [('1d', 1), ('5d', 5), ('20d', 20)]
    type_display = dict(NewsRelease.RELEASE_TYPES)
    by_type = {}  # release_type -> {'1d': [...], '5d': [...], '20d': [...]}
    events = []

    first_price_date = price_dates[0]
    for ev in news:
        # Skip events that predate the price history - anchoring them to the
        # first available day would yield a spurious, identical "reaction"
        # for every such event.
        if ev.release_date < first_price_date:
            continue
        # First trading day on/after the release date.
        idx = next(
            (i for i, d in enumerate(price_dates) if d >= ev.release_date), None
        )
        if idx is None:
            continue
        base_price = float(prices[idx].close_price or 0)
        if base_price <= 0:
            continue

        reactions = {}
        for label, offset in horizons:
            tgt = idx + offset
            if tgt < len(prices) and prices[tgt].close_price:
                reactions[label] = round(
                    (float(prices[tgt].close_price) - base_price)
                    / base_price * 100, 2,
                )
            else:
                reactions[label] = None

        bucket = by_type.setdefault(
            ev.release_type, {'1d': [], '5d': [], '20d': []}
        )
        for label, _ in horizons:
            if reactions[label] is not None:
                bucket[label].append(reactions[label])

        events.append({
            'date': ev.release_date.isoformat(),
            'title': ev.title,
            'release_type': type_display.get(ev.release_type, ev.release_type),
            'url': ev.url,
            'change_1d': reactions['1d'],
            'change_5d': reactions['5d'],
            'change_20d': reactions['20d'],
        })

    by_catalyst_type = []
    for rtype, hd in by_type.items():
        entry = {
            'release_type': type_display.get(rtype, rtype),
            'event_count': max(len(hd['1d']), len(hd['5d']), len(hd['20d'])),
        }
        for label, _ in horizons:
            vals = hd[label]
            entry[f'avg_{label}'] = (
                round(sum(vals) / len(vals), 2) if vals else None
            )
            entry[f'sample_{label}'] = len(vals)
        by_catalyst_type.append(entry)

    by_catalyst_type.sort(key=lambda e: e['event_count'], reverse=True)
    events.sort(key=lambda e: e['date'], reverse=True)

    data = {
        **base,
        'total_events': len(events),
        'by_catalyst_type': by_catalyst_type,
        'events': events,
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# PROJECT DUE-DILIGENCE RETRIEVAL
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(truncate=('sections', 'source_documents'))
def due_diligence(request):
    """
    Structured due-diligence retrieval: ranked NI 43-101 report passages that
    answer a question for one company (RAG hybrid search, no LLM synthesis).
    GET /api/tools/due-diligence/?company_id=1&question=metallurgical recovery

    With no company_id/question, returns just the available-companies list
    (those that have processed documents) for the frontend picker.
    """
    from core.models import DocumentChunk

    # Companies that have processed report content - powers the picker.
    doc_company_ids = DocumentChunk.objects.values_list(
        'document__company_id', flat=True,
    ).distinct()
    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
        }
        for c in Company.objects.filter(
            id__in=doc_company_ids, is_active=True,
        ).order_by('name')
    ]

    company_id_raw = request.GET.get('company_id', '').strip()
    question = request.GET.get('question', '').strip()
    if not company_id_raw.isdigit() or not question:
        return Response({
            'available_companies': available_companies,
            'sections': [],
        })

    company = Company.objects.filter(id=int(company_id_raw), is_active=True).first()
    if not company:
        return Response({'error': 'Company not found'}, status=404)

    max_sections = max(1, min(int(request.GET.get('max_sections', 8)), 15))

    cached_key = f"due_diligence_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    try:
        from mcp_servers.rag_utils import RAGManager
        results = RAGManager().search_documents(
            query=question, n_results=max_sections, filter_company=company.name,
        )
    except Exception as e:
        logger.error(f"due_diligence RAG search failed: {e}")
        return Response(
            {'error': 'Document search failed. Please try again.'},
            status=500,
        )

    # Resolve each passage's real Document by exact chunk-text match. The
    # hybrid search's BM25 branch returns thin metadata without document
    # titles, so trusting result metadata alone yields "Unknown report".
    texts = [r.get('text', '') for r in results if r.get('text')]
    chunk_doc = {}
    if texts:
        for ch in DocumentChunk.objects.filter(
            text__in=texts,
        ).select_related('document'):
            chunk_doc.setdefault(ch.text, ch.document)

    sections = []
    documents_seen = {}
    for idx, r in enumerate(results, 1):
        text = r.get('text', '')
        meta = r.get('metadata', {}) or {}
        doc = chunk_doc.get(text)
        if doc is not None:
            doc_id = doc.id
            title = _clean_doc_title(doc.title)
            doc_date = (
                doc.document_date.isoformat() if doc.document_date else None
            )
            doc_type = doc.document_type
        else:
            doc_id = meta.get('document_id')
            title = _clean_doc_title(meta.get('document_title')) or 'Unknown report'
            doc_date = meta.get('document_date')
            doc_type = meta.get('document_type')
        if doc_id is not None:
            documents_seen.setdefault(doc_id, title)
        sections.append({
            'rank': idx,
            'text': text,
            'document_id': doc_id,
            'document_title': title,
            'document_date': doc_date,
            'document_type': doc_type,
        })

    data = {
        'available_companies': available_companies,
        'company': {
            'id': company.id,
            'name': company.name,
            'ticker': company.ticker_symbol,
        },
        'question': question,
        'sections': sections,
        'source_documents': [
            {'document_id': k, 'title': v} for k, v in documents_seen.items()
        ],
    }
    cache.set(cached_key, data, 600)
    return Response(data)


# ============================================================================
# METAL LEVERAGE ANALYZER  (Stock-Metal Price Correlation)
# ============================================================================

# Maps a Project.primary_commodity to its closest MetalPrice symbol so the
# frontend can pre-select a sensible default for a chosen company.
_COMMODITY_TO_METAL = {
    'gold': 'XAU',
    'silver': 'XAG',
    'platinum': 'XPT',
    'palladium': 'XPD',
    'copper': 'CU',
    'nickel': 'NI',
    'lithium': 'LI',
    'cobalt': 'CO',
    'rare_earths': 'REE',
    'uranium': 'U',
}


def _pearson(xs, ys):
    """Pearson correlation of two equal-length numeric sequences."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    denom = (dx * dy) ** 0.5
    if denom == 0:
        return None
    return num / denom


@api_view(['GET'])
@permission_classes([AllowAny])
@tier_gated(stub=('companies',), truncate=('heatmap',))
def metal_correlation(request):
    """
    Stock-metal price correlation analytics.

    For each selected company, computes daily-return correlation, beta
    (sensitivity), R-squared, and a volatility-based leverage ratio against
    a chosen metal's daily price series over a configurable window. Returns
    normalized price series for chart overlay and a pairwise correlation
    matrix for the heatmap.

    GET /api/tools/metal-correlation/?metal=XAU&company_ids=1,2,3&days=180

    With no params, returns the available metals + companies that have at
    least one stock-price record, so the frontend can render the picker.
    """
    cached_key = f"metal_correlation_{request.GET.urlencode()}"
    cached = cache.get(cached_key)
    if cached:
        return Response(cached)

    # Pickers: every company with any price history, every metal with any
    # scraped price. Cheaper than instantiating model objects for the metal
    # list — we only need the labels.
    priced_ids = StockPrice.objects.values_list('company_id', flat=True).distinct()

    # Bulk-map company_id → flagship primary_commodity in a single query so
    # the per-company `suggested_metal` lookup isn't N+1 (~500 companies
    # used to push this endpoint above 60s on a cold cache).
    company_commodity = {}
    for p in Project.objects.filter(
        company_id__in=priced_ids, is_active=True,
    ).order_by('company_id', '-is_flagship').values('company_id', 'primary_commodity'):
        company_commodity.setdefault(p['company_id'], p['primary_commodity'])

    available_companies = [
        {
            'id': c.id,
            'name': c.name,
            'ticker': c.ticker_symbol,
            'exchange': c.exchange,
            # Closest metal symbol based on flagship/primary project's commodity.
            # Lets the frontend pre-select a sensible default per company.
            'suggested_metal': _COMMODITY_TO_METAL.get(
                company_commodity.get(c.id) or '', None,
            ),
        }
        for c in Company.objects.filter(
            id__in=priced_ids, is_active=True,
        ).order_by('name')
    ]
    metals_with_data = set(
        MetalPrice.objects.values_list('metal', flat=True).distinct()
    )
    available_metals = [
        {'symbol': sym, 'name': name}
        for sym, name in MetalPrice.METAL_CHOICES
        if sym in metals_with_data
    ]

    metal = request.GET.get('metal', '').strip().upper()
    company_ids_raw = request.GET.get('company_ids', '')
    company_ids = [
        int(x) for x in company_ids_raw.split(',') if x.strip().isdigit()
    ][:10]

    base_payload = {
        'available_companies': available_companies,
        'available_metals': available_metals,
    }

    if not metal or not company_ids:
        return Response({**base_payload, 'companies': [], 'metal_series': []})

    if metal not in dict(MetalPrice.METAL_CHOICES):
        return Response({'error': f'Unknown metal symbol: {metal}'}, status=400)

    days = max(30, min(int(request.GET.get('days', 180)), 730))
    start_date = timezone.now().date() - timedelta(days=days)

    # One representative metal price per calendar day. Metals are scraped
    # twice daily so we collapse to the latest scrape of each day.
    metal_rows = MetalPrice.get_daily_series(metal, days=days)
    metal_by_date = {}
    metal_series_out = []
    base_metal_price = None
    for mr in metal_rows:
        day = mr.scraped_at.date()
        if day < start_date:
            continue
        price = float(mr.bid_price)
        metal_by_date[day] = price
        if base_metal_price is None and price > 0:
            base_metal_price = price
        metal_series_out.append({
            'date': day.isoformat(),
            'price': round(price, 2),
            'pct': round(
                (price - base_metal_price) / base_metal_price * 100, 2,
            ) if base_metal_price else 0,
        })

    metal_display = dict(MetalPrice.METAL_CHOICES).get(metal, metal)
    metal_unit = next(
        (mr.unit for mr in metal_rows if mr.unit), 'oz',
    )

    if len(metal_by_date) < 5:
        data = {
            **base_payload,
            'metal': {
                'symbol': metal,
                'name': metal_display,
                'unit': metal_unit,
            },
            'metal_series': metal_series_out,
            'companies': [],
            'days': days,
            'message': (
                f'Not enough {metal_display} price history in the window. '
                'Try a longer window.'
            ),
        }
        cache.set(cached_key, data, 600)
        return Response(data)

    # Daily metal returns indexed by date, used to compute correlations and
    # beta against each stock's overlapping return stream.
    metal_dates_sorted = sorted(metal_by_date.keys())
    metal_returns_by_date = {}
    for i in range(1, len(metal_dates_sorted)):
        prev_d = metal_dates_sorted[i - 1]
        cur_d = metal_dates_sorted[i]
        p0 = metal_by_date[prev_d]
        p1 = metal_by_date[cur_d]
        if p0 > 0:
            metal_returns_by_date[cur_d] = (p1 - p0) / p0

    companies_out = []
    # Stock return streams keyed by date — collected so we can build a
    # pairwise correlation matrix (stocks + metal) for the heatmap.
    stock_returns_map = {}

    for cid in company_ids:
        company = Company.objects.filter(id=cid, is_active=True).first()
        if not company:
            continue
        prices = list(
            StockPrice.objects.filter(
                company=company, date__gte=start_date,
            ).order_by('date')
        )
        if len(prices) < 5:
            companies_out.append({
                'company_id': cid,
                'company_name': company.name,
                'ticker': company.ticker_symbol,
                'error': 'Not enough stock price history in this window.',
            })
            continue

        base_stock = float(prices[0].close_price)
        stock_series = []
        stock_returns_by_date = {}
        prev_close = None
        prev_date = None
        for p in prices:
            close = float(p.close_price)
            stock_series.append({
                'date': p.date.isoformat(),
                'close': round(close, 4),
                'pct': round(
                    (close - base_stock) / base_stock * 100, 2,
                ) if base_stock else 0,
            })
            if prev_close and prev_close > 0:
                stock_returns_by_date[p.date] = (close - prev_close) / prev_close
            prev_close = close
            prev_date = p.date

        # Inner-join stock & metal daily returns on shared dates. With
        # weekend / holiday gaps we generally get the trading-day subset.
        shared_dates = sorted(
            set(stock_returns_by_date) & set(metal_returns_by_date)
        )
        stock_rets = [stock_returns_by_date[d] for d in shared_dates]
        metal_rets = [metal_returns_by_date[d] for d in shared_dates]

        n_pairs = len(stock_rets)
        correlation = _pearson(stock_rets, metal_rets) if n_pairs >= 5 else None

        # Beta = Cov(stock, metal) / Var(metal). Captures sensitivity:
        # beta > 1 means the stock has historically amplified metal moves.
        beta = None
        if n_pairs >= 5:
            mm = sum(metal_rets) / n_pairs
            sm = sum(stock_rets) / n_pairs
            var_m = sum((m - mm) ** 2 for m in metal_rets) / n_pairs
            cov = sum(
                (s - sm) * (m - mm) for s, m in zip(stock_rets, metal_rets)
            ) / n_pairs
            beta = (cov / var_m) if var_m > 0 else None

        stock_vol = (
            statistics.pstdev(stock_rets) * 100 if n_pairs >= 2 else None
        )
        metal_vol = (
            statistics.pstdev(metal_rets) * 100 if n_pairs >= 2 else None
        )
        leverage = (
            round(stock_vol / metal_vol, 2)
            if stock_vol is not None and metal_vol and metal_vol > 0
            else None
        )

        # Two-tailed t-test on Pearson r: t = r * sqrt(n-2) / sqrt(1-r^2).
        # |t| > 1.96 ~= 95% confidence the correlation isn't zero.
        t_stat = None
        significant = False
        if correlation is not None and n_pairs > 2 and abs(correlation) < 1:
            t_stat = correlation * ((n_pairs - 2) ** 0.5) / (
                (1 - correlation ** 2) ** 0.5
            )
            significant = abs(t_stat) >= 1.96

        first, last = prices[0], prices[-1]
        end_close = float(last.close_price)

        companies_out.append({
            'company_id': cid,
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'currency': last.currency,
            'stock_series': stock_series,
            'start_date': first.date.isoformat(),
            'end_date': last.date.isoformat(),
            'start_price': round(base_stock, 4),
            'end_price': round(end_close, 4),
            'stock_pct_change': round(
                (end_close - base_stock) / base_stock * 100, 2,
            ) if base_stock else 0,
            'correlation': round(correlation, 3) if correlation is not None else None,
            'r_squared': round(correlation ** 2, 3) if correlation is not None else None,
            'beta': round(beta, 3) if beta is not None else None,
            'stock_volatility_pct': round(stock_vol, 2) if stock_vol is not None else None,
            'metal_volatility_pct': round(metal_vol, 2) if metal_vol is not None else None,
            'leverage_ratio': leverage,
            't_stat': round(t_stat, 2) if t_stat is not None else None,
            'significant': significant,
            'data_points': n_pairs,
        })
        stock_returns_map[cid] = stock_returns_by_date

    # Metal-window change for the summary header.
    metal_pct_change = None
    if len(metal_dates_sorted) >= 2:
        first_p = metal_by_date[metal_dates_sorted[0]]
        last_p = metal_by_date[metal_dates_sorted[-1]]
        if first_p > 0:
            metal_pct_change = round(
                (last_p - first_p) / first_p * 100, 2,
            )

    # Pairwise correlation matrix: every selected stock + the metal itself.
    # Ordered to match `companies_out` so the heatmap labels line up.
    heatmap_labels = []
    heatmap_ids = []
    for c in companies_out:
        if c.get('correlation') is None:
            continue
        heatmap_labels.append(c['ticker'] or c['company_name'])
        heatmap_ids.append(c['company_id'])
    heatmap_labels.append(metal_display)

    returns_lookup = {cid: stock_returns_map[cid] for cid in heatmap_ids}
    returns_lookup['__metal__'] = metal_returns_by_date
    matrix_keys = heatmap_ids + ['__metal__']

    heatmap = []
    for a in matrix_keys:
        row = []
        for b in matrix_keys:
            if a == b:
                row.append(1.0)
                continue
            shared = sorted(set(returns_lookup[a]) & set(returns_lookup[b]))
            if len(shared) < 5:
                row.append(None)
                continue
            xs = [returns_lookup[a][d] for d in shared]
            ys = [returns_lookup[b][d] for d in shared]
            r = _pearson(xs, ys)
            row.append(round(r, 3) if r is not None else None)
        heatmap.append(row)

    # Sort companies by |correlation| desc so the table leads with the
    # most-leveraged names; errors sink to the bottom.
    companies_out.sort(
        key=lambda c: abs(c['correlation']) if c.get('correlation') is not None else -1,
        reverse=True,
    )

    data = {
        **base_payload,
        'metal': {
            'symbol': metal,
            'name': metal_display,
            'unit': metal_unit,
            'pct_change': metal_pct_change,
            'volatility_pct': (
                round(statistics.pstdev(list(metal_returns_by_date.values())) * 100, 2)
                if len(metal_returns_by_date) >= 2 else None
            ),
        },
        'metal_series': metal_series_out,
        'companies': companies_out,
        'heatmap': {
            'labels': heatmap_labels,
            'matrix': heatmap,
        },
        'days': days,
    }
    cache.set(cached_key, data, 600)
    return Response(data)
