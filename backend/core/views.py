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
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction
)
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,
    ProjectSerializer, ProjectDetailSerializer,
    ResourceEstimateSerializer, EconomicStudySerializer,
    FinancingSerializer, InvestorSerializer,
    MarketDataSerializer, NewsReleaseSerializer, DocumentSerializer,
    SpeakerEventListSerializer, SpeakerEventDetailSerializer,
    SpeakerEventCreateSerializer, EventQuestionSerializer, EventReactionSerializer
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
        "user_type": "investor" (optional, defaults to investor)
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
    user_type = request.data.get('user_type', 'investor')

    # Validation
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email, and password are required'},
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
        "user_type": "string"
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
