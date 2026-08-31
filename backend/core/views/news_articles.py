"""
API Views for GoldVenture Platform
"""

import logging
from datetime import timedelta

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
from ..query_guard import guard_query_params

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
# NEWS ARTICLES API
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@guard_query_params("days", "limit", "offset", "source", strict=False)
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

    try:
        limit = min(int(request.query_params.get('limit', 10)), 50)
        offset = int(request.query_params.get('offset', 0))
        days = int(request.query_params.get('days', 7))
    except (ValueError, TypeError):
        return Response({'error': 'Invalid query parameters'}, status=status.HTTP_400_BAD_REQUEST)
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
    from django.db.models import Count, Q

    # Use annotation to avoid N+1 query
    sources = NewsSource.objects.filter(is_active=True).annotate(
        visible_article_count=Count('articles', filter=Q(articles__is_visible=True))
    )

    return Response({
        'sources': [
            {
                'id': source.id,
                'name': source.name,
                'url': source.url,
                'article_count': source.visible_article_count,
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
            except Exception as job_err:
                logger.error(f"Failed to update job status: {job_err}")

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

