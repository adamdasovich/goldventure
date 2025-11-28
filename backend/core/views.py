"""
API Views for GoldVenture Platform
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q

from .models import (
    Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, MarketData, NewsRelease, Document
)
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,
    ProjectSerializer, ProjectDetailSerializer,
    ResourceEstimateSerializer, EconomicStudySerializer,
    FinancingSerializer, InvestorSerializer,
    MarketDataSerializer, NewsReleaseSerializer, DocumentSerializer
)
from claude_integration.client import ClaudeClient
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
    Get current precious metals prices from Alpha Vantage.

    GET /api/metals/prices/

    Returns prices for Gold (XAU), Silver (XAG), Platinum (XPT), Palladium (XPD)
    Data is cached for 5 minutes to avoid excessive API calls.
    """

    # Check cache first
    cached_data = cache.get('metals_prices')
    if cached_data:
        cached_data['cached'] = True
        return Response(cached_data)

    api_key = getattr(settings, 'TWELVE_DATA_API_KEY', None)
    if not api_key:
        return Response(
            {'error': 'Twelve Data API key not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    metals = {
        'XAU/USD': {'name': 'Gold', 'symbol': 'XAU', 'unit': 'oz'},
        'XAG/USD': {'name': 'Silver', 'symbol': 'XAG', 'unit': 'oz'},
        'XPT/USD': {'name': 'Platinum', 'symbol': 'XPT', 'unit': 'oz'},
        'XPD/USD': {'name': 'Palladium', 'symbol': 'XPD', 'unit': 'oz'}
    }

    results = []

    for symbol_pair, info in metals.items():
        try:
            # Twelve Data API endpoint for commodities
            url = "https://api.twelvedata.com/price"
            params = {
                'symbol': symbol_pair,
                'apikey': api_key
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'price' in data:
                current_price = float(data['price'])

                # Get previous day's price for change calculation
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
                # API error or requires paid plan - use fallback mock data
                error_msg = data.get('message', data.get('note', 'Unknown error'))

                # Fallback to approximate prices for metals not in free tier
                fallback_prices = {
                    'XAG': 31.50,    # Silver
                    'XPT': 960.00,   # Platinum
                    'XPD': 1030.00   # Palladium
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
                        'source': 'Estimated (requires paid API tier)',
                        'note': 'Upgrade to paid plan for real-time data'
                    })
                else:
                    results.append({
                        'metal': info['name'],
                        'symbol': info['symbol'],
                        'price': None,
                        'error': error_msg
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
        'cached': False
    }

    # Cache for 5 minutes
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
        "system_prompt": "..."  # optional
    }
    """

    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    system_prompt = request.data.get('system_prompt')

    if not message:
        return Response(
            {'error': 'message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Initialize Claude client
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
    }
    """

    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])

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

You have access to comprehensive company data including:
- Projects and resource estimates
- Financial data and market information
- News releases and company updates
- Technical reports and documents

Provide accurate, helpful information about the company. When asked about specific data:
1. Use the available tools to fetch current information
2. Cite your sources and data dates when relevant
3. Be concise but thorough in your responses

