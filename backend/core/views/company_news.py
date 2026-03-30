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
# NEWS SCRAPING API
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_company_news(request, company_id):
    """
    Scrape and classify company news releases from their website.
    Requires authentication to prevent DoS via repeated scraping.

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
        from ..tasks import scrape_company_news_task

        task = scrape_company_news_task.delay(company_id)

        return Response({
            'status': 'processing',
            'message': 'News scraping started in background',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"scrape_company_news error for company {company_id}: {str(e)}")
        return Response(
            {'error': 'Failed to start news scraping. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
        # SECURITY: Log the actual error but don't expose internal details
        logger.error(f"Task {task_id} failed: {str(task_result.info)}")
        response = {
            'state': task_result.state,
            'error': 'Task processing failed. Please try again later.'
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

    # Get company news from NewsRelease (primary source - updated by daily scraper)
    # The daily scraper (crawl_news_releases) writes to NewsRelease, which has
    # the most up-to-date data. CompanyNews is only populated during onboarding
    # and was stale (missing recent releases like Feb 10th).
    news_releases = NewsRelease.objects.filter(company=company).order_by('-release_date')[:20]
    non_financial_data = []
    last_updated = None

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
    if news_releases.exists():
        latest = news_releases.first()
        last_updated = str(latest.updated_at) if latest and latest.updated_at else None

    return Response({
        'financial': financial_data,
        'non_financial': non_financial_data,
        'last_updated': last_updated,
        'financial_count': len(financial_data),
        'non_financial_count': len(non_financial_data)
    })

