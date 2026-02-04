"""
Stock Price Scraper
Fetches daily closing prices and volume for all companies in the database.
Primary source: Stockwatch.com
Designed to run after market close (4:30 PM ET weekdays).
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime, date
import decimal
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class StockPriceScraper:
    """
    Scrapes daily stock prices for all companies using Stockwatch.com.
    Falls back to Alpha Vantage or Yahoo Finance if Stockwatch fails.
    """

    def __init__(self):
        self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.alpha_vantage_url = "https://www.alphavantage.co/query"
        self.stockwatch_url = "https://www.stockwatch.com/Quote/Detail"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_stockwatch_exchange_prefix(self, exchange: str) -> str:
        """
        Get the Stockwatch exchange prefix for a given exchange.
        Stockwatch uses: V: for TSX-V, T: for TSX, C: for CSE
        """
        exchange_map = {
            'tsxv': 'V',
            'tsx': 'T',
            'cse': 'C',
        }
        return exchange_map.get(exchange.lower(), 'V')

    def _parse_price(self, text: str) -> Optional[Decimal]:
        """Parse price string to Decimal, handling various formats"""
        if not text:
            return None
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = re.sub(r'[$,\s]', '', text.strip())
            if cleaned and cleaned != '-':
                return Decimal(cleaned)
        except (ValueError, decimal.InvalidOperation) as e:
            logger.debug(f"Failed to parse price '{text}': {e}")
        return None

    def _parse_volume(self, text: str) -> int:
        """Parse volume string (often in thousands on Stockwatch)"""
        if not text:
            return 0
        try:
            cleaned = re.sub(r'[,\s]', '', text.strip())
            if cleaned and cleaned != '-':
                # Stockwatch shows volume in thousands
                value = float(cleaned)
                return int(value * 1000)  # Convert to actual shares
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse volume '{text}': {e}")
        return 0

    def fetch_quote_stockwatch(self, ticker: str, exchange: str) -> Optional[Dict]:
        """
        Fetch stock quote from Stockwatch.com
        URL format: https://www.stockwatch.com/Quote/Detail?V:TICKER

        Stockwatch table structure (approximate cell indices):
        0: Symbol info (e.g., "BAY- V↑ATS")
        1: Large number (52-week shares traded or similar) - NOT the price
        2-4: Bid · Ask (e.g., "0.045", "·", "0.05")
        5: Volume in thousands (e.g., "655.0")
        6: Last/Current price (e.g., "0.05")
        7: Change amount (e.g., "+0.005")
        8: Change percent (e.g., "11.1")
        12: Open-High-Low concatenated (e.g., "0.050.050.05")
        13: 52-week High-Low (e.g., "0.08  0.04")
        """
        try:
            # Format the URL with exchange prefix
            exchange_prefix = self._get_stockwatch_exchange_prefix(exchange)
            url = f"{self.stockwatch_url}?{exchange_prefix}:{ticker.upper()}"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the quote table
            quote_table = soup.find('table', class_='Quote')
            if not quote_table:
                logger.warning(f"No Quote table found for {ticker}")
                return None

            # Extract all table cells
            cells = quote_table.find_all('td')
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Initialize data structure
            quote_data = {
                'ticker': ticker,
                'close': None,
                'open': None,
                'high': None,
                'low': None,
                'volume': 0,
                'change': Decimal('0'),
                'change_percent': Decimal('0'),
                'date': date.today().strftime('%Y-%m-%d'),
                'source': 'Stockwatch'
            }

            # Strategy: Use positional parsing based on Stockwatch's table structure
            # Structure after separator "·": [ask] [vol?] [last_price] [change] [percent] [more_vol] ...
            # The last price is typically the 2nd numeric value after the ask (index 4 -> 6)

            separator_idx = None
            for i, text in enumerate(cell_texts):
                if text == '·':
                    separator_idx = i
                    break

            if separator_idx is not None:
                # After separator: cell[sep+1] = ask, cell[sep+2] = volume?, cell[sep+3] = last price
                # Actually: sep+1=ask, sep+2=small_vol, sep+3=last_price
                after_sep = cell_texts[separator_idx + 1:]

                # Find numeric values after separator
                numeric_values = []
                for i, text in enumerate(after_sep[:10]):  # Only look at first 10 cells
                    # Skip cells that start with +/- (these are change values)
                    if text.startswith('+') or text.startswith('-'):
                        change = self._parse_price(text)
                        if change is not None and abs(change) < 100:
                            quote_data['change'] = change
                        continue

                    price = self._parse_price(text)
                    if price and price > 0:
                        numeric_values.append((i, price))

                # Pattern analysis:
                # Index 0: Ask price (e.g., 6.42)
                # Index 1: Volume or small number (0.8 or 655.0)
                # Index 2: Last price (same or similar to ask)
                # Index 3+: Change percent, more volume numbers, etc.

                if len(numeric_values) >= 3:
                    ask_price = numeric_values[0][1]  # First value is ask
                    second_val = numeric_values[1][1]  # Could be volume or another price
                    third_val = numeric_values[2][1]   # Could be last price or volume

                    # The last price should be very close to the ask price (within ~5%)
                    # If third_val is close to ask, it's probably the last price
                    # Otherwise, second_val might be the price

                    if abs(third_val - ask_price) / max(ask_price, Decimal('0.01')) < Decimal('0.1'):
                        # Third value is close to ask - it's the price
                        quote_data['close'] = third_val
                        quote_data['volume'] = int(second_val * 1000)
                    elif abs(second_val - ask_price) / max(ask_price, Decimal('0.01')) < Decimal('0.1'):
                        # Second value is close to ask - it's the price, third is volume
                        quote_data['close'] = second_val
                        quote_data['volume'] = int(third_val * 1000)
                    else:
                        # Unclear - assume position-based: ask, vol, price
                        quote_data['close'] = third_val
                        quote_data['volume'] = int(second_val * 1000)

            # Try to find Open-High-Low from concatenated values like "0.050.050.05"
            for text in cell_texts:
                # Pattern: 3 prices concatenated without spaces
                match = re.match(r'^(\d+\.\d+)(\d+\.\d+)(\d+\.\d+)$', text)
                if match:
                    try:
                        vals = [Decimal(match.group(i)) for i in [1, 2, 3]]
                        quote_data['open'] = vals[0]
                        quote_data['high'] = vals[1]
                        quote_data['low'] = vals[2]
                        break
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass

            # Extract change percent from a standalone number near the change
            for i, text in enumerate(cell_texts):
                # Look for percent values (usually single or double digit number after change)
                if quote_data['change'] != Decimal('0'):
                    try:
                        pct = Decimal(text)
                        if -50 < pct < 100:  # Reasonable percent range
                            quote_data['change_percent'] = pct
                            break
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass

            if quote_data['close'] is None or quote_data['close'] <= 0:
                logger.warning(f"Could not parse price for {ticker}")
                return None

            return quote_data

        except Exception as e:
            logger.error(f"Error fetching Stockwatch quote for {ticker}: {e}")
            return None

    def fetch_quote_alpha_vantage(self, ticker: str, exchange: str) -> Optional[Dict]:
        """
        Fallback: Fetch real-time quote from Alpha Vantage.
        """
        if not self.alpha_vantage_key:
            return None

        try:
            # Format ticker for Alpha Vantage
            api_ticker = ticker.upper()
            if exchange == 'tsx':
                api_ticker = f"{ticker}.TO"
            elif exchange == 'tsxv':
                api_ticker = f"{ticker}.V"
            elif exchange == 'cse':
                api_ticker = f"{ticker}.CN"

            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": api_ticker,
                "apikey": self.alpha_vantage_key
            }

            response = requests.get(self.alpha_vantage_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if "Error Message" in data or "Note" in data:
                return None

            quote = data.get("Global Quote", {})
            if not quote:
                return None

            return {
                'ticker': ticker,
                'open': Decimal(quote.get("02. open", "0")) if quote.get("02. open") else None,
                'high': Decimal(quote.get("03. high", "0")) if quote.get("03. high") else None,
                'low': Decimal(quote.get("04. low", "0")) if quote.get("04. low") else None,
                'close': Decimal(quote.get("05. price", "0")),
                'volume': int(quote.get("06. volume", "0")),
                'date': quote.get("07. latest trading day", date.today().strftime('%Y-%m-%d')),
                'change': Decimal(quote.get("09. change", "0")),
                'change_percent': Decimal(quote.get("10. change percent", "0%").rstrip("%")),
                'source': 'Alpha Vantage'
            }

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage quote for {ticker}: {e}")
            return None

    def fetch_company_price(self, company) -> Optional[Dict]:
        """
        Fetch price for a single company, trying multiple sources.
        Priority: Stockwatch (Canadian exchanges) -> Alpha Vantage -> Yahoo
        """
        if not company.ticker_symbol:
            return None

        ticker = company.ticker_symbol.upper()
        exchange = company.exchange or 'tsxv'

        # For Canadian exchanges, try Stockwatch first
        if exchange in ['tsx', 'tsxv', 'cse']:
            quote = self.fetch_quote_stockwatch(ticker, exchange)
            if quote:
                return quote

        # Fallback to Alpha Vantage
        quote = self.fetch_quote_alpha_vantage(ticker, exchange)
        if quote:
            return quote

        return None

    def save_price(self, company, quote: Dict) -> bool:
        """
        Save price data to both StockPrice and MarketData models.
        This ensures data is accessible via both the scheduled task results
        and the AI assistant's financial tools.
        """
        from core.models import StockPrice, MarketData

        try:
            trade_date = datetime.strptime(quote['date'], '%Y-%m-%d').date() if quote.get('date') else date.today()

            # Determine currency based on exchange
            currency = 'CAD' if company.exchange in ['tsx', 'tsxv', 'cse'] else 'USD'

            # Create or update the StockPrice record
            price_obj, created = StockPrice.objects.update_or_create(
                company=company,
                date=trade_date,
                defaults={
                    'close_price': quote['close'],
                    'volume': quote.get('volume', 0),
                    'open_price': quote.get('open'),
                    'high_price': quote.get('high'),
                    'low_price': quote.get('low'),
                    'change_amount': quote.get('change', Decimal('0')),
                    'change_percent': quote.get('change_percent', Decimal('0')),
                    'currency': currency,
                    'source': quote.get('source', 'Unknown')
                }
            )

            # Also save to MarketData for AI assistant access
            # MarketData requires non-null OHLC values, so provide defaults
            MarketData.objects.update_or_create(
                company=company,
                date=trade_date,
                defaults={
                    'open_price': quote.get('open') or quote['close'],
                    'high_price': quote.get('high') or quote['close'],
                    'low_price': quote.get('low') or quote['close'],
                    'close_price': quote['close'],
                    'volume': quote.get('volume', 0),
                    'change_amount': quote.get('change', Decimal('0')),
                    'change_percent': quote.get('change_percent', Decimal('0')),
                    'currency': currency,
                    'source': quote.get('source', 'Unknown')
                }
            )

            # Also update the company's current_price field
            company.current_price = quote['close']
            company.save(update_fields=['current_price', 'updated_at'])

            logger.info(f"{'Created' if created else 'Updated'} price for {company.ticker_symbol}: ${quote['close']}")
            return True

        except Exception as e:
            logger.error(f"Error saving price for {company.ticker_symbol}: {e}")
            return False

    def fetch_all_company_prices(self) -> Dict:
        """
        Fetch and save prices for all companies with ticker symbols.
        Returns summary of results.
        """
        from core.models import Company

        # Get all active companies with ticker symbols
        companies = Company.objects.filter(
            is_active=True,
            ticker_symbol__isnull=False
        ).exclude(ticker_symbol='')

        results = {
            'success': True,
            'total_companies': companies.count(),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': [],
            'errors': [],
            'timestamp': timezone.now().isoformat()
        }

        for company in companies:
            try:
                quote = self.fetch_company_price(company)

                if quote:
                    if self.save_price(company, quote):
                        results['successful'] += 1
                        results['details'].append({
                            'ticker': company.ticker_symbol,
                            'price': float(quote['close']),
                            'source': quote.get('source')
                        })
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"{company.ticker_symbol}: Failed to save")
                else:
                    results['skipped'] += 1
                    results['errors'].append(f"{company.ticker_symbol}: No quote data available")

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{company.ticker_symbol}: {str(e)}")

        results['success'] = results['failed'] == 0

        return results


def fetch_and_save_stock_prices() -> Dict:
    """
    Main function to fetch and save all stock prices.
    Call this from scheduled task.
    """
    scraper = StockPriceScraper()
    return scraper.fetch_all_company_prices()
