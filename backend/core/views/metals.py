"""
API Views for GoldVenture Platform
"""

import logging
import requests
from django.conf import settings
from datetime import datetime
import json
from django.core.cache import cache

from rest_framework import viewsets, status, permissions

# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q

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
    from ..models import MetalPrice

    # Check cache first
    cached_data = cache.get('metals_prices')
    if cached_data:
        cached_data['cached'] = True
        return Response(cached_data)

    # Metal display info. `category` lets the frontend group precious metals
    # (the 4-card grid + gold/silver ratio) separately from base/critical
    # minerals. `unit` here is a fallback; stored rows carry their own unit.
    metal_info = {
        'XAU': {'name': 'Gold', 'unit': 'oz', 'category': 'precious'},
        'XAG': {'name': 'Silver', 'unit': 'oz', 'category': 'precious'},
        'XPT': {'name': 'Platinum', 'unit': 'oz', 'category': 'precious'},
        'XPD': {'name': 'Palladium', 'unit': 'oz', 'category': 'precious'},
        'CU': {'name': 'Copper', 'unit': 'lb', 'category': 'base'},
        'NI': {'name': 'Nickel', 'unit': 'lb', 'category': 'base'},
        'LI': {'name': 'Lithium', 'unit': 'T', 'category': 'critical'},
        'CO': {'name': 'Cobalt Hydroxide', 'unit': 'MT', 'category': 'critical'},
        'REE': {'name': 'Rare Earth Elements', 'unit': 'kg', 'category': 'critical'},
        'U': {'name': 'Uranium', 'unit': 'lb', 'category': 'critical'},
    }

    results = []

    # Try to get Kitco scraped data first
    try:
        kitco_prices = MetalPrice.get_latest_prices()
        if kitco_prices:
            for symbol, price_obj in kitco_prices.items():
                info = metal_info.get(symbol, {'name': symbol, 'unit': 'oz', 'category': 'base'})
                results.append({
                    'metal': info['name'],
                    'symbol': symbol,
                    'price': float(price_obj.bid_price),
                    'ask_price': float(price_obj.ask_price),
                    'change_amount': float(price_obj.change_amount),
                    'change_percent': float(price_obj.change_percent),
                    'unit': price_obj.unit or info['unit'],
                    'category': info['category'],
                    'currency': 'USD',
                    'last_updated': price_obj.scraped_at.isoformat(),
                    'source': price_obj.source
                })

            if results:
                response_data = {
                    'metals': results,
                    'timestamp': datetime.now().isoformat(),
                    'cached': False,
                    'source': 'Kitco (scraped)'
                }
                cache.set('metals_prices', response_data, CacheTTL.DEFAULT)
                return Response(response_data)
    except Exception as e:
        logger.error(f"Error fetching Kitco prices: {e}")

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
        cache.set('metals_prices', response_data, CacheTTL.DEFAULT)
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

            response = requests.get(url, params=params, timeout=Timeouts.DEFAULT)
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
                    prev_response = requests.get(prev_url, params=prev_params, timeout=Timeouts.DEFAULT)
                    prev_data = prev_response.json()

                    if 'values' in prev_data and len(prev_data['values']) >= 2:
                        prev_price = float(prev_data['values'][1]['close'])
                        change_percent = ((current_price - prev_price) / prev_price) * 100
                    else:
                        change_percent = 0.0
                except (ValueError, TypeError, ZeroDivisionError, KeyError, IndexError):
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
                    results.append({
                        'metal': info['name'],
                        'symbol': info['symbol'],
                        'price': fallback_prices[info['symbol']],
                        'change_percent': None,  # Don't fabricate price changes
                        'unit': info['unit'],
                        'currency': 'USD',
                        'last_updated': datetime.now().isoformat(),
                        'source': 'Estimated (stale)',
                        'stale': True,
                        'note': 'Real-time data temporarily unavailable'
                    })

        except Exception as e:
            logger.warning(f"Failed to fetch price for {info['name']}: {str(e)}")
            results.append({
                'metal': info['name'],
                'symbol': info['symbol'],
                'price': None,
                'error': 'Price temporarily unavailable'
            })

    response_data = {
        'metals': results,
        'timestamp': datetime.now().isoformat(),
        'cached': False,
        'source': 'Twelve Data (fallback)'
    }

    cache.set('metals_prices', response_data, CacheTTL.DEFAULT)
    return Response(response_data)




@api_view(['GET'])
@permission_classes([AllowAny])
def metal_historical(request, symbol):
    """
    Get historical price data for a specific metal from stored MetalPrice rows.

    GET /api/metals/historical/<symbol>/?days=30

    symbol: XAU, XAG, XPT, XPD
    days: number of days of historical data (default: 30, max: 365)

    Data comes from our own database (Kitco prices scraped twice daily and
    saved to the MetalPrice model) — no external API call. One representative
    point per calendar day (the last scrape of the day) is returned, oldest
    first.
    """
    from ..models import MetalPrice

    try:
        days = int(request.query_params.get('days', 30))
    except (ValueError, TypeError):
        return Response({'error': 'Invalid days parameter'}, status=status.HTTP_400_BAD_REQUEST)
    days = min(days, 365)  # Max 1 year

    valid_symbols = ['XAU', 'XAG', 'XPT', 'XPD', 'CU', 'U', 'CO', 'LI']
    if symbol not in valid_symbols:
        return Response(
            {'error': f'Invalid symbol. Must be one of: {", ".join(valid_symbols)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check cache
    cache_key = f'metal_historical_{symbol}_{days}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        # One representative price per calendar day from our stored data
        daily_rows = MetalPrice.get_daily_series(symbol, days=days)

        historical_data = []
        for row in daily_rows:
            close = float(row.bid_price)
            # We store a daily high/low when available; otherwise fall back to
            # the close so the chart still has consistent OHLC values.
            high = float(row.high_price) if row.high_price is not None else close
            low = float(row.low_price) if row.low_price is not None else close
            historical_data.append({
                'date': row.day.isoformat(),
                'open': close,   # intraday open is not scraped; use the close
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
            })

        response_data = {
            'symbol': symbol,
            'data': historical_data,
            'days': len(historical_data),
            'timestamp': datetime.now().isoformat(),
            'source': 'GoldVenture (stored Kitco data)'
        }

        # Cache for 1 hour
        cache.set(cache_key, response_data, CacheTTL.LONG)

        return Response(response_data)

    except Exception as e:
        logger.error(f"metal_historical error for symbol {symbol}: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve historical data. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

