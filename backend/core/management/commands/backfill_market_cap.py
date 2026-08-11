"""
Backfill shares outstanding and market capitalisation from Yahoo Finance.

Why this exists
---------------
`companies.market_cap_usd` was populated for 28 of 396 companies and
`market_data.market_cap_usd` for 0 of 53,053 rows, so every market-cap-derived
metric on the platform resolved to null and any sort by market cap sorted by
zero. `shares_outstanding` was only 18% filled, so it could not be computed
locally either.

Source
------
Yahoo's quoteSummary endpoint carries both `sharesOutstanding` and `marketCap`.
It requires a cookie + crumb handshake; the bundled yfinance (0.2.36) predates
Yahoo's change and fails with a JSON decode error, so this talks to the endpoint
directly. Values are converted to USD via Yahoo's own FX pairs.

Usage
-----
    python manage.py backfill_market_cap --dry-run
    python manage.py backfill_market_cap --limit 20
    python manage.py backfill_market_cap
"""

import json
import time
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Company, MarketData

UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

# Company.exchange -> Yahoo suffix. OTC tickers carry no suffix.
SUFFIX = {
    'tsx': '.TO',
    'tsxv': '.V',
    'cse': '.CN',
    'asx': '.AX',
    'aim': '.L',
    'otc': '',
    'other': '',
}


class Command(BaseCommand):
    help = "Backfill shares outstanding and market cap from Yahoo Finance."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0,
                            help="Only process this many companies. 0 = all.")
        parser.add_argument('--delay', type=float, default=0.7,
                            help="Seconds between requests (default 0.7). Yahoo 429s on bursts.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Fetch and report without writing.")
        parser.add_argument('--only-missing', action='store_true',
                            help="Skip companies that already have shares outstanding.")

    # ------------------------------------------------------------------

    def handle(self, *args, **opts):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor()
        )
        self.opener.addheaders = [('User-Agent', UA)]

        if not self._authenticate():
            self.stderr.write(self.style.ERROR("Could not obtain a Yahoo crumb — aborting."))
            return

        self.fx = self._load_fx()
        self.stdout.write(f"FX to USD: { {k: round(v, 4) for k, v in self.fx.items()} }")

        companies = Company.objects.filter(
            is_active=True, is_deleted=False
        ).exclude(ticker_symbol='').order_by('name')
        if opts['only_missing']:
            companies = companies.filter(shares_outstanding__isnull=True)
        if opts['limit']:
            companies = companies[:opts['limit']]

        total = companies.count()
        self.stdout.write(f"Processing {total} companies\n")

        ok = skipped = failed = 0
        for i, company in enumerate(companies, 1):
            symbol = self._symbol(company)
            if not symbol:
                skipped += 1
                continue

            data = self._quote(symbol)
            if not data:
                failed += 1
                self.stdout.write(f"  [{i}/{total}] {company.name[:34]:34s} {symbol:12s} no data")
                time.sleep(opts['delay'])
                continue

            shares, mcap_usd, currency, price = data
            self.stdout.write(
                f"  [{i}/{total}] {company.name[:34]:34s} {symbol:12s} "
                f"shares={shares or '-':>14} mcap_usd={mcap_usd or '-':>16} ({currency})"
            )

            if not opts['dry_run']:
                self._save(company, shares, mcap_usd, price)
            ok += 1
            time.sleep(opts['delay'])

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. updated={ok} skipped_no_symbol={skipped} no_data={failed}"
        ))
        if opts['dry_run']:
            self.stdout.write(self.style.NOTICE("Dry run — nothing written."))

    # ------------------------------------------------------------------

    def _authenticate(self):
        """Yahoo requires a session cookie plus a matching crumb."""
        try:
            self.opener.open('https://fc.yahoo.com', timeout=20).read()
        except Exception:
            pass  # This request is expected to error; it exists to set the cookie.
        try:
            resp = self.opener.open(
                'https://query1.finance.yahoo.com/v1/test/getcrumb', timeout=20
            )
            self.crumb = resp.read().decode().strip()
            return bool(self.crumb)
        except Exception as exc:
            self.stderr.write(f"crumb fetch failed: {exc}")
            return False

    def _get(self, url, retries=3):
        for attempt in range(retries):
            try:
                with self.opener.open(url, timeout=30) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    # Backoff and re-handshake; the crumb may have expired.
                    time.sleep(3 * (attempt + 1))
                    self._authenticate()
                    continue
                return None
            except Exception:
                time.sleep(1)
        return None

    def _load_fx(self):
        """Rates to convert a quote currency into USD."""
        rates = {'USD': 1.0}
        for pair, code in (('CADUSD=X', 'CAD'), ('AUDUSD=X', 'AUD'),
                           ('GBPUSD=X', 'GBP'), ('EURUSD=X', 'EUR')):
            data = self._get(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{pair}'
                f'?range=1d&interval=1d'
            )
            try:
                meta = data['chart']['result'][0]['meta']
                rates[code] = float(meta['regularMarketPrice'])
            except Exception:
                self.stderr.write(f"  FX {pair} unavailable — {code} left unconverted")
            time.sleep(0.3)
        # GBp (pence) shows up on AIM listings.
        if 'GBP' in rates:
            rates['GBP_PENCE'] = rates['GBP'] / 100
        return rates

    def _symbol(self, company):
        ticker = (company.ticker_symbol or '').strip().upper()
        if not ticker:
            return None
        # Some tickers are already stored with a suffix, e.g. "ABA.V".
        if '.' in ticker:
            return ticker
        suffix = SUFFIX.get((company.exchange or '').lower())
        return None if suffix is None else f"{ticker}{suffix}"

    def _quote(self, symbol):
        data = self._get(
            'https://query1.finance.yahoo.com/v10/finance/quoteSummary/'
            f'{symbol}?modules=defaultKeyStatistics,price&crumb={self.crumb}'
        )
        try:
            result = data['quoteSummary']['result'][0]
        except (TypeError, KeyError, IndexError):
            return None

        stats = result.get('defaultKeyStatistics') or {}
        price_mod = result.get('price') or {}

        raw = lambda obj, key: (
            obj.get(key, {}).get('raw') if isinstance(obj.get(key), dict) else obj.get(key)
        )

        shares = raw(stats, 'sharesOutstanding')
        mcap = raw(price_mod, 'marketCap')
        price = raw(price_mod, 'regularMarketPrice')
        currency = (price_mod.get('currency') or 'USD').upper()

        rate = self.fx.get('GBP_PENCE' if currency == 'GBP' and price and price > 50
                           else currency)
        if rate is None:
            return None

        mcap_usd = int(mcap * rate) if mcap else None
        return shares, mcap_usd, currency, price

    def _save(self, company, shares, mcap_usd, price):
        fields = []
        if shares:
            company.shares_outstanding = int(shares)
            fields.append('shares_outstanding')
        if mcap_usd:
            try:
                company.market_cap_usd = Decimal(mcap_usd)
                fields.append('market_cap_usd')
            except (InvalidOperation, TypeError):
                pass
        if price:
            company.current_price = Decimal(str(round(float(price), 4)))
            fields.append('current_price')
        if fields:
            company.save(update_fields=fields)

        # Stamp the most recent price bar too — peer_comparison and the
        # screeners read market cap off MarketData, and every row was null.
        if mcap_usd:
            latest = MarketData.objects.filter(company=company).order_by('-date').first()
            if latest and latest.market_cap_usd is None:
                latest.market_cap_usd = Decimal(mcap_usd)
                latest.save(update_fields=['market_cap_usd'])
