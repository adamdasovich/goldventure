"""
Alpha Vantage MCP Server
Fetches real-time market data from Alpha Vantage API and caches it in the database
"""

import requests
from typing import Dict, List, Any
from datetime import datetime, date
from decimal import Decimal
from .base import BaseMCPServer
from django.conf import settings
from django.db.models import Q
from core.models import Company, MarketData


class AlphaVantageServer(BaseMCPServer):
    """
    MCP Server for fetching real-time market data from Alpha Vantage.
    Automatically caches fetched data in the database.
    """

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id, user)
        self.api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.base_url = "https://www.alphavantage.co/query"

    def _register_tools(self):
        """Register all Alpha Vantage tools"""

        # Tool 1: Fetch real-time quote
        self.register_tool(
            name="alphavantage_get_quote",
            description=(
                "Fetch real-time stock quote from Alpha Vantage for any company by ticker symbol. "
                "Returns latest price, volume, and trading data. "
                "Data is automatically cached in the database for future use. "
                "Use this when market data is not available in the database."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, TSLA, BAY.V for TSX Venture)"
                    }
                },
                "required": ["ticker_symbol"]
            },
            handler=self._get_quote
        )

        # Tool 2: Fetch intraday data
        self.register_tool(
            name="alphavantage_get_intraday",
            description=(
                "Fetch intraday (minute-by-minute or hourly) price data from Alpha Vantage. "
                "Useful for getting recent trading activity. "
                "Returns time series data for the current trading day."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval: 1min, 5min, 15min, 30min, 60min",
                        "default": "60min"
                    }
                },
                "required": ["ticker_symbol"]
            },
            handler=self._get_intraday
        )

        # Tool 3: Fetch daily time series (with caching)
        self.register_tool(
            name="alphavantage_get_daily",
            description=(
                "Fetch daily historical price data from Alpha Vantage. "
                "Returns up to 100 days of daily OHLCV data. "
                "Data is automatically saved to the database for future queries."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "outputsize": {
                        "type": "string",
                        "description": "compact (100 days) or full (20+ years)",
                        "default": "compact"
                    }
                },
                "required": ["ticker_symbol"]
            },
            handler=self._get_daily
        )

    # =============================================================================
    # TOOL HANDLERS
    # =============================================================================

    def _get_quote(self, ticker_symbol: str) -> Dict:
        """Fetch real-time quote and cache in database"""
        try:
            if not self.api_key:
                return {
                    "error": "Alpha Vantage API key not configured",
                    "message": "Please add ALPHA_VANTAGE_API_KEY to your Django settings"
                }

            # Call Alpha Vantage API
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker_symbol,
                "apikey": self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                return {"error": f"Alpha Vantage error: {data['Error Message']}"}

            if "Note" in data:
                return {"error": "API rate limit reached. Please try again in a minute."}

            # Parse response
            quote = data.get("Global Quote", {})
            if not quote:
                return {"error": f"No data found for ticker symbol: {ticker_symbol}"}

            # Extract data
            symbol = quote.get("01. symbol", ticker_symbol)
            open_price = Decimal(quote.get("02. open", "0"))
            high_price = Decimal(quote.get("03. high", "0"))
            low_price = Decimal(quote.get("04. low", "0"))
            close_price = Decimal(quote.get("05. price", "0"))
            volume = int(quote.get("06. volume", "0"))
            latest_day = quote.get("07. latest trading day", "")
            change = Decimal(quote.get("09. change", "0"))
            change_percent = quote.get("10. change percent", "0%").rstrip("%")

            # Try to find company in database
            company = Company.objects.filter(
                Q(ticker_symbol__iexact=ticker_symbol) |
                Q(ticker_symbol__iexact=ticker_symbol.replace('.V', '').replace('.TO', ''))
            ).first()

            # Cache data in database if company exists
            cached = False
            if company and latest_day:
                try:
                    trade_date = datetime.strptime(latest_day, "%Y-%m-%d").date()

                    # Create or update market data
                    market_data, created = MarketData.objects.update_or_create(
                        company=company,
                        date=trade_date,
                        defaults={
                            'open_price': open_price,
                            'high_price': high_price,
                            'low_price': low_price,
                            'close_price': close_price,
                            'volume': volume
                        }
                    )
                    cached = True
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Error caching data: {str(e)}")

            return {
                "ticker": symbol,
                "latest_trading_day": latest_day,
                "price": float(close_price),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "volume": volume,
                "change": float(change),
                "change_percent": change_percent,
                "cached_in_database": cached,
                "source": "Alpha Vantage (real-time)"
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_intraday(self, ticker_symbol: str, interval: str = "60min") -> Dict:
        """Fetch intraday data"""
        try:
            if not self.api_key:
                return {
                    "error": "Alpha Vantage API key not configured",
                    "message": "Please add ALPHA_VANTAGE_API_KEY to your Django settings"
                }

            # Call Alpha Vantage API
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": ticker_symbol,
                "interval": interval,
                "apikey": self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                return {"error": f"Alpha Vantage error: {data['Error Message']}"}

            if "Note" in data:
                return {"error": "API rate limit reached. Please try again in a minute."}

            # Parse time series
            time_series_key = f"Time Series ({interval})"
            time_series = data.get(time_series_key, {})

            if not time_series:
                return {"error": f"No intraday data found for ticker symbol: {ticker_symbol}"}

            # Convert to list of data points (last 10 points)
            data_points = []
            for timestamp, values in list(time_series.items())[:10]:
                data_points.append({
                    "timestamp": timestamp,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })

            return {
                "ticker": ticker_symbol,
                "interval": interval,
                "data_points": data_points,
                "count": len(data_points),
                "source": "Alpha Vantage (intraday)"
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_daily(self, ticker_symbol: str, outputsize: str = "compact") -> Dict:
        """Fetch daily historical data and cache in database"""
        try:
            if not self.api_key:
                return {
                    "error": "Alpha Vantage API key not configured",
                    "message": "Please add ALPHA_VANTAGE_API_KEY to your Django settings"
                }

            # Call Alpha Vantage API
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker_symbol,
                "outputsize": outputsize,
                "apikey": self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                return {"error": f"Alpha Vantage error: {data['Error Message']}"}

            if "Note" in data:
                return {"error": "API rate limit reached. Please try again in a minute."}

            # Parse time series
            time_series = data.get("Time Series (Daily)", {})

            if not time_series:
                return {"error": f"No daily data found for ticker symbol: {ticker_symbol}"}

            # Try to find company in database
            company = Company.objects.filter(
                Q(ticker_symbol__iexact=ticker_symbol) |
                Q(ticker_symbol__iexact=ticker_symbol.replace('.V', '').replace('.TO', ''))
            ).first()

            # Cache data in database if company exists
            cached_count = 0
            if company:
                for date_str, values in time_series.items():
                    try:
                        trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        open_price = Decimal(values.get("1. open", 0))
                        high_price = Decimal(values.get("2. high", 0))
                        low_price = Decimal(values.get("3. low", 0))
                        close_price = Decimal(values.get("4. close", 0))
                        volume = int(values.get("5. volume", 0))

                        # Create or update market data
                        market_data, created = MarketData.objects.update_or_create(
                            company=company,
                            date=trade_date,
                            defaults={
                                'open_price': open_price,
                                'high_price': high_price,
                                'low_price': low_price,
                                'close_price': close_price,
                                'volume': volume
                            }
                        )
                        if created:
                            cached_count += 1

                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error caching date {date_str}: {str(e)}")
                        continue

            # Format response with summary
            daily_data = []
            for date_str, values in list(time_series.items())[:30]:  # Last 30 days
                daily_data.append({
                    "date": date_str,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })

            return {
                "ticker": ticker_symbol,
                "daily_data": daily_data,
                "total_days_received": len(time_series),
                "showing_last_days": len(daily_data),
                "cached_in_database": cached_count,
                "source": "Alpha Vantage (daily)"
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
