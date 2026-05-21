"""
User-dashboard API endpoints.

Powers the Personalized Daily Briefing: a watchlist of companies plus a
recent-activity digest (price moves, news, financings, new documents) with
a generated headline.
"""

import logging
from datetime import timedelta

from django.core.cache import cache
from django.core import signing
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

from ..models import (
    Company, Watchlist, StockPrice, NewsRelease, Financing, Document, User,
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


def _generate_ai_briefing(blocks, stats, company_count):
    """
    Write a short, engaging briefing narrative with Claude (Haiku — fast and
    cheap). Returns None on any failure so the caller falls back to the
    deterministic template. Only runs on a briefing cache miss.
    """
    from django.conf import settings
    import anthropic

    facts = [f"Watchlist: {company_count} junior-mining companies."]
    if stats.get('top_gainer'):
        g = stats['top_gainer']
        facts.append(f"Top gainer (1 week): {g['ticker']} {g['change_pct']:+.1f}%.")
    if stats.get('top_loser'):
        ls = stats['top_loser']
        facts.append(f"Top decliner (1 week): {ls['ticker']} {ls['change_pct']:+.1f}%.")
    facts.append(
        f"Price moves: {stats['movers_up']} up, {stats['movers_down']} down."
    )
    facts.append(
        f"This week: {stats['news_count']} news releases, "
        f"{stats['financing_count']} financings, "
        f"{stats['document_count']} new technical reports."
    )
    headlines = []
    for c in blocks:
        for n in c['news']:
            tag = ' [material]' if n['is_material'] else ''
            headlines.append(f"- {c['ticker']}: {n['title']}{tag}")
            if len(headlines) >= 6:
                break
        if len(headlines) >= 6:
            break
    if headlines:
        facts.append("Recent headlines:")
        facts.extend(headlines)

    prompt = (
        "You are writing the opening of a junior-mining investor's personal "
        "daily briefing. Using ONLY the facts below, write 2-3 short, engaging "
        "sentences in second person (\"your watchlist\"). Lead with the most "
        "interesting development. Be specific with tickers and numbers. "
        "Professional but warm. Output only the sentences — no preamble, "
        "bullet points, or headers.\n\n"
        f"FACTS:\n{chr(10).join(facts)}"
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=240,
        messages=[{'role': 'user', 'content': prompt}],
    )
    text = ''.join(
        b.text for b in response.content if hasattr(b, 'text')
    ).strip()
    return text or None


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

def build_briefing(user):
    """
    Build the watchlist-activity briefing for a user — price moves, news,
    financings and new documents over the window, with a generated headline.

    Pure computation: no request, no caching, no last-visit handling — so it
    is shared by the dashboard view and the weekly briefing email task.
    """
    watchlist = _get_default_watchlist(user)
    companies = list(watchlist.companies.filter(is_deleted=False))
    today = timezone.now().date()

    if not companies:
        return {
            'has_watchlist': False,
            'date': today.isoformat(),
            'watchlist_name': watchlist.name,
            'company_count': 0,
            'window_days': BRIEFING_WINDOW_DAYS,
            'headline': None,
            'stats': {},
            'companies': [],
        }

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

    # Prefer an AI-written narrative; fall back to the deterministic template.
    try:
        headline = _generate_ai_briefing(blocks, stats, len(companies))
    except Exception as e:
        logger.warning("AI briefing generation failed (%s) — using template.", e)
        headline = None
    if not headline:
        headline = _build_headline(blocks, stats, len(companies))

    return {
        'has_watchlist': True,
        'date': today.isoformat(),
        'window_days': BRIEFING_WINDOW_DAYS,
        'watchlist_name': watchlist.name,
        'company_count': len(companies),
        'headline': headline,
        'stats': stats,
        'companies': blocks,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_briefing(request):
    """
    GET /api/dashboard/daily-briefing/
    Recent-activity digest across the user's watchlist. Cached 30 min/user;
    'last_visit' and 'email_briefing_enabled' are layered on per-request.
    """
    user = request.user

    # "Since your last visit" — capture the prior marker, then advance it.
    last_visit = user.last_briefing_seen
    last_visit_iso = last_visit.isoformat() if last_visit else None
    User.objects.filter(pk=user.pk).update(last_briefing_seen=timezone.now())

    cache_key = f'daily_briefing_{user.id}'
    data = cache.get(cache_key)
    if data is None:
        data = build_briefing(user)
        cache.set(cache_key, data, BRIEFING_CACHE_SECONDS)

    return Response({
        **data,
        'last_visit': last_visit_iso,
        'email_briefing_enabled': user.email_briefing_enabled,
    })


# --------------------------------------------------------------------------
# Weekly briefing email — opt-in toggle + unsubscribe
# --------------------------------------------------------------------------

_UNSUBSCRIBE_SALT = 'briefing-email-unsubscribe'


def briefing_email_token(user):
    """Signed, tamper-proof token identifying a user for one-click unsubscribe."""
    return signing.dumps({'uid': user.id}, salt=_UNSUBSCRIBE_SALT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def briefing_email_toggle(request):
    """
    POST /api/dashboard/briefing-email/  {"enabled": true|false}
    Set the user's opt-in for the weekly briefing email.
    """
    enabled = bool(request.data.get('enabled'))
    User.objects.filter(pk=request.user.pk).update(email_briefing_enabled=enabled)
    return Response({'email_briefing_enabled': enabled})


@require_GET
def briefing_email_unsubscribe(request):
    """
    GET /api/briefing-email/unsubscribe/?token=...
    One-click unsubscribe from a briefing email — no login required.
    """
    token = request.GET.get('token', '')
    try:
        payload = signing.loads(
            token, salt=_UNSUBSCRIBE_SALT, max_age=60 * 60 * 24 * 365,
        )
        User.objects.filter(pk=payload['uid']).update(
            email_briefing_enabled=False,
        )
        message = (
            "You've been unsubscribed from the weekly GoldVenture briefing "
            "email. You can re-enable it any time from your dashboard."
        )
    except Exception:
        message = "This unsubscribe link is invalid or has expired."

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Unsubscribe</title></head>
<body style="font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;
text-align:center;padding:80px 24px;">
  <h2 style="color:#d4af37;margin-bottom:16px;">GoldVenture</h2>
  <p style="font-size:16px;max-width:480px;margin:0 auto 24px;">{message}</p>
  <a href="https://juniorminingintelligence.com/dashboard"
     style="color:#d4af37;text-decoration:none;">→ Back to your dashboard</a>
</body></html>"""
    return HttpResponse(html)
