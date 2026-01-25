"""
API Views for GoldVenture Platform
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q


class FlexiblePagePagination(PageNumberPagination):
    """Custom pagination that allows page_size query parameter"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

from .models import (
    Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, MarketData, NewsRelease, Document,
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    # Property Exchange models
    ProspectorProfile, PropertyListing, PropertyMedia, PropertyInquiry,
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement,
    InquiryMessage, FeaturedPropertyConfig,
    # News models
    NewsSource, NewsArticle, NewsScrapeJob,
    # Company Portal models
    CompanyResource, SpeakingEvent, CompanySubscription, SubscriptionInvoice,
    CompanyAccessRequest,
    # Investment Interest models
    InvestmentInterest, InvestmentInterestAggregate,
    # Store models
    StoreCategory, StoreProduct, StoreProductImage, StoreProductVariant,
    StoreDigitalAsset, StoreCart, StoreCartItem, StoreOrder, StoreOrderItem,
    StoreShippingRate, StoreProductShare, StoreRecentPurchase,
    StoreProductInquiry, UserStoreBadge,
    # Glossary
    GlossaryTerm, GlossaryTermSubmission,
)
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,
    ProjectSerializer, ProjectDetailSerializer,
    ResourceEstimateSerializer, EconomicStudySerializer,
    FinancingSerializer, InvestorSerializer,
    MarketDataSerializer, NewsReleaseSerializer, DocumentSerializer,
    SpeakerEventListSerializer, SpeakerEventDetailSerializer,
    SpeakerEventCreateSerializer, EventQuestionSerializer, EventReactionSerializer,
    # Property Exchange serializers
    ProspectorProfileSerializer, PropertyListingListSerializer,
    PropertyListingDetailSerializer, PropertyListingCreateSerializer,
    PropertyMediaSerializer, PropertyInquirySerializer, PropertyWatchlistSerializer,
    SavedPropertySearchSerializer, PropertyChoicesSerializer,
    ProspectorCommissionAgreementSerializer, ProspectorCommissionAgreementCreateSerializer,
    # Inquiry message serializers
    InquiryMessageSerializer, InquiryMessageCreateSerializer, PropertyInquiryWithMessagesSerializer,
    # Company Portal serializers
    CompanyResourceSerializer, CompanyResourceCreateSerializer, CompanyResourceChoicesSerializer,
    SpeakingEventSerializer, SpeakingEventCreateSerializer, SpeakingEventListSerializer,
    SpeakingEventChoicesSerializer, CompanySubscriptionSerializer, CompanySubscriptionStatusSerializer,
    SubscriptionInvoiceSerializer,
    # Company Access Request serializers
    CompanyAccessRequestSerializer, CompanyAccessRequestCreateSerializer,
    CompanyAccessRequestReviewSerializer, CompanyAccessRequestChoicesSerializer,
    # Investment Interest serializers
    InvestmentInterestSerializer, InvestmentInterestCreateSerializer,
    InvestmentInterestAggregateSerializer, InvestmentInterestStatusSerializer,
    # Store serializers
    StoreCategorySerializer, StoreProductListSerializer, StoreProductDetailSerializer,
    StoreCartSerializer, StoreCartItemSerializer, StoreOrderSerializer,
    StoreShippingRateSerializer, StoreRecentPurchaseSerializer,
    StoreProductShareSerializer, StoreProductInquirySerializer,
    StoreProductInquiryCreateSerializer, UserStoreBadgeSerializer,
    AddToCartSerializer, UpdateCartItemSerializer, CheckoutSerializer,
    # Store Admin serializers
    StoreCategoryAdminSerializer, StoreProductAdminListSerializer,
    StoreProductAdminDetailSerializer, StoreProductAdminCreateSerializer,
    StoreProductImageAdminSerializer, StoreProductVariantAdminSerializer,
    StoreDigitalAssetAdminSerializer, StoreOrderAdminSerializer,
    # Glossary serializers
    GlossaryTermSerializer, GlossaryTermSubmissionSerializer,
    GlossaryTermSubmissionCreateSerializer,
)
from claude_integration.client import ClaudeClient
from claude_integration.client_optimized import OptimizedClaudeClient
import requests
from django.conf import settings
from datetime import datetime, timedelta
from django.core.cache import cache


