"""
API Views for GoldVenture Platform
"""

import logging

from rest_framework import viewsets, status, permissions

from ..models import (
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
    # Additional models for this module
    User,

)

from ..serializers import (
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


# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q





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

        response = requests.get(url, headers=headers, timeout=Timeouts.DEFAULT)
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
    Fetch real-time stock quote from Yahoo Finance using direct API.
    The yfinance library has issues with some Canadian stocks, so we use
    direct HTTP requests to the Yahoo Finance API instead.
    Returns dict with quote data or error.
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}'
        params = {'interval': '1d', 'range': '5d'}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        response = requests.get(url, params=params, headers=headers, timeout=Timeouts.DEFAULT)
        data = response.json()

        # Check for valid response
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            error_msg = data.get('chart', {}).get('error', {}).get('description', 'No data found')
            return {'error': f'Yahoo Finance: {error_msg}'}

        result = data['chart']['result'][0]
        meta = result.get('meta', {})

        price = meta.get('regularMarketPrice', 0)
        if not price or price <= 0:
            return {'error': f'No price data for {ticker_symbol}'}

        previous_close = meta.get('chartPreviousClose', price)
        change = price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0

        volume = meta.get('regularMarketVolume', 0)
        day_high = meta.get('regularMarketDayHigh', price)
        day_low = meta.get('regularMarketDayLow', price)

        return {
            'price': round(float(price), 4),
            'previous_close': round(float(previous_close), 4),
            'change': round(float(change), 4),
            'change_percent': round(float(change_percent), 2),
            'volume': int(volume) if volume else 0,
            'day_high': round(float(day_high), 4),
            'day_low': round(float(day_low), 4),
            'source': 'yahoo_finance'
        }
    except requests.RequestException as e:
        return {'error': f'Yahoo Finance request error: {str(e)}'}
    except (KeyError, ValueError, TypeError) as e:
        return {'error': f'Yahoo Finance parse error: {str(e)}'}




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

    # Validate ticker symbol exists
    if not company.ticker_symbol:
        return Response(
            {'error': 'No ticker symbol configured for this company'},
            status=status.HTTP_400_BAD_REQUEST
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

    # Normalize exchange variations to standard codes
    if exchange_upper in ('TSXV', 'TSX VENTURE', 'TSX-V', 'TSXVENTURE'):
        yahoo_ticker = f"{ticker}.V"
        av_ticker = f"{ticker}.V"
        exchange_code = 'TSXV'
    elif exchange_upper in ('TSX', 'TORONTO', 'TORONTO STOCK EXCHANGE'):
        yahoo_ticker = f"{ticker}.TO"
        av_ticker = f"{ticker}.TO"
        exchange_code = 'TSX'
    elif exchange_upper in ('CSE', 'CANADIAN SECURITIES EXCHANGE'):
        yahoo_ticker = f"{ticker}.CN"
        av_ticker = f"{ticker}.CN"
        exchange_code = 'CSE'
    elif exchange_upper in ('ASX', 'AUSTRALIAN SECURITIES EXCHANGE'):
        yahoo_ticker = f"{ticker}.AX"
        av_ticker = f"{ticker}.AX"
        exchange_code = 'ASX'
    elif exchange_upper in ('AIM', 'LSE', 'LONDON STOCK EXCHANGE'):
        yahoo_ticker = f"{ticker}.L"
        av_ticker = f"{ticker}.L"
        exchange_code = exchange_upper
    elif exchange_upper in ('NYSE', 'NASDAQ', 'AMEX', 'OTC', 'OTCQX', 'OTCQB'):
        yahoo_ticker = ticker  # US stocks don't need suffix
        av_ticker = ticker
        exchange_code = exchange_upper
    else:
        yahoo_ticker = ticker
        av_ticker = ticker
        exchange_code = exchange_upper

    logger.debug(
        f"Stock quote lookup: {company.name} - raw exchange='{company.exchange}' "
        f"normalized='{exchange_code}' yahoo_ticker='{yahoo_ticker}'"
    )

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
    if exchange_code in ['CSE', 'TSXV', 'TSX']:
        stockwatch_result = _get_stockwatch_quote(ticker, exchange_code)

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
    if exchange_code != 'CSE':
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
        cache.set(cache_key, response_data, CacheTTL.SHORT)
        return Response(response_data)

    # No data available from any source
    logger.warning(
        f"Stock quote failed for {company.name} ({company.ticker_symbol}:{company.exchange}). "
        f"Yahoo: {yahoo_result.get('error', 'N/A')}"
    )
    return Response(
        {
            'error': 'Unable to fetch stock data',
            'ticker': company.ticker_symbol,
            'exchange': company.exchange,
            'details': f"Try setting ticker to format like 'XYZ.V' for TSXV or 'XYZ.TO' for TSX"
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


# ============================================================================
# CLAUDE CHAT API
# ============================================================================

import re

# Prompt injection patterns to detect and block
PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)',
    r'disregard\s+(all\s+)?(previous|prior|above)',
    r'forget\s+(all\s+)?(previous|prior|above|your)\s+(instructions|rules|context)',
    r'new\s+instructions?\s*:',
    r'system\s*:\s*you\s+are',
    r'you\s+are\s+now\s+a',
    r'act\s+as\s+if\s+you\s+(are|were)',
    r'pretend\s+(you\s+)?(are|were|to\s+be)',
    r'override\s+(your\s+)?(instructions|rules|guidelines)',
    r'(reveal|show|output|print)\s+(your\s+)?(system\s+)?prompt',
    r'what\s+(is|are)\s+your\s+(system\s+)?prompt',
]

