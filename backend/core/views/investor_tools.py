"""
Investor Tools API endpoints.
Provides data for grade ranking, peer comparison, financing flow, and sector pulse.
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum, Count, Avg, Q, F, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import (
    Company, Project, ResourceEstimate, EconomicStudy,
    Financing, MarketData, StockPrice, MetalPrice,
    NewsRelease, NewsArticle,
)

logger = logging.getLogger(__name__)


# ============================================================================
# RESOURCE GRADE RANKER
# ============================================================================

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
        # Get best resource estimate (most recent, prefer M&I)
        resources = ResourceEstimate.objects.filter(project=project).order_by('-report_date')
        if not resources.exists():
            continue

        # Aggregate across categories
        totals = resources.aggregate(
            total_tonnes=Sum('tonnes'),
            total_gold_oz=Sum('gold_ounces'),
            total_silver_oz=Sum('silver_ounces'),
            avg_gold_grade=Avg('gold_grade_gpt'),
            avg_silver_grade=Avg('silver_grade_gpt'),
            avg_copper_grade=Avg('copper_grade_pct'),
        )

        gold_oz = float(totals['total_gold_oz'] or 0)
        silver_oz = float(totals['total_silver_oz'] or 0)
        tonnes = float(totals['total_tonnes'] or 0)

        # Determine primary grade based on commodity
        if commodity in ('gold', 'multi_metal'):
            grade = float(totals['avg_gold_grade'] or 0)
            ounces = gold_oz
            grade_unit = 'g/t Au'
        elif commodity == 'silver':
            grade = float(totals['avg_silver_grade'] or 0)
            ounces = silver_oz
            grade_unit = 'g/t Ag'
        elif commodity == 'copper':
            grade = float(totals['avg_copper_grade'] or 0)
            ounces = tonnes  # Use tonnes for copper
            grade_unit = '% Cu'
        else:
            grade = float(totals['avg_gold_grade'] or 0)
            ounces = gold_oz
            grade_unit = 'g/t'

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
def peer_comparison(request):
    """
    Compare a company against auto-detected or manual peer group.
    GET /api/tools/peer-comparison/?company_id=123
    GET /api/tools/peer-comparison/?company_ids=1,2,3,4,5
    """
    company_id = request.GET.get('company_id')
    company_ids_raw = request.GET.get('company_ids', '')

    if company_ids_raw:
        company_ids = [int(x) for x in company_ids_raw.split(',') if x.strip()]
    elif company_id:
        # Auto-detect peers
        try:
            target = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=404)

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
        published_date__gte=today - timedelta(days=7)
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