# ============================================================================
# METALS PRICING API
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def metals_prices(request):
    """
    Get current precious metals prices from Kitco (scraped) or Twelve Data API fallback.

    GET /api/metals/prices/

    Returns prices for Gold (XAU), Silver (XAG), Platinum (XPT), Palladium (XPD)
    Primary source: Kitco scraped data (updated twice daily)
    Fallback: Twelve Data API (if no recent scraped data)
    Data is cached for 5 minutes.
    """
    from .models import MetalPrice

    # Check cache first
    cached_data = cache.get('metals_prices')
    if cached_data:
        cached_data['cached'] = True
        return Response(cached_data)

    # Metal display info
    metal_info = {
        'XAU': {'name': 'Gold', 'unit': 'oz'},
        'XAG': {'name': 'Silver', 'unit': 'oz'},
        'XPT': {'name': 'Platinum', 'unit': 'oz'},
        'XPD': {'name': 'Palladium', 'unit': 'oz'}
    }

    results = []

    # Try to get Kitco scraped data first
    try:
        kitco_prices = MetalPrice.get_latest_prices()
        if kitco_prices:
            for symbol, price_obj in kitco_prices.items():
                info = metal_info.get(symbol, {'name': symbol, 'unit': 'oz'})
                results.append({
                    'metal': info['name'],
                    'symbol': symbol,
                    'price': float(price_obj.bid_price),
                    'ask_price': float(price_obj.ask_price),
                    'change_amount': float(price_obj.change_amount),
                    'change_percent': float(price_obj.change_percent),
                    'unit': info['unit'],
                    'currency': 'USD',
                    'last_updated': price_obj.scraped_at.isoformat(),
                    'source': 'Kitco'
                })

            if results:
                response_data = {
                    'metals': results,
                    'timestamp': datetime.now().isoformat(),
                    'cached': False,
                    'source': 'Kitco (scraped)'
                }
                cache.set('metals_prices', response_data, 300)
                return Response(response_data)
    except Exception as e:
        print(f"Error fetching Kitco prices: {e}")

    # Fallback to Twelve Data API if no Kitco data
    api_key = getattr(settings, 'TWELVE_DATA_API_KEY', None)
    if not api_key:
        # Return estimated prices if no API key and no Kitco data
        fallback_prices = {
            'XAU': 2650.00,
            'XAG': 31.50,
            'XPT': 960.00,
            'XPD': 1030.00
        }
        for symbol, price in fallback_prices.items():
            info = metal_info.get(symbol, {'name': symbol, 'unit': 'oz'})
            results.append({
                'metal': info['name'],
                'symbol': symbol,
                'price': price,
                'change_percent': 0.0,
                'unit': info['unit'],
                'currency': 'USD',
                'last_updated': datetime.now().isoformat(),
                'source': 'Estimated (no data source configured)',
                'note': 'Configure Kitco scraping for real-time data'
            })

        response_data = {
            'metals': results,
            'timestamp': datetime.now().isoformat(),
            'cached': False,
            'source': 'Estimated'
        }
        cache.set('metals_prices', response_data, 300)
        return Response(response_data)

    # Use Twelve Data API as fallback
    metals = {
        'XAU/USD': {'name': 'Gold', 'symbol': 'XAU', 'unit': 'oz'},
        'XAG/USD': {'name': 'Silver', 'symbol': 'XAG', 'unit': 'oz'},
        'XPT/USD': {'name': 'Platinum', 'symbol': 'XPT', 'unit': 'oz'},
        'XPD/USD': {'name': 'Palladium', 'symbol': 'XPD', 'unit': 'oz'}
    }

    for symbol_pair, info in metals.items():
        try:
            url = "https://api.twelvedata.com/price"
            params = {
                'symbol': symbol_pair,
                'apikey': api_key
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'price' in data:
                current_price = float(data['price'])

                try:
                    prev_url = "https://api.twelvedata.com/time_series"
                    prev_params = {
                        'symbol': symbol_pair,
                        'interval': '1day',
                        'outputsize': 2,
                        'apikey': api_key
                    }
                    prev_response = requests.get(prev_url, params=prev_params, timeout=10)
                    prev_data = prev_response.json()

                    if 'values' in prev_data and len(prev_data['values']) >= 2:
                        prev_price = float(prev_data['values'][1]['close'])
                        change_percent = ((current_price - prev_price) / prev_price) * 100
                    else:
                        change_percent = 0.0
                except:
                    change_percent = 0.0

                results.append({
                    'metal': info['name'],
                    'symbol': info['symbol'],
                    'price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'unit': info['unit'],
                    'currency': 'USD',
                    'last_updated': datetime.now().isoformat(),
                    'source': 'Twelve Data'
                })
            else:
                fallback_prices = {
                    'XAU': 2650.00,
                    'XAG': 31.50,
                    'XPT': 960.00,
                    'XPD': 1030.00
                }

                if info['symbol'] in fallback_prices:
                    import random
                    results.append({
                        'metal': info['name'],
                        'symbol': info['symbol'],
                        'price': fallback_prices[info['symbol']],
                        'change_percent': round(random.uniform(-2.5, 2.5), 2),
                        'unit': info['unit'],
                        'currency': 'USD',
                        'last_updated': datetime.now().isoformat(),
                        'source': 'Estimated',
                        'note': 'API limit reached'
                    })

        except Exception as e:
            results.append({
                'metal': info['name'],
                'symbol': info['symbol'],
                'price': None,
                'error': str(e)
            })

    response_data = {
        'metals': results,
        'timestamp': datetime.now().isoformat(),
        'cached': False,
        'source': 'Twelve Data (fallback)'
    }

    cache.set('metals_prices', response_data, 300)
    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def metal_historical(request, symbol):
    """
    Get historical price data for a specific metal.

    GET /api/metals/historical/<symbol>/?days=30

    symbol: XAU, XAG, XPT, XPD
    days: number of days of historical data (default: 30, max: 365)
    """

    days = int(request.query_params.get('days', 30))
    days = min(days, 365)  # Max 1 year

    # Check cache
    cache_key = f'metal_historical_{symbol}_{days}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    api_key = getattr(settings, 'TWELVE_DATA_API_KEY', None)
    if not api_key:
        return Response(
            {'error': 'Twelve Data API key not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    valid_symbols = ['XAU', 'XAG', 'XPT', 'XPD']
    if symbol not in valid_symbols:
        return Response(
            {'error': f'Invalid symbol. Must be one of: {", ".join(valid_symbols)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Twelve Data API for historical data
        symbol_pair = f'{symbol}/USD'
        url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': symbol_pair,
            'interval': '1day',
            'outputsize': days,
            'apikey': api_key
        }

        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        if 'values' in data and data['values']:
            # Convert Twelve Data format to our format
            historical_data = []
            for item in reversed(data['values']):  # Reverse to get oldest first
                historical_data.append({
                    'date': item['datetime'],
                    'open': round(float(item['open']), 2),
                    'high': round(float(item['high']), 2),
                    'low': round(float(item['low']), 2),
                    'close': round(float(item['close']), 2)
                })

            response_data = {
                'symbol': symbol,
                'data': historical_data,
                'days': len(historical_data),
                'timestamp': datetime.now().isoformat(),
                'source': 'Twelve Data'
            }

            # Cache for 1 hour
            cache.set(cache_key, response_data, 3600)

            return Response(response_data)
        else:
            error_msg = data.get('message', data.get('note', 'No data available'))
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# STOCK QUOTE API
# ============================================================================

def _get_stockwatch_quote(ticker_symbol: str, exchange: str) -> dict:
    """
    Fetch real-time stock quote from StockWatch.com for Canadian stocks.
    StockWatch provides excellent coverage for TSX, TSXV, and CSE stocks.

    Data format from StockWatch table row:
    CSE - C | 0.5 | 0.98 | · | 0.99 | 1.0 | 0.99 | +0.06 | 6.5 | 189.7 | 183 | 98 | ...
    [exch] | [bid_size] | [bid] | [·] | [ask] | [ask_size] | [last] | [chg] | [%ch] | [vol] | ...
    """
    import requests
    from bs4 import BeautifulSoup
    import re

    try:
        # Build StockWatch URL based on exchange
        exchange_upper = exchange.upper() if exchange else ''
        if exchange_upper == 'CSE':
            stockwatch_symbol = f"C:{ticker_symbol}"
            exchange_prefix = 'CSE - C'
        elif exchange_upper == 'TSXV':
            stockwatch_symbol = f"V:{ticker_symbol}"
            exchange_prefix = 'TSX-V - V'
        elif exchange_upper == 'TSX':
            stockwatch_symbol = f"T:{ticker_symbol}"
            exchange_prefix = 'TSX - T'
        else:
            return {'error': f'StockWatch does not support exchange: {exchange}'}

        url = f"https://www.stockwatch.com/Quote/Detail?{stockwatch_symbol}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse the quote data from StockWatch HTML
        price = None
        change = None
        change_percent = None
        volume = None

        # Find the data row for the primary exchange
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 10:
                first_cell = cells[0].get_text(strip=True)

                # Match exchange pattern like "CSE - C" or similar
                if exchange_prefix in first_cell:
                    # Extract all cell text values
                    cell_texts = [c.get_text(strip=True) for c in cells]

                    # Based on observed format:
                    # 0: "CSE - C", 1: bid_size, 2: bid, 3: "·", 4: ask, 5: ask_size,
                    # 6: last, 7: change, 8: %change, 9: volume, 10: $volume, 11: trades

                    try:
                        # Last price is typically at index 6
                        if len(cell_texts) > 6:
                            price_text = cell_texts[6]
                            price_match = re.search(r'(\d+\.?\d*)', price_text)
                            if price_match:
                                price = float(price_match.group(1))

                        # Change is at index 7 (has +/- prefix)
                        if len(cell_texts) > 7:
                            change_text = cell_texts[7]
                            change_match = re.search(r'([+-]?\d+\.?\d*)', change_text)
                            if change_match:
                                change = float(change_match.group(1))

                        # Percent change is at index 8
                        if len(cell_texts) > 8:
                            pct_text = cell_texts[8]
                            pct_match = re.search(r'([+-]?\d+\.?\d*)', pct_text)
                            if pct_match:
                                change_percent = float(pct_match.group(1))

                        # Volume is at index 9 (in thousands)
                        if len(cell_texts) > 9:
                            vol_text = cell_texts[9].replace(',', '')
                            vol_match = re.search(r'(\d+\.?\d*)', vol_text)
                            if vol_match:
                                volume = int(float(vol_match.group(1)) * 1000)

                        if price:
                            break
                    except (ValueError, IndexError):
                        pass

        if not price:
            return {'error': f'Could not parse price from StockWatch for {ticker_symbol}'}

        return {
            'price': round(price, 4),
            'change': round(change, 4) if change else 0,
            'change_percent': round(change_percent, 2) if change_percent else 0,
            'volume': volume or 0,
            'day_high': price,
            'day_low': price,
            'source': 'stockwatch'
        }

    except requests.exceptions.RequestException as e:
        return {'error': f'StockWatch request error: {str(e)}'}
    except Exception as e:
        return {'error': f'StockWatch parsing error: {str(e)}'}


def _get_yahoo_finance_quote(ticker_symbol: str) -> dict:
    """
    Fetch real-time stock quote from Yahoo Finance using yfinance.
    Uses history() method which is more reliable than info property.
    Returns dict with quote data or error.
    """
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker_symbol)

        # Use history() which is more reliable and less rate-limited
        # Get last 2 days of data to calculate change
        hist = stock.history(period='2d')

        if hist.empty:
            return {'error': f'No data found for {ticker_symbol}'}

        # Get the most recent data
        latest = hist.iloc[-1]
        price = float(latest['Close'])
        volume = int(latest['Volume'])

        # Calculate change from previous day
        if len(hist) >= 2:
            prev = hist.iloc[-2]
            previous_close = float(prev['Close'])
            change = price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
        else:
            previous_close = price
            change = 0
            change_percent = 0

        return {
            'price': round(price, 4),
            'previous_close': round(previous_close, 4),
            'change': round(change, 4),
            'change_percent': round(change_percent, 2),
            'volume': volume,
            'day_high': float(latest.get('High', price)),
            'day_low': float(latest.get('Low', price)),
            'source': 'yahoo_finance'
        }
    except Exception as e:
        return {'error': f'Yahoo Finance error: {str(e)}'}


@api_view(['GET'])
@permission_classes([AllowAny])
def stock_quote(request, company_id):
    """
    Get real-time stock quote for a company.

    GET /api/companies/<company_id>/stock-quote/

    Fetches stock data with the following priority:
    1. In-memory cache (5 minute TTL)
    2. Yahoo Finance (more up-to-date for Canadian stocks)
    3. StockWatch.com (fallback for Canadian CSE/TSXV/TSX stocks)
    4. Alpha Vantage (fallback for non-CSE stocks - CSE not supported)
    5. Database (last resort fallback)

    Returns only essential data (ticker, price, change) to minimize payload.
    """
    from datetime import date

    # Get company
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check in-memory cache first (5 minute TTL)
    cache_key = f'stock_quote_{company_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        cached_data['cached'] = True
        return Response(cached_data)

    today = date.today()

    # Build ticker symbol for Yahoo Finance / Alpha Vantage
    ticker = company.ticker_symbol
    exchange_upper = company.exchange.upper() if company.exchange else ''
    if exchange_upper == 'TSXV':
        yahoo_ticker = f"{ticker}.V"
        av_ticker = f"{ticker}.V"
    elif exchange_upper == 'TSX':
        yahoo_ticker = f"{ticker}.TO"
        av_ticker = f"{ticker}.TO"
    elif exchange_upper == 'CSE':
        yahoo_ticker = f"{ticker}.CN"
        av_ticker = f"{ticker}.CN"
    elif exchange_upper == 'ASX':
        yahoo_ticker = f"{ticker}.AX"
        av_ticker = f"{ticker}.AX"
    elif exchange_upper == 'AIM' or exchange_upper == 'LSE':
        yahoo_ticker = f"{ticker}.L"
        av_ticker = f"{ticker}.L"
    else:
        yahoo_ticker = ticker
        av_ticker = ticker

    # Try Yahoo Finance first (more up-to-date for Canadian stocks)
    yahoo_result = _get_yahoo_finance_quote(yahoo_ticker)

    if 'error' not in yahoo_result and yahoo_result.get('price', 0) > 0:
        response_data = {
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'price': yahoo_result['price'],
            'change': yahoo_result['change'],
            'change_percent': yahoo_result['change_percent'],
            'volume': yahoo_result['volume'],
            'date': str(today),
            'source': 'yahoo_finance',
            'cached': False
        }

        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)
        return Response(response_data)

    # Yahoo Finance failed - try StockWatch for Canadian stocks (CSE, TSXV, TSX)
    if exchange_upper in ['CSE', 'TSXV', 'TSX']:
        stockwatch_result = _get_stockwatch_quote(ticker, exchange_upper)

        if 'error' not in stockwatch_result and stockwatch_result.get('price', 0) > 0:
            response_data = {
                'ticker': company.ticker_symbol,
                'exchange': company.exchange,
                'price': stockwatch_result['price'],
                'change': stockwatch_result['change'],
                'change_percent': stockwatch_result['change_percent'],
                'volume': stockwatch_result['volume'],
                'date': str(today),
                'source': 'stockwatch',
                'cached': False
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, 300)
            return Response(response_data)

    # StockWatch failed or not Canadian - try Alpha Vantage as fallback
    # Note: Alpha Vantage does NOT support CSE stocks
    if exchange_upper != 'CSE':
        from mcp_servers.alpha_vantage import AlphaVantageServer

        alpha_vantage = AlphaVantageServer(company_id=company_id)
        quote_result = alpha_vantage._get_quote(av_ticker)

        if 'error' not in quote_result and quote_result.get('price', 0) > 0:
            response_data = {
                'ticker': company.ticker_symbol,
                'exchange': company.exchange,
                'price': quote_result.get('price', 0),
                'change': quote_result.get('change', 0),
                'change_percent': float(quote_result.get('change_percent', '0')),
                'volume': quote_result.get('volume', 0),
                'date': quote_result.get('latest_trading_day', str(today)),
                'source': 'alpha_vantage',
                'cached': False
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, 300)
            return Response(response_data)

    # All external APIs failed - try database as last resort
    market_data = MarketData.objects.filter(
        company=company,
        date=today
    ).first()

    if market_data:
        # Calculate change from previous day
        yesterday_data = MarketData.objects.filter(
            company=company,
            date__lt=today
        ).order_by('-date').first()

        change = 0.0
        change_percent = 0.0
        if yesterday_data and yesterday_data.close_price:
            change = float(market_data.close_price - yesterday_data.close_price)
            if yesterday_data.close_price > 0:
                change_percent = (change / float(yesterday_data.close_price)) * 100

        response_data = {
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'price': float(market_data.close_price),
            'change': round(change, 4),
            'change_percent': round(change_percent, 2),
            'volume': market_data.volume,
            'date': str(market_data.date),
            'source': 'database_fallback',
            'cached': False
        }

        # Cache for 2 minutes (shorter since it's fallback data)
        cache.set(cache_key, response_data, 120)
        return Response(response_data)

    # No data available from any source
    error_msg = yahoo_result.get('error', quote_result.get('error', 'Unable to fetch stock data'))
    return Response(
        {'error': error_msg},
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


# ============================================================================
# CLAUDE CHAT API
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def claude_chat(request):
    """
    Handle Claude chat requests with MCP tool access.

    POST /api/claude/chat/
    {
        "message": "What are our total gold resources?",
        "conversation_history": [...],  # optional
        "system_prompt": "...",  # optional
        "optimized": true  # optional - use token-efficient client
    }

    The optimized client uses progressive tool discovery and result filtering
    for significant token savings (50-90% reduction in tool tokens).
    """

    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    system_prompt = request.data.get('system_prompt')
    use_optimized = request.data.get('optimized', True)  # Default to optimized

    if not message:
        return Response(
            {'error': 'message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Initialize Claude client (optimized or standard)
        if use_optimized:
            client = OptimizedClaudeClient()
        else:
            client = ClaudeClient()

        # Get response
        result = client.chat(
            message=message,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )

        return Response(result)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def company_chat(request, company_id):
    """
    Handle company-specific Claude chat requests with MCP tool access.

    POST /api/companies/{company_id}/chat/
    {
        "message": "What are the latest news releases?",
        "conversation_history": [...],  # optional
        "optimized": true  # optional - use token-efficient client
    }
    """

    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    use_optimized = request.data.get('optimized', True)  # Default to optimized

    if not message:
        return Response(
            {'error': 'message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get company for context
        company = Company.objects.get(pk=company_id)

        # Create company-specific system prompt
        system_prompt = f"""You are a helpful AI assistant for {company.name} ({company.ticker_symbol}).

You have access to tools for company data including projects, resources, financials, news, and documents.
If you need a tool that isn't loaded, use search_available_tools to find it.

Company context:
- Name: {company.name}
- Ticker: {company.ticker_symbol} ({company.exchange.upper() if company.exchange else 'N/A'})
- CEO: {company.ceo_name if company.ceo_name else 'N/A'}
- HQ: {company.headquarters_city}, {company.headquarters_country}

Be concise but thorough. Cite data sources and dates when relevant."""

        # Initialize Claude client with company context
        user = request.user if request.user.is_authenticated else None
        if use_optimized:
            client = OptimizedClaudeClient(company_id=company_id, user=user)
        else:
            client = ClaudeClient(company_id=company_id, user=user)

        # Get response
        result = client.chat(
            message=message,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )

        return Response(result)

    except Company.DoesNotExist:
        return Response(
            {'error': f'Company with id {company_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def available_tools(request):
    """
    Get list of all available MCP tools.

    GET /api/claude/tools/
    GET /api/claude/tools/?query=stock&detail=full

    Query parameters:
    - query: Search for tools by keyword
    - category: Filter by category (mining, financial, market, documents, news, search)
    - detail: Level of detail (name_only, description, full)
    """
    from mcp_servers.tool_registry import get_registry, ToolCategory, DetailLevel

    try:
        query = request.query_params.get('query')
        category_str = request.query_params.get('category')
        detail_str = request.query_params.get('detail', 'description')

        # Map detail level
        detail_map = {
            'name_only': DetailLevel.NAME_ONLY,
            'description': DetailLevel.WITH_DESCRIPTION,
            'full': DetailLevel.FULL_SCHEMA
        }
        detail_level = detail_map.get(detail_str, DetailLevel.WITH_DESCRIPTION)

        # Map category
        category = None
        if category_str:
            category_map = {
                'mining': ToolCategory.MINING,
                'financial': ToolCategory.FINANCIAL,
                'market': ToolCategory.MARKET,
                'documents': ToolCategory.DOCUMENTS,
                'news': ToolCategory.NEWS,
                'search': ToolCategory.SEARCH,
            }
            category = category_map.get(category_str)

        # Use registry for progressive discovery
        registry = get_registry()
        result = registry.search_tools(
            query=query,
            category=category,
            detail_level=detail_level,
            limit=50
        )

        # Add category list for reference
        result['available_categories'] = ['mining', 'financial', 'market', 'documents', 'news', 'search']

        return Response(result)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# NEWS SCRAPING API
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def scrape_company_news(request, company_id):
    """
    Scrape and classify company news releases from their website.

    POST /api/companies/<company_id>/scrape-news/

    Returns:
        {
            "status": "success",
            "message": "Scraped 10 news releases",
            "financial_count": 3,
            "non_financial_count": 7,
            "last_scraped": "2025-01-15T10:30:00Z"
        }
    """
    try:
        company = Company.objects.get(id=company_id, is_active=True)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not company.website:
        return Response(
            {'error': 'Company website not configured'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check cache - don't scrape if done within last 24 hours
    cache_key = f'news_scrape_{company_id}'
    last_scrape_data = cache.get(cache_key)

    if last_scrape_data:
        time_since_scrape = datetime.now() - datetime.fromisoformat(last_scrape_data['timestamp'])
        if time_since_scrape.total_seconds() < 86400:  # 24 hours
            return Response({
                'status': 'cached',
                'message': 'News releases were recently scraped',
                'last_scraped': last_scrape_data['timestamp'],
                'financial_count': last_scrape_data['financial_count'],
                'non_financial_count': last_scrape_data['non_financial_count']
            })

    try:
        # Trigger async Celery task for news scraping
        from .tasks import scrape_company_news_task

        task = scrape_company_news_task.delay(company_id)

        return Response({
            'status': 'processing',
            'message': 'News scraping started in background',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_scrape_status(request, task_id):
    """
    Check the status of a background news scraping task.

    GET /api/tasks/<task_id>/status/

    Returns:
        {
            "state": "PENDING|STARTED|SUCCESS|FAILURE",
            "result": {...task result if completed...}
        }
    """
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Task is waiting to be processed...'
        }
    elif task_result.state == 'STARTED':
        response = {
            'state': task_result.state,
            'status': 'Task is currently running...'
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': task_result.state,
            'result': task_result.result
        }
    elif task_result.state == 'FAILURE':
        response = {
            'state': task_result.state,
            'error': str(task_result.info)
        }
    else:
        response = {
            'state': task_result.state,
            'status': 'Unknown state'
        }

    return Response(response)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_news_releases(request, company_id):
    """
    Get news releases for a company, separated by financial and company updates.

    GET /api/companies/<company_id>/news-releases/

    Returns:
        {
            "financial": [...5 most recent financing news from NewsRelease...],
            "non_financial": [...10 most recent news...],
            "last_updated": "2025-01-15T10:30:00Z"
        }

    Financial news comes from NewsRelease (flagged financing items with is_material=True).
    Company updates come from NewsRelease (all news), with fallback to CompanyNews if empty.
    """
    from core.models import CompanyNews

    try:
        company = Company.objects.get(id=company_id, is_active=True)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get financial news from NewsRelease (flagged financing items)
    financial_releases = NewsRelease.objects.filter(
        company=company,
        is_material=True
    ).order_by('-release_date')[:5]
    financial_data = NewsReleaseSerializer(financial_releases, many=True).data

    # Get company updates - prefer NewsRelease, fallback to CompanyNews
    news_releases = NewsRelease.objects.filter(company=company).order_by('-release_date')[:10]
    non_financial_data = []
    last_updated = None

    if news_releases.exists():
        # Use NewsRelease data (from staggered scraping)
        for news in news_releases:
            news_item = {
                'id': news.id,
                'title': news.title,
                'release_date': str(news.release_date) if news.release_date else None,
                'release_type': news.release_type or 'general',
                'summary': news.summary or '',
                'url': news.url,
                'is_material': news.is_material or False,
            }
            non_financial_data.append(news_item)
        latest = news_releases.first()
        last_updated = str(latest.updated_at) if latest and latest.updated_at else None
    else:
        # Fallback to CompanyNews (legacy scraped news)
        scraped_news = CompanyNews.objects.filter(company=company).order_by('-publication_date')[:10]
        for news in scraped_news:
            news_item = {
                'id': news.id,
                'title': news.title,
                'release_date': str(news.publication_date) if news.publication_date else None,
                'release_type': news.news_type or 'corporate',
                'summary': news.summary or '',
                'url': news.source_url,
                'is_material': news.is_material or False,
            }
            non_financial_data.append(news_item)
        if scraped_news.exists():
            latest_scraped = scraped_news.first()
            last_updated = str(latest_scraped.extracted_at) if latest_scraped else None

    return Response({
        'financial': financial_data,
        'non_financial': non_financial_data,
        'last_updated': last_updated,
        'financial_count': len(financial_data),
        'non_financial_count': len(non_financial_data)
    })


# ============================================================================
# COMPANY VIEWSET
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    """API endpoint for companies"""
    queryset = Company.objects.all()
    permission_classes = [AllowAny]
    pagination_class = FlexiblePagePagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer

    def get_queryset(self):
        queryset = Company.objects.filter(is_active=True)

        # Only show approved companies to non-superusers
        if not (self.request.user and self.request.user.is_superuser):
            queryset = queryset.filter(approval_status='approved')

        # Filter by ticker
        ticker = self.request.query_params.get('ticker')
        if ticker:
            queryset = queryset.filter(ticker_symbol__iexact=ticker)

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(ticker_symbol__icontains=search)
            )

        # Filter by commodity - find companies with projects in specified commodity
        commodity = self.request.query_params.get('commodity')
        if commodity:
            # Support comma-separated commodities for multi-select
            commodities = [c.strip() for c in commodity.split(',') if c.strip()]
            if commodities:
                queryset = queryset.filter(
                    projects__primary_commodity__in=commodities
                ).distinct()

        return queryset.order_by('name')

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects for a company"""
        company = self.get_object()
        projects = company.projects.filter(is_active=True)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_description(self, request, pk=None):
        """
        Update company description.

        PATCH /api/companies/{id}/update_description/

        Only allowed for:
        - Superusers (is_superuser=True)
        - Company representatives (user.company == this company)

        Request body:
        {
            "description": "New company description text..."
        }
        """
        company = self.get_object()
        user = request.user

        # Check authorization
        is_authorized = (
            user.is_superuser or
            (user.company and user.company.id == company.id)
        )

        if not is_authorized:
            return Response(
                {'error': 'You do not have permission to edit this company description.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request data
        description = request.data.get('description')
        if description is None:
            return Response(
                {'error': 'Description field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the description
        company.description = description
        company.save(update_fields=['description', 'updated_at'])

        return Response({
            'success': True,
            'description': company.description,
            'message': 'Company description updated successfully.'
        })

    @action(detail=True, methods=['get'])
    def can_edit(self, request, pk=None):
        """
        Check if the current user can edit this company.

        GET /api/companies/{id}/can_edit/

        Returns:
        {
            "can_edit": true/false,
            "reason": "superuser" | "company_representative" | null
        }
        """
        company = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response({
                'can_edit': False,
                'reason': None
            })

        if user.is_superuser:
            return Response({
                'can_edit': True,
                'reason': 'superuser'
            })

        if user.company and user.company.id == company.id:
            return Response({
                'can_edit': True,
                'reason': 'company_representative'
            })

        return Response({
            'can_edit': False,
            'reason': None
        })

    def create(self, request, *args, **kwargs):
        """
        Submit a company for approval.

        POST /api/companies/

        Requires authentication. Companies submitted by users will have approval_status='pending_approval'
        and must be approved by a superuser before becoming visible to the public.
        """
        print("=== CUSTOM CREATE METHOD CALLED ===")
        print(f"Request data: {request.data}")

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to submit a company.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validate required fields
        name = request.data.get('name', '').strip()
        website_url = request.data.get('website_url', '').strip()
        presentation = request.data.get('presentation', '').strip()
        company_size = request.data.get('company_size', '').strip()
        industry = request.data.get('industry', '').strip()
        location = request.data.get('location', '').strip()
        contact_email = request.data.get('contact_email', '').strip()
        brief_description = request.data.get('brief_description', '').strip()

        errors = {}

        # Validate name
        if not name or len(name) < 2 or len(name) > 100:
            errors['name'] = ['Company name must be between 2 and 100 characters.']

        # Auto-add https:// to website URL if missing
        if website_url and not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url

        # Validate conditional: website OR presentation (200+ chars)
        if not website_url and (not presentation or len(presentation) < 200):
            errors['_conditional'] = ['Please provide either a website URL or a detailed company presentation (200+ characters).']

        # Validate website URL format if provided
        if website_url and len(website_url) > 255:
            errors['website_url'] = ['Website URL must be 255 characters or less.']

        # Validate presentation length if provided
        if presentation and len(presentation) > 2000:
            errors['presentation'] = ['Company presentation must be 2000 characters or less.']

        # Validate company size
        valid_sizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']
        if not company_size or company_size not in valid_sizes:
            errors['company_size'] = [f'Company size must be one of: {", ".join(valid_sizes)}']

        # Validate industry
        if not industry or len(industry) < 2 or len(industry) > 100:
            errors['industry'] = ['Industry must be between 2 and 100 characters.']

        # Validate location
        if not location or len(location) < 2 or len(location) > 100:
            errors['location'] = ['Location must be between 2 and 100 characters.']

        # Validate contact email
        if not contact_email:
            errors['contact_email'] = ['Contact email is required.']
        elif len(contact_email) > 255:
            errors['contact_email'] = ['Contact email must be 255 characters or less.']
        elif '@' not in contact_email or '.' not in contact_email:
            errors['contact_email'] = ['Please provide a valid email address.']

        # Validate brief description
        if not brief_description or len(brief_description) < 100 or len(brief_description) > 2000:
            errors['brief_description'] = ['Brief description must be between 100 and 2000 characters.']

        # Check for duplicate company name (case-insensitive) in approved/pending status
        if name:
            existing = Company.objects.filter(
                name__iexact=name,
                approval_status__in=['approved', 'pending_approval']
            ).exists()
            if existing:
                errors['name'] = ['A company with this name already exists or is pending approval.']

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Create the company with pending_approval status
        try:
            company = Company.objects.create(
                name=name,
                website=website_url,
                presentation=presentation,
                company_size=company_size,
                industry=industry,
                headquarters_city=location,
                contact_email=contact_email,
                brief_description=brief_description,
                approval_status='pending_approval',
                is_user_submitted=True,
                submitted_by=request.user,
                status='private',  # Default company status
                is_active=True
            )
        except Exception as e:
            import traceback
            print(f"ERROR creating company: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'error': f'Failed to create company: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'id': company.id,
            'status': 'pending_approval',
            'message': 'Company submitted successfully. It will be reviewed by our team.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending')
    def pending_companies(self, request):
        """
        Get all companies pending approval.

        GET /api/companies/pending/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to view pending companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 20)), 100)

        queryset = Company.objects.filter(
            approval_status='pending_approval'
        ).select_related('submitted_by').order_by('-created_at')

        # Pagination
        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        companies = queryset[start:end]

        data = []
        for company in companies:
            data.append({
                'id': company.id,
                'name': company.name,
                'website_url': company.website,
                'presentation': company.presentation,
                'company_size': company.company_size,
                'industry': company.industry,
                'location': company.headquarters_city,
                'contact_email': company.contact_email,
                'brief_description': company.brief_description,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'submitter': {
                    'id': company.submitted_by.id if company.submitted_by else None,
                    'username': company.submitted_by.username if company.submitted_by else 'Unknown',
                    'email': company.submitted_by.email if company.submitted_by else ''
                }
            })

        return Response({
            'companies': data,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='approve')
    def approve_company(self, request, pk=None):
        """
        Approve a pending company and trigger onboarding/scraping.

        PATCH /api/companies/{id}/approve/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to approve companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()

        if company.approval_status != 'pending_approval':
            return Response(
                {'error': 'This company is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        import asyncio
        from mcp_servers.company_scraper import scrape_company_website
        from core.models import ScrapingJob

        # Approve the company first
        company.approval_status = 'approved'
        company.reviewed_by = request.user
        company.reviewed_at = timezone.now()
        company.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at', 'updated_at'])

        # Trigger onboarding/scraping if website URL is provided
        if company.website:
            try:
                # Create scraping job
                job = ScrapingJob.objects.create(
                    company_name_input=company.name,
                    website_url=company.website,
                    status='running',
                    started_at=timezone.now(),
                    sections_to_process=['all'],
                    initiated_by=request.user,
                    company=company
                )

                # Run the scraper
                result = asyncio.run(scrape_company_website(company.website))
                data = result['data']
                errors = result['errors']

                # Update the existing company with scraped data
                updated_company = _save_scraped_company_data(data, company.website, update_existing=True, user=request.user)

                # Update job with success
                job.company = updated_company or company
                job.status = 'success'
                job.completed_at = timezone.now()
                job.data_extracted = data
                job.documents_found = len(data.get('documents', []))
                job.people_found = len(data.get('people', []))
                job.news_found = len(data.get('news', []))
                job.sections_completed = ['all']
                job.error_messages = errors
                job.save()

                # Document processing jobs are created by the scraper
                # The GPU Orchestrator will automatically pick them up and process on GPU
                # DO NOT process on CPU - it causes 100% CPU and is very slow
                processing_jobs = data.get('_processing_jobs_created', [])
                if processing_jobs:
                    # Jobs will be processed by GPU worker automatically
                    pass

                # CRITICAL: Trigger comprehensive news scraping via Celery task
                # scrape_company_website() has LIMITED news strategies
                # scrape_company_news_task uses crawl_news_releases() with ALL strategies
                # (NEWS-ENTRY, G2, WP-BLOCK, ELEMENTOR, UIKIT, ITEM, LINK, ASPX)
                from .tasks import scrape_company_news_task
                final_company = updated_company or company
                news_task = scrape_company_news_task.delay(final_company.id)

                return Response({
                    'success': True,
                    'message': f'{company.name} has been approved and onboarded successfully. Comprehensive news scraping triggered.',
                    'company_id': company.id,
                    'onboarding_completed': True,
                    'documents_found': len(data.get('documents', [])),
                    'people_found': len(data.get('people', [])),
                    'news_found': len(data.get('news', [])),
                    'news_scrape_task_id': news_task.id,
                })

            except Exception as e:
                # If scraping fails, still keep the company approved
                # but mark the scraping job as failed
                if 'job' in locals():
                    job.status = 'failed'
                    job.completed_at = timezone.now()
                    job.error_messages = [str(e)]
                    job.save()

                return Response({
                    'success': True,
                    'message': f'{company.name} has been approved, but onboarding failed.',
                    'company_id': company.id,
                    'onboarding_completed': False,
                    'onboarding_error': str(e)
                })

        # No website URL provided, just approve
        return Response({
            'success': True,
            'message': f'{company.name} has been approved and is now visible to all users.',
            'company_id': company.id,
            'onboarding_completed': False
        })

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='reject')
    def reject_company(self, request, pk=None):
        """
        Reject a pending company.

        PATCH /api/companies/{id}/reject/

        Request body (optional):
        {
            "reason": "Rejection reason here..."
        }

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to reject companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()

        if company.approval_status != 'pending_approval':
            return Response(
                {'error': 'This company is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone

        rejection_reason = request.data.get('reason', '')
        if rejection_reason and len(rejection_reason) > 500:
            return Response(
                {'error': 'Rejection reason must be 500 characters or less.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        company.approval_status = 'rejected'
        company.rejection_reason = rejection_reason
        company.reviewed_by = request.user
        company.reviewed_at = timezone.now()
        company.save(update_fields=['approval_status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'])

        return Response({
            'success': True,
            'message': f'{company.name} has been rejected.',
            'company_id': company.id
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete a company - only superusers can delete.

        DELETE /api/companies/{id}/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to delete companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()
        company_name = company.name

        # Soft delete by setting is_active=False
        company.is_active = False
        company.save(update_fields=['is_active', 'updated_at'])

        return Response({
            'success': True,
            'message': f'{company_name} has been deleted.'
        }, status=status.HTTP_200_OK)


# ============================================================================
# PROJECT VIEWSET
# ============================================================================

class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for projects"""
    queryset = Project.objects.all()

    def get_permissions(self):
        """Allow anyone to read, but only superusers can create/update/delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True)

        # Filter by company
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by commodity
        commodity = self.request.query_params.get('commodity')
        if commodity:
            queryset = queryset.filter(primary_commodity=commodity)

        return queryset.select_related('company').order_by('-is_flagship', 'name')


# ============================================================================
# OTHER VIEWSETS
# ============================================================================

class ResourceEstimateViewSet(viewsets.ModelViewSet):
    queryset = ResourceEstimate.objects.all()
    serializer_class = ResourceEstimateSerializer
    permission_classes = [AllowAny]


class FinancingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financings (private placements, etc.)

    - GET /api/financings/ - List all financings (public)
    - GET /api/financings/{id}/ - Get financing details (public)
    - POST /api/financings/ - Create financing (superuser or company rep)
    - PUT/PATCH /api/financings/{id}/ - Update financing (superuser or company rep)
    - DELETE /api/financings/{id}/ - Delete financing (superuser only)
    """
    serializer_class = FinancingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter financings by company if company query param is provided"""
        queryset = Financing.objects.select_related('company').all()
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset.order_by('-announced_date')

    def get_permissions(self):
        """Allow read for anyone, require auth for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        """Create a new financing - only superuser or company rep can create"""
        user = request.user
        company_id = request.data.get('company')

        if not company_id:
            return Response({'error': 'Company ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has permission (superuser, staff, or company rep)
        if not user.is_superuser and not user.is_staff:
            if not hasattr(user, 'company_id') or user.company_id != int(company_id):
                return Response(
                    {'error': 'You do not have permission to create financings for this company'},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update a financing - only superuser or company rep can update"""
        user = request.user
        financing = self.get_object()

        if not user.is_superuser and not user.is_staff:
            if not hasattr(user, 'company_id') or user.company_id != financing.company_id:
                return Response(
                    {'error': 'You do not have permission to update this financing'},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a financing - only superuser or authorized company rep can delete"""
        user = request.user
        financing = self.get_object()

        # Allow superusers and staff
        if user.is_superuser or user.is_staff:
            return super().destroy(request, *args, **kwargs)

        # Allow company representatives for their own company
        if hasattr(user, 'company_id') and user.company_id == financing.company_id:
            return super().destroy(request, *args, **kwargs)

        return Response(
            {'error': 'You do not have permission to delete this financing'},
            status=status.HTTP_403_FORBIDDEN
        )


# ============================================================================
# GUEST SPEAKER EVENT VIEWSETS
# ============================================================================

class SpeakerEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing speaker events

    Endpoints:
    - GET /api/events/ - List all events (with filters)
    - GET /api/events/{id}/ - Get event details
    - POST /api/events/ - Create new event (company admins only)
    - PUT/PATCH /api/events/{id}/ - Update event
    - DELETE /api/events/{id}/ - Delete event
    - POST /api/events/{id}/register/ - Register for event
    - POST /api/events/{id}/unregister/ - Unregister from event
    - POST /api/events/{id}/start/ - Start event (change status to live)
    - POST /api/events/{id}/end/ - End event
    - GET /api/events/upcoming/ - Get upcoming events
    """
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = SpeakerEvent.objects.select_related('company', 'created_by').prefetch_related('speakers__user')

        # Filter by company
        company_id = self.request.query_params.get('company', None)
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by format
        format_param = self.request.query_params.get('format', None)
        if format_param:
            queryset = queryset.filter(format=format_param)

        return queryset.order_by('-scheduled_start')

    def get_serializer_class(self):
        if self.action == 'list':
            return SpeakerEventListSerializer
        elif self.action == 'create':
            return SpeakerEventCreateSerializer
        return SpeakerEventDetailSerializer

    def perform_create(self, serializer):
        """Set the created_by field to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register current user for an event"""
        event = self.get_object()

        # Check if event is open for registration
        if event.status != 'scheduled':
            return Response(
                {'error': 'Event is not open for registration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already registered
        if event.registrations.filter(user=request.user, status='registered').exists():
            return Response(
                {'error': 'Already registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check capacity
        if event.max_participants and event.registered_count >= event.max_participants:
            return Response(
                {'error': 'Event is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has a cancelled registration and reactivate it
        existing_registration = event.registrations.filter(user=request.user).first()
        if existing_registration:
            existing_registration.status = 'registered'
            existing_registration.save()
            registration = existing_registration
        else:
            # Create new registration
            registration = EventRegistration.objects.create(
                event=event,
                user=request.user,
                status='registered'
            )

        # Update event registered count
        event.registered_count += 1
        event.save(update_fields=['registered_count'])

        return Response(
            {'message': 'Successfully registered for event'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def unregister(self, request, pk=None):
        """Unregister current user from an event"""
        event = self.get_object()

        try:
            registration = event.registrations.get(user=request.user, status='registered')
            registration.status = 'cancelled'
            registration.save()

            # Update event registered count
            event.registered_count = max(0, event.registered_count - 1)
            event.save(update_fields=['registered_count'])

            return Response({'message': 'Successfully unregistered from event'})
        except EventRegistration.DoesNotExist:
            return Response(
                {'error': 'Not registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        """Start an event (change status to live)"""
        event = self.get_object()

        # Check if user is authorized (event creator or company admin)
        if event.created_by != request.user:
            return Response(
                {'error': 'Not authorized to start this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        if event.status != 'scheduled':
            return Response(
                {'error': 'Event must be scheduled to start'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.status = 'live'
        event.actual_start = datetime.now()
        event.save(update_fields=['status', 'actual_start'])

        return Response({'message': 'Event started successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def end(self, request, pk=None):
        """End an event"""
        event = self.get_object()

        # Check if user is authorized
        if event.created_by != request.user:
            return Response(
                {'error': 'Not authorized to end this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        if event.status != 'live':
            return Response(
                {'error': 'Event must be live to end'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.status = 'ended'
        event.actual_end = datetime.now()
        event.save(update_fields=['status', 'actual_end'])

        return Response({'message': 'Event ended successfully'})

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events across all companies"""
        from django.utils import timezone

        # Get events scheduled for the next 90 days or events that are scheduled (even if in near past)
        now = timezone.now()
        upcoming_events = SpeakerEvent.objects.filter(
            status='scheduled'
        ).select_related('company', 'created_by').prefetch_related('speakers__user').order_by('scheduled_start')[:10]

        serializer = SpeakerEventListSerializer(upcoming_events, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def registrations(self, request, pk=None):
        """Get list of registered users for an event (staff/admin only)"""
        event = self.get_object()

        # Check if user is staff, admin, or event creator
        if not (request.user.is_staff or request.user.is_superuser or event.created_by == request.user):
            return Response(
                {'error': 'Not authorized to view registrations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all registrations for this event
        registrations = event.registrations.filter(
            status__in=['registered', 'attended']
        ).select_related('user').order_by('-registered_at')

        # Serialize registration data
        registration_data = []
        for reg in registrations:
            registration_data.append({
                'id': reg.id,
                'user': {
                    'id': reg.user.id,
                    'username': reg.user.username,
                    'email': reg.user.email,
                    'full_name': reg.user.get_full_name() if hasattr(reg.user, 'get_full_name') else f"{reg.user.first_name} {reg.user.last_name}".strip() or reg.user.username,
                },
                'status': reg.status,
                'registered_at': reg.registered_at,
                'joined_at': reg.joined_at,
                'left_at': reg.left_at,
            })

        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'total_registrations': len(registration_data),
            'max_participants': event.max_participants,
            'registrations': registration_data
        })


class EventQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event questions

    Endpoints:
    - GET /api/event-questions/?event={event_id} - List questions for an event
    - POST /api/event-questions/ - Submit a question
    - PATCH /api/event-questions/{id}/ - Update question (moderate/answer)
    - POST /api/event-questions/{id}/upvote/ - Upvote a question
    """
    serializer_class = EventQuestionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = EventQuestion.objects.select_related('user', 'answered_by')

        # Filter by event
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.order_by('-upvotes', '-created_at')

    def perform_create(self, serializer):
        """Set the user field to current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote a question"""
        question = self.get_object()
        question.upvotes += 1
        question.save(update_fields=['upvotes'])

        # Update event questions count
        event = question.event
        event.questions_count = event.questions.count()
        event.save(update_fields=['questions_count'])

        return Response({'message': 'Question upvoted', 'upvotes': question.upvotes})


class EventReactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event reactions

    Endpoints:
    - POST /api/event-reactions/ - Send a reaction
    - GET /api/event-reactions/?event={event_id} - Get reactions for an event
    """
    serializer_class = EventReactionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = EventReaction.objects.select_related('user')

        # Filter by event
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        return queryset.order_by('-timestamp')

    def perform_create(self, serializer):
        """Set the user field to current user"""
        serializer.save(user=self.request.user)


# ============================================================================
# USER AUTHENTICATION API
# ============================================================================

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user account
    POST /api/auth/register/
    Body: {
        "username": "string",
        "email": "string",
        "password": "string",
        "full_name": "string",
        "user_type": "investor|mining_company|prospector|student" (required)
    }
    Returns: {
        "user": {...},
        "access": "token",
        "refresh": "token"
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('full_name', '')
    user_type = request.data.get('user_type', '')

    # Validation
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email, and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate user_type is required and valid
    valid_user_types = ['investor', 'mining_company', 'prospector', 'student']
    if not user_type:
        return Response(
            {'error': 'User type is required. Please select: Investor, Mining Company, Prospector, or Student'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if user_type not in valid_user_types:
        return Response(
            {'error': f'Invalid user type. Must be one of: {", ".join(valid_user_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type
        )

        # Set full name (split into first and last name)
        if full_name:
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Get full name
        user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user_full_name,
                'user_type': user.user_type,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login and get JWT tokens
    POST /api/auth/login/
    Body: {
        "username": "string",
        "password": "string"
    }
    Returns: {
        "user": {...},
        "access": "token",
        "refresh": "token"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    # Get full name
    user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user_full_name,
            'user_type': user.user_type,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user info
    GET /api/auth/me/
    Headers: Authorization: Bearer <access_token>
    Returns: {
        "id": int,
        "username": "string",
        "email": "string",
        "full_name": "string",
        "user_type": "string",
        "company_id": int | null,
        "company_name": "string" | null
    }
    """
    user = request.user

    # Get full name
    user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user_full_name,
        'user_type': user.user_type,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'company_id': user.company_id,
        'company_name': user.company.name if user.company else None,
    }, status=status.HTTP_200_OK)


# ============================================================================
# FINANCIAL HUB API
# ============================================================================

from .models import (
    EducationalModule, ModuleCompletion, AccreditedInvestorQualification,
    SubscriptionAgreement, InvestmentTransaction, FinancingAggregate,
    PaymentInstruction, DRSDocument
)
from .serializers import (
    EducationalModuleSerializer, ModuleCompletionSerializer,
    AccreditedInvestorQualificationSerializer, SubscriptionAgreementSerializer,
    SubscriptionAgreementDetailSerializer, InvestmentTransactionSerializer,
    FinancingAggregateSerializer, PaymentInstructionSerializer, DRSDocumentSerializer
)
from django.utils import timezone


class EducationalModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Educational Modules

    Endpoints:
    - GET /api/education/modules/ - List all published modules
    - GET /api/education/modules/{id}/ - Get module details
    - POST /api/education/modules/{id}/complete/ - Mark module as complete
    """
    serializer_class = EducationalModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EducationalModule.objects.filter(is_published=True)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a module as completed"""
        module = self.get_object()
        user = request.user

        # Get or create completion record
        completion, created = ModuleCompletion.objects.get_or_create(
            user=user,
            module=module,
            defaults={
                'time_spent_seconds': request.data.get('time_spent_seconds', 0),
                'passed': request.data.get('passed', True),
            }
        )

        if not created:
            # Update existing completion
            completion.time_spent_seconds += request.data.get('time_spent_seconds', 0)
            completion.passed = request.data.get('passed', True)

        # Mark as completed
        if not completion.completed_at:
            completion.completed_at = timezone.now()

        completion.save()

        return Response({
            'message': 'Module marked as complete',
            'completion': ModuleCompletionSerializer(completion).data
        }, status=status.HTTP_200_OK)


class ModuleCompletionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Module Completions

    Endpoints:
    - GET /api/education/completions/ - List user's completions
    """
    serializer_class = ModuleCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ModuleCompletion.objects.filter(user=self.request.user).select_related('module')


class AccreditedInvestorQualificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Accredited Investor Qualifications

    Endpoints:
    - GET /api/qualifications/ - List user's qualifications
    - POST /api/qualifications/ - Submit qualification
    - GET /api/qualifications/status/ - Get current qualification status
    """
    serializer_class = AccreditedInvestorQualificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AccreditedInvestorQualification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get user's current qualification status"""
        qualification = AccreditedInvestorQualification.objects.filter(
            user=request.user
        ).order_by('-created_at').first()

        if qualification:
            return Response(
                AccreditedInvestorQualificationSerializer(qualification).data,
                status=status.HTTP_200_OK
            )

        return Response({
            'status': 'pending',
            'criteria_met': None,
            'qualified_at': None
        }, status=status.HTTP_200_OK)


class SubscriptionAgreementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subscription Agreements

    Endpoints:
    - GET /api/agreements/ - List user's agreements
    - GET /api/agreements/{id}/ - Get agreement details
    - POST /api/agreements/ - Create new agreement
    - PATCH /api/agreements/{id}/ - Update agreement
    - POST /api/agreements/{id}/sign/ - Sign agreement
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionAgreementDetailSerializer
        return SubscriptionAgreementSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = SubscriptionAgreement.objects.select_related(
            'investor', 'financing', 'company'
        )

        # If user is investor, show their agreements
        if user.user_type == 'investor':
            queryset = queryset.filter(investor=user)
        # If user is company, show their company's agreements
        elif user.user_type == 'company' and user.company:
            queryset = queryset.filter(company=user.company)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Sign a subscription agreement"""
        agreement = self.get_object()

        # Verify user is the investor
        if agreement.investor != request.user:
            return Response(
                {'error': 'Only the investor can sign this agreement'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already signed
        if agreement.investor_signed_at:
            return Response(
                {'error': 'Agreement already signed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sign the agreement
        agreement.investor_signed_at = timezone.now()
        agreement.investor_ip_address = request.META.get('REMOTE_ADDR')
        agreement.status = 'signed'
        agreement.save(update_fields=['investor_signed_at', 'investor_ip_address', 'status'])

        return Response({
            'message': 'Agreement signed successfully',
            'agreement': SubscriptionAgreementSerializer(agreement).data
        }, status=status.HTTP_200_OK)


class InvestmentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Investment Transactions

    Endpoints:
    - GET /api/investments/transactions/ - List user's transactions
    - GET /api/investments/transactions/{id}/ - Get transaction details
    """
    serializer_class = InvestmentTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InvestmentTransaction.objects.filter(
            user=self.request.user
        ).select_related('subscription_agreement', 'financing', 'user')


class FinancingAggregateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Financing Aggregates

    Endpoints:
    - GET /api/investments/aggregates/ - List financing aggregates
    - GET /api/investments/aggregates/{id}/ - Get aggregate details
    """
    serializer_class = FinancingAggregateSerializer
    permission_classes = [IsAuthenticated]
    queryset = FinancingAggregate.objects.select_related('financing')


class PaymentInstructionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Payment Instructions

    Endpoints:
    - GET /api/investments/payment-instructions/ - List user's payment instructions
    - GET /api/investments/payment-instructions/{id}/ - Get payment instruction details
    """
    serializer_class = PaymentInstructionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentInstruction.objects.filter(
            subscription_agreement__investor=self.request.user
        ).select_related('subscription_agreement', 'company')


class DRSDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for DRS Documents

    Endpoints:
    - GET /api/drs/documents/ - List user's DRS documents
    - GET /api/drs/documents/{id}/ - Get document details
    """
    serializer_class = DRSDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DRSDocument.objects.filter(
            user=self.request.user
        ).select_related('subscription_agreement', 'company', 'user')


# ============================================================================
# PROSPECTOR PROPERTY EXCHANGE
# ============================================================================

class ProspectorProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prospector Profiles

    Endpoints:
    - GET /api/properties/prospectors/ - List all prospectors
    - GET /api/properties/prospectors/{id}/ - Get prospector profile
    - POST /api/properties/prospectors/ - Create prospector profile (authenticated)
    - PUT /api/properties/prospectors/{id}/ - Update profile (owner only)
    - GET /api/properties/prospectors/me/ - Get current user's profile
    """
    serializer_class = ProspectorProfileSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'agreement_text']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = ProspectorProfile.objects.select_related('user').prefetch_related('listings')

        # Filter by verified status
        is_verified = self.request.query_params.get('verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(display_name__icontains=search) |
                Q(company_name__icontains=search)
            )

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow owners to update their profile
        if serializer.instance.user != self.request.user:
            raise PermissionError("You can only update your own profile")
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get the current user's prospector profile"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response(
                {'detail': 'Prospector profile not found. Create one to list properties.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def agreement_text(self, request):
        """Get the current commission agreement text"""
        return Response({
            'version': ProspectorCommissionAgreement.AGREEMENT_VERSION,
            'commission_rate': str(ProspectorCommissionAgreement.COMMISSION_RATE),
            'agreement_text': ProspectorCommissionAgreement.get_agreement_text()
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept_agreement(self, request):
        """Accept the commission agreement"""
        from django.utils import timezone

        # Get or create prospector profile - auto-create if doesn't exist
        # Use get_full_name() method from AbstractUser, fallback to username
        display_name = request.user.get_full_name() or request.user.username
        profile, created = ProspectorProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'display_name': display_name,
            }
        )

        # Check if already accepted
        if profile.commission_agreement_accepted:
            return Response(
                {'detail': 'You have already accepted the commission agreement.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input
        serializer = ProspectorCommissionAgreementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')

        # Create agreement record
        agreement = ProspectorCommissionAgreement.objects.create(
            prospector=profile,
            full_legal_name=serializer.validated_data['full_legal_name'],
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            agreement_text=ProspectorCommissionAgreement.get_agreement_text()
        )

        # Update profile
        profile.commission_agreement_accepted = True
        profile.commission_agreement_date = timezone.now()
        profile.commission_agreement_ip = ip_address
        profile.save()

        return Response({
            'detail': 'Commission agreement accepted successfully.',
            'agreement_id': agreement.id,
            'accepted_at': agreement.accepted_at,
            'can_list_properties': True
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_agreements(self, request):
        """Get the current user's commission agreements"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            agreements = profile.commission_agreements.all()
            serializer = ProspectorCommissionAgreementSerializer(agreements, many=True)
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response([])


class PropertyListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Listings

    Endpoints:
    - GET /api/properties/listings/ - List all active listings (public)
    - GET /api/properties/listings/{slug}/ - Get listing details (public)
    - POST /api/properties/listings/ - Create listing (prospector only)
    - PUT /api/properties/listings/{slug}/ - Update listing (owner only)
    - DELETE /api/properties/listings/{slug}/ - Delete listing (owner only)
    - GET /api/properties/listings/my-listings/ - Get current user's listings
    - GET /api/properties/listings/choices/ - Get all dropdown choices
    - POST /api/properties/listings/{slug}/view/ - Record a view
    """
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices', 'record_view']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyListingCreateSerializer
        return PropertyListingDetailSerializer

    def get_queryset(self):
        queryset = PropertyListing.objects.select_related('prospector', 'prospector__user').prefetch_related('media')

        # For list view, only show active listings to non-owners
        if self.action == 'list':
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(status='active')
            elif not self.request.user.is_staff:
                queryset = queryset.filter(
                    Q(status='active') | Q(prospector__user=self.request.user)
                )

        # Apply filters
        filters = {}

        # Mineral type filter
        mineral = self.request.query_params.get('mineral')
        if mineral:
            queryset = queryset.filter(
                Q(primary_mineral=mineral) | Q(secondary_minerals__contains=[mineral])
            )

        # Country filter
        country = self.request.query_params.get('country')
        if country:
            filters['country'] = country

        # Province/state filter
        province = self.request.query_params.get('province')
        if province:
            filters['province_state__icontains'] = province

        # Property type filter
        property_type = self.request.query_params.get('property_type')
        if property_type:
            filters['property_type'] = property_type

        # Exploration stage filter
        stage = self.request.query_params.get('stage')
        if stage:
            filters['exploration_stage'] = stage

        # Price range filters
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(asking_price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(asking_price__lte=max_price)

        # Size range filters (hectares)
        min_size = self.request.query_params.get('min_size')
        if min_size:
            queryset = queryset.filter(total_hectares__gte=min_size)

        max_size = self.request.query_params.get('max_size')
        if max_size:
            queryset = queryset.filter(total_hectares__lte=max_size)

        # Open to offers filter
        open_to_offers = self.request.query_params.get('open_to_offers')
        if open_to_offers is not None:
            filters['open_to_offers'] = open_to_offers.lower() == 'true'

        # Has NI 43-101 report
        has_report = self.request.query_params.get('has_43_101')
        if has_report is not None:
            filters['has_43_101_report'] = has_report.lower() == 'true'

        # Search in title and description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(location_description__icontains=search)
            )

        # Filter for user's own listings
        my_listings = self.request.query_params.get('my_listings')
        if my_listings and my_listings.lower() == 'true' and self.request.user.is_authenticated:
            try:
                profile = ProspectorProfile.objects.get(user=self.request.user)
                queryset = queryset.filter(prospector=profile)
            except ProspectorProfile.DoesNotExist:
                queryset = queryset.none()

        # Filter by prospector ID
        prospector_id = self.request.query_params.get('prospector')
        if prospector_id:
            queryset = queryset.filter(prospector_id=prospector_id)

        queryset = queryset.filter(**filters)

        # Sorting
        sort = self.request.query_params.get('sort', '-created_at')
        valid_sorts = ['created_at', '-created_at', 'asking_price', '-asking_price',
                      'total_hectares', '-total_hectares', 'views_count', '-views_count']
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def perform_create(self, serializer):
        # Ensure user has a prospector profile
        try:
            profile = ProspectorProfile.objects.get(user=self.request.user)
        except ProspectorProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must create a prospector profile before listing properties"
            )

        # Check if commission agreement has been accepted
        if not profile.commission_agreement_accepted:
            raise serializers.ValidationError(
                "You must accept the 5% commission agreement before listing properties. "
                "This ensures free listings while supporting the platform through successful transactions."
            )

        serializer.save(prospector=profile)

    def perform_update(self, serializer):
        # Only allow owners to update their listings
        if serializer.instance.prospector.user != self.request.user:
            raise PermissionError("You can only update your own listings")
        serializer.save()

    def perform_destroy(self, instance):
        # Allow superusers to delete any listing, owners can only delete their own
        if not self.request.user.is_superuser and instance.prospector.user != self.request.user:
            raise PermissionError("You can only delete your own listings")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """Get the current user's property listings"""
        try:
            profile = ProspectorProfile.objects.get(user=request.user)
            listings = PropertyListing.objects.filter(prospector=profile).order_by('-created_at')
            serializer = PropertyListingListSerializer(listings, many=True, context={'request': request})
            return Response(serializer.data)
        except ProspectorProfile.DoesNotExist:
            return Response([])

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get all dropdown choice options for the listing form"""
        serializer = PropertyChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def record_view(self, request, slug=None):
        """Record a view for a listing"""
        listing = self.get_object()
        listing.views_count += 1
        listing.save(update_fields=['views_count'])
        return Response({'views_count': listing.views_count})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get all listings pending review (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to view pending listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listings = PropertyListing.objects.filter(
            status='pending_review'
        ).select_related('prospector', 'prospector__user').order_by('-created_at')

        serializer = PropertyListingListSerializer(listings, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, slug=None):
        """Approve a listing (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to approve listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listing = self.get_object()
        if listing.status != 'pending_review':
            return Response(
                {'detail': f'Listing is not pending review (current status: {listing.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        listing.status = 'active'
        listing.published_at = timezone.now()
        listing.save(update_fields=['status', 'published_at'])

        serializer = PropertyListingDetailSerializer(listing, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, slug=None):
        """Reject a listing (admin/superuser only)"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to reject listings'},
                status=status.HTTP_403_FORBIDDEN
            )

        listing = self.get_object()
        if listing.status not in ['pending_review', 'active']:
            return Response(
                {'detail': f'Listing cannot be rejected (current status: {listing.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '')
        listing.status = 'rejected'
        listing.save(update_fields=['status'])

        # TODO: Send email notification to prospector with rejection reason

        return Response({
            'detail': 'Listing has been rejected',
            'slug': listing.slug,
            'reason': reason
        })


class PropertyMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Media (images, documents, videos)

    Endpoints:
    - POST /api/properties/media/ - Upload media to a listing
    - POST /api/properties/media/upload/ - Upload file and create media record
    - DELETE /api/properties/media/{id}/ - Delete media
    - PATCH /api/properties/media/{id}/ - Update media (e.g., set as primary)
    """
    serializer_class = PropertyMediaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only manage media for their own listings
        return PropertyMedia.objects.filter(
            listing__prospector__user=self.request.user
        ).select_related('listing')

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')
        if listing.prospector.user != self.request.user:
            raise PermissionError("You can only add media to your own listings")
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a file and create a media record
        POST /api/properties/media/upload/
        """
        import os
        import uuid
        from django.core.files.storage import default_storage
        from django.conf import settings

        file = request.FILES.get('file')
        listing_id = request.data.get('listing')
        category = request.data.get('category')
        title = request.data.get('title')
        description = request.data.get('description', '')
        media_type = request.data.get('media_type', 'document')

        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not listing_id or not category or not title:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate listing ownership
        try:
            listing = PropertyListing.objects.get(id=listing_id)
            if listing.prospector.user != request.user:
                return Response({'error': 'You can only upload to your own listings'}, status=status.HTTP_403_FORBIDDEN)
        except PropertyListing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate file size (50MB max)
        if file.size > 50 * 1024 * 1024:
            return Response({'error': 'File size must be less than 50MB'}, status=status.HTTP_400_BAD_REQUEST)

        # Get file extension and generate unique filename
        ext = os.path.splitext(file.name)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # Determine storage path based on media type
        storage_path = f"properties/{listing_id}/{media_type}s/{unique_filename}"

        # Save file
        try:
            saved_path = default_storage.save(storage_path, file)
            file_url = default_storage.url(saved_path)

            # If using local storage, prepend the domain
            if not file_url.startswith('http'):
                file_url = f"{settings.MEDIA_URL}{saved_path}"

            # Create media record
            media = PropertyMedia.objects.create(
                listing=listing,
                media_type=media_type,
                category=category,
                title=title,
                description=description,
                file_url=file_url,
                file_size_mb=round(file.size / (1024 * 1024), 2),
                file_format=ext.replace('.', ''),
                uploaded_by=request.user,
            )

            return Response(PropertyMediaSerializer(media).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Failed to save file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        # Only allow owner to delete
        if instance.listing.prospector.user != self.request.user:
            raise PermissionError("You can only delete media from your own listings")

        # Delete the file from storage
        from django.core.files.storage import default_storage
        try:
            # Extract path from URL if needed
            file_path = instance.file_url
            if file_path.startswith('/media/'):
                file_path = file_path[7:]  # Remove /media/ prefix
            default_storage.delete(file_path)
        except Exception:
            pass  # File might not exist, continue with deletion

        instance.delete()


class PropertyInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Inquiries

    Endpoints:
    - GET /api/properties/inquiries/ - List inquiries (prospector sees received, others see sent)
    - POST /api/properties/inquiries/ - Send an inquiry
    - GET /api/properties/inquiries/{id}/ - Get inquiry details
    - PATCH /api/properties/inquiries/{id}/ - Update inquiry status (owner only)
    """
    serializer_class = PropertyInquirySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import PropertyInquiryCreateSerializer
        if self.action == 'create':
            return PropertyInquiryCreateSerializer
        return PropertyInquirySerializer

    def get_queryset(self):
        user = self.request.user

        # Check if user is a prospector
        try:
            profile = ProspectorProfile.objects.get(user=user)
            # Prospectors see inquiries received on their listings
            received = PropertyInquiry.objects.filter(listing__prospector=profile)
        except ProspectorProfile.DoesNotExist:
            received = PropertyInquiry.objects.none()

        # All users see inquiries they've sent
        sent = PropertyInquiry.objects.filter(inquirer=user)

        # Combine and return
        return (received | sent).distinct().select_related(
            'listing', 'inquirer', 'listing__prospector'
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Create a new inquiry"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            listing = serializer.validated_data.get('listing')

            # Can't inquire on own listing
            if listing.prospector.user == request.user:
                return Response(
                    {'error': 'You cannot inquire on your own listing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update listing inquiry count
            listing.inquiries_count += 1
            listing.save(update_fields=['inquiries_count'])

            # Save the inquiry
            inquiry = serializer.save(inquirer=request.user)

            # Return the full inquiry data
            response_serializer = PropertyInquirySerializer(inquiry)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating inquiry: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to create inquiry: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        # Only listing owner can update inquiry status
        if instance.listing.prospector.user != self.request.user:
            raise PermissionError("Only the listing owner can update inquiry status")
        serializer.save()

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        Respond to an inquiry (prospector only)
        POST /api/properties/inquiries/{id}/respond/
        """
        from .serializers import PropertyInquiryResponseSerializer
        from django.utils import timezone

        inquiry = self.get_object()

        # Only listing owner can respond
        if inquiry.listing.prospector.user != request.user:
            return Response(
                {'error': 'Only the listing owner can respond to inquiries'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PropertyInquiryResponseSerializer(data=request.data)
        if serializer.is_valid():
            inquiry.response = serializer.validated_data['response']
            inquiry.status = 'responded'
            inquiry.responded_at = timezone.now()
            inquiry.save()

            return Response(PropertyInquirySerializer(inquiry).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark inquiry as read (prospector only)
        POST /api/properties/inquiries/{id}/mark_read/
        """
        inquiry = self.get_object()

        # Only listing owner can mark as read
        if inquiry.listing.prospector.user != request.user:
            return Response(
                {'error': 'Only the listing owner can mark inquiries as read'},
                status=status.HTTP_403_FORBIDDEN
            )

        if inquiry.status == 'new':
            inquiry.status = 'read'
            inquiry.save()

        return Response(PropertyInquirySerializer(inquiry).data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for an inquiry conversation
        GET /api/properties/inquiries/{id}/messages/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to view this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all messages for this inquiry
        messages = inquiry.messages.select_related('sender').order_by('created_at')

        # Mark messages from the other party as read
        messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        serializer = InquiryMessageSerializer(messages, many=True)
        return Response({
            'inquiry_id': inquiry.id,
            'messages': serializer.data,
            'total_count': messages.count()
        })

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a new message in an inquiry conversation
        POST /api/properties/inquiries/{id}/send_message/
        Body: { "message": "Your message here" }
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to send messages in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InquiryMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Create the message
            message = InquiryMessage.objects.create(
                inquiry=inquiry,
                sender=user,
                message=serializer.validated_data['message']
            )

            # Update inquiry status if needed
            if inquiry.status == 'new':
                inquiry.status = 'read'
                inquiry.save(update_fields=['status'])

            return Response(
                InquiryMessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def conversation(self, request, pk=None):
        """
        Get full inquiry details with conversation thread
        GET /api/properties/inquiries/{id}/conversation/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized (either inquirer or listing owner)
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to view this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark messages from the other party as read
        inquiry.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        serializer = PropertyInquiryWithMessagesSerializer(inquiry, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_messages_read(self, request, pk=None):
        """
        Mark all messages in a conversation as read for the current user
        POST /api/properties/inquiries/{id}/mark_messages_read/
        """
        inquiry = self.get_object()
        user = request.user

        # Check if user is authorized
        is_inquirer = inquiry.inquirer == user
        is_prospector = inquiry.listing.prospector.user == user

        if not is_inquirer and not is_prospector:
            return Response(
                {'error': 'You are not authorized to access this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark all messages from the other party as read
        updated = inquiry.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        return Response({
            'marked_read': updated,
            'message': f'{updated} messages marked as read'
        })


class PropertyWatchlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property Watchlist

    Endpoints:
    - GET /api/properties/watchlist/ - List user's watchlisted properties
    - POST /api/properties/watchlist/ - Add to watchlist
    - DELETE /api/properties/watchlist/{id}/ - Remove from watchlist
    - POST /api/properties/watchlist/toggle/ - Toggle watchlist status for a listing
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'toggle']:
            from .serializers import PropertyWatchlistCreateSerializer
            return PropertyWatchlistCreateSerializer
        return PropertyWatchlistSerializer

    def get_queryset(self):
        return PropertyWatchlist.objects.filter(
            user=self.request.user
        ).select_related('listing', 'listing__prospector').prefetch_related('listing__media')

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')

        # Check if already watchlisted
        if PropertyWatchlist.objects.filter(user=self.request.user, listing=listing).exists():
            raise serializers.ValidationError("This property is already in your watchlist")

        # Update listing watchlist count
        listing.watchlist_count += 1
        listing.save(update_fields=['watchlist_count'])

        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # Update listing watchlist count
        instance.listing.watchlist_count = max(0, instance.listing.watchlist_count - 1)
        instance.listing.save(update_fields=['watchlist_count'])
        instance.delete()

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle watchlist status for a listing"""
        listing_id = request.data.get('listing')
        if not listing_id:
            return Response(
                {'error': 'listing is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            listing = PropertyListing.objects.get(id=listing_id)
        except PropertyListing.DoesNotExist:
            return Response(
                {'error': 'Listing not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already watchlisted
        watchlist_item = PropertyWatchlist.objects.filter(
            user=request.user, listing=listing
        ).first()

        if watchlist_item:
            # Remove from watchlist
            listing.watchlist_count = max(0, listing.watchlist_count - 1)
            listing.save(update_fields=['watchlist_count'])
            watchlist_item.delete()
            return Response({
                'is_watchlisted': False,
                'watchlist_count': listing.watchlist_count,
                'message': 'Removed from watchlist'
            })
        else:
            # Add to watchlist
            listing.watchlist_count += 1
            listing.save(update_fields=['watchlist_count'])
            PropertyWatchlist.objects.create(user=request.user, listing=listing)
            return Response({
                'is_watchlisted': True,
                'watchlist_count': listing.watchlist_count,
                'message': 'Added to watchlist'
            })


class SavedPropertySearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Saved Property Searches

    Endpoints:
    - GET /api/properties/saved-searches/ - List user's saved searches
    - POST /api/properties/saved-searches/ - Save a search
    - DELETE /api/properties/saved-searches/{id}/ - Delete saved search
    - PATCH /api/properties/saved-searches/{id}/ - Update alert settings
    """
    serializer_class = SavedPropertySearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedPropertySearch.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ============================================================================
# HOMEPAGE HERO SECTION CARDS API
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def hero_section_data(request):
    """
    Get data for the three hero section cards on the homepage.

    GET /api/hero-section/

    Returns:
    - upcoming_events: Speaker events within the next 7 days
    - active_financings: Companies with active financing rounds
    - featured_property: The currently featured property listing
    """
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    seven_days_from_now = now + timedelta(days=7)
    one_hour_ago = now - timedelta(hours=1)

    # Card 1: Upcoming Speaking Events (next 7 days)
    # Show events scheduled within 7 days, remove events 1 hour after start
    upcoming_events = SpeakerEvent.objects.filter(
        Q(status='scheduled') | Q(status='live'),
        scheduled_start__lte=seven_days_from_now,
        scheduled_start__gte=one_hour_ago
    ).select_related('company').prefetch_related('speakers__user').order_by('scheduled_start')[:5]

    events_data = []
    for event in upcoming_events:
        # Determine if event is live or upcoming
        is_live = event.status == 'live' or (
            event.scheduled_start <= now <= event.scheduled_end if event.scheduled_end else False
        )
        events_data.append({
            'id': event.id,
            'title': event.title,
            'company_id': event.company.id,
            'company_name': event.company.name,
            'company_ticker': event.company.ticker_symbol,
            'scheduled_start': event.scheduled_start.isoformat(),
            'scheduled_end': event.scheduled_end.isoformat() if event.scheduled_end else None,
            'status': 'live' if is_live else 'upcoming',
            'format': event.format,
            'registered_count': event.registrations.count(),
        })

    # Card 2: Active Financing Opportunities
    active_financings = Financing.objects.filter(
        status__in=['announced', 'closing']
    ).select_related('company').order_by('-announced_date')[:5]

    financings_data = []
    for financing in active_financings:
        financings_data.append({
            'id': financing.id,
            'company_id': financing.company.id,
            'company_name': financing.company.name,
            'company_ticker': financing.company.ticker_symbol,
            'financing_type': financing.financing_type,
            'financing_type_display': financing.get_financing_type_display(),
            'amount_raised_usd': float(financing.amount_raised_usd) if financing.amount_raised_usd else None,
            'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            'status': financing.status,
        })

    # Card 3: Featured Property Listing
    featured_property = None
    config = FeaturedPropertyConfig.get_current_featured()

    # Check if we need to auto-rotate (it's past the next rotation date)
    if config.next_auto_rotation and now >= config.next_auto_rotation and not config.is_manual_selection:
        config = FeaturedPropertyConfig.rotate_featured_property()

    # If no property is set but there are active listings, pick one
    if not config.listing:
        active_listings = PropertyListing.objects.filter(status='active')
        if active_listings.exists():
            from random import choice
            config.listing = choice(list(active_listings))
            # Set next rotation to next Monday
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = (now + timedelta(days=days_until_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            config.next_auto_rotation = next_monday
            config.save()

    if config.listing:
        listing = config.listing
        # Get primary image
        primary_image = listing.media.filter(media_type='image', is_primary=True).first()
        if not primary_image:
            primary_image = listing.media.filter(media_type='image').first()

        featured_property = {
            'id': listing.id,
            'slug': listing.slug,
            'title': listing.title,
            'summary': listing.summary,
            'location': f"{listing.nearest_town}, {listing.province_state}" if listing.nearest_town else listing.province_state,
            'country': listing.get_country_display(),
            'primary_mineral': listing.get_primary_mineral_display(),
            'total_hectares': float(listing.total_hectares) if listing.total_hectares else None,
            'asking_price': float(listing.asking_price) if listing.asking_price else None,
            'price_currency': listing.price_currency,
            'listing_type': listing.get_listing_type_display(),
            'exploration_stage': listing.get_exploration_stage_display(),
            'primary_image_url': primary_image.file_url if primary_image else None,
            'next_rotation': config.next_auto_rotation.isoformat() if config.next_auto_rotation else None,
            'is_manual_selection': config.is_manual_selection,
        }

    return Response({
        'upcoming_events': events_data,
        'active_financings': financings_data,
        'featured_property': featured_property,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_featured_property(request):
    """
    Set a specific property as featured (superuser only).

    POST /api/hero-section/set-featured/
    Body: { "listing_id": 123 }
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can set featured properties'},
            status=status.HTTP_403_FORBIDDEN
        )

    listing_id = request.data.get('listing_id')
    if not listing_id:
        return Response(
            {'error': 'listing_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        listing = PropertyListing.objects.get(id=listing_id, status='active')
    except PropertyListing.DoesNotExist:
        return Response(
            {'error': 'Property listing not found or not active'},
            status=status.HTTP_404_NOT_FOUND
        )

    from django.utils import timezone
    from datetime import timedelta

    config = FeaturedPropertyConfig.get_current_featured()
    config.listing = listing
    config.is_manual_selection = True
    config.selected_by = request.user
    # Next auto-rotation is still next Monday, but won't trigger since is_manual_selection=True
    now = timezone.now()
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    config.next_auto_rotation = next_monday
    config.save()

    return Response({
        'message': f'Featured property set to: {listing.title}',
        'listing_id': listing.id,
        'listing_title': listing.title,
        'next_auto_rotation': config.next_auto_rotation.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_featured_property(request):
    """
    Reset featured property to auto-rotation mode (superuser only).

    POST /api/hero-section/reset-featured/
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can reset featured properties'},
            status=status.HTTP_403_FORBIDDEN
        )

    config = FeaturedPropertyConfig.rotate_featured_property()

    return Response({
        'message': 'Featured property reset to auto-rotation',
        'listing_id': config.listing.id if config.listing else None,
        'listing_title': config.listing.title if config.listing else None,
        'next_auto_rotation': config.next_auto_rotation.isoformat() if config.next_auto_rotation else None,
    })


# ============================================================================
# NEWS ARTICLES API
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def news_articles_list(request):
    """
    Get list of recent news articles.

    GET /api/news/articles/

    Query params:
    - limit: Number of articles to return (default 10, max 50)
    - offset: Pagination offset (default 0)
    - days: Only show articles from last N days (default 7)
    - source: Filter by source ID
    """
    from django.utils import timezone

    limit = min(int(request.query_params.get('limit', 10)), 50)
    offset = int(request.query_params.get('offset', 0))
    days = int(request.query_params.get('days', 7))
    source_id = request.query_params.get('source')

    # Filter to visible articles from last N days (or with no published date - treated as recent)
    cutoff_date = timezone.now() - timedelta(days=days)
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    queryset = NewsArticle.objects.filter(
        Q(is_visible=True) & (Q(published_at__gte=cutoff_date) | Q(published_at__isnull=True))
    ).select_related('source').order_by(Coalesce('published_at', 'scraped_at').desc())

    if source_id:
        queryset = queryset.filter(source_id=source_id)

    total_count = queryset.count()
    articles = queryset[offset:offset + limit]

    return Response({
        'articles': [
            {
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'source_name': article.source.name,
                'source_id': article.source_id,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'author': article.author,
                'summary': article.summary,
                'image_url': article.image_url,
            }
            for article in articles
        ],
        'total': total_count,
        'limit': limit,
        'offset': offset,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def news_sources_list(request):
    """
    Get list of news sources (public - active sources only).

    GET /api/news/sources/
    """
    sources = NewsSource.objects.filter(is_active=True)

    return Response({
        'sources': [
            {
                'id': source.id,
                'name': source.name,
                'url': source.url,
                'article_count': source.articles.filter(is_visible=True).count(),
            }
            for source in sources
        ]
    })


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def news_sources_admin(request, source_id=None):
    """
    Admin endpoint for managing news sources (superuser only).

    GET /api/news/sources/admin/ - List all sources with admin details
    POST /api/news/sources/admin/ - Add new source
    DELETE /api/news/sources/admin/<source_id>/ - Delete source
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can manage news sources'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        sources = NewsSource.objects.all()
        return Response({
            'sources': [
                {
                    'id': source.id,
                    'name': source.name,
                    'url': source.url,
                    'is_active': source.is_active,
                    'scrape_selector': source.scrape_selector,
                    'last_scraped_at': source.last_scraped_at.isoformat() if source.last_scraped_at else None,
                    'last_scrape_status': source.last_scrape_status,
                    'articles_found_last_scrape': source.articles_found_last_scrape,
                    'created_at': source.created_at.isoformat(),
                }
                for source in sources
            ]
        })

    elif request.method == 'POST':
        name = request.data.get('name')
        url = request.data.get('url')
        is_active = request.data.get('is_active', True)
        scrape_selector = request.data.get('scrape_selector', '')

        if not name or not url:
            return Response(
                {'error': 'Name and URL are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for duplicate URL
        if NewsSource.objects.filter(url=url).exists():
            return Response(
                {'error': 'A source with this URL already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        source = NewsSource.objects.create(
            name=name,
            url=url,
            is_active=is_active,
            scrape_selector=scrape_selector,
            created_by=request.user
        )

        return Response({
            'message': f'News source "{name}" created successfully',
            'source': {
                'id': source.id,
                'name': source.name,
                'url': source.url,
                'is_active': source.is_active,
            }
        }, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        if not source_id:
            return Response(
                {'error': 'Source ID required for deletion'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            source = NewsSource.objects.get(id=source_id)
            source_name = source.name
            source.delete()
            return Response({
                'message': f'News source "{source_name}" deleted successfully'
            })
        except NewsSource.DoesNotExist:
            return Response(
                {'error': 'News source not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def news_source_update(request, source_id):
    """
    Update a news source (superuser only).

    PATCH /api/news/sources/admin/<source_id>/
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can manage news sources'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        source = NewsSource.objects.get(id=source_id)
    except NewsSource.DoesNotExist:
        return Response(
            {'error': 'News source not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Update fields if provided
    if 'name' in request.data:
        source.name = request.data['name']
    if 'url' in request.data:
        source.url = request.data['url']
    if 'is_active' in request.data:
        source.is_active = request.data['is_active']
    if 'scrape_selector' in request.data:
        source.scrape_selector = request.data['scrape_selector']

    source.save()

    return Response({
        'message': f'News source "{source.name}" updated successfully',
        'source': {
            'id': source.id,
            'name': source.name,
            'url': source.url,
            'is_active': source.is_active,
            'scrape_selector': source.scrape_selector,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def news_scrape_trigger(request):
    """
    Trigger an immediate news scraping job (superuser only).

    POST /api/news/scrape/

    This creates a scrape job and triggers the Crawl4AI scraper to scrape all active sources.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can trigger news scraping'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.utils import timezone
    import threading
    import asyncio

    # Check if there's already a running job
    running_job = NewsScrapeJob.objects.filter(status='running').first()
    if running_job:
        return Response({
            'error': 'A scrape job is already running',
            'job_id': running_job.id,
            'started_at': running_job.started_at.isoformat() if running_job.started_at else None,
        }, status=status.HTTP_409_CONFLICT)

    # Create new scrape job
    job = NewsScrapeJob.objects.create(
        status='pending',
        triggered_by=request.user,
        is_scheduled=False
    )

    # Run the scraper in a background thread
    def run_scraper(job_id):
        """Run the news scraper in a background thread."""
        try:
            from mcp_servers.news_scraper import run_scrape_job
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_scrape_job(job_id))
            finally:
                loop.close()
        except Exception as e:
            # Update job status on failure
            from core.models import NewsScrapeJob
            from django.utils import timezone
            try:
                job = NewsScrapeJob.objects.get(id=job_id)
                job.status = 'failed'
                job.errors = [str(e)]
                job.completed_at = timezone.now()
                job.save()
            except:
                pass

    # Start the scraper in a background thread
    thread = threading.Thread(target=run_scraper, args=(job.id,))
    thread.daemon = True
    thread.start()

    return Response({
        'message': 'Scrape job started',
        'job_id': job.id,
        'status': 'running',
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def news_scrape_status(request, job_id=None):
    """
    Get status of scrape jobs (superuser only).

    GET /api/news/scrape/status/ - Get all recent jobs
    GET /api/news/scrape/status/<job_id>/ - Get specific job status
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can view scrape job status'},
            status=status.HTTP_403_FORBIDDEN
        )

    if job_id:
        try:
            job = NewsScrapeJob.objects.get(id=job_id)
            return Response({
                'job': {
                    'id': job.id,
                    'status': job.status,
                    'is_scheduled': job.is_scheduled,
                    'triggered_by': job.triggered_by.username if job.triggered_by else 'Scheduled',
                    'sources_processed': job.sources_processed,
                    'articles_found': job.articles_found,
                    'articles_new': job.articles_new,
                    'errors': job.errors,
                    'created_at': job.created_at.isoformat(),
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                }
            })
        except NewsScrapeJob.DoesNotExist:
            return Response(
                {'error': 'Scrape job not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # Return recent jobs
    jobs = NewsScrapeJob.objects.all()[:10]
    return Response({
        'jobs': [
            {
                'id': job.id,
                'status': job.status,
                'is_scheduled': job.is_scheduled,
                'triggered_by': job.triggered_by.username if job.triggered_by else 'Scheduled',
                'articles_new': job.articles_new,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ]
    })


# ============================================================================
# COMPANY PORTAL VIEWSETS (Resources, Events, Subscriptions)
# ============================================================================

class CompanyResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company Resources (documents, images, videos)

    Endpoints:
    - GET /api/company-portal/resources/ - List all resources for a company
    - GET /api/company-portal/resources/{id}/ - Get resource details
    - POST /api/company-portal/resources/ - Upload a new resource (company rep only)
    - PUT /api/company-portal/resources/{id}/ - Update resource (company rep only)
    - DELETE /api/company-portal/resources/{id}/ - Delete resource (company rep only)
    - POST /api/company-portal/resources/upload/ - Upload file and create resource
    - GET /api/company-portal/resources/choices/ - Get dropdown choices
    """
    serializer_class = CompanyResourceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CompanyResourceCreateSerializer
        return CompanyResourceSerializer

    def get_queryset(self):
        queryset = CompanyResource.objects.select_related('company', 'project', 'uploaded_by')

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by project if provided
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by resource type if provided
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Non-public resources only visible to company reps
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        elif self.request.user.company_id:
            queryset = queryset.filter(
                Q(is_public=True) | Q(company=self.request.user.company)
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)

        return queryset.order_by('sort_order', '-uploaded_at')

    def perform_create(self, serializer):
        # Verify user can add resources to this company
        company = serializer.validated_data.get('company')
        if not self.request.user.is_staff:
            if self.request.user.company != company:
                raise PermissionError("You can only add resources to your own company")
        serializer.save(uploaded_by=self.request.user)

    def perform_update(self, serializer):
        # Verify user can update this resource
        instance = self.get_object()
        if not self.request.user.is_staff:
            if self.request.user.company != instance.company:
                raise PermissionError("You can only update resources for your own company")
        serializer.save()

    def perform_destroy(self, instance):
        # Verify user can delete this resource
        if not self.request.user.is_staff:
            if self.request.user.company != instance.company:
                raise PermissionError("You can only delete resources for your own company")
        instance.delete()

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for resource forms"""
        serializer = CompanyResourceChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_resources(self, request):
        """Get resources for the current user's company"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.company:
            return Response(
                {'results': [], 'count': 0, 'message': 'You are not associated with a company'}
            )

        queryset = CompanyResource.objects.filter(
            company=request.user.company
        ).select_related('company', 'project', 'uploaded_by').order_by('sort_order', '-uploaded_at')

        serializer = CompanyResourceSerializer(queryset, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a file and create a resource record
        POST /api/company-portal/resources/upload/
        """
        import os
        import uuid
        from django.core.files.storage import default_storage
        from django.conf import settings

        file = request.FILES.get('file')
        company_id = request.data.get('company')
        category = request.data.get('category')
        title = request.data.get('title')
        description = request.data.get('description', '')
        resource_type = request.data.get('resource_type', 'document')
        project_id = request.data.get('project')
        is_public = request.data.get('is_public', 'true').lower() == 'true'

        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not company_id or not category or not title:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate company access
        try:
            company = Company.objects.get(id=company_id)
            if not request.user.is_staff and request.user.company != company:
                return Response(
                    {'error': 'You can only upload resources for your own company'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate unique filename
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"company_resources/{company_id}/{uuid.uuid4().hex}{ext}"

        # Save file
        try:
            saved_path = default_storage.save(filename, file)
            file_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)

            # Calculate file size
            file_size_mb = file.size / (1024 * 1024)

            # Create resource record
            resource = CompanyResource.objects.create(
                company=company,
                resource_type=resource_type,
                category=category,
                title=title,
                description=description,
                file_url=file_url,
                file_size_mb=round(file_size_mb, 2),
                file_format=ext.lstrip('.').upper(),
                is_public=is_public,
                project_id=project_id if project_id else None,
                uploaded_by=request.user
            )

            return Response(
                CompanyResourceSerializer(resource).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'File upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SpeakingEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Speaking Events

    Endpoints:
    - GET /api/company-portal/events/ - List all events (filterable by company, status, date)
    - GET /api/company-portal/events/{id}/ - Get event details
    - POST /api/company-portal/events/ - Create a new event (company rep only)
    - PUT /api/company-portal/events/{id}/ - Update event (company rep only)
    - DELETE /api/company-portal/events/{id}/ - Delete event (company rep only)
    - GET /api/company-portal/events/choices/ - Get dropdown choices
    - GET /api/company-portal/events/upcoming/ - Get upcoming events across all companies
    """
    serializer_class = SpeakingEventSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'choices', 'upcoming']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SpeakingEventCreateSerializer
        if self.action == 'list':
            return SpeakingEventListSerializer
        return SpeakingEventSerializer

    def get_queryset(self):
        queryset = SpeakingEvent.objects.select_related('company', 'created_by')

        # Filter by company if provided
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        # Filter by status if provided
        event_status = self.request.query_params.get('status')
        if event_status:
            queryset = queryset.filter(status=event_status)

        # Filter by event type if provided
        event_type = self.request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by featured
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        # Filter by date range
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')
        if from_date:
            queryset = queryset.filter(start_datetime__gte=from_date)
        if to_date:
            queryset = queryset.filter(start_datetime__lte=to_date)

        return queryset.order_by('-start_datetime')

    def perform_create(self, serializer):
        # Verify user can add events for this company
        company = serializer.validated_data.get('company')
        if not self.request.user.is_staff:
            if self.request.user.company != company:
                raise PermissionError("You can only create events for your own company")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # Verify user can update this event
        instance = self.get_object()
        if not self.request.user.is_staff:
            if self.request.user.company != instance.company:
                raise PermissionError("You can only update events for your own company")
        serializer.save()

    def perform_destroy(self, instance):
        # Verify user can delete this event
        if not self.request.user.is_staff:
            if self.request.user.company != instance.company:
                raise PermissionError("You can only delete events for your own company")
        instance.delete()

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for event forms"""
        serializer = SpeakingEventChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events across all companies"""
        from django.utils import timezone

        queryset = SpeakingEvent.objects.filter(
            status__in=['upcoming', 'live'],
            start_datetime__gte=timezone.now()
        ).select_related('company').order_by('start_datetime')[:20]

        serializer = SpeakingEventListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events for the current user's company"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.company:
            return Response(
                {'results': [], 'count': 0, 'message': 'You are not associated with a company'}
            )

        queryset = SpeakingEvent.objects.filter(
            company=request.user.company
        ).select_related('company', 'created_by').order_by('-start_datetime')

        serializer = SpeakingEventSerializer(queryset, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})


class CompanySubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company Subscriptions

    Endpoints:
    - GET /api/company-portal/subscriptions/ - List subscriptions (admin only)
    - GET /api/company-portal/subscriptions/{id}/ - Get subscription details
    - GET /api/company-portal/subscriptions/my-subscription/ - Get current user's company subscription
    - GET /api/company-portal/subscriptions/status/ - Quick subscription status check
    """
    serializer_class = CompanySubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CompanySubscription.objects.all().select_related('company').prefetch_related('invoices')

        # Regular users can only see their own company's subscription
        if self.request.user.company:
            return CompanySubscription.objects.filter(
                company=self.request.user.company
            ).select_related('company').prefetch_related('invoices')

        return CompanySubscription.objects.none()

    @action(detail=False, methods=['get'])
    def my_subscription(self, request):
        """Get subscription for current user's company"""
        if not request.user.company:
            return Response(
                {'error': 'You are not associated with a company'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subscription = CompanySubscription.objects.get(company=request.user.company)
            serializer = CompanySubscriptionSerializer(subscription)
            return Response(serializer.data)
        except CompanySubscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found for your company', 'has_subscription': False},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Quick subscription status check"""
        if not request.user.company:
            return Response({
                'has_company': False,
                'has_subscription': False,
                'is_active': False,
                'can_access_premium': False
            })

        try:
            subscription = CompanySubscription.objects.get(company=request.user.company)
            return Response({
                'has_company': True,
                'has_subscription': True,
                'is_active': subscription.is_active,
                'can_access_premium': subscription.can_access_premium,
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end
            })
        except CompanySubscription.DoesNotExist:
            return Response({
                'has_company': True,
                'has_subscription': False,
                'is_active': False,
                'can_access_premium': False
            })


class CompanyAccessRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company Access Requests

    Endpoints:
    - GET /api/company-portal/access-requests/ - List requests (own for users, all for admins)
    - POST /api/company-portal/access-requests/ - Create new request
    - GET /api/company-portal/access-requests/{id}/ - Get request details
    - DELETE /api/company-portal/access-requests/{id}/ - Cancel a pending request
    - GET /api/company-portal/access-requests/my_request/ - Get current user's pending request
    - GET /api/company-portal/access-requests/choices/ - Get dropdown choices
    - POST /api/company-portal/access-requests/{id}/review/ - Admin: approve/reject request
    - GET /api/company-portal/access-requests/pending/ - Admin: list all pending requests
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyAccessRequestCreateSerializer
        if self.action == 'review':
            return CompanyAccessRequestReviewSerializer
        if self.action == 'choices':
            return CompanyAccessRequestChoicesSerializer
        return CompanyAccessRequestSerializer

    def get_queryset(self):
        user = self.request.user

        # Staff can see all requests
        if user.is_staff:
            return CompanyAccessRequest.objects.all().select_related(
                'user', 'company', 'reviewer'
            )

        # Regular users can only see their own requests
        return CompanyAccessRequest.objects.filter(user=user).select_related(
            'user', 'company', 'reviewer'
        )

    def perform_destroy(self, instance):
        """Users can only cancel their own pending requests"""
        if instance.user != self.request.user:
            raise PermissionError("You can only cancel your own requests")
        if instance.status != 'pending':
            raise PermissionError("You can only cancel pending requests")

        instance.status = 'cancelled'
        instance.save()

    @action(detail=False, methods=['get'])
    def my_request(self, request):
        """Get current user's pending request if any"""
        pending_request = CompanyAccessRequest.objects.filter(
            user=request.user,
            status='pending'
        ).select_related('company').first()

        if pending_request:
            serializer = CompanyAccessRequestSerializer(pending_request)
            return Response(serializer.data)

        return Response({
            'has_pending_request': False,
            'has_company': request.user.company is not None,
            'company_name': request.user.company.name if request.user.company else None
        })

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get dropdown choices for request forms"""
        serializer = CompanyAccessRequestChoicesSerializer({})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Admin: List all pending requests"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        pending = CompanyAccessRequest.objects.filter(
            status='pending'
        ).select_related('user', 'company').order_by('-created_at')

        serializer = CompanyAccessRequestSerializer(pending, many=True)
        return Response({'results': serializer.data, 'count': len(serializer.data)})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Admin: Approve or reject a request"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        access_request = self.get_object()

        if access_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CompanyAccessRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        if action == 'approve':
            access_request.approve(reviewer=request.user, notes=notes)
            message = f"Request approved. {access_request.user.username} is now associated with {access_request.company.name}."
        else:
            access_request.reject(reviewer=request.user, notes=notes)
            message = "Request rejected."

        return Response({
            'message': message,
            'request': CompanyAccessRequestSerializer(access_request).data
        })


# ============================================================================
# STRIPE SUBSCRIPTION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for a new subscription.

    POST /api/company-portal/subscriptions/create-checkout/
    Body: {
        "success_url": "https://...",
        "cancel_url": "https://..."
    }

    Returns:
        checkout_url: URL to redirect user to Stripe Checkout
        session_id: Stripe session ID
    """
    from .stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company to subscribe'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not StripeService.is_configured():
        return Response(
            {'error': 'Payment system is not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    success_url = request.data.get('success_url')
    cancel_url = request.data.get('cancel_url')

    if not success_url or not cancel_url:
        return Response(
            {'error': 'success_url and cancel_url are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if company already has an active subscription
    try:
        existing_sub = CompanySubscription.objects.get(company=request.user.company)
        if existing_sub.is_active:
            return Response(
                {'error': 'Company already has an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except CompanySubscription.DoesNotExist:
        pass

    try:
        session = StripeService.create_checkout_session(
            company=request.user.company,
            user=request.user,
            success_url=success_url,
            cancel_url=cancel_url
        )
        return Response({
            'checkout_url': session.url,
            'session_id': session.id
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to create checkout session: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_billing_portal(request):
    """
    Create a Stripe billing portal session for subscription management.

    POST /api/company-portal/subscriptions/billing-portal/
    Body: {
        "return_url": "https://..."
    }

    Returns:
        portal_url: URL to redirect user to Stripe Billing Portal
    """
    from .stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_customer_id:
            return Response(
                {'error': 'No billing account found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    return_url = request.data.get('return_url')
    if not return_url:
        return Response(
            {'error': 'return_url is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = StripeService.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )
        return Response({
            'portal_url': session.url
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to create billing portal: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """
    Cancel the company's subscription.

    POST /api/company-portal/subscriptions/cancel/
    Body: {
        "immediate": false  # Optional, defaults to canceling at period end
    }

    Returns:
        success: true
        cancel_at_period_end: boolean
    """
    from .stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    immediate = request.data.get('immediate', False)

    try:
        stripe_sub = StripeService.cancel_subscription(
            subscription_id=subscription.stripe_subscription_id,
            at_period_end=not immediate
        )

        # Update local record
        if immediate:
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
        else:
            subscription.cancel_at_period_end = True
        subscription.save()

        return Response({
            'success': True,
            'cancel_at_period_end': not immediate,
            'status': subscription.status
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to cancel subscription: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reactivate_subscription(request):
    """
    Reactivate a subscription that was set to cancel at period end.

    POST /api/company-portal/subscriptions/reactivate/

    Returns:
        success: true
    """
    from .stripe_service import StripeService

    if not request.user.company:
        return Response(
            {'error': 'You must be associated with a company'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = CompanySubscription.objects.get(company=request.user.company)
        if not subscription.stripe_subscription_id:
            return Response(
                {'error': 'No subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not subscription.cancel_at_period_end:
            return Response(
                {'error': 'Subscription is not set to cancel'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except CompanySubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for your company'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        StripeService.reactivate_subscription(subscription.stripe_subscription_id)

        # Update local record
        subscription.cancel_at_period_end = False
        subscription.save(update_fields=['cancel_at_period_end'])

        return Response({
            'success': True,
            'status': subscription.status
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to reactivate subscription: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.

    POST /api/company-portal/webhooks/stripe/

    This endpoint verifies the webhook signature and processes
    subscription events from Stripe.
    """
    from .stripe_service import StripeService, process_subscription_webhook
    import json

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not sig_header:
        return Response(
            {'error': 'Missing Stripe signature'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        event = StripeService.construct_webhook_event(payload, sig_header)
    except ValueError:
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Webhook verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Process the event
    result = process_subscription_webhook(event)

    if result.get('success'):
        return Response({'received': True, 'event_type': result.get('event_type')})
    else:
        return Response(
            {'error': result.get('error')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# INVESTMENT INTEREST VIEWS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_investment_interest(request):
    """
    Register investment interest in a financing round.

    POST /api/investment-interest/register/

    Required fields:
    - financing: Financing ID
    - is_accredited_investor: boolean
    - shares_requested: integer
    - term_sheet_confirmed: boolean
    - subscription_agreement_confirmed: boolean
    - contact_email: string
    - risk_acknowledged: boolean

    Optional fields:
    - contact_phone: string
    """
    serializer = InvestmentInterestCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        interest = serializer.save()
        return Response(
            InvestmentInterestSerializer(interest).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_investment_interest(request, financing_id):
    """
    Check if the current user has registered interest in a financing.

    GET /api/investment-interest/my-interest/<financing_id>/
    """
    try:
        interest = InvestmentInterest.objects.get(
            user=request.user,
            financing_id=financing_id
        )
        return Response({
            'has_interest': True,
            'interest_id': interest.id,
            'status': interest.status,
            'shares_requested': interest.shares_requested,
            'investment_amount': str(interest.investment_amount),
            'created_at': interest.created_at,
        })
    except InvestmentInterest.DoesNotExist:
        return Response({
            'has_interest': False,
            'interest_id': None,
            'status': None,
            'shares_requested': None,
            'investment_amount': None,
            'created_at': None,
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_financing_interest_aggregate(request, financing_id):
    """
    Get public aggregate data for investment interests (NO PII).

    GET /api/investment-interest/aggregate/<financing_id>/

    Returns:
    - total_interest_count: Number of investors who expressed interest
    - total_shares_requested: Total shares requested
    - total_amount_interested: Total investment amount
    - percentage_filled: % of financing goal filled
    """
    try:
        financing = Financing.objects.get(id=financing_id)
    except Financing.DoesNotExist:
        return Response(
            {'error': 'Financing not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get or create and recalculate aggregate
    aggregate = InvestmentInterestAggregate.update_for_financing(financing)

    return Response(InvestmentInterestAggregateSerializer(aggregate).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_investment_interests(request, financing_id):
    """
    List all investment interests for a financing (admin/company only).

    GET /api/investment-interest/list/<financing_id>/

    Query params:
    - status: Filter by status (pending, qualified, contacted, converted, rejected, withdrawn)
    - search: Search by user name/email
    """
    # Check permissions - must be superuser or company representative
    try:
        financing = Financing.objects.get(id=financing_id)
    except Financing.DoesNotExist:
        return Response(
            {'error': 'Financing not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Permission check
    is_admin = request.user.is_superuser or request.user.is_staff
    is_company_rep = (
        request.user.company_id == financing.company_id and
        request.user.user_type == 'company'
    )

    if not (is_admin or is_company_rep):
        return Response(
            {'error': 'You do not have permission to view this data'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Build queryset with filters
    interests = financing.investment_interests.select_related('user', 'company', 'financing')

    # Status filter
    status_filter = request.query_params.get('status')
    if status_filter:
        interests = interests.filter(status=status_filter)

    # Search filter
    search = request.query_params.get('search')
    if search:
        interests = interests.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(contact_email__icontains=search)
        )

    # Ordering
    interests = interests.order_by('-created_at')

    serializer = InvestmentInterestSerializer(interests, many=True)
    return Response({
        'count': interests.count(),
        'results': serializer.data
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_investment_interest_status(request, interest_id):
    """
    Update the status of an investment interest (admin/company only).

    PATCH /api/investment-interest/<interest_id>/status/

    Body:
    - status: new status (qualified, contacted, converted, rejected, withdrawn)
    - status_notes: optional notes
    """
    try:
        interest = InvestmentInterest.objects.select_related(
            'financing__company'
        ).get(id=interest_id)
    except InvestmentInterest.DoesNotExist:
        return Response(
            {'error': 'Investment interest not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Permission check
    is_admin = request.user.is_superuser or request.user.is_staff
    is_company_rep = (
        request.user.company_id == interest.company_id and
        request.user.user_type == 'company'
    )

    if not (is_admin or is_company_rep):
        return Response(
            {'error': 'You do not have permission to update this'},
            status=status.HTTP_403_FORBIDDEN
        )

    new_status = request.data.get('status')
    valid_statuses = ['pending', 'qualified', 'contacted', 'converted', 'rejected', 'withdrawn']

    if new_status not in valid_statuses:
        return Response(
            {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    interest.status = new_status
    if 'status_notes' in request.data:
        interest.status_notes = request.data['status_notes']
    interest.save()

    # Recalculate aggregate
    InvestmentInterestAggregate.update_for_financing(interest.financing)

    return Response(InvestmentInterestSerializer(interest).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def withdraw_investment_interest(request, interest_id):
    """
    Withdraw investment interest (user can withdraw their own).

    DELETE /api/investment-interest/<interest_id>/withdraw/
    """
    try:
        interest = InvestmentInterest.objects.get(id=interest_id, user=request.user)
    except InvestmentInterest.DoesNotExist:
        return Response(
            {'error': 'Investment interest not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Only allow withdrawal if status is pending or qualified
    if interest.status not in ['pending', 'qualified']:
        return Response(
            {'error': 'Cannot withdraw interest at this stage. Please contact support.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    interest.status = 'withdrawn'
    interest.save()

    # Recalculate aggregate
    InvestmentInterestAggregate.update_for_financing(interest.financing)

    return Response({'message': 'Investment interest withdrawn successfully'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_my_investment_interest(request, interest_id):
    """
    Update investment interest (user can update their own if status is pending).

    PATCH /api/investment-interest/<interest_id>/update/

    Body:
    - shares_requested: number of shares (optional)
    - investment_amount: amount in USD (optional)
    """
    try:
        interest = InvestmentInterest.objects.get(id=interest_id, user=request.user)
    except InvestmentInterest.DoesNotExist:
        return Response(
            {'error': 'Investment interest not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Only allow updates if status is pending
    if interest.status != 'pending':
        return Response(
            {'error': 'Cannot update interest at this stage. Please contact support.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update fields
    shares_requested = request.data.get('shares_requested')
    investment_amount = request.data.get('investment_amount')

    if shares_requested is not None:
        interest.shares_requested = int(shares_requested)

    if investment_amount is not None:
        from decimal import Decimal
        interest.investment_amount = Decimal(str(investment_amount))

    interest.save()

    # Recalculate aggregate
    InvestmentInterestAggregate.update_for_financing(interest.financing)

    return Response({
        'message': 'Investment interest updated successfully',
        'interest_id': interest.id,
        'shares_requested': interest.shares_requested,
        'investment_amount': str(interest.investment_amount),
        'status': interest.status
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_investment_interests(request, financing_id):
    """
    Export investment interests to CSV (admin only).

    GET /api/investment-interest/export/<financing_id>/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        financing = Financing.objects.get(id=financing_id)
    except Financing.DoesNotExist:
        return Response(
            {'error': 'Financing not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="investment_interests_{financing_id}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'User', 'Email', 'Phone', 'Accredited',
        'Shares Requested', 'Investment Amount', 'Status',
        'Term Sheet Confirmed', 'Subscription Agreement Confirmed',
        'Risk Acknowledged', 'Created At'
    ])

    interests = financing.investment_interests.select_related('user').order_by('-created_at')

    for interest in interests:
        writer.writerow([
            interest.id,
            interest.user.get_full_name() or interest.user.username,
            interest.contact_email,
            interest.contact_phone,
            'Yes' if interest.is_accredited_investor else 'No',
            interest.shares_requested,
            f'${interest.investment_amount:,.2f}',
            interest.get_status_display(),
            'Yes' if interest.term_sheet_confirmed else 'No',
            'Yes' if interest.subscription_agreement_confirmed else 'No',
            'Yes' if interest.risk_acknowledged else 'No',
            interest.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_investment_interest_dashboard(request):
    """
    Get dashboard data for investment interests (superuser only).

    GET /api/investment-interest/admin/dashboard/

    Returns aggregate stats across all active financings.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Superuser access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.db.models import Sum, Count, Avg

    # Get all active financing rounds with interests (announced or closing status)
    active_financings = Financing.objects.filter(
        status__in=['announced', 'closing']
    ).select_related('company').prefetch_related('investment_interests')

    # Overall stats
    total_interests = InvestmentInterest.objects.filter(
        status__in=['pending', 'qualified', 'contacted', 'converted']
    ).aggregate(
        count=Count('id'),
        total_shares=Sum('shares_requested'),
        total_amount=Sum('investment_amount')
    )

    # By status breakdown
    status_breakdown = InvestmentInterest.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('investment_amount')
    ).order_by('status')

    # Recent interests (last 7 days)
    from django.utils import timezone
    week_ago = timezone.now() - timedelta(days=7)
    recent_count = InvestmentInterest.objects.filter(
        created_at__gte=week_ago
    ).count()

    # Per-financing summary
    financing_summaries = []
    for financing in active_financings:
        try:
            aggregate = financing.interest_aggregate
        except InvestmentInterestAggregate.DoesNotExist:
            aggregate = InvestmentInterestAggregate.update_for_financing(financing)

        financing_summaries.append({
            'financing_id': financing.id,
            'company_name': financing.company.name,
            'financing_type': financing.financing_type,
            'target_amount': str(financing.amount_raised_usd) if financing.amount_raised_usd else None,
            'total_interests': aggregate.total_interest_count,
            'total_amount': str(aggregate.total_amount_interested),
            'percentage_filled': str(aggregate.percentage_filled),
        })

    return Response({
        'total_interests': total_interests['count'] or 0,
        'total_shares_requested': total_interests['total_shares'] or 0,
        'total_amount_interested': str(total_interests['total_amount'] or 0),
        'recent_interests_7d': recent_count,
        'status_breakdown': list(status_breakdown),
        'active_financings': financing_summaries,
    })


# ============================================================================
# STORE MODULE API
# ============================================================================

class StoreCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for store categories.

    GET /api/store/categories/           - List all active categories
    GET /api/store/categories/{slug}/    - Get category by slug
    """
    queryset = StoreCategory.objects.filter(is_active=True)
    serializer_class = StoreCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class StoreProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for store products.

    GET /api/store/products/            - List all active products
    GET /api/store/products/{slug}/     - Get product by slug
    GET /api/store/products/featured/   - Get featured products
    GET /api/store/products/by-category/{category_slug}/ - Get products by category
    """
    queryset = StoreProduct.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related('images', 'variants')
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoreProductDetailSerializer
        return StoreProductListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by product type
        product_type = self.request.query_params.get('type')
        if product_type in ['physical', 'digital']:
            queryset = queryset.filter(product_type=product_type)

        # Filter by badge
        badge = self.request.query_params.get('badge')
        if badge:
            queryset = queryset.filter(badges__contains=[badge])

        # Price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price_cents__gte=int(float(min_price) * 100))

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price_cents__lte=int(float(max_price) * 100))

        # Sorting
        sort = self.request.query_params.get('sort', '-created_at')
        if sort == 'price_asc':
            queryset = queryset.order_by('price_cents')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price_cents')
        elif sort == 'popular':
            queryset = queryset.order_by('-total_sold')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-is_featured', '-created_at')

        return queryset

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = StoreProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_slug>[^/.]+)')
    def by_category(self, request, category_slug=None):
        """Get products by category slug"""
        products = self.get_queryset().filter(category__slug=category_slug)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = StoreProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StoreProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def share(self, request, slug=None):
        """Track product share to chat"""
        product = self.get_object()
        shared_to = request.data.get('shared_to', 'forum')
        destination_id = request.data.get('destination_id', '')

        share = StoreProductShare.objects.create(
            user=request.user,
            product=product,
            shared_to=shared_to,
            destination_id=destination_id
        )

        return Response({
            'success': True,
            'share_id': share.id,
            'message': f'Product shared successfully'
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def inquire(self, request, slug=None):
        """Create inquiry for high-value product"""
        product = self.get_object()

        if not product.requires_inquiry:
            return Response(
                {'error': 'This product does not require an inquiry'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StoreProductInquiryCreateSerializer(
            data={**request.data, 'product': product.id},
            context={'request': request}
        )

        if serializer.is_valid():
            inquiry = serializer.save()
            return Response(
                StoreProductInquirySerializer(inquiry).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreCartViewSet(viewsets.ViewSet):
    """
    API for shopping cart management.
    Supports both authenticated users and guest carts (via session).

    GET  /api/store/cart/           - Get current user's cart
    POST /api/store/cart/add/       - Add item to cart
    PUT  /api/store/cart/items/{id}/ - Update cart item quantity
    DELETE /api/store/cart/items/{id}/ - Remove item from cart
    POST /api/store/cart/clear/     - Clear entire cart
    """
    permission_classes = [AllowAny]

    def get_or_create_cart(self, request):
        """Get or create cart for user or guest session"""
        if request.user.is_authenticated:
            cart, created = StoreCart.objects.get_or_create(user=request.user)
        else:
            # Guest cart using session
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            cart, created = StoreCart.objects.get_or_create(session_key=session_key, user=None)
        return cart

    def list(self, request):
        """Get current cart"""
        cart = self.get_or_create_cart(request)
        serializer = StoreCartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_or_create_cart(request)
        product_id = serializer.validated_data['product_id']
        variant_id = serializer.validated_data.get('variant_id')
        quantity = serializer.validated_data['quantity']

        product = StoreProduct.objects.get(id=product_id)
        variant = None
        if variant_id:
            variant = StoreProductVariant.objects.get(id=variant_id)

        # Check if item already in cart
        existing_item = cart.items.filter(product=product, variant=variant).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            item = existing_item
        else:
            item = StoreCartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )

        # Update cart timestamp
        cart.save()

        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })

    @action(detail=False, methods=['put', 'delete'], url_path='items/(?P<item_id>[^/.]+)')
    def item(self, request, item_id=None):
        """Update or remove cart item.

        PUT: Update cart item quantity
        DELETE: Remove item from cart
        """
        cart = self.get_or_create_cart(request)
        try:
            item = cart.items.get(id=item_id)
        except StoreCartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'DELETE':
            # Remove item
            item.delete()
        else:
            # Update quantity (PUT)
            serializer = UpdateCartItemSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            quantity = serializer.validated_data['quantity']
            if quantity == 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        cart.save()  # Update timestamp
        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear entire cart"""
        cart = self.get_or_create_cart(request)
        cart.items.all().delete()
        cart.save()
        return Response({
            'success': True,
            'cart': StoreCartSerializer(cart).data
        })


class StoreOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for viewing user orders.

    GET /api/store/orders/          - List user's orders
    GET /api/store/orders/{id}/     - Get order details
    """
    serializer_class = StoreOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StoreOrder.objects.filter(
            user=self.request.user
        ).prefetch_related('items')


class StoreShippingRateViewSet(viewsets.ViewSet):
    """
    API for shipping rates.

    GET /api/store/shipping-rates/  - Get available shipping rates
    """
    permission_classes = [AllowAny]

    def list(self, request):
        """Get all active shipping rates"""
        country = request.query_params.get('country', 'US')
        rates = StoreShippingRate.objects.filter(
            is_active=True,
            countries__contains=[country]
        )
        serializer = StoreShippingRateSerializer(rates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate shipping rate based on cart contents"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        cart = StoreCart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        country = request.data.get('country', 'US')
        if country not in ['US', 'CA']:
            return Response(
                {'error': 'Shipping only available to US and Canada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total weight
        total_weight = sum(
            item.product.weight_grams * item.quantity
            for item in cart.items.filter(product__product_type='physical')
        )

        # Get applicable rates
        rates = StoreShippingRate.objects.filter(
            is_active=True,
            countries__contains=[country],
            min_weight_grams__lte=total_weight,
            max_weight_grams__gte=total_weight
        )

        serializer = StoreShippingRateSerializer(rates, many=True)
        return Response({
            'total_weight_grams': total_weight,
            'rates': serializer.data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def store_ticker(request):
    """
    Get recent purchases for The Ticker social proof feed.

    GET /api/store/ticker/

    Only returns purchases over $100 threshold.
    """
    # Get recent purchases above threshold (10000 cents = $100)
    recent = StoreRecentPurchase.objects.filter(
        amount_cents__gte=10000
    ).select_related('product').order_by('-created_at')[:20]

    serializer = StoreRecentPurchaseSerializer(recent, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_store_badges(request):
    """
    Get current user's store badges.

    GET /api/store/badges/
    """
    badges = UserStoreBadge.objects.filter(user=request.user)
    serializer = UserStoreBadgeSerializer(badges, many=True)
    return Response(serializer.data)


# ============================================================================
# COMPANY FORUM DISCUSSION
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_discussion(request, company_id):
    """
    Get or create the main forum discussion for a company.

    GET /api/companies/<company_id>/discussion/

    Returns the discussion ID for the company's main forum thread.
    Creates one if it doesn't exist.
    """
    from core.models import Company, ForumDiscussion

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get or create the main discussion for this company
    discussion, created = ForumDiscussion.objects.get_or_create(
        company=company,
        is_archived=False,
        defaults={
            'title': f'{company.name} Community Discussion',
            'description': f'Main discussion thread for {company.name} investors and analysts.',
            'created_by': request.user,
            'is_active': True,
            'is_pinned': True,
        }
    )

    return Response({
        'discussion_id': discussion.id,
        'title': discussion.title,
        'description': discussion.description,
        'message_count': discussion.message_count,
        'participant_count': discussion.participant_count,
        'created': created,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_checkout(request):
    """
    Create Stripe checkout session for store purchase.

    POST /api/store/checkout/
    {
        "shipping_address": {...},  // Required for physical items
        "shipping_rate_id": 1,      // Required for physical items
        "success_url": "https://...",
        "cancel_url": "https://..."
    }
    """
    serializer = CheckoutSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cart = StoreCart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    # Import the store stripe service (will be created next)
    from .store_stripe_service import StoreStripeService

    try:
        checkout_data = StoreStripeService.create_checkout_session(
            cart=cart,
            user=request.user,
            shipping_address=serializer.validated_data.get('shipping_address'),
            shipping_rate_id=serializer.validated_data.get('shipping_rate_id'),
            success_url=serializer.validated_data['success_url'],
            cancel_url=serializer.validated_data['cancel_url']
        )

        return Response(checkout_data)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def store_webhook(request):
    """
    Handle Stripe webhooks for store purchases.

    POST /api/store/webhook/
    """
    import stripe
    import logging
    from django.conf import settings

    logger = logging.getLogger(__name__)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_STORE_WEBHOOK_SECRET', None)

    logger.info(f"Store webhook received. Secret configured: {bool(webhook_secret)}, Sig header: {bool(sig_header)}")

    if not webhook_secret:
        logger.error("STRIPE_STORE_WEBHOOK_SECRET not configured")
        return Response({'error': 'Webhook secret not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Store webhook invalid payload: {str(e)}")
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Store webhook signature verification failed: {str(e)}")
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    # Import the store stripe service
    from .store_stripe_service import StoreStripeService

    try:
        result = StoreStripeService.process_webhook(event)
        return Response(result)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Store webhook error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# STORE ADMIN VIEWS
# ============================================================================

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin/staff users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        """Admin users have permission on all objects"""
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class StoreAdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin API for store categories.
    Requires admin/staff authentication.

    GET    /api/admin/store/categories/        - List all categories
    POST   /api/admin/store/categories/        - Create category
    GET    /api/admin/store/categories/{id}/   - Get category
    PUT    /api/admin/store/categories/{id}/   - Update category
    DELETE /api/admin/store/categories/{id}/   - Delete category
    """
    queryset = StoreCategory.objects.all().order_by('display_order', 'name')
    serializer_class = StoreCategoryAdminSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]


class StoreAdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin API for store products.
    Requires admin/staff authentication.

    GET    /api/admin/store/products/          - List all products (with filters)
    POST   /api/admin/store/products/          - Create product
    GET    /api/admin/store/products/{id}/     - Get product with details
    PUT    /api/admin/store/products/{id}/     - Update product
    DELETE /api/admin/store/products/{id}/     - Delete product
    POST   /api/admin/store/products/{id}/images/    - Add image
    POST   /api/admin/store/products/{id}/variants/  - Add variant
    """
    queryset = StoreProduct.objects.all().select_related('category').prefetch_related(
        'images', 'variants', 'digital_assets'
    ).order_by('-created_at')
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'list':
            return StoreProductAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StoreProductAdminCreateSerializer
        return StoreProductAdminDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search by name/SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by product type
        product_type = self.request.query_params.get('type')
        if product_type in ['physical', 'digital']:
            queryset = queryset.filter(product_type=product_type)

        # Filter by stock status
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(
                    Q(inventory_count__gt=0) | Q(product_type='digital')
                )
            else:
                queryset = queryset.filter(inventory_count=0, product_type='physical')

        return queryset

    @action(detail=True, methods=['post'])
    def images(self, request, pk=None):
        """Add image to product"""
        product = self.get_object()
        serializer = StoreProductImageAdminSerializer(data=request.data)

        if serializer.is_valid():
            # If this is set as primary, unset other primary images
            if serializer.validated_data.get('is_primary'):
                product.images.update(is_primary=False)

            image = StoreProductImage.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreProductImageAdminSerializer(image).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def variants(self, request, pk=None):
        """Add variant to product"""
        product = self.get_object()
        serializer = StoreProductVariantAdminSerializer(data=request.data)

        if serializer.is_valid():
            variant = StoreProductVariant.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreProductVariantAdminSerializer(variant).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def digital_assets(self, request, pk=None):
        """Add digital asset to product"""
        product = self.get_object()
        serializer = StoreDigitalAssetAdminSerializer(data=request.data)

        if serializer.is_valid():
            asset = StoreDigitalAsset.objects.create(
                product=product,
                **serializer.validated_data
            )
            return Response(
                StoreDigitalAssetAdminSerializer(asset).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a product"""
        product = self.get_object()

        # Create new product with copied data
        new_product = StoreProduct.objects.create(
            category=product.category,
            name=f"{product.name} (Copy)",
            slug=f"{product.slug}-copy-{StoreProduct.objects.count()}",
            description=product.description,
            short_description=product.short_description,
            price_cents=product.price_cents,
            compare_at_price_cents=product.compare_at_price_cents,
            product_type=product.product_type,
            inventory_count=0,
            weight_grams=product.weight_grams,
            is_active=False,  # Start as inactive
            is_featured=False,
            badges=product.badges,
            provenance_info=product.provenance_info,
            authentication_docs=product.authentication_docs,
            min_price_for_inquiry=product.min_price_for_inquiry,
        )

        # Copy images
        for image in product.images.all():
            StoreProductImage.objects.create(
                product=new_product,
                image_url=image.image_url,
                alt_text=image.alt_text,
                display_order=image.display_order,
                is_primary=image.is_primary,
            )

        # Copy variants
        for variant in product.variants.all():
            StoreProductVariant.objects.create(
                product=new_product,
                name=variant.name,
                sku=f"{variant.sku}-copy" if variant.sku else None,
                price_cents_override=variant.price_cents_override,
                inventory_count=0,
                is_active=variant.is_active,
                display_order=variant.display_order,
            )

        return Response(
            StoreProductAdminDetailSerializer(new_product).data,
            status=status.HTTP_201_CREATED
        )


class StoreAdminImageViewSet(viewsets.ModelViewSet):
    """
    Admin API for product images.
    For updating/deleting individual images.

    PUT    /api/admin/store/images/{id}/    - Update image
    DELETE /api/admin/store/images/{id}/    - Delete image
    """
    queryset = StoreProductImage.objects.all()
    serializer_class = StoreProductImageAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]


class StoreAdminVariantViewSet(viewsets.ModelViewSet):
    """
    Admin API for product variants.
    For updating/deleting individual variants.

    PUT    /api/admin/store/variants/{id}/    - Update variant
    DELETE /api/admin/store/variants/{id}/    - Delete variant
    """
    queryset = StoreProductVariant.objects.all()
    serializer_class = StoreProductVariantAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]


class StoreAdminDigitalAssetViewSet(viewsets.ModelViewSet):
    """
    Admin API for digital assets.
    For updating/deleting individual assets.

    PUT    /api/admin/store/digital-assets/{id}/    - Update asset
    DELETE /api/admin/store/digital-assets/{id}/    - Delete asset
    """
    queryset = StoreDigitalAsset.objects.all()
    serializer_class = StoreDigitalAssetAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]


class StoreAdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin API for store orders.
    Requires admin/staff authentication.

    GET    /api/admin/store/orders/         - List all orders
    GET    /api/admin/store/orders/{id}/    - Get order details
    PUT    /api/admin/store/orders/{id}/    - Update order (status, tracking)
    """
    queryset = StoreOrder.objects.all().select_related('user').prefetch_related(
        'items'
    ).order_by('-created_at')
    serializer_class = StoreOrderAdminSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)

        # Search by email or order ID
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer_email__icontains=search) |
                Q(id__icontains=search) |
                Q(tracking_number__icontains=search)
            )

        return queryset

    def partial_update(self, request, *args, **kwargs):
        """Handle order status updates with email notifications"""
        order = self.get_object()
        old_status = order.status

        response = super().partial_update(request, *args, **kwargs)

        # Send shipping notification if status changed to shipped
        order.refresh_from_db()
        if old_status != 'shipped' and order.status == 'shipped':
            from .email_service import EmailService
            EmailService.send_shipping_notification(order)

        return response

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get order statistics for dashboard"""
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        stats = {
            'total_orders': StoreOrder.objects.count(),
            'pending_orders': StoreOrder.objects.filter(status='paid').count(),
            'processing_orders': StoreOrder.objects.filter(status='processing').count(),
            'shipped_orders': StoreOrder.objects.filter(status='shipped').count(),
            'delivered_orders': StoreOrder.objects.filter(status='delivered').count(),
            'total_revenue_cents': StoreOrder.objects.filter(
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).aggregate(total=Sum('total_cents'))['total'] or 0,
            'last_30_days_orders': StoreOrder.objects.filter(
                created_at__date__gte=thirty_days_ago
            ).count(),
            'last_30_days_revenue_cents': StoreOrder.objects.filter(
                created_at__date__gte=thirty_days_ago,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).aggregate(total=Sum('total_cents'))['total'] or 0,
        }

        # Convert cents to dollars
        stats['total_revenue_dollars'] = stats['total_revenue_cents'] / 100
        stats['last_30_days_revenue_dollars'] = stats['last_30_days_revenue_cents'] / 100

        return Response(stats)


# ============================================================================
# COMPANY AUTO-ONBOARDING ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_company_preview(request):
    """
    Start an async company scrape preview job.
    Returns immediately with a job_id that can be polled for status.

    POST /api/admin/companies/scrape-preview/

    Body:
    - url: Company website URL
    - sections: Optional list of sections to scrape

    Returns:
    - job_id: ID of the scraping job
    - status: 'pending' initially
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    url = request.data.get('url')
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sections = request.data.get('sections')

    from core.models import ScrapingJob
    from core.tasks import scrape_company_website_task

    try:
        # Create a scraping job record
        job = ScrapingJob.objects.create(
            company_name_input=url,
            website_url=url,
            status='pending',
            sections_to_process=sections or ['all'],
            initiated_by=request.user
        )

        # Queue the Celery task
        scrape_company_website_task.delay(job.id, sections=sections)

        return Response({
            'success': True,
            'job_id': job.id,
            'status': 'pending',
            'message': 'Scraping job queued. Poll /api/admin/companies/scraping-jobs/<job_id>/ for status.'
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_company_save(request):
    """
    Scrape and save company data from a website (ASYNC via Celery).

    POST /api/admin/companies/scrape-save/

    Body:
    - url: Company website URL
    - sections: Optional list of sections to scrape
    - update_existing: Boolean, whether to update if company exists

    Returns immediately with job_id. Poll /api/admin/companies/scraping-jobs/{job_id}/
    to check status.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    url = request.data.get('url')
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sections = request.data.get('sections')
    update_existing = request.data.get('update_existing', False)

    from core.models import ScrapingJob
    from core.tasks import scrape_and_save_company_task

    # Create scraping job with 'pending' status
    job = ScrapingJob.objects.create(
        company_name_input=url,
        website_url=url,
        status='pending',
        sections_to_process=sections or ['all'],
        initiated_by=request.user
    )

    # Trigger async Celery task
    task = scrape_and_save_company_task.delay(
        job_id=job.id,
        update_existing=update_existing,
        user_id=request.user.id
    )

    return Response({
        'success': True,
        'status': 'processing',
        'message': 'Scraping started in background. Poll job status to check completion.',
        'job_id': job.id,
        'task_id': task.id,
        'poll_url': f'/api/admin/companies/scraping-jobs/{job.id}/',
    })


def _infer_commodity_from_name(name: str) -> str:
    """
    Infer the primary commodity from a project name.
    Looks for commodity keywords in the name and returns the appropriate commodity code.
    Defaults to 'gold' if no commodity is detected.
    """
    name_lower = name.lower()

    # Check for specific commodities in order of specificity
    # Check compound commodities first
    if 'gold-silver' in name_lower or 'gold silver' in name_lower:
        return 'gold'  # Gold-silver projects typically listed as gold primary
    if 'silver-gold' in name_lower or 'silver gold' in name_lower:
        return 'silver'

    # Check individual commodities
    if 'silver' in name_lower:
        return 'silver'
    if 'copper' in name_lower:
        return 'copper'
    if 'zinc' in name_lower:
        return 'zinc'
    if 'nickel' in name_lower:
        return 'nickel'
    if 'lithium' in name_lower:
        return 'lithium'
    if 'uranium' in name_lower:
        return 'uranium'
    if 'cobalt' in name_lower:
        return 'cobalt'
    if 'platinum' in name_lower or 'palladium' in name_lower or 'pgm' in name_lower:
        return 'pgm'
    if 'rare earth' in name_lower or 'ree' in name_lower:
        return 'ree'
    if 'base metal' in name_lower:
        return 'base metals'
    if 'gold' in name_lower:
        return 'gold'

    # Default to gold for mining companies
    return 'gold'


def _is_invalid_project_name(name: str) -> bool:
    """
    Check if a project name is invalid (geochemistry data, sample labels, etc.)
    Returns True if the name should be filtered out.
    """
    import re
    name_lower = name.lower()

    # Filter out geochemistry/assay data labels
    # e.g., "Epworth Ag ppm", "Epworth Au ppb", "Epworth Cu pct", "Lake Sed Au Ag"
    geochemistry_patterns = [
        r'\b(ppm|ppb|ppt|g/t|oz/t|pct)\b',  # Unit suffixes
        r'\b(au|ag|cu|pb|zn|ni|co|pt|pd|li|u|mo|w|sn|fe|mn|as|sb|bi|cd|hg)\s+(ppm|ppb|ppt|g/t|pct)\b',  # Element + unit
        r'\bsed\s+(au|ag|cu|pb|zn)',  # Sediment samples like "Lake Sed Au Ag"
        r'\b(lake|stream|soil|rock)\s+sed\b',  # Sediment sample types
    ]

    for pattern in geochemistry_patterns:
        if re.search(pattern, name_lower):
            return True

    return False


def _infer_project_stage_from_name(name: str) -> str:
    """
    Infer the project stage from a project name.
    Looks for stage-related keywords in the name.
    Defaults to 'early_exploration' if no stage is detected.

    Stages: grassroots, early_exploration, advanced_exploration, resource,
            pea, pfs, fs, permitting, development, production
    """
    name_lower = name.lower()

    # Production/Operating indicators
    if any(kw in name_lower for kw in ['mine', 'operation', 'operating', 'producer', 'producing', 'mill']):
        return 'production'

    # Development indicators
    if any(kw in name_lower for kw in ['development', 'construction', 'building']):
        return 'development'

    # Permitting indicators
    if any(kw in name_lower for kw in ['permitting', 'permitted']):
        return 'permitting'

    # Feasibility indicators
    if any(kw in name_lower for kw in ['feasibility', 'fs ']):
        return 'fs'

    # PFS indicators
    if 'pfs' in name_lower or 'pre-feasibility' in name_lower or 'prefeasibility' in name_lower:
        return 'pfs'

    # PEA indicators
    if 'pea' in name_lower or 'preliminary economic' in name_lower:
        return 'pea'

    # Resource stage indicators
    if any(kw in name_lower for kw in ['resource', 'deposit']):
        return 'resource'

    # Advanced exploration indicators
    if any(kw in name_lower for kw in ['advanced', 'drill', 'drilling']):
        return 'advanced_exploration'

    # Grassroots indicators
    if any(kw in name_lower for kw in ['grassroots', 'greenfield', 'early stage']):
        return 'grassroots'

    # Default - most scraped projects are exploration stage
    return 'early_exploration'


def _classify_news(title: str) -> dict:
    """
    Classify a news release based on its title.
    Returns a dict with news_type, is_material, financing info, and drill result info.
    """
    import re
    from decimal import Decimal

    title_lower = title.lower()
    result = {
        'news_type': 'general',
        'is_material': False,
        'financing_type': 'none',
        'financing_amount': None,
        'financing_price_per_unit': None,
        'has_drill_results': False,
        'best_intercept': '',
    }

    # ===== DRILL RESULTS DETECTION =====
    drill_patterns = [
        r'drill\s*result',
        r'drilling\s*result',
        r'intersect',
        r'intercept',
        r'assay\s*result',
        r'returns?\s+\d+',  # "returns 5.2 g/t"
        r'\d+\.?\d*\s*g/t',  # grade mentions
        r'\d+\.?\d*\s*%\s*(cu|zn|pb|ni)',  # percentage grades
        r'metres?\s+of\s+\d+',  # "10 metres of 5 g/t"
        r'meters?\s+of\s+\d+',
        r'grading\s+\d+',
    ]
    for pattern in drill_patterns:
        if re.search(pattern, title_lower):
            result['news_type'] = 'drill_results'
            result['is_material'] = True
            result['has_drill_results'] = True
            # Try to extract best intercept
            intercept_match = re.search(
                r'(\d+\.?\d*)\s*(m|metres?|meters?)\s*(of|@|at)\s*(\d+\.?\d*)\s*(g/t|%)',
                title_lower
            )
            if intercept_match:
                result['best_intercept'] = intercept_match.group(0)
            break

    # ===== RESOURCE ESTIMATE DETECTION =====
    resource_patterns = [
        r'resource\s*estimate',
        r'mineral\s*resource',
        r'indicated\s*resource',
        r'inferred\s*resource',
        r'measured\s*resource',
        r'resource\s*update',
        r'ni\s*43-?101',
        r'43-?101',
        r'million\s*(oz|ounces)',
        r'moz',
        r'resource\s*of\s*\d+',
    ]
    if result['news_type'] == 'general':
        for pattern in resource_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'resource_estimate'
                result['is_material'] = True
                break

    # ===== FINANCING DETECTION =====
    financing_patterns = {
        'private_placement': [
            r'private\s*placement',
            r'non-?brokered',
            r'closes?\s*private',
            r'announces?\s*private',
        ],
        'bought_deal': [
            r'bought\s*deal',
            r'brokered\s*offering',
            r'underwritten\s*offering',
            r'prospectus\s*offering',
        ],
        'flow_through': [
            r'flow-?through',
            r'flow\s*through\s*shares?',
            r'fts\s*financing',
        ],
        'rights_offering': [
            r'rights\s*offering',
            r'rights\s*issue',
        ],
        'warrant_exercise': [
            r'warrant\s*exercise',
            r'exercises?\s*warrants?',
        ],
        'debt': [
            r'debt\s*financing',
            r'loan\s*facility',
            r'credit\s*facility',
            r'convertible\s*debenture',
        ],
    }

    for financing_type, patterns in financing_patterns.items():
        for pattern in patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'financing'
                result['is_material'] = True
                result['financing_type'] = financing_type
                # Try to extract financing amount
                amount_match = re.search(
                    r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|m\b)',
                    title_lower
                )
                if amount_match:
                    try:
                        amount_str = amount_match.group(1).replace(',', '')
                        result['financing_amount'] = Decimal(amount_str) * 1000000
                    except:
                        pass
                # Try to extract price per unit
                price_match = re.search(
                    r'\$\s*(\d+\.?\d*)\s*per\s*(unit|share)',
                    title_lower
                )
                if price_match:
                    try:
                        result['financing_price_per_unit'] = Decimal(price_match.group(1))
                    except:
                        pass
                break
        if result['financing_type'] != 'none':
            break

    # ===== ACQUISITION/MERGER DETECTION =====
    acquisition_patterns = [
        r'acqui(re|sition)',
        r'merger',
        r'amalgamat',
        r'take-?over',
        r'business\s*combination',
        r'purchase\s*agreement',
        r'option\s*agreement',
        r'earn-?in',
    ]
    if result['news_type'] == 'general':
        for pattern in acquisition_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'acquisition'
                result['is_material'] = True
                break

    # ===== MANAGEMENT CHANGE DETECTION =====
    management_patterns = [
        r'appoint',
        r'ceo\s*(change|transition|resign|depart)',
        r'new\s*(ceo|cfo|president|director)',
        r'board\s*(change|appointment)',
        r'management\s*change',
        r'executive\s*change',
    ]
    if result['news_type'] == 'general':
        for pattern in management_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'management'
                break

    # ===== EXPLORATION UPDATE =====
    exploration_patterns = [
        r'exploration\s*update',
        r'exploration\s*program',
        r'field\s*program',
        r'sampling\s*result',
        r'geophysic',
        r'survey\s*result',
        r'commence.*drill',
        r'start.*drill',
    ]
    if result['news_type'] == 'general':
        for pattern in exploration_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'exploration'
                break

    # ===== PRODUCTION UPDATE =====
    production_patterns = [
        r'production\s*update',
        r'production\s*result',
        r'quarterly\s*production',
        r'annual\s*production',
        r'gold\s*pour',
        r'first\s*pour',
        r'commercial\s*production',
    ]
    if result['news_type'] == 'general':
        for pattern in production_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'production'
                result['is_material'] = True
                break

    # ===== REGULATORY/PERMITTING =====
    regulatory_patterns = [
        r'permit',
        r'environmental\s*assessment',
        r'eia\b',
        r'regulatory\s*approv',
        r'license\s*grant',
        r'licence\s*grant',
    ]
    if result['news_type'] == 'general':
        for pattern in regulatory_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'regulatory'
                break

    return result


def _save_scraped_company_data(data: dict, source_url: str, update_existing: bool, user) -> 'Company':
    """Helper function to save scraped data to database."""
    from core.models import (
        Company, Project, CompanyPerson, CompanyDocument, CompanyNews, DocumentProcessingJob,
        NewsRelease, NewsReleaseFlag
    )

    # Validate scraped data using Claude-powered validation
    # This filters out invalid projects, news with date-only titles, and garbage descriptions
    try:
        from core.claude_validator import validate_scraped_data
        data = validate_scraped_data(data, source_url)
    except Exception as e:
        print(f"[SAVE COMPANY] Claude validation failed, using raw data: {e}")

    company_data = data.get('company', {})

    if not company_data.get('name'):
        raise Exception("No company name extracted - cannot create record")

    # Check for existing company
    existing_company = None
    if company_data.get('ticker_symbol'):
        existing_company = Company.objects.filter(
            ticker_symbol__iexact=company_data['ticker_symbol']
        ).first()

    if not existing_company:
        existing_company = Company.objects.filter(
            name__iexact=company_data['name']
        ).first()

    if existing_company and not update_existing:
        return existing_company

    # Prepare company fields with length truncation to prevent DB errors
    company_fields = {
        'name': (company_data.get('name') or '')[:200],
        'legal_name': (company_data.get('legal_name') or company_data.get('name') or '')[:200],
        'ticker_symbol': (company_data.get('ticker_symbol') or '')[:10],
        'description': (company_data.get('description') or '')[:2000],
        'tagline': (company_data.get('tagline') or '')[:500],
        'logo_url': (company_data.get('logo_url') or '')[:200],
        'website': source_url[:200],
        'source_website_url': source_url[:200],
        'auto_populated': True,
        'last_scraped_at': timezone.now(),
        # Contact info
        'ir_contact_email': (company_data.get('ir_contact_email') or '')[:254],
        'general_email': (company_data.get('general_email') or '')[:254],
        'media_email': (company_data.get('media_email') or '')[:254],
        'general_phone': (company_data.get('general_phone') or '')[:30],
        'street_address': (company_data.get('street_address') or '')[:300],
        # Social media
        'linkedin_url': (company_data.get('linkedin_url') or '')[:200],
        'twitter_url': (company_data.get('twitter_url') or '')[:200],
        'facebook_url': (company_data.get('facebook_url') or '')[:200],
        'youtube_url': (company_data.get('youtube_url') or '')[:200],
    }

    # Map exchange
    exchange_map = {
        'TSX': 'tsx', 'TSXV': 'tsxv', 'TSX-V': 'tsxv',
        'CSE': 'cse', 'OTC': 'otc', 'ASX': 'asx', 'AIM': 'aim',
    }
    if company_data.get('exchange'):
        company_fields['exchange'] = exchange_map.get(company_data['exchange'].upper(), 'other')

    # Market data
    if company_data.get('market_cap_usd'):
        company_fields['market_cap_usd'] = company_data['market_cap_usd']
    if company_data.get('shares_outstanding'):
        company_fields['shares_outstanding'] = company_data['shares_outstanding']

    # Set status
    if company_fields.get('ticker_symbol') and company_fields.get('exchange'):
        company_fields['status'] = 'public'
    else:
        company_fields['status'] = 'private'

    # Create or update company
    if existing_company:
        for field, value in company_fields.items():
            if value:
                setattr(existing_company, field, value)
        existing_company.save()
        company = existing_company
    else:
        company = Company.objects.create(**company_fields)

    # Calculate completeness score
    company.calculate_completeness_score()
    company.save()

    # Save people
    for i, person_data in enumerate(data.get('people', [])):
        CompanyPerson.objects.update_or_create(
            company=company,
            full_name=person_data.get('full_name', '')[:200],
            defaults={
                'role_type': person_data.get('role_type', 'executive'),
                'title': person_data.get('title', '')[:200],
                'biography': person_data.get('biography', ''),
                'photo_url': person_data.get('photo_url', '')[:200],
                'linkedin_url': person_data.get('linkedin_url', '')[:200],
                'source_url': person_data.get('source_url', '')[:200],
                'extracted_at': timezone.now(),
                'display_order': i,
            }
        )

    # Save documents and create processing jobs for key document types
    from core.models import DocumentProcessingJob
    processing_job_types = ['ni43101', 'pea', 'presentation', 'fact_sheet']
    processing_jobs_created = []

    for doc_data in data.get('documents', []):
        doc_type = doc_data.get('document_type', 'other')
        source_url = doc_data.get('source_url', '')

        # Skip documents with URLs that are too long (max 200 chars for source_url field)
        if len(source_url) > 200:
            continue

        # Save document record
        CompanyDocument.objects.update_or_create(
            company=company,
            source_url=source_url,
            defaults={
                'document_type': doc_type,
                'title': doc_data.get('title', 'Untitled')[:500],  # Truncate title to max length
                'year': doc_data.get('year'),
                'extracted_at': timezone.now(),
            }
        )

        # Create document processing job for key document types (if PDF)
        if doc_type in processing_job_types and source_url and '.pdf' in source_url.lower():
            # Check if job already exists for this URL
            existing_job = DocumentProcessingJob.objects.filter(url=source_url).first()
            if not existing_job:
                job = DocumentProcessingJob.objects.create(
                    url=source_url,
                    document_type=doc_type,
                    company_name=company.name,
                    status='pending',
                    created_by=user,
                )
                processing_jobs_created.append({
                    'id': job.id,
                    'type': doc_type,
                    'url': source_url
                })

    # Store processing jobs info for later use
    data['_processing_jobs_created'] = processing_jobs_created

    # Save news with classification and document processing
    from datetime import datetime
    news_processing_jobs = []

    # FALLBACK: If company_scraper found no news, use website_crawler which has better extraction
    news_items = data.get('news', [])
    if not news_items and company and company.website:
        try:
            import asyncio
            from mcp_servers.website_crawler import crawl_news_releases
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                crawler_news = loop.run_until_complete(crawl_news_releases(company.website, months=12))
                news_items = []
                for item in crawler_news:
                    news_items.append({
                        'title': item.get('title', ''),
                        'source_url': item.get('url', ''),
                        'publication_date': item.get('date'),
                    })
                print(f"[FALLBACK] website_crawler found {len(news_items)} news items")
            finally:
                loop.close()
        except Exception as e:
            print(f"[FALLBACK] website_crawler error: {e}")

    for news_item in news_items[:50]:
        pub_date = None
        if news_item.get('publication_date'):
            try:
                pub_date = datetime.strptime(news_item['publication_date'], '%Y-%m-%d').date()
            except:
                pass

        # Skip news without dates
        if not pub_date:
            continue

        news_url = news_item.get('source_url', '')
        news_title = news_item.get('title', 'Untitled')[:500]

        # Skip news items with URLs that are too long (max 200 chars for source_url field)
        if len(news_url) > 200:
            continue

        # Skip items with very short titles
        if len(news_title) < 10:
            continue

        # Skip titles that are just dates (e.g., "January 8, 2026", "December 23, 2025")
        import re
        date_only_pattern = re.compile(
            r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$',
            re.IGNORECASE
        )
        if date_only_pattern.match(news_title.strip()):
            continue

        is_pdf = '.pdf' in news_url.lower()

        # Classify the news item
        classification = _classify_news(news_title)

        # Create or update the news record with classification data
        news_record, created = CompanyNews.objects.update_or_create(
            company=company,
            source_url=news_url,
            defaults={
                'title': news_title,
                'publication_date': pub_date,
                'is_pdf': is_pdf,
                'news_type': classification['news_type'],
                'is_material': classification['is_material'],
                'financing_type': classification['financing_type'],
                'financing_amount': classification['financing_amount'],
                'financing_price_per_unit': classification['financing_price_per_unit'],
                'has_drill_results': classification['has_drill_results'],
                'best_intercept': classification['best_intercept'][:200] if classification['best_intercept'] else '',
            }
        )

        # Create financing flag for superuser review if financing-related AND recent (within 7 days)
        if classification['news_type'] == 'financing' and pub_date:
            # Only flag recent financing news (within 7 days) - older ones are not actionable
            from datetime import timedelta
            cutoff_date = timezone.now().date() - timedelta(days=7)
            is_recent = pub_date >= cutoff_date

            if is_recent:
                financing_keywords = [
                    'private placement', 'financing', 'funding round', 'capital raise',
                    'bought deal', 'equity financing', 'debt financing', 'flow-through',
                    'warrant', 'subscription', 'offering', 'closes', 'tranche',
                    'non-brokered', 'brokered', 'strategic investment', 'strategic partner'
                ]
                title_lower = news_title.lower()
                detected_keywords = [kw for kw in financing_keywords if kw in title_lower]

                if detected_keywords:
                    # Import NewsReleaseFlag here to ensure it's available in this scope
                    from core.models import NewsReleaseFlag
                    # Create NewsRelease record (needed for NewsReleaseFlag)
                    news_release, _ = NewsRelease.objects.get_or_create(
                        company=company,
                        url=news_url,
                        defaults={
                            'title': news_title,
                            'release_date': pub_date,
                            'is_material': True,
                        }
                    )
                    # Create the flag
                    NewsReleaseFlag.objects.get_or_create(
                        news_release=news_release,
                        defaults={
                            'detected_keywords': detected_keywords,
                            'status': 'pending'
                        }
                    )

        # Create DocumentProcessingJob for PDF news releases
        if is_pdf and news_url and not news_record.is_processed:
            existing_job = DocumentProcessingJob.objects.filter(url=news_url).first()
            if not existing_job:
                job = DocumentProcessingJob.objects.create(
                    url=news_url,
                    document_type='news_release',
                    company_name=company.name,
                    project_name='',
                    status='pending',
                    created_by=user,
                )
                news_record.processing_job = job
                news_record.save(update_fields=['processing_job'])
                news_processing_jobs.append({
                    'id': job.id,
                    'type': 'news_release',
                    'url': news_url,
                    'is_material': classification['is_material'],
                })

    # Add news processing jobs to the list
    if news_processing_jobs:
        processing_jobs_created.extend(news_processing_jobs)

    # Save projects
    for project_data in data.get('projects', []):
        if project_data.get('name'):
            project_name = project_data.get('name', '')[:200]

            # Skip invalid project names (geochemistry data, sample labels, etc.)
            if _is_invalid_project_name(project_name):
                continue

            # Check if project already exists
            existing_project = Project.objects.filter(
                company=company,
                name=project_name
            ).first()

            if existing_project:
                # Only update description and location, preserve commodity and stage
                # (to avoid overwriting manual corrections)
                if project_data.get('description'):
                    existing_project.description = (project_data.get('description') or '')[:2000]
                if project_data.get('location'):
                    existing_project.country = (project_data.get('location') or '')[:100]
                existing_project.save()
            else:
                # New project - infer commodity and stage from name
                commodity = _infer_commodity_from_name(project_name)
                stage = _infer_project_stage_from_name(project_name)
                # Use 'Unknown' as default country if not provided (NOT NULL constraint)
                country = (project_data.get('location') or project_data.get('country') or 'Unknown')[:100]
                Project.objects.create(
                    company=company,
                    name=project_name,
                    description=(project_data.get('description') or '')[:2000],
                    country=country,
                    project_stage=stage,
                    primary_commodity=commodity,
                )

    return company


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scraping_jobs(request):
    """
    List scraping jobs with pagination.

    GET /api/admin/companies/scraping-jobs/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import ScrapingJob

    jobs = ScrapingJob.objects.select_related('company', 'initiated_by').order_by('-created_at')[:50]

    results = []
    for job in jobs:
        results.append({
            'id': job.id,
            'company_name_input': job.company_name_input,
            'website_url': job.website_url,
            'status': job.status,
            'company_id': job.company_id,
            'company_name': job.company.name if job.company else None,
            'documents_found': job.documents_found,
            'people_found': job.people_found,
            'news_found': job.news_found,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'duration_seconds': job.duration_seconds,
            'initiated_by': job.initiated_by.username if job.initiated_by else None,
            'error_messages': job.error_messages,
        })

    return Response({'results': results})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_failed_discoveries(request):
    """
    List failed company discoveries.

    GET /api/admin/companies/failed-discoveries/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import FailedCompanyDiscovery

    failures = FailedCompanyDiscovery.objects.filter(resolved=False).order_by('-last_attempted_at')[:50]

    results = []
    for f in failures:
        results.append({
            'id': f.id,
            'company_name': f.company_name,
            'website_url': f.website_url,
            'failure_reason': f.failure_reason,
            'attempts': f.attempts,
            'last_attempted_at': f.last_attempted_at,
            'resolved': f.resolved,
        })

    return Response({'results': results})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scraping_job(request, job_id):
    """
    Get details of a specific scraping job.

    GET /api/admin/companies/scraping-jobs/<job_id>/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import ScrapingJob

    try:
        job = ScrapingJob.objects.get(id=job_id)
    except ScrapingJob.DoesNotExist:
        return Response(
            {'error': 'Scraping job not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'id': job.id,
        'company_name_input': job.company_name_input,
        'website_url': job.website_url,
        'status': job.status,
        'started_at': job.started_at,
        'completed_at': job.completed_at,
        'company_id': job.company_id,
        'company_name': job.company.name if job.company else None,
        'data_extracted': job.data_extracted,
        'documents_found': job.documents_found,
        'people_found': job.people_found,
        'news_found': job.news_found,
        'sections_to_process': job.sections_to_process,
        'sections_completed': job.sections_completed,
        'initiated_by': job.initiated_by.username if job.initiated_by else None,
        'error_messages': job.error_messages,
        'error_traceback': job.error_traceback,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_failed_discovery(request, discovery_id):
    """
    Retry a failed company discovery.

    POST /api/admin/companies/failed-discoveries/<discovery_id>/retry/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import FailedCompanyDiscovery, ScrapingJob
    from mcp_servers.company_scraper import scrape_company_website
    import asyncio

    try:
        discovery = FailedCompanyDiscovery.objects.get(id=discovery_id)
    except FailedCompanyDiscovery.DoesNotExist:
        return Response(
            {'error': 'Failed discovery not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Create a new scraping job
    job = ScrapingJob.objects.create(
        company_name_input=discovery.company_name,
        website_url=discovery.website_url,
        status='running',
        started_at=timezone.now(),
        initiated_by=request.user
    )

    # Increment attempt count
    discovery.attempts += 1
    discovery.last_attempted_at = timezone.now()
    discovery.save()

    try:
        # Run the scraper
        result = asyncio.run(scrape_company_website(discovery.website_url))

        data = result['data']
        errors = result['errors']

        # Save the company
        from core.management.commands.onboard_company import Command
        cmd = Command()
        company = cmd._save_company_data(data, discovery.website_url, update_existing=True)

        if company:
            job.company = company
            job.status = 'success'
            job.completed_at = timezone.now()
            job.data_extracted = data
            job.documents_found = len(data.get('documents', []))
            job.people_found = len(data.get('people', []))
            job.news_found = len(data.get('news', []))
            job.sections_completed = ['all']
            job.error_messages = errors
            job.save()

            # Mark discovery as resolved
            discovery.resolved = True
            discovery.save()

            return Response({
                'success': True,
                'company_id': company.id,
                'company_name': company.name,
                'job_id': job.id,
            })

    except Exception as e:
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_messages = [str(e)]
        job.error_traceback = str(e)
        job.save()

        discovery.failure_reason = str(e)
        discovery.save()

        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# GLOSSARY VIEWSET
# ============================================================================

class GlossaryTermViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for mining glossary terms
    Provides read-only access to glossary (superuser can edit via admin)
    """
    queryset = GlossaryTerm.objects.all()
    serializer_class = GlossaryTermSerializer
    permission_classes = [permissions.AllowAny]  # Public access for SEO
    filterset_fields = ['category']
    search_fields = ['term', 'definition', 'keywords']
    ordering_fields = ['term', 'created_at', 'category']
    ordering = ['term']  # Default alphabetical ordering

    @action(detail=False, methods=['get'])
    def by_letter(self, request):
        """Get glossary terms grouped by first letter"""
        letter = request.query_params.get('letter', '').upper()
        if not letter or len(letter) != 1:
            return Response(
                {'error': 'Please provide a single letter parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        terms = self.queryset.filter(term__istartswith=letter)
        serializer = self.get_serializer(terms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_term(self, request):
        """Search for a specific term definition (for chatbot)"""
        term = request.query_params.get('term', '')
        if not term:
            return Response(
                {'error': 'Please provide a term parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try exact match first
        glossary_term = self.queryset.filter(term__iexact=term).first()
        if glossary_term:
            serializer = self.get_serializer(glossary_term)
            return Response(serializer.data)

        # Try partial match
        terms = self.queryset.filter(term__icontains=term)[:5]
        if terms:
            serializer = self.get_serializer(terms, many=True)
            return Response({
                'exact_match': False,
                'suggestions': serializer.data
            })

        return Response(
            {'error': 'Term not found', 'term': term},
            status=status.HTTP_404_NOT_FOUND
        )


class GlossaryTermSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user-submitted glossary terms
    - POST: Authenticated users can submit new terms
    - GET: Superusers can view pending submissions
    - PUT/PATCH: Superusers can approve or reject submissions
    """
    queryset = GlossaryTermSubmission.objects.all()
    filterset_fields = ['status', 'submitted_by', 'category']
    search_fields = ['term', 'definition']
    ordering_fields = ['submitted_at', 'term', 'status']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return GlossaryTermSubmissionCreateSerializer
        return GlossaryTermSubmissionSerializer

    def get_permissions(self):
        """
        - Create: Authenticated users
        - List/Retrieve/Update: Superusers only
        """
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        # Regular users can only see their own submissions
        return self.queryset.filter(submitted_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending(self, request):
        """Get all pending submissions (superuser only)"""
        pending_submissions = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending_submissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a submission and create GlossaryTerm (superuser only)"""
        submission = self.get_object()

        if submission.status != 'pending':
            return Response(
                {'error': f'Cannot approve submission with status: {submission.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            approved_term = submission.approve(reviewer=request.user)
            return Response({
                'message': 'Submission approved successfully',
                'approved_term_id': approved_term.id,
                'term': approved_term.term
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a submission (superuser only)"""
        submission = self.get_object()

        if submission.status != 'pending':
            return Response(
                {'error': f'Cannot reject submission with status: {submission.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rejection_reason = request.data.get('reason', 'No reason provided')

        try:
            submission.reject(reviewer=request.user, reason=rejection_reason)
            return Response({
                'message': 'Submission rejected successfully',
                'term': submission.term,
                'reason': rejection_reason
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# NEWS RELEASE FINANCING FLAG VIEWS
# =============================================================================

class NewsReleaseFlagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reviewing news releases flagged for potential financing announcements.
    Superusers can review and create financing records from flagged news.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Will define serializer inline
    queryset = None  # Will define in get_queryset()

    def get_queryset(self):
        from core.models import NewsReleaseFlag

        # Only superusers can access
        if not self.request.user.is_superuser:
            return NewsReleaseFlag.objects.none()

        # Filter by status if provided
        status_filter = self.request.query_params.get('status', 'pending')
        if status_filter:
            return NewsReleaseFlag.objects.filter(status=status_filter).select_related(
                'news_release__company',
                'reviewed_by',
                'created_financing'
            )

        return NewsReleaseFlag.objects.all().select_related(
            'news_release__company',
            'reviewed_by',
            'created_financing'
        )

    def list(self, request, *args, **kwargs):
        """List all flagged news releases with filtering"""
        flags = self.get_queryset()

        # Build response
        data = []
        for flag in flags:
            data.append({
                'id': flag.id,
                'company_name': flag.news_release.company.name,
                'company_id': flag.news_release.company.id,
                'news_release_id': flag.news_release.id,
                'news_title': flag.news_release.title,
                'news_url': flag.news_release.url,
                'news_date': flag.news_release.release_date,
                'detected_keywords': flag.detected_keywords,
                'status': flag.status,
                'flagged_at': flag.flagged_at,
                'reviewed_by': flag.reviewed_by.username if flag.reviewed_by else None,
                'reviewed_at': flag.reviewed_at,
                'created_financing_id': flag.created_financing.id if flag.created_financing else None,
                'review_notes': flag.review_notes
            })

        return Response(data)

    @action(detail=True, methods=['post'], url_path='create-financing')
    def create_financing(self, request, pk=None):
        """
        Create a Financing record from a flagged news release.
        Marks the flag as 'reviewed_financing'.
        """
        from core.models import NewsReleaseFlag, Financing
        from decimal import Decimal
        from datetime import datetime

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get financing details from request
        financing_data = request.data

        try:
            # Parse announced date
            announced_date = financing_data.get('announced_date')
            if isinstance(announced_date, str):
                announced_date = datetime.strptime(announced_date, '%Y-%m-%d').date()

            # Create Financing record
            financing = Financing.objects.create(
                company=flag.news_release.company,
                financing_type=financing_data.get('financing_type', 'private_placement'),
                status=financing_data.get('status', 'announced'),
                announced_date=announced_date or flag.news_release.release_date,
                amount_raised_usd=Decimal(financing_data.get('amount_raised_usd', 0)),
                price_per_share=Decimal(financing_data.get('price_per_share', 0)) if financing_data.get('price_per_share') else None,
                shares_issued=financing_data.get('shares_issued'),
                has_warrants=financing_data.get('has_warrants', False),
                warrant_strike_price=Decimal(financing_data.get('warrant_strike_price', 0)) if financing_data.get('warrant_strike_price') else None,
                use_of_proceeds=financing_data.get('use_of_proceeds', ''),
                lead_agent=financing_data.get('lead_agent', ''),
                press_release_url=flag.news_release.url,
                notes=financing_data.get('notes', '')
            )

            # Mark flag as reviewed and link financing
            flag.mark_as_financing(
                reviewer=request.user,
                financing_record=financing,
                notes=financing_data.get('review_notes', 'Financing created from flagged news release')
            )

            return Response({
                'message': 'Financing created successfully',
                'financing_id': financing.id,
                'flag_id': flag.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error creating financing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss_flag(self, request, pk=None):
        """
        Dismiss a flagged news release as a false positive.
        """
        from core.models import NewsReleaseFlag

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', 'Dismissed as false positive')

        try:
            flag.dismiss_as_false_positive(
                reviewer=request.user,
                notes=notes
            )

            return Response({
                'message': 'Flag dismissed successfully',
                'flag_id': flag.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error dismissing flag: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='mark-reviewed')
    def mark_reviewed(self, request, pk=None):
        """
        Mark a flagged news release as reviewed after financing was created separately.
        Used when CreateFinancingModal creates financing via /api/financings/ endpoint.
        """
        from core.models import NewsReleaseFlag

        flag = self.get_object()

        if flag.status != 'pending':
            return Response(
                {'error': 'This flag has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('notes', 'Financing created from news flag')

        try:
            # Mark as reviewed (without linking specific financing since it was created separately)
            flag.status = 'reviewed_financing'
            flag.reviewed_by = request.user
            flag.reviewed_at = timezone.now()
            flag.review_notes = notes
            flag.save()

            return Response({
                'message': 'Flag marked as reviewed',
                'flag_id': flag.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error marking flag as reviewed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='close-financing')
    def close_financing(self, request, pk=None):
        """
        Mark an existing financing as closed and remove from the news-flags queue.
        Used when a financing announcement has been confirmed closed.

        The financing record is NOT deleted - it's marked as closed with is_closed=True
        and will appear on the /closed-financings page.
        """
        from core.models import NewsReleaseFlag, Financing

        flag = self.get_object()

        # Check if flag has a linked financing
        if not flag.created_financing:
            return Response(
                {'error': 'This flag does not have an associated financing record. Create a financing first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            financing = flag.created_financing

            # Update closing_date if provided
            closing_date = request.data.get('closing_date')
            if closing_date:
                from datetime import datetime
                if isinstance(closing_date, str):
                    closing_date = datetime.strptime(closing_date, '%Y-%m-%d').date()
                financing.closing_date = closing_date

            # Mark financing as closed
            financing.mark_as_closed(user=request.user)

            # Link the source news flag
            financing.source_news_flag = flag
            financing.save()

            # Update flag notes if provided
            notes = request.data.get('notes', '')
            if notes:
                flag.review_notes = (flag.review_notes or '') + f'\n[Closed] {notes}'
                flag.save()

            return Response({
                'message': 'Financing marked as closed successfully',
                'financing_id': financing.id,
                'flag_id': flag.id,
                'closed_at': financing.closed_at.isoformat() if financing.closed_at else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error closing financing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# CLOSED FINANCINGS API (For /closed-financings page)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def closed_financings_list(request):
    """
    List all closed financings for display on the /closed-financings page.

    GET /api/closed-financings/

    Query Parameters:
    - company: Filter by company name (partial match)
    - financing_type: Filter by financing type
    - date_from: Filter by closing date (YYYY-MM-DD)
    - date_to: Filter by closing date (YYYY-MM-DD)
    - sort_by: Sort field (closed_at, company, amount, closing_date)
    - sort_order: asc or desc (default: desc)

    Access Control:
    - Currently: All authenticated users can access
    - Future: Set CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION = True to restrict to paying users
    """
    from core.models import Financing
    from django.db.models import Q

    # ========== ACCESS CONTROL ==========
    # Set this to True to restrict access to paying users only
    CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION = False

    if CLOSED_FINANCINGS_REQUIRES_SUBSCRIPTION:
        # Check if user has an active subscription
        # TODO: Implement subscription check when payment system is ready
        # Example: if not request.user.has_active_subscription:
        #     return Response({'error': 'Subscription required'}, status=403)
        pass
    # ====================================

    # Base queryset - only closed financings
    queryset = Financing.objects.filter(is_closed=True).select_related(
        'company',
        'closed_by',
        'source_news_flag__news_release'
    )

    # Apply filters
    company_filter = request.query_params.get('company')
    if company_filter:
        queryset = queryset.filter(company__name__icontains=company_filter)

    financing_type_filter = request.query_params.get('financing_type')
    if financing_type_filter:
        queryset = queryset.filter(financing_type=financing_type_filter)

    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(closing_date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(closing_date__lte=date_to)

    # Sorting
    sort_by = request.query_params.get('sort_by', 'closed_at')
    sort_order = request.query_params.get('sort_order', 'desc')

    sort_mapping = {
        'closed_at': 'closed_at',
        'company': 'company__name',
        'amount': 'amount_raised_usd',
        'closing_date': 'closing_date',
        'announced_date': 'announced_date',
    }

    sort_field = sort_mapping.get(sort_by, 'closed_at')
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'

    queryset = queryset.order_by(sort_field)

    # Build response
    data = []
    for financing in queryset:
        # Get source news release URL if available
        source_news_url = None
        source_news_title = None
        source_news_date = None

        if financing.source_news_flag and financing.source_news_flag.news_release:
            source_news_url = financing.source_news_flag.news_release.url
            source_news_title = financing.source_news_flag.news_release.title
            source_news_date = financing.source_news_flag.news_release.release_date
        elif financing.press_release_url:
            source_news_url = financing.press_release_url

        data.append({
            'id': financing.id,
            'company_id': financing.company.id,
            'company_name': financing.company.name,
            'company_ticker': financing.company.ticker_symbol,
            'company_exchange': financing.company.exchange,
            'financing_type': financing.financing_type,
            'financing_type_display': dict(Financing.FINANCING_TYPES).get(financing.financing_type, financing.financing_type),
            'status': financing.status,
            'amount_raised_usd': str(financing.amount_raised_usd) if financing.amount_raised_usd else None,
            'price_per_share': str(financing.price_per_share) if financing.price_per_share else None,
            'shares_issued': financing.shares_issued,
            'has_warrants': financing.has_warrants,
            'warrant_strike_price': str(financing.warrant_strike_price) if financing.warrant_strike_price else None,
            'warrant_expiry_date': financing.warrant_expiry_date.isoformat() if financing.warrant_expiry_date else None,
            'announced_date': financing.announced_date.isoformat() if financing.announced_date else None,
            'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            'closed_at': financing.closed_at.isoformat() if financing.closed_at else None,
            'closed_by': financing.closed_by.username if financing.closed_by else None,
            'lead_agent': financing.lead_agent,
            'use_of_proceeds': financing.use_of_proceeds,
            'source_news_url': source_news_url,
            'source_news_title': source_news_title,
            'source_news_date': source_news_date.isoformat() if source_news_date else None,
            'notes': financing.notes,
        })

    # Get available financing types for filter dropdown
    financing_types = [
        {'value': ft[0], 'label': ft[1]}
        for ft in Financing.FINANCING_TYPES
    ]

    return Response({
        'count': len(data),
        'results': data,
        'financing_types': financing_types,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_closed_financing(request):
    """
    Create a new closed financing directly (for adding historical/past financings).

    POST /api/closed-financings/create/

    Request Body:
    {
        "company_id": 123,
        "financing_type": "private_placement",
        "amount_raised_usd": 5000000,
        "price_per_share": 0.15,
        "shares_issued": 33333333,
        "has_warrants": true,
        "warrant_strike_price": 0.20,
        "warrant_expiry_date": "2026-01-15",
        "announced_date": "2024-12-01",
        "closing_date": "2024-12-15",
        "lead_agent": "Agent Name",
        "use_of_proceeds": "Exploration activities",
        "press_release_url": "https://...",
        "notes": "Optional notes",
        "source_news_flag_id": 456  // Optional - links to news flag and triggers duplicate detection
    }

    When source_news_flag_id is provided:
    - Links the new financing to the news flag
    - Detects and removes duplicate 'announced' financing rounds for the same company
    - Updates the news flag status to 'reviewed_financing'

    Superuser access required.
    """
    from core.models import Financing, Company, NewsReleaseFlag
    from django.utils import timezone
    from decimal import Decimal
    from datetime import timedelta

    # Superuser check
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can add closed financings'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Validate required fields
    company_id = request.data.get('company_id')
    if not company_id:
        return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    financing_type = request.data.get('financing_type')
    if not financing_type:
        return Response({'error': 'financing_type is required'}, status=status.HTTP_400_BAD_REQUEST)

    amount_raised = request.data.get('amount_raised_usd')
    if not amount_raised:
        return Response({'error': 'amount_raised_usd is required'}, status=status.HTTP_400_BAD_REQUEST)

    closing_date = request.data.get('closing_date')
    if not closing_date:
        return Response({'error': 'closing_date is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Get company
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Parse dates
        from datetime import datetime
        if isinstance(closing_date, str):
            closing_date = datetime.strptime(closing_date, '%Y-%m-%d').date()

        announced_date = request.data.get('announced_date')
        if announced_date and isinstance(announced_date, str):
            announced_date = datetime.strptime(announced_date, '%Y-%m-%d').date()
        else:
            announced_date = closing_date  # Default to closing date

        warrant_expiry_date = request.data.get('warrant_expiry_date')
        if warrant_expiry_date and isinstance(warrant_expiry_date, str):
            warrant_expiry_date = datetime.strptime(warrant_expiry_date, '%Y-%m-%d').date()

        # Check for source_news_flag_id to link and handle duplicates
        source_news_flag_id = request.data.get('source_news_flag_id')
        source_news_flag = None
        duplicates_removed = 0

        if source_news_flag_id:
            try:
                source_news_flag = NewsReleaseFlag.objects.get(id=source_news_flag_id)
            except NewsReleaseFlag.DoesNotExist:
                # Log warning but don't fail - the flag might have been deleted
                print(f"Warning: NewsReleaseFlag {source_news_flag_id} not found")

        # Detect and remove duplicate financing rounds if this came from a news flag
        # Look for 'announced' status financings for the same company within a date range
        if source_news_flag:
            # Define date range for duplicate detection (±30 days from closing date)
            date_range_start = closing_date - timedelta(days=30)
            date_range_end = closing_date + timedelta(days=30)

            # Find potential duplicate financings (announced but not closed, same company, similar timeframe)
            duplicate_financings = Financing.objects.filter(
                company=company,
                status='announced',  # Only look at announced (not yet closed) financings
                is_closed=False,
            ).filter(
                # Match by announced_date OR closing_date within range
                announced_date__gte=date_range_start,
                announced_date__lte=date_range_end,
            )

            # Delete duplicates
            duplicates_removed = duplicate_financings.count()
            if duplicates_removed > 0:
                print(f"Removing {duplicates_removed} duplicate announced financing(s) for {company.name}")
                duplicate_financings.delete()

        # Create the financing
        financing = Financing.objects.create(
            company=company,
            financing_type=financing_type,
            status='closed',
            amount_raised_usd=Decimal(str(amount_raised)),
            price_per_share=Decimal(str(request.data.get('price_per_share', 0))) if request.data.get('price_per_share') else None,
            shares_issued=request.data.get('shares_issued'),
            has_warrants=request.data.get('has_warrants', False),
            warrant_strike_price=Decimal(str(request.data.get('warrant_strike_price', 0))) if request.data.get('warrant_strike_price') else None,
            warrant_expiry_date=warrant_expiry_date,
            announced_date=announced_date,
            closing_date=closing_date,
            lead_agent=request.data.get('lead_agent', ''),
            use_of_proceeds=request.data.get('use_of_proceeds', ''),
            press_release_url=request.data.get('press_release_url', ''),
            notes=request.data.get('notes', ''),
            # Mark as closed
            is_closed=True,
            closed_at=timezone.now(),
            closed_by=request.user,
            # Link to source news flag if provided
            source_news_flag=source_news_flag,
        )

        # Update the news flag status if it was provided
        if source_news_flag:
            source_news_flag.status = 'reviewed_financing'
            source_news_flag.reviewed_by = request.user
            source_news_flag.reviewed_at = timezone.now()
            source_news_flag.created_financing = financing
            source_news_flag.review_notes = f'Closed financing created directly from flag (Amount: ${amount_raised:,.2f})'
            source_news_flag.save()

        return Response({
            'message': 'Closed financing created successfully',
            'financing': {
                'id': financing.id,
                'company_name': company.name,
                'company_ticker': company.ticker_symbol,
                'financing_type': financing.financing_type,
                'amount_raised_usd': str(financing.amount_raised_usd),
                'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            },
            'duplicates_removed': duplicates_removed,
            'news_flag_updated': source_news_flag is not None,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'Error creating financing: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_closed_financing(request, financing_id):
    """
    Update an existing closed financing.

    PUT/PATCH /api/closed-financings/<id>/update/

    Request Body (all fields optional for PATCH):
    {
        "financing_type": "private_placement",
        "amount_raised_usd": 5000000,
        "price_per_share": 0.15,
        "shares_issued": 33333333,
        "has_warrants": true,
        "warrant_strike_price": 0.20,
        "warrant_expiry_date": "2026-01-15",
        "announced_date": "2024-12-01",
        "closing_date": "2024-12-15",
        "lead_agent": "Agent Name",
        "use_of_proceeds": "Exploration activities",
        "press_release_url": "https://...",
        "notes": "Optional notes"
    }

    Superuser access required.
    """
    from core.models import Financing
    from decimal import Decimal

    # Superuser check
    if not request.user.is_superuser:
        return Response(
            {'error': 'Only superusers can update closed financings'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get the financing
    try:
        financing = Financing.objects.get(id=financing_id)
    except Financing.DoesNotExist:
        return Response({'error': 'Financing not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Parse dates if provided
        from datetime import datetime

        # Update fields if provided
        if 'financing_type' in request.data:
            financing.financing_type = request.data['financing_type']

        if 'amount_raised_usd' in request.data:
            financing.amount_raised_usd = Decimal(str(request.data['amount_raised_usd']))

        if 'price_per_share' in request.data:
            price = request.data['price_per_share']
            financing.price_per_share = Decimal(str(price)) if price else None

        if 'shares_issued' in request.data:
            financing.shares_issued = request.data['shares_issued'] or None

        if 'has_warrants' in request.data:
            financing.has_warrants = request.data['has_warrants']

        if 'warrant_strike_price' in request.data:
            price = request.data['warrant_strike_price']
            financing.warrant_strike_price = Decimal(str(price)) if price else None

        if 'warrant_expiry_date' in request.data:
            date_str = request.data['warrant_expiry_date']
            if date_str and isinstance(date_str, str):
                financing.warrant_expiry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                financing.warrant_expiry_date = None

        if 'announced_date' in request.data:
            date_str = request.data['announced_date']
            if date_str and isinstance(date_str, str):
                financing.announced_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if 'closing_date' in request.data:
            date_str = request.data['closing_date']
            if date_str and isinstance(date_str, str):
                financing.closing_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if 'lead_agent' in request.data:
            financing.lead_agent = request.data['lead_agent'] or ''

        if 'use_of_proceeds' in request.data:
            financing.use_of_proceeds = request.data['use_of_proceeds'] or ''

        if 'press_release_url' in request.data:
            financing.press_release_url = request.data['press_release_url'] or ''

        if 'notes' in request.data:
            financing.notes = request.data['notes'] or ''

        financing.save()

        return Response({
            'message': 'Financing updated successfully',
            'financing': {
                'id': financing.id,
                'company_name': financing.company.name,
                'company_ticker': financing.company.ticker_symbol,
                'financing_type': financing.financing_type,
                'amount_raised_usd': str(financing.amount_raised_usd),
                'closing_date': financing.closing_date.isoformat() if financing.closing_date else None,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error updating financing: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# DOCUMENT PROCESSING SUMMARY DASHBOARD (Superuser Only)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_processing_summary(request):
    """
    Get summary statistics for processed documents from ChromaDB and PostgreSQL.

    GET /api/admin/document-summary/

    Returns aggregate counts of processed documents by type:
    - NI 43-101 Technical Reports
    - Corporate Presentations
    - Fact Sheets
    - News Releases

    Superuser access required.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Superuser access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.db.models import Count, Sum
    from django.utils import timezone
    from core.models import Document, DocumentChunk, DocumentProcessingJob

    try:
        # Get document counts by type from PostgreSQL (Documents that have chunks)
        documents_with_chunks = Document.objects.filter(
            chunks__isnull=False
        ).distinct()

        # Count by document type
        document_type_counts = documents_with_chunks.values('document_type').annotate(
            count=Count('id', distinct=True),
            total_chunks=Count('chunks')
        ).order_by('document_type')

        # Map document types to display names
        type_display_names = {
            'ni43101': 'NI 43-101 Technical Reports',
            'presentation': 'Corporate Presentations',
            'factsheet': 'Fact Sheets',
            'financial_stmt': 'Financial Statements',
            'mda': 'MD&A',
            'annual_report': 'Annual Reports',
            'map': 'Project Maps',
            'other': 'Other Documents',
        }

        # Format document type summary
        document_summary = []
        for item in document_type_counts:
            doc_type = item['document_type']
            document_summary.append({
                'type': doc_type,
                'display_name': type_display_names.get(doc_type, doc_type.title()),
                'document_count': item['count'],
                'chunk_count': item['total_chunks'],
            })

        # Get processing job statistics
        job_stats = DocumentProcessingJob.objects.aggregate(
            total_jobs=Count('id'),
            completed_jobs=Count('id', filter=Q(status='completed')),
            failed_jobs=Count('id', filter=Q(status='failed')),
            pending_jobs=Count('id', filter=Q(status='pending')),
            processing_jobs=Count('id', filter=Q(status='processing')),
            total_chunks_created=Sum('chunks_created'),
        )

        # Get recent processing activity (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_jobs = DocumentProcessingJob.objects.filter(
            completed_at__gte=week_ago,
            status='completed'
        ).count()

        # Get ACTUAL processed documents with chunks, grouped by type
        # This shows real processed documents, not stale job history
        processed_docs_by_type = Document.objects.filter(
            chunks__isnull=False
        ).values('document_type').annotate(
            count=Count('id', distinct=True),
            total_chunks=Count('chunks')
        ).order_by('-total_chunks')

        processed_breakdown = []
        for item in processed_docs_by_type:
            doc_type = item['document_type']
            processed_breakdown.append({
                'type': doc_type,
                'display_name': type_display_names.get(doc_type, doc_type.title() if doc_type else 'Unknown'),
                'count': item['count'],
                'chunks_created': item['total_chunks'] or 0,
            })

        # Get detailed list of processed documents with company info
        processed_documents_detail = []
        processed_docs = Document.objects.filter(
            chunks__isnull=False
        ).select_related('company').annotate(
            chunk_count=Count('chunks')
        ).order_by('-chunk_count').distinct()[:50]

        for doc in processed_docs:
            processed_documents_detail.append({
                'id': doc.id,
                'title': doc.title[:80] + '...' if len(doc.title) > 80 else doc.title,
                'document_type': doc.document_type,
                'display_type': type_display_names.get(doc.document_type, doc.document_type.title() if doc.document_type else 'Unknown'),
                'company_name': doc.company.name if doc.company else 'Unknown',
                'chunk_count': doc.chunk_count,
                'document_date': doc.document_date.isoformat() if doc.document_date else None,
            })

        # Get failed jobs with details for investigation
        failed_jobs_list = DocumentProcessingJob.objects.filter(
            status='failed'
        ).select_related('document').order_by('-created_at')[:20]

        failed_jobs_details = []
        for job in failed_jobs_list:
            failed_jobs_details.append({
                'id': job.id,
                'url': job.url[:100] + '...' if len(job.url) > 100 else job.url,
                'document_type': job.document_type,
                'company_name': job.company_name or 'Unknown',
                'error_message': job.error_message[:200] if job.error_message else 'No error message',
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
            })

        # Get news releases with full text content
        from core.models import NewsRelease
        news_with_content = NewsRelease.objects.exclude(
            full_text__isnull=True
        ).exclude(full_text='').count()

        # Try to get ChromaDB stats if available
        chroma_stats = {
            'document_chunks_collection': 0,
            'news_chunks_collection': 0,
        }

        try:
            from mcp_servers.rag_utils import RAGManager
            rag = RAGManager()
            chroma_stats['document_chunks_collection'] = rag.collection.count()
            chroma_stats['news_chunks_collection'] = rag.news_collection.count()
        except Exception as e:
            # ChromaDB may not be available
            chroma_stats['error'] = str(e)

        # Total documents and chunks
        total_documents = documents_with_chunks.count()
        total_chunks = DocumentChunk.objects.count()

        # Get list of companies with processed documents
        companies_with_docs = Document.objects.filter(
            chunks__isnull=False
        ).values('company__name').annotate(
            doc_count=Count('id', distinct=True)
        ).order_by('-doc_count')[:10]

        return Response({
            'summary': {
                'total_processed_documents': total_documents,
                'total_chunks': total_chunks,
                'news_releases_with_content': news_with_content,
            },
            'by_document_type': document_summary,
            'processed_documents': {
                'by_type': processed_breakdown,
                'detail': processed_documents_detail,
            },
            'processing_jobs': {
                'total': job_stats['total_jobs'] or 0,
                'completed': job_stats['completed_jobs'] or 0,
                'failed': job_stats['failed_jobs'] or 0,
                'pending': job_stats['pending_jobs'] or 0,
                'processing': job_stats['processing_jobs'] or 0,
                'total_chunks_created': job_stats['total_chunks_created'] or 0,
                'completed_last_7_days': recent_jobs,
                'failed_jobs': failed_jobs_details,
            },
            'chromadb': chroma_stats,
            'top_companies': [
                {'company': c['company__name'], 'document_count': c['doc_count']}
                for c in companies_with_docs
            ],
            'generated_at': timezone.now().isoformat(),
        })

    except Exception as e:
        return Response(
            {'error': f'Error generating summary: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
