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
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement
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
    ProspectorCommissionAgreementSerializer, ProspectorCommissionAgreementCreateSerializer
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

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')

        # Can't inquire on own listing
        if listing.prospector.user == self.request.user:
            raise serializers.ValidationError("You cannot inquire on your own listing")

        # Update listing inquiry count
        listing.inquiries_count += 1
        listing.save(update_fields=['inquiries_count'])

        serializer.save(inquirer=self.request.user)

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
