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

    # Get all active financing rounds with interests
    active_financings = Financing.objects.filter(
        status='open'
    ).prefetch_related('investment_interests')

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
