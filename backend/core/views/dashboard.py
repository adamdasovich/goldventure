"""
User-dashboard API endpoints.

Powers the Personalized Daily Briefing: a watchlist of companies plus a
recent-activity digest (price moves, news, financings, new documents) with
a generated headline.
"""

import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

from ..models import (
    Company, Watchlist, StockPrice, NewsRelease, Financing, Document,
)

logger = logging.getLogger(__name__)

BRIEFING_WINDOW_DAYS = 7
BRIEFING_CACHE_SECONDS = 1800  # 30 minutes
NOTABLE_MOVE_PCT = 5.0         # a price move this big counts as "activity"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _get_default_watchlist(user):
    """Return the user's default watchlist, creating one if none exists."""
    watchlist = (
        Watchlist.objects.filter(user=user, is_default=True).first()
        or Watchlist.objects.filter(user=user).first()
    )
    if watchlist is None:
        watchlist = Watchlist.objects.create(
            user=user, name='My Watchlist', is_default=True,
        )
    return watchlist


def _ticker_display(company):
    """Human ticker, e.g. 'GROY.TSXV' — without doubling an existing suffix."""
    ticker = (company.ticker_symbol or '').strip()
    exchange = (company.exchange or '').upper()
    if not ticker:
        return company.name
    if '.' in ticker:
        return ticker
    return f"{ticker}.{exchange}" if exchange else ticker


def _company_brief(company):
    return {
        'id': company.id,
        'name': company.name,
        'ticker': _ticker_display(company),
        'exchange': company.exchange,
    }


def _build_headline(blocks, stats, company_count):
    """
    Compose a short, human briefing headline from the aggregated data.
    Deterministic (no LLM) but varies with what actually happened.
    """
    label = 'company' if company_count == 1 else 'companies'
    top_gainer = stats.get('top_gainer')
    top_loser = stats.get('top_loser')
    news_count = stats['news_count']
    financing_count = stats['financing_count']

    # A material news item makes the best "notably" hook.
    material = None
    for c in blocks:
        for n in c['news']:
            if n['is_material']:
                material = (c['ticker'], n['title'])
                break
        if material:
            break

    parts = []

    # Lead with the strongest signal.
    if top_gainer and top_gainer['change_pct'] >= 3:
        parts.append(
            f"{top_gainer['ticker']} led your watchlist, "
            f"up {top_gainer['change_pct']:.1f}% over the past week."
        )
    elif top_loser and top_loser['change_pct'] <= -3:
        parts.append(
            f"{top_loser['ticker']} had the roughest week on your watchlist, "
            f"down {abs(top_loser['change_pct']):.1f}%."
        )
    elif news_count == 0 and financing_count == 0:
        return (
            f"A quiet week across your {company_count} watched {label} — "
            f"no major news or financings. Markets don't always move; "
            f"this is a good time to scan for new ideas."
        )
    else:
        parts.append("A steady week across your watchlist.")

    # Follow with news / financing volume.
    bits = []
    if financing_count:
        bits.append(
            f"{financing_count} new financing"
            f"{'s' if financing_count > 1 else ''}"
        )
    if news_count:
        bits.append(
            f"{news_count} news release{'s' if news_count > 1 else ''}"
        )
    if bits:
        parts.append(f"{' and '.join(bits)} across your {label}.")

    if material:
        parts.append(f"Notably — {material[0]}: “{material[1]}”.")

    return ' '.join(parts)


