"""
Base / critical metals price fetcher.

Precious metals (gold, silver, platinum, palladium) come from Kitco via
``kitco_scraper.py``. This module handles the base and critical minerals that
Kitco's precious-metals page does not cover.

Currently implemented:
    * Copper (CU) — sourced from Yahoo Finance copper futures (HG=F),
      quoted in USD per pound. Yahoo has no Cloudflare protection and
      returns clean daily OHLC JSON.

Other metals (nickel, lithium, cobalt, uranium) are not yet wired up — the
intended source (dailymetalprice.com) is behind a Cloudflare challenge that
the server's datacenter IP cannot pass. See project notes.
"""

import logging
from datetime import datetime, timezone as dt_timezone

import requests

logger = logging.getLogger(__name__)

# Yahoo Finance futures ticker -> (MetalPrice.metal code, quote unit)
YAHOO_METALS = {
    'HG=F': {'metal': 'CU', 'unit': 'lb', 'name': 'Copper'},
}

_YAHOO_CHART_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
_REQUEST_TIMEOUT = 20


def _fetch_yahoo_daily(ticker: str, range_param: str = '1y') -> list:
    """
    Fetch daily OHLC data for a Yahoo Finance ticker.

    Returns a list of dicts (oldest first):
        {'dt': datetime (UTC), 'open', 'high', 'low', 'close'}
    Rows with a null close are skipped (non-trading days / gaps).
    """
    url = _YAHOO_CHART_URL.format(ticker=ticker)
    params = {'interval': '1d', 'range': range_param}

    response = requests.get(url, params=params, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    result = (data.get('chart', {}).get('result') or [None])[0]
    if not result:
        raise ValueError(f'Yahoo Finance returned no result for {ticker}')

    timestamps = result.get('timestamp') or []
    quote = (result.get('indicators', {}).get('quote') or [{}])[0]
    opens = quote.get('open') or []
    highs = quote.get('high') or []
    lows = quote.get('low') or []
    closes = quote.get('close') or []

    series = []
    for i, ts in enumerate(timestamps):
        close = closes[i] if i < len(closes) else None
        if close is None:
            continue
        series.append({
            'dt': datetime.fromtimestamp(ts, tz=dt_timezone.utc),
            'open': opens[i] if i < len(opens) and opens[i] is not None else close,
            'high': highs[i] if i < len(highs) and highs[i] is not None else close,
            'low': lows[i] if i < len(lows) and lows[i] is not None else close,
            'close': close,
        })
    return series


def backfill_copper(start_date: str = '2026-01-01') -> dict:
    """
    Backfill historical daily copper prices into MetalPrice from Yahoo Finance.

    Only inserts days on/after ``start_date`` that do not already have a CU
    row, so it is safe to re-run.

    Returns a status dict.
    """
    from core.models import MetalPrice

    cutoff = datetime.strptime(start_date, '%Y-%m-%d').date()

    try:
        series = _fetch_yahoo_daily('HG=F', range_param='2y')
    except Exception as e:
        logger.error(f'Copper backfill: Yahoo fetch failed: {e}')
        return {'success': False, 'error': str(e), 'created': 0}

    series = [pt for pt in series if pt['dt'].date() >= cutoff]
    if not series:
        return {'success': True, 'created': 0, 'skipped': 0,
                'message': 'No copper data in requested range'}

    # Days already stored, so re-runs don't duplicate.
    existing_dates = {
        dt.date() for dt in MetalPrice.objects.filter(
            metal='CU', scraped_at__date__gte=cutoff
        ).values_list('scraped_at', flat=True)
    }

    created = 0
    skipped = 0
    prev_close = None
    for pt in series:
        day = pt['dt'].date()
        if day in existing_dates:
            prev_close = pt['close']
            skipped += 1
            continue

        change_amount = 0.0
        change_percent = 0.0
        if prev_close:
            change_amount = pt['close'] - prev_close
            change_percent = (change_amount / prev_close) * 100

        MetalPrice.objects.create(
            metal='CU',
            bid_price=round(pt['close'], 4),
            ask_price=round(pt['close'], 4),
            high_price=round(pt['high'], 4),
            low_price=round(pt['low'], 4),
            change_amount=round(change_amount, 4),
            change_percent=round(change_percent, 2),
            unit='lb',
            source='Yahoo Finance',
            scraped_at=pt['dt'],
        )
        created += 1
        prev_close = pt['close']

    logger.info(f'Copper backfill complete: {created} created, {skipped} skipped')
    return {'success': True, 'created': created, 'skipped': skipped,
            'first_day': series[0]['dt'].date().isoformat(),
            'last_day': series[-1]['dt'].date().isoformat()}


def fetch_daily_copper() -> dict:
    """
    Fetch the latest daily copper close from Yahoo Finance and store it as a
    new MetalPrice row. Intended to run once per weekday after market close.
    """
    from core.models import MetalPrice

    try:
        series = _fetch_yahoo_daily('HG=F', range_param='5d')
    except Exception as e:
        logger.error(f'Daily copper fetch: Yahoo request failed: {e}')
        return {'success': False, 'error': str(e)}

    if not series:
        return {'success': False, 'error': 'No copper data returned by Yahoo'}

    latest = series[-1]
    prev_close = series[-2]['close'] if len(series) >= 2 else None

    change_amount = 0.0
    change_percent = 0.0
    if prev_close:
        change_amount = latest['close'] - prev_close
        change_percent = (change_amount / prev_close) * 100

    MetalPrice.objects.create(
        metal='CU',
        bid_price=round(latest['close'], 4),
        ask_price=round(latest['close'], 4),
        high_price=round(latest['high'], 4),
        low_price=round(latest['low'], 4),
        change_amount=round(change_amount, 4),
        change_percent=round(change_percent, 2),
        unit='lb',
        source='Yahoo Finance',
        scraped_at=latest['dt'],
    )

    logger.info(f"Daily copper price stored: ${latest['close']:.4f}/lb "
                f"({latest['dt'].date().isoformat()})")
    return {'success': True, 'metal': 'CU',
            'price': round(latest['close'], 4),
            'date': latest['dt'].date().isoformat()}
