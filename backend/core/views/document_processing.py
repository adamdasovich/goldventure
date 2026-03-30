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
# DOCUMENT PROCESSING SUMMARY DASHBOARD (Superuser Only)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_processing_summary(request):
    """
    Get summary statistics for processed documents from ChromaDB and PostgreSQL.

    GET /api/admin/document-summary/

    Returns aggregate counts of processed documents by type:
    - NI 43-101 Technical Reports
    - Corporate Presentations
    - Fact Sheets
    - News Releases

    Superuser access required.
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Superuser access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.db.models import Count, Sum
    from django.utils import timezone
    from core.models import Document, DocumentChunk, DocumentProcessingJob

    try:
        # Get document counts by type from PostgreSQL (Documents that have chunks)
        documents_with_chunks = Document.objects.filter(
            chunks__isnull=False
        ).distinct()

        # Count by document type
        document_type_counts = documents_with_chunks.values('document_type').annotate(
            count=Count('id', distinct=True),
            total_chunks=Count('chunks')
        ).order_by('document_type')

        # Map document types to display names
        type_display_names = {
            'ni43101': 'NI 43-101 Technical Reports',
            'presentation': 'Corporate Presentations',
            'factsheet': 'Fact Sheets',
            'financial_stmt': 'Financial Statements',
            'mda': 'MD&A',
            'annual_report': 'Annual Reports',
            'map': 'Project Maps',
            'other': 'Other Documents',
        }

        # Format document type summary
        document_summary = []
        for item in document_type_counts:
            doc_type = item['document_type']
            document_summary.append({
                'type': doc_type,
                'display_name': type_display_names.get(doc_type, doc_type.title()),
                'document_count': item['count'],
                'chunk_count': item['total_chunks'],
            })

        # Get processing job statistics
        job_stats = DocumentProcessingJob.objects.aggregate(
            total_jobs=Count('id'),
            completed_jobs=Count('id', filter=Q(status='completed')),
            failed_jobs=Count('id', filter=Q(status='failed')),
            pending_jobs=Count('id', filter=Q(status='pending')),
            processing_jobs=Count('id', filter=Q(status='processing')),
            total_chunks_created=Sum('chunks_created'),
        )

        # Get recent processing activity (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_jobs = DocumentProcessingJob.objects.filter(
            completed_at__gte=week_ago,
            status='completed'
        ).count()

        # Get ACTUAL processed documents with chunks, grouped by type
        # This shows real processed documents, not stale job history
        processed_docs_by_type = Document.objects.filter(
            chunks__isnull=False
        ).values('document_type').annotate(
            count=Count('id', distinct=True),
            total_chunks=Count('chunks')
        ).order_by('-total_chunks')

        processed_breakdown = []
        for item in processed_docs_by_type:
            doc_type = item['document_type']
            processed_breakdown.append({
                'type': doc_type,
                'display_name': type_display_names.get(doc_type, doc_type.title() if doc_type else 'Unknown'),
                'count': item['count'],
                'chunks_created': item['total_chunks'] or 0,
            })

        # Get detailed list of processed documents with company info
        processed_documents_detail = []
        processed_docs = Document.objects.filter(
            chunks__isnull=False
        ).select_related('company').annotate(
            chunk_count=Count('chunks')
        ).order_by('-chunk_count').distinct()[:50]

        for doc in processed_docs:
            processed_documents_detail.append({
                'id': doc.id,
                'title': doc.title[:80] + '...' if len(doc.title) > 80 else doc.title,
                'document_type': doc.document_type,
                'display_type': type_display_names.get(doc.document_type, doc.document_type.title() if doc.document_type else 'Unknown'),
                'company_name': doc.company.name if doc.company else 'Unknown',
                'chunk_count': doc.chunk_count,
                'document_date': doc.document_date.isoformat() if doc.document_date else None,
            })

        # Get failed jobs with details for investigation
        failed_jobs_list = DocumentProcessingJob.objects.filter(
            status='failed'
        ).select_related('document').order_by('-created_at')[:20]

        failed_jobs_details = []
        for job in failed_jobs_list:
            failed_jobs_details.append({
                'id': job.id,
                'url': job.url[:100] + '...' if len(job.url) > 100 else job.url,
                'document_type': job.document_type,
                'company_name': job.company_name or 'Unknown',
                'error_message': job.error_message[:200] if job.error_message else 'No error message',
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
            })

        # Get news releases with full text content
        from core.models import NewsRelease
        news_with_content = NewsRelease.objects.exclude(
            full_text__isnull=True
        ).exclude(full_text='').count()

        # Try to get ChromaDB stats if available
        chroma_stats = {
            'document_chunks_collection': 0,
            'news_chunks_collection': 0,
        }

        try:
            from mcp_servers.rag_utils import RAGManager
            rag = RAGManager()
            chroma_stats['document_chunks_collection'] = rag.collection.count()
            chroma_stats['news_chunks_collection'] = rag.news_collection.count()
        except Exception as e:
            # ChromaDB may not be available
            logger.warning(f"ChromaDB stats unavailable: {str(e)}")
            chroma_stats['error'] = 'ChromaDB unavailable'

        # Total documents and chunks
        total_documents = documents_with_chunks.count()
        total_chunks = DocumentChunk.objects.count()

        # Get list of companies with processed documents
        companies_with_docs = Document.objects.filter(
            chunks__isnull=False
        ).values('company__name').annotate(
            doc_count=Count('id', distinct=True)
        ).order_by('-doc_count')[:10]

        return Response({
            'summary': {
                'total_processed_documents': total_documents,
                'total_chunks': total_chunks,
                'news_releases_with_content': news_with_content,
            },
            'by_document_type': document_summary,
            'processed_documents': {
                'by_type': processed_breakdown,
                'detail': processed_documents_detail,
            },
            'processing_jobs': {
                'total': job_stats['total_jobs'] or 0,
                'completed': job_stats['completed_jobs'] or 0,
                'failed': job_stats['failed_jobs'] or 0,
                'pending': job_stats['pending_jobs'] or 0,
                'processing': job_stats['processing_jobs'] or 0,
                'total_chunks_created': job_stats['total_chunks_created'] or 0,
                'completed_last_7_days': recent_jobs,
                'failed_jobs': failed_jobs_details,
            },
            'chromadb': chroma_stats,
            'top_companies': [
                {'company': c['company__name'], 'document_count': c['doc_count']}
                for c in companies_with_docs
            ],
            'generated_at': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error generating document processing summary: {str(e)}")
        return Response(
            {'error': 'Failed to generate summary. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

