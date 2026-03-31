"""
API Views for GoldVenture Platform
"""

import logging
import requests
import re
import anthropic

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

from claude_integration.client import ClaudeClient
from claude_integration.client_optimized import OptimizedClaudeClient

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


def check_prompt_injection(message: str) -> tuple:
    """
    Check message for potential prompt injection attacks.
    Returns (is_safe, matched_pattern) - is_safe=True means no injection detected.
    """
    if not message:
        return True, None
    message_lower = message.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return False, pattern
    return True, None




def get_or_create_ai_usage(user):
    """Get or create AI usage record for user."""
    from ..models import UserAIUsage
    usage, created = UserAIUsage.objects.get_or_create(user=user)
    return usage




@api_view(['POST'])
@permission_classes([IsAuthenticated])
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

    Rate limited: 50 messages/day, 100k tokens/day per user (configurable).
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

    # Check for prompt injection
    is_safe, matched_pattern = check_prompt_injection(message)
    if not is_safe:
        return Response(
            {'error': 'Message contains disallowed content patterns.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check user AI usage limits
    usage = get_or_create_ai_usage(request.user)
    can_send, limit_error = usage.can_send_message()
    if not can_send:
        return Response(
            {'error': limit_error, 'limit_reached': True},
            status=status.HTTP_429_TOO_MANY_REQUESTS
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

        # Record usage (estimate tokens if not provided)
        tokens_used = result.get('tokens_used', 0) or result.get('usage', {}).get('total_tokens', 1000)
        usage.record_usage(tokens_used)

        # Add usage info to response
        result['usage_remaining'] = {
            'messages_today': usage.messages_today,
            'message_limit': usage.daily_message_limit,
            'tokens_today': usage.tokens_today,
            'token_limit': usage.daily_token_limit,
        }

        return Response(result)

    except anthropic.APIStatusError as e:
        logger.error(f"Claude chat API error for user {request.user.id}: {e.status_code} {str(e)}")
        if e.status_code == 529:
            return Response(
                {'error': 'The AI service is temporarily busy. Please try again in a moment.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        if e.status_code == 429:
            return Response(
                {'error': 'AI rate limit reached. Please wait a minute and try again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return Response(
            {'error': 'An error occurred processing your request. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Claude chat error for user {request.user.id}: {str(e)}")
        return Response(
            {'error': 'An error occurred processing your request. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_chat(request, company_id):
    """
    Handle company-specific Claude chat requests with MCP tool access.

    POST /api/companies/{company_id}/chat/
    {
        "message": "What are the latest news releases?",
        "conversation_history": [...],  # optional
        "optimized": true  # optional - use token-efficient client
    }

    Rate limited: 50 messages/day, 100k tokens/day per user (configurable).
    """

    message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    use_optimized = request.data.get('optimized', True)  # Default to optimized

    if not message:
        return Response(
            {'error': 'message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check for prompt injection
    is_safe, matched_pattern = check_prompt_injection(message)
    if not is_safe:
        return Response(
            {'error': 'Message contains disallowed content patterns.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check user AI usage limits
    usage = get_or_create_ai_usage(request.user)
    can_send, limit_error = usage.can_send_message()
    if not can_send:
        return Response(
            {'error': limit_error, 'limit_reached': True},
            status=status.HTTP_429_TOO_MANY_REQUESTS
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

        # Record usage (estimate tokens if not provided)
        tokens_used = result.get('tokens_used', 0) or result.get('usage', {}).get('total_tokens', 1000)
        usage.record_usage(tokens_used)

        # Add usage info to response
        result['usage_remaining'] = {
            'messages_today': usage.messages_today,
            'message_limit': usage.daily_message_limit,
            'tokens_today': usage.tokens_today,
            'token_limit': usage.daily_token_limit,
        }

        return Response(result)

    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except anthropic.APIStatusError as e:
        logger.error(f"company_chat API error for company {company_id}: {e.status_code} {str(e)}")
        if e.status_code == 529:
            return Response(
                {'error': 'The AI service is temporarily busy. Please try again in a moment.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        if e.status_code == 429:
            return Response(
                {'error': 'AI rate limit reached. Please wait a minute and try again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        return Response(
            {'error': 'An error occurred processing your request. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"company_chat error for company {company_id}: {str(e)}")
        return Response(
            {'error': 'An error occurred processing your request. Please try again.'},
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
        logger.error(f"available_tools error: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve available tools. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