Current company context:
- Name: {company.name}
- Ticker: {company.ticker_symbol} ({company.exchange.upper() if company.exchange else 'N/A'})
- CEO: {company.ceo_name if company.ceo_name else 'Not specified'}
- Website: {company.website if company.website else 'Not specified'}
- Headquarters: {company.headquarters_city}, {company.headquarters_country}
"""

        # Initialize Claude client with company context
        client = ClaudeClient(company_id=company_id, user=request.user if request.user.is_authenticated else None)

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
    """

    try:
        client = ClaudeClient()
        tools = client._get_all_tools()

        return Response({
            'tools': tools,
            'count': len(tools)
        })

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
        # Use real web crawler to scrape news releases
        from mcp_servers.website_crawler import crawl_news_releases
        import asyncio

        # Run async crawler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            news_releases = loop.run_until_complete(
                crawl_news_releases(
                    url=company.website,
                    months=6,  # Get news from last 6 months
                    max_depth=2
                )
            )
        finally:
            loop.close()

        if not news_releases:
            # No news releases found
            return Response({
                'status': 'success',
                'message': 'No news releases found on company website',
                'financial_count': 0,
                'non_financial_count': 0,
                'last_scraped': datetime.now().isoformat()
            })

        # Save to database and count by category
        financial_count = 0
        non_financial_count = 0

        for release_data in news_releases:
            title = release_data.get('title', '')
            url = release_data.get('url', '')
            date_str = release_data.get('date')

            # Classify as financial or non-financial based on title
            title_lower = title.lower()
            is_financial = any(keyword in title_lower for keyword in ['financial', 'financials', 'financing'])

            # Determine release type
            if is_financial:
                # Financial releases include financial statements, financials, and financing announcements
                release_type = 'financing' if 'financing' in title_lower or 'placement' in title_lower else 'corporate'
                financial_count += 1
            else:
                non_financial_count += 1
                # Try to categorize non-financial releases
                if 'drill' in title_lower or 'assay' in title_lower:
                    release_type = 'drill_results'
                elif 'resource' in title_lower:
                    release_type = 'resource_update'
                elif 'acquisition' in title_lower or 'disposition' in title_lower:
                    release_type = 'acquisition'
                elif 'management' in title_lower or 'appoint' in title_lower:
                    release_type = 'management'
                else:
                    release_type = 'other'

            # Parse date
            if date_str:
                try:
                    release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    release_date = None
            else:
                release_date = None

            # Skip if no URL or date
            if not url or not release_date:
                continue

            # Create or update news release (using URL as unique identifier)
            NewsRelease.objects.update_or_create(
                company=company,
                url=url,
                defaults={
                    'title': title,
                    'release_type': release_type,
                    'release_date': release_date,
                    'summary': '',  # Could be extracted later with Claude or PDF parsing
                    'is_material': is_financial,
                    'full_text': ''  # Could be extracted from PDF later
                }
            )

        # Cache the scrape results for 24 hours
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'financial_count': financial_count,
            'non_financial_count': non_financial_count
        }
        cache.set(cache_key, cache_data, 86400)  # 24 hours

        return Response({
            'status': 'success',
            'message': f'Scraped {len(news_releases)} news releases',
            'financial_count': financial_count,
            'non_financial_count': non_financial_count,
            'last_scraped': datetime.now().isoformat()
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def company_news_releases(request, company_id):
    """
    Get news releases for a company, separated by financial and non-financial.

    GET /api/companies/<company_id>/news-releases/

    Returns:
        {
            "financial": [...5 most recent financial releases...],
            "non_financial": [...5 most recent non-financial releases...],
            "last_updated": "2025-01-15T10:30:00Z"
        }
    """
    try:
        company = Company.objects.get(id=company_id, is_active=True)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get financial news (is_material=True)
    financial_releases = NewsRelease.objects.filter(
        company=company,
        is_material=True
    ).order_by('-release_date')[:5]

    # Get non-financial news (is_material=False)
    non_financial_releases = NewsRelease.objects.filter(
        company=company,
        is_material=False
    ).order_by('-release_date')[:5]

    # Get last scrape time from cache
    cache_key = f'news_scrape_{company_id}'
    last_scrape_data = cache.get(cache_key)
    last_updated = last_scrape_data.get('timestamp') if last_scrape_data else None

    return Response({
        'financial': NewsReleaseSerializer(financial_releases, many=True).data,
        'non_financial': NewsReleaseSerializer(non_financial_releases, many=True).data,
        'last_updated': last_updated,
        'financial_count': financial_releases.count(),
        'non_financial_count': non_financial_releases.count()
    })


# ============================================================================
# COMPANY VIEWSET
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    """API endpoint for companies"""
    queryset = Company.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer

    def get_queryset(self):
        queryset = Company.objects.filter(is_active=True)

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

        return queryset.order_by('name')

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects for a company"""
        company = self.get_object()
        projects = company.projects.filter(is_active=True)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


# ============================================================================
# PROJECT VIEWSET
# ============================================================================

class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for projects"""
    queryset = Project.objects.all()
    permission_classes = [AllowAny]

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
    queryset = Financing.objects.all()
    serializer_class = FinancingSerializer
    permission_classes = [AllowAny]