# --------------------------------------------------------------------------
# Watchlist endpoints
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def watchlist_detail(request):
    """
    GET /api/watchlist/
    Return the current user's default watchlist of companies.
    """
    watchlist = _get_default_watchlist(request.user)
    companies = watchlist.companies.filter(is_deleted=False).order_by('name')
    return Response({
        'watchlist_name': watchlist.name,
        'company_count': companies.count(),
        'companies': [_company_brief(c) for c in companies],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def watchlist_toggle(request):
    """
    POST /api/watchlist/toggle/  {"company_id": 123}
    Add the company to the user's watchlist if absent, remove it if present.
    """
    company_id = request.data.get('company_id')
    company = Company.objects.filter(
        id=company_id, is_deleted=False,
    ).first() if company_id else None
    if company is None:
        return Response(
            {'error': 'Company not found.'},
            status=http_status.HTTP_404_NOT_FOUND,
        )

    watchlist = _get_default_watchlist(request.user)
    if watchlist.companies.filter(id=company.id).exists():
        watchlist.companies.remove(company)
        watched = False
    else:
        watchlist.companies.add(company)
        watched = True

    # The briefing depends on watchlist membership — invalidate its cache.
    cache.delete(f'daily_briefing_{request.user.id}')

    return Response({'company_id': company.id, 'watched': watched})


# --------------------------------------------------------------------------
# Daily briefing
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_briefing(request):
    """
    GET /api/dashboard/daily-briefing/
    Recent-activity digest across the user's watchlist: price moves, news,
    financings and new documents, with a generated headline.
    """
    cache_key = f'daily_briefing_{request.user.id}'
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    watchlist = _get_default_watchlist(request.user)
    companies = list(watchlist.companies.filter(is_deleted=False))
    today = timezone.now().date()

    if not companies:
        data = {
            'has_watchlist': False,
            'date': today.isoformat(),
            'watchlist_name': watchlist.name,
            'company_count': 0,
            'window_days': BRIEFING_WINDOW_DAYS,
            'headline': None,
            'stats': {},
            'companies': [],
        }
        cache.set(cache_key, data, BRIEFING_CACHE_SECONDS)
        return Response(data)

    cutoff = today - timedelta(days=BRIEFING_WINDOW_DAYS)
    blocks = []

    for company in companies:
        # --- price move over the window ---
        history = list(
            StockPrice.get_company_history(company, days=BRIEFING_WINDOW_DAYS)
        )
        price = None
        if history:
            latest, first = history[-1], history[0]
            change_pct = None
            if len(history) >= 2 and first.close_price:
                change_pct = round(
                    (float(latest.close_price) - float(first.close_price))
                    / float(first.close_price) * 100, 2,
                )
            price = {
                'latest': float(latest.close_price),
                'currency': latest.currency,
                'as_of': latest.date.isoformat(),
                'change_pct': change_pct,
            }

        # --- news / financings / documents in the window ---
        news = NewsRelease.objects.filter(
            company=company, release_date__gte=cutoff,
        ).order_by('-release_date')[:4]
        financings = Financing.objects.filter(
            company=company, is_deleted=False, announced_date__gte=cutoff,
        ).order_by('-announced_date')[:3]
        documents = Document.objects.filter(
            company=company, created_at__date__gte=cutoff,
        ).order_by('-created_at')[:3]

        news_items = [{
            'title': n.title,
            'date': n.release_date.isoformat(),
            'type': n.get_release_type_display(),
            'release_type': n.release_type,
            'url': n.url,
            'is_material': n.is_material,
        } for n in news]
        financing_items = [{
            'type': f.get_financing_type_display(),
            'amount_usd': float(f.amount_raised_usd or 0),
            'status': f.get_status_display(),
            'date': f.announced_date.isoformat(),
        } for f in financings]
        document_items = [{
            'title': d.title,
            'type': d.get_document_type_display(),
            'date': d.document_date.isoformat() if d.document_date else None,
        } for d in documents]

        move = price['change_pct'] if price and price['change_pct'] is not None else 0.0
        has_activity = bool(
            news_items or financing_items or document_items
            or abs(move) >= NOTABLE_MOVE_PCT
        )

        # Activity score drives card ordering — most interesting first.
        score = (
            len(news_items) * 3
            + len(financing_items) * 5
            + len(document_items) * 2
            + sum(4 for n in news_items if n['is_material'])
            + min(abs(move), 30)
        )

        block = _company_brief(company)
        block.update({
            'company_id': company.id,
            'price': price,
            'news': news_items,
            'financings': financing_items,
            'documents': document_items,
            'activity_score': round(score, 1),
            'has_activity': has_activity,
        })
        blocks.append(block)

    blocks.sort(key=lambda b: b['activity_score'], reverse=True)

    # --- aggregate stats ---
    moves = [
        b['price']['change_pct'] for b in blocks
        if b['price'] and b['price']['change_pct'] is not None
    ]
    priced = [
        b for b in blocks
        if b['price'] and b['price']['change_pct'] is not None
    ]
    top_gainer = max(
        priced, key=lambda b: b['price']['change_pct'], default=None,
    )
    top_loser = min(
        priced, key=lambda b: b['price']['change_pct'], default=None,
    )

    def _mover(b):
        return {
            'company_id': b['company_id'],
            'ticker': b['ticker'],
            'name': b['name'],
            'change_pct': b['price']['change_pct'],
        }

    stats = {
        'movers_up': sum(1 for m in moves if m > 0),
        'movers_down': sum(1 for m in moves if m < 0),
        'news_count': sum(len(b['news']) for b in blocks),
        'financing_count': sum(len(b['financings']) for b in blocks),
        'document_count': sum(len(b['documents']) for b in blocks),
        'active_company_count': sum(1 for b in blocks if b['has_activity']),
        'top_gainer': (
            _mover(top_gainer)
            if top_gainer and top_gainer['price']['change_pct'] > 0 else None
        ),
        'top_loser': (
            _mover(top_loser)
            if top_loser and top_loser['price']['change_pct'] < 0 else None
        ),
    }

    data = {
        'has_watchlist': True,
        'date': today.isoformat(),
        'window_days': BRIEFING_WINDOW_DAYS,
        'watchlist_name': watchlist.name,
        'company_count': len(companies),
        'headline': _build_headline(blocks, stats, len(companies)),
        'stats': stats,
        'companies': blocks,
    }
    cache.set(cache_key, data, BRIEFING_CACHE_SECONDS)
    return Response(data)
