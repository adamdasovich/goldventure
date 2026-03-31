"""
API Views for GoldVenture Platform
"""

import logging
import json
import requests
from django.core.cache import cache

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

# Exchange suffix mapping for Yahoo Finance / Alpha Vantage ticker formats
_EXCHANGE_SUFFIXES = {
    'TSXV': '.V', 'TSX VENTURE': '.V', 'TSX-V': '.V', 'TSXVENTURE': '.V',
    'TSX': '.TO', 'TORONTO': '.TO', 'TORONTO STOCK EXCHANGE': '.TO',
    'CSE': '.CN', 'CANADIAN SECURITIES EXCHANGE': '.CN',
    'ASX': '.AX', 'AUSTRALIAN SECURITIES EXCHANGE': '.AX',
    'AIM': '.L', 'LSE': '.L', 'LONDON STOCK EXCHANGE': '.L',
}
# Canonical exchange code mapping
_EXCHANGE_CODES = {
    'TSXV': 'TSXV', 'TSX VENTURE': 'TSXV', 'TSX-V': 'TSXV', 'TSXVENTURE': 'TSXV',
    'TSX': 'TSX', 'TORONTO': 'TSX', 'TORONTO STOCK EXCHANGE': 'TSX',
    'CSE': 'CSE', 'CANADIAN SECURITIES EXCHANGE': 'CSE',
    'ASX': 'ASX', 'AUSTRALIAN SECURITIES EXCHANGE': 'ASX',
}


def _normalize_exchange(exchange: str) -> tuple:
    """Return (yahoo_ticker_suffix, exchange_code) for a given exchange string."""
    upper = exchange.upper() if exchange else ''
    suffix = _EXCHANGE_SUFFIXES.get(upper, '')
    code = _EXCHANGE_CODES.get(upper, upper)
    return suffix, code


def _build_quote_response(company, price, change, change_pct, volume, date_str, source, cache_ttl=300):
    """Build, cache, and return a stock quote response."""
    response_data = {
        'ticker': company.ticker_symbol,
        'exchange': company.exchange,
        'price': price,
        'change': change,
        'change_percent': change_pct,
        'volume': volume,
        'date': date_str,
        'source': source,
        'cached': False,
    }
    cache_key = f'stock_quote_{company.id}'
    cache.set(cache_key, response_data, cache_ttl)
    return Response(response_data)


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
    Tries: cache -> Yahoo Finance -> StockWatch -> Alpha Vantage -> database.
    """
    from datetime import date

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    if not company.ticker_symbol:
        return Response({'error': 'No ticker symbol configured for this company'}, status=status.HTTP_400_BAD_REQUEST)

    # Check cache first (5 minute TTL)
    cache_key = f'stock_quote_{company_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        cached_data['cached'] = True
        return Response(cached_data)

    today = date.today()
    ticker = company.ticker_symbol
    suffix, exchange_code = _normalize_exchange(company.exchange)
    api_ticker = f"{ticker}{suffix}" if suffix else ticker

    logger.debug(f"Stock quote lookup: {company.name} - exchange='{exchange_code}' ticker='{api_ticker}'")

    # 1. Yahoo Finance
    result = _get_yahoo_finance_quote(api_ticker)
    if 'error' not in result and result.get('price', 0) > 0:
        return _build_quote_response(company, result['price'], result['change'],
                                     result['change_percent'], result['volume'], str(today), 'yahoo_finance')

    # 2. StockWatch (Canadian stocks only)
    if exchange_code in ('CSE', 'TSXV', 'TSX'):
        result = _get_stockwatch_quote(ticker, exchange_code)
        if 'error' not in result and result.get('price', 0) > 0:
            return _build_quote_response(company, result['price'], result['change'],
                                         result['change_percent'], result['volume'], str(today), 'stockwatch')

    # 3. Alpha Vantage (not CSE)
    if exchange_code != 'CSE':
        from mcp_servers.alpha_vantage import AlphaVantageServer
        quote_result = AlphaVantageServer(company_id=company_id)._get_quote(api_ticker)
        if 'error' not in quote_result and quote_result.get('price', 0) > 0:
            return _build_quote_response(
                company, quote_result.get('price', 0), quote_result.get('change', 0),
                float(quote_result.get('change_percent', '0')), quote_result.get('volume', 0),
                quote_result.get('latest_trading_day', str(today)), 'alpha_vantage')

    # 4. Database fallback
    market_data = MarketData.objects.filter(company=company, date=today).first()
    if market_data:
        yesterday = MarketData.objects.filter(company=company, date__lt=today).order_by('-date').first()
        change, change_pct = 0.0, 0.0
        if yesterday and yesterday.close_price and yesterday.close_price > 0:
            change = float(market_data.close_price - yesterday.close_price)
            change_pct = (change / float(yesterday.close_price)) * 100
        return _build_quote_response(
            company, float(market_data.close_price), round(change, 4),
            round(change_pct, 2), market_data.volume, str(market_data.date),
            'database_fallback', cache_ttl=CacheTTL.SHORT)

    # No data from any source
    logger.warning(f"Stock quote failed for {company.name} ({ticker}:{exchange_code})")
    return Response(
        {'error': 'Unable to fetch stock data', 'ticker': ticker, 'exchange': company.exchange},
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )

