"""
Base / critical metals price fetcher.

Precious metals (gold, silver, platinum, palladium) come from Kitco via
``kitco_scraper.py``. This module handles the base and critical minerals that
Kitco's precious-metals page does not cover.

Currently implemented:
    * Copper (CU) — Yahoo Finance copper futures (HG=F), USD per pound.
      Clean daily OHLC JSON, used for both backfill and the daily task.
    * Uranium (U), Cobalt Hydroxide (CO), Lithium (LI) — scraped daily from
      tradingeconomics.com/commodities. Lithium is quoted there in CNY per
      tonne and is converted to USD using a live USD/CNY rate from Yahoo.

Nickel and rare earths are not yet wired up — their historical data is being
purchased separately.
"""

import logging
import re
from datetime import datetime, timezone as dt_timezone

import requests
from bs4 import BeautifulSoup

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


# ---------------------------------------------------------------------------
# Trading Economics — Uranium, Cobalt Hydroxide, Lithium
# ---------------------------------------------------------------------------

_TE_COMMODITIES_URL = 'https://tradingeconomics.com/commodities'

# tradingeconomics commodity slug -> MetalPrice metadata.
# `source_currency` is the currency the site quotes in; LI is converted to USD.
TRADINGECONOMICS_METALS = {
    'uranium': {'metal': 'U', 'unit': 'lb', 'source_currency': 'USD'},
    'cobalt-hydroxide': {'metal': 'CO', 'unit': 'MT', 'source_currency': 'USD'},
    'lithium': {'metal': 'LI', 'unit': 'T', 'source_currency': 'CNY'},
}


def _to_number(text: str):
    """Parse a numeric string like '56,528.66' or '-0.4500' to float, or None."""
    if text is None:
        return None
    cleaned = re.sub(r'[^\d.\-]', '', str(text))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _fetch_cny_per_usd() -> float:
    """
    Return the current USD/CNY rate (how many CNY per 1 USD, ~7.x) from Yahoo
    Finance ticker CNY=X. Raises on failure.
    """
    series = _fetch_yahoo_daily('CNY=X', range_param='5d')
    if not series:
        raise ValueError('Yahoo returned no CNY=X data')
    rate = series[-1]['close']
    if not rate or rate <= 0:
        raise ValueError(f'Invalid USD/CNY rate: {rate}')
    return rate


def _scrape_tradingeconomics() -> dict:
    """
    Fetch the tradingeconomics commodities page and parse the rows for the
    metals in TRADINGECONOMICS_METALS.

    Returns {slug: {'price', 'change_amount', 'change_percent'}} for each
    metal successfully parsed. Each value is in the site's source currency.
    """
    response = requests.get(_TE_COMMODITIES_URL, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    parsed = {}
    for slug in TRADINGECONOMICS_METALS:
        link = soup.find('a', href=f'/commodity/{slug}')
        if not link:
            logger.warning(f'Trading Economics: row not found for /commodity/{slug}')
            continue
        row = link.find_parent('tr')
        if not row:
            logger.warning(f'Trading Economics: no parent row for /commodity/{slug}')
            continue

        # IDs are reused across rows (invalid HTML), so scope the lookup to
        # this <tr>. nch/pch carry a clean machine value in data-value.
        price_cell = row.find('td', id='p')
        nch_cell = row.find('td', id='nch')
        pch_cell = row.find('td', id='pch')

        price = _to_number(price_cell.get_text() if price_cell else None)
        if price is None:
            logger.warning(f'Trading Economics: no price parsed for {slug}')
            continue

        change_amount = _to_number(nch_cell.get('data-value') if nch_cell else None) or 0.0
        change_percent = _to_number(pch_cell.get('data-value') if pch_cell else None) or 0.0

        parsed[slug] = {
            'price': price,
            'change_amount': change_amount,
            'change_percent': change_percent,
        }

    return parsed


def fetch_daily_tradingeconomics_metals() -> dict:
    """
    Scrape the daily Uranium, Cobalt Hydroxide and Lithium prices from
    tradingeconomics.com and store them as MetalPrice rows.

    Lithium is quoted in CNY/tonne; it is converted to USD/tonne with a live
    USD/CNY rate so every stored price is in USD (the model assumes USD).

    Intended to run once per weekday alongside the copper task.
    """
    from core.models import MetalPrice
    from django.utils import timezone

    try:
        parsed = _scrape_tradingeconomics()
    except Exception as e:
        logger.error(f'Trading Economics scrape failed: {e}')
        return {'success': False, 'error': str(e), 'saved': []}

    if not parsed:
        return {'success': False, 'error': 'No metals parsed from Trading Economics',
                'saved': []}

    # Only fetch the FX rate if we actually scraped a CNY-quoted metal.
    cny_per_usd = None
    needs_fx = any(
        TRADINGECONOMICS_METALS[s]['source_currency'] != 'USD' for s in parsed
    )
    if needs_fx:
        try:
            cny_per_usd = _fetch_cny_per_usd()
            logger.info(f'USD/CNY rate for lithium conversion: {cny_per_usd}')
        except Exception as e:
            logger.error(f'Could not fetch USD/CNY rate: {e}')

    saved = []
    errors = []
    now = timezone.now()
    for slug, data in parsed.items():
        meta = TRADINGECONOMICS_METALS[slug]
        price = data['price']
        change_amount = data['change_amount']
        change_percent = data['change_percent']

        # Convert CNY-quoted metals (lithium) to USD. change_percent is a
        # ratio and currency-agnostic, so only price/change_amount convert.
        if meta['source_currency'] == 'CNY':
            if not cny_per_usd:
                errors.append(f'{slug}: skipped (no USD/CNY rate)')
                continue
            price = price / cny_per_usd
            change_amount = change_amount / cny_per_usd

        try:
            MetalPrice.objects.create(
                metal=meta['metal'],
                bid_price=round(price, 2),
                ask_price=round(price, 2),
                change_amount=round(change_amount, 2),
                change_percent=round(change_percent, 2),
                unit=meta['unit'],
                source='Trading Economics',
                scraped_at=now,
            )
            saved.append({'metal': meta['metal'], 'price': round(price, 2),
                          'unit': meta['unit']})
            logger.info(f"Stored {meta['metal']} price: ${price:,.2f}/{meta['unit']}")
        except Exception as e:
            errors.append(f"{slug}: save failed ({e})")
            logger.error(f'Failed to save {slug}: {e}')

    return {'success': bool(saved), 'saved': saved, 'errors': errors}
