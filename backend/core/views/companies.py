"""
API Views for GoldVenture Platform
"""

import logging

from rest_framework import viewsets, status, permissions

# Configure logger for views
logger = logging.getLogger(__name__)

from ..constants import CacheTTL, Timeouts

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Max, Q





class FlexiblePagePagination(PageNumberPagination):
    """Custom pagination that allows page_size query parameter"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

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
from claude_integration.client import ClaudeClient
from claude_integration.client_optimized import OptimizedClaudeClient
import requests
from django.conf import settings
from datetime import datetime, timedelta
from django.core.cache import cache




# ============================================================================
# COMPANY VIEWSET
# ============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    """API endpoint for companies"""
    queryset = Company.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow reads, require auth for writes
    pagination_class = FlexiblePagePagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanySerializer

    def get_queryset(self):
        # Filter to active companies only
        # Note: is_deleted field requires migration 0041 to be applied
        queryset = Company.objects.filter(is_active=True)

        # Only show approved companies to non-superusers
        if not (self.request.user and self.request.user.is_superuser):
            queryset = queryset.filter(approval_status='approved')

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

        # Filter by commodity - find companies with projects in specified commodity
        commodity = self.request.query_params.get('commodity')
        if commodity:
            # Support comma-separated commodities for multi-select.
            commodities = [c.strip() for c in commodity.split(',') if c.strip()]
            if commodities:
                # Case-insensitive: `__in` is an exact match, but stored
                # primary_commodity values are lowercase while callers pass
                # title-case labels ("Rare Earths", "Lithium"). That mismatch
                # silently returned zero companies and noindexed the commodity
                # landing pages that depend on this filter.
                commodity_q = Q()
                for c in commodities:
                    commodity_q |= Q(projects__primary_commodity__iexact=c)
                queryset = queryset.filter(commodity_q).distinct()

        # Annotate counts to avoid N+1 in serializers
        queryset = queryset.annotate(
            _project_count=Count('projects', filter=Q(projects__is_active=True)),
            # Date of the company's most recent press release. `updated_at` is
            # useless as a freshness signal because the daily scrape rewrites
            # the row whether or not anything changed — 89% of companies carried
            # an updated_at within two days on 2026-08-18. The sitemap needs a
            # date that reflects an actual change to the page.
            _latest_news_date=Max('news_releases__release_date'),
        )

        # For list views, defer heavy text fields not needed in the list response
        if self.action == 'list':
            queryset = queryset.defer('description', 'presentation', 'rejection_reason')

        # Optimize queries to avoid N+1 - prefetch commonly accessed relations
        # This prevents separate queries for each company's projects/news/documents
        queryset = queryset.prefetch_related(
            'projects',
            'news_releases',
            'documents',
            'financings',
        )

        return queryset.order_by('name')

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects for a company"""
        company = self.get_object()
        projects = company.projects.filter(is_active=True)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_description(self, request, pk=None):
        """
        Update company description.

        PATCH /api/companies/{id}/update_description/

        Only allowed for:
        - Superusers (is_superuser=True)
        - Company representatives (user.company == this company)

        Request body:
        {
            "description": "New company description text..."
        }
        """
        company = self.get_object()
        user = request.user

        # Check authorization
        is_authorized = (
            user.is_superuser or
            (user.company and user.company.id == company.id)
        )

        if not is_authorized:
            return Response(
                {'error': 'You do not have permission to edit this company description.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request data
        description = request.data.get('description')
        if description is None:
            return Response(
                {'error': 'Description field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the description
        company.description = description
        company.save(update_fields=['description', 'updated_at'])

        return Response({
            'success': True,
            'description': company.description,
            'message': 'Company description updated successfully.'
        })

    @action(detail=True, methods=['get'])
    def can_edit(self, request, pk=None):
        """
        Check if the current user can edit this company.

        GET /api/companies/{id}/can_edit/

        Returns:
        {
            "can_edit": true/false,
            "reason": "superuser" | "company_representative" | null
        }
        """
        company = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response({
                'can_edit': False,
                'reason': None
            })

        if user.is_superuser:
            return Response({
                'can_edit': True,
                'reason': 'superuser'
            })

        if user.company and user.company.id == company.id:
            return Response({
                'can_edit': True,
                'reason': 'company_representative'
            })

        return Response({
            'can_edit': False,
            'reason': None
        })

    def create(self, request, *args, **kwargs):
        """
        Submit a company for approval.

        POST /api/companies/

        Requires authentication. Companies submitted by users will have approval_status='pending_approval'
        and must be approved by a superuser before becoming visible to the public.
        """
        logger.debug(f"CompanyViewSet.create called with data: {request.data}")

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to submit a company.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validate required fields
        name = request.data.get('name', '').strip()
        website_url = request.data.get('website_url', '').strip()
        presentation = request.data.get('presentation', '').strip()
        company_size = request.data.get('company_size', '').strip()
        industry = request.data.get('industry', '').strip()
        location = request.data.get('location', '').strip()
        contact_email = request.data.get('contact_email', '').strip()
        brief_description = request.data.get('brief_description', '').strip()

        errors = {}

        # Validate name
        if not name or len(name) < 2 or len(name) > 100:
            errors['name'] = ['Company name must be between 2 and 100 characters.']

        # Auto-add https:// to website URL if missing
        if website_url and not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url

        # Validate conditional: website OR presentation (200+ chars)
        if not website_url and (not presentation or len(presentation) < 200):
            errors['_conditional'] = ['Please provide either a website URL or a detailed company presentation (200+ characters).']

        # Validate website URL format if provided
        if website_url and len(website_url) > 255:
            errors['website_url'] = ['Website URL must be 255 characters or less.']

        # Validate presentation length if provided
        if presentation and len(presentation) > 2000:
            errors['presentation'] = ['Company presentation must be 2000 characters or less.']

        # Validate company size
        valid_sizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']
        if not company_size or company_size not in valid_sizes:
            errors['company_size'] = [f'Company size must be one of: {", ".join(valid_sizes)}']

        # Validate industry
        if not industry or len(industry) < 2 or len(industry) > 100:
            errors['industry'] = ['Industry must be between 2 and 100 characters.']

        # Validate location
        if not location or len(location) < 2 or len(location) > 100:
            errors['location'] = ['Location must be between 2 and 100 characters.']

        # Validate contact email
        if not contact_email:
            errors['contact_email'] = ['Contact email is required.']
        elif len(contact_email) > 255:
            errors['contact_email'] = ['Contact email must be 255 characters or less.']
        elif '@' not in contact_email or '.' not in contact_email:
            errors['contact_email'] = ['Please provide a valid email address.']

        # Validate brief description
        if not brief_description or len(brief_description) < 100 or len(brief_description) > 2000:
            errors['brief_description'] = ['Brief description must be between 100 and 2000 characters.']

        # Check for duplicate company name (case-insensitive) in approved/pending status
        if name:
            existing = Company.objects.filter(
                name__iexact=name,
                approval_status__in=['approved', 'pending_approval']
            ).exists()
            if existing:
                errors['name'] = ['A company with this name already exists or is pending approval.']

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Create the company with pending_approval status
        try:
            company = Company.objects.create(
                name=name,
                website=website_url,
                presentation=presentation,
                company_size=company_size,
                industry=industry,
                headquarters_city=location,
                contact_email=contact_email,
                brief_description=brief_description,
                approval_status='pending_approval',
                is_user_submitted=True,
                submitted_by=request.user,
                status='private',  # Default company status
                is_active=True
            )
        except Exception as e:
            logger.exception(f"Error creating company: {str(e)}")
            return Response({
                'error': 'Failed to create company. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'id': company.id,
            'status': 'pending_approval',
            'message': 'Company submitted successfully. It will be reviewed by our team.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending')
    def pending_companies(self, request):
        """
        Get all companies pending approval.

        GET /api/companies/pending/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to view pending companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            page = int(request.query_params.get('page', 1))
            limit = min(int(request.query_params.get('limit', 20)), 100)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid pagination parameters'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Company.objects.filter(
            approval_status='pending_approval'
        ).select_related('submitted_by').order_by('-created_at')

        # Pagination
        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        companies = queryset[start:end]

        data = []
        for company in companies:
            data.append({
                'id': company.id,
                'name': company.name,
                'website_url': company.website,
                'presentation': company.presentation,
                'company_size': company.company_size,
                'industry': company.industry,
                'location': company.headquarters_city,
                'contact_email': company.contact_email,
                'brief_description': company.brief_description,
                'created_at': company.created_at.isoformat() if company.created_at else None,
                'submitter': {
                    'id': company.submitted_by.id if company.submitted_by else None,
                    'username': company.submitted_by.username if company.submitted_by else 'Unknown',
                    'email': company.submitted_by.email if company.submitted_by else ''
                }
            })

        return Response({
            'companies': data,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='approve')
    def approve_company(self, request, pk=None):
        """
        Approve a pending company and trigger onboarding/scraping.

        PATCH /api/companies/{id}/approve/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to approve companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()

        if company.approval_status != 'pending_approval':
            return Response(
                {'error': 'This company is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone

        # Approve the company first
        company.approval_status = 'approved'
        company.reviewed_by = request.user
        company.reviewed_at = timezone.now()
        company.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at', 'updated_at'])

        # Trigger onboarding/scraping if website URL is provided
        # IMPORTANT: This is now ASYNC - scraping runs in background via Celery
        # Previously this blocked the HTTP request for 60-120 seconds
        if company.website:
            from ..tasks import scrape_and_save_company_task
            from core.models import ScrapingJob

            # Create scraping job record (will be updated by Celery task)
            job = ScrapingJob.objects.create(
                company_name_input=company.name,
                website_url=company.website,
                status='pending',
                sections_to_process=['all'],
                initiated_by=request.user,
                company=company
            )

            # Queue the scraping task - returns immediately
            # The task will: scrape website, save data, run verification, trigger news scrape
            task = scrape_and_save_company_task.delay(
                job_id=job.id,
                user_id=request.user.id
            )

            return Response({
                'success': True,
                'message': f'{company.name} has been approved. Onboarding is now running in the background.',
                'company_id': company.id,
                'onboarding_status': 'in_progress',
                'scraping_job_id': job.id,
                'task_id': task.id,
                'note': 'Check scraping job status for progress. News scraping will be triggered automatically after onboarding completes.'
            })

        # No website URL provided, just approve
        return Response({
            'success': True,
            'message': f'{company.name} has been approved and is now visible to all users.',
            'company_id': company.id,
            'onboarding_completed': False
        })

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='reject')
    def reject_company(self, request, pk=None):
        """
        Reject a pending company.

        PATCH /api/companies/{id}/reject/

        Request body (optional):
        {
            "reason": "Rejection reason here..."
        }

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to reject companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()

        if company.approval_status != 'pending_approval':
            return Response(
                {'error': 'This company is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone

        rejection_reason = request.data.get('reason', '')
        if rejection_reason and len(rejection_reason) > 500:
            return Response(
                {'error': 'Rejection reason must be 500 characters or less.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        company.approval_status = 'rejected'
        company.rejection_reason = rejection_reason
        company.reviewed_by = request.user
        company.reviewed_at = timezone.now()
        company.save(update_fields=['approval_status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'])

        return Response({
            'success': True,
            'message': f'{company.name} has been rejected.',
            'company_id': company.id
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete a company - only superusers can delete.

        DELETE /api/companies/{id}/

        Only accessible to superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to delete companies.'},
                status=status.HTTP_403_FORBIDDEN
            )

        company = self.get_object()
        company_name = company.name

        # Soft delete by setting is_active=False
        company.is_active = False
        company.save(update_fields=['is_active', 'updated_at'])

        return Response({
            'success': True,
            'message': f'{company_name} has been deleted.'
        }, status=status.HTTP_200_OK)

