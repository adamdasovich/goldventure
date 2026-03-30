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
    # Additional models for this module
    CompanyNews, CompanyDocument, CompanyPerson,

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
# COMPANY AUTO-ONBOARDING ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_company_preview(request):
    """
    Start an async company scrape preview job.
    Returns immediately with a job_id that can be polled for status.

    POST /api/admin/companies/scrape-preview/

    Body:
    - url: Company website URL
    - sections: Optional list of sections to scrape

    Returns:
    - job_id: ID of the scraping job
    - status: 'pending' initially
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    url = request.data.get('url')
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sections = request.data.get('sections')

    from core.models import ScrapingJob
    from core.tasks import scrape_company_website_task

    try:
        # Create a scraping job record
        job = ScrapingJob.objects.create(
            company_name_input=url,
            website_url=url,
            status='pending',
            sections_to_process=sections or ['all'],
            initiated_by=request.user
        )
    except Exception as e:
        logger.error(f"[PREVIEW] Failed to create ScrapingJob: {e}")
        return Response(
            {'error': 'Failed to create scraping job. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Queue the Celery task with separate error handling
    try:
        task = scrape_company_website_task.delay(job.id, sections=sections)
        logger.info(f"[PREVIEW] Task {task.id} queued for ScrapingJob {job.id}")
    except Exception as e:
        # If task queueing fails (e.g., Redis down), mark job as failed
        job.status = 'failed'
        job.error_messages = ['Failed to queue task - task queue unavailable']
        job.completed_at = timezone.now()
        job.save()
        logger.error(f"[PREVIEW] Failed to queue task for job {job.id}: {e}")
        return Response({
            'error': 'Failed to queue scraping task. Task queue may be unavailable.',
            'job_id': job.id,
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'success': True,
        'job_id': job.id,
        'status': 'pending',
        'message': 'Scraping job queued. Poll /api/admin/companies/scraping-jobs/<job_id>/ for status.'
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_company_save(request):
    """
    Scrape and save company data from a website (ASYNC via Celery).

    POST /api/admin/companies/scrape-save/

    Body:
    - url: Company website URL
    - sections: Optional list of sections to scrape
    - update_existing: Boolean, whether to update if company exists

    Returns immediately with job_id. Poll /api/admin/companies/scraping-jobs/{job_id}/
    to check status.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    url = request.data.get('url')
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sections = request.data.get('sections')
    update_existing = request.data.get('update_existing', False)

    from core.models import ScrapingJob
    from core.tasks import scrape_and_save_company_task

    # Create scraping job with 'pending' status
    job = ScrapingJob.objects.create(
        company_name_input=url,
        website_url=url,
        status='pending',
        sections_to_process=sections or ['all'],
        initiated_by=request.user
    )

    # Trigger async Celery task with error handling
    try:
        task = scrape_and_save_company_task.delay(
            job_id=job.id,
            update_existing=update_existing,
            user_id=request.user.id
        )
        logger.info(f"[ONBOARD] Task {task.id} queued for ScrapingJob {job.id}")
    except Exception as e:
        # If task queueing fails (e.g., Redis down), mark job as failed
        job.status = 'failed'
        job.error_messages = ['Failed to queue task - task queue unavailable']
        job.completed_at = timezone.now()
        job.save()
        logger.error(f"[ONBOARD] Failed to queue task for job {job.id}: {e}")
        return Response({
            'error': 'Failed to queue scraping task. Task queue may be unavailable.',
            'job_id': job.id,
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'success': True,
        'status': 'processing',
        'message': 'Scraping started in background. Poll job status to check completion.',
        'job_id': job.id,
        'task_id': task.id,
        'poll_url': f'/api/admin/companies/scraping-jobs/{job.id}/',
    })




def _infer_commodity_from_name(name: str) -> str:
    """
    Infer the primary commodity from a project name.
    Looks for commodity keywords in the name and returns the appropriate commodity code.
    Defaults to 'gold' if no commodity is detected.
    """
    name_lower = name.lower()

    # Check for specific commodities in order of specificity
    # Check compound commodities first
    if 'gold-silver' in name_lower or 'gold silver' in name_lower:
        return 'gold'  # Gold-silver projects typically listed as gold primary
    if 'silver-gold' in name_lower or 'silver gold' in name_lower:
        return 'silver'

    # Check individual commodities
    if 'silver' in name_lower:
        return 'silver'
    if 'copper' in name_lower:
        return 'copper'
    if 'zinc' in name_lower:
        return 'zinc'
    if 'nickel' in name_lower:
        return 'nickel'
    if 'lithium' in name_lower:
        return 'lithium'
    if 'uranium' in name_lower:
        return 'uranium'
    if 'cobalt' in name_lower:
        return 'cobalt'
    if 'platinum' in name_lower or 'palladium' in name_lower or 'pgm' in name_lower:
        return 'pgm'
    if 'rare earth' in name_lower or 'ree' in name_lower:
        return 'ree'
    if 'base metal' in name_lower:
        return 'base metals'
    if 'gold' in name_lower:
        return 'gold'

    # Default to gold for mining companies
    return 'gold'




def _is_invalid_project_name(name: str) -> bool:
    """
    Check if a project name is invalid (geochemistry data, sample labels, etc.)
    Returns True if the name should be filtered out.
    """
    import re
    name_lower = name.lower()

    # Filter out geochemistry/assay data labels
    # e.g., "Epworth Ag ppm", "Epworth Au ppb", "Epworth Cu pct", "Lake Sed Au Ag"
    geochemistry_patterns = [
        r'\b(ppm|ppb|ppt|g/t|oz/t|pct)\b',  # Unit suffixes
        r'\b(au|ag|cu|pb|zn|ni|co|pt|pd|li|u|mo|w|sn|fe|mn|as|sb|bi|cd|hg)\s+(ppm|ppb|ppt|g/t|pct)\b',  # Element + unit
        r'\bsed\s+(au|ag|cu|pb|zn)',  # Sediment samples like "Lake Sed Au Ag"
        r'\b(lake|stream|soil|rock)\s+sed\b',  # Sediment sample types
    ]

    for pattern in geochemistry_patterns:
        if re.search(pattern, name_lower):
            return True

    return False




def _infer_project_stage_from_name(name: str) -> str:
    """
    Infer the project stage from a project name.
    Looks for stage-related keywords in the name.
    Defaults to 'early_exploration' if no stage is detected.

    Stages: grassroots, early_exploration, advanced_exploration, resource,
            pea, pfs, fs, permitting, development, production
    """
    name_lower = name.lower()

    # Production/Operating indicators
    if any(kw in name_lower for kw in ['mine', 'operation', 'operating', 'producer', 'producing', 'mill']):
        return 'production'

    # Development indicators
    if any(kw in name_lower for kw in ['development', 'construction', 'building']):
        return 'development'

    # Permitting indicators
    if any(kw in name_lower for kw in ['permitting', 'permitted']):
        return 'permitting'

    # PFS indicators (must check before FS — 'pre-feasibility' contains 'feasibility')
    if 'pfs' in name_lower or 'pre-feasibility' in name_lower or 'prefeasibility' in name_lower:
        return 'pfs'

    # Feasibility indicators
    if any(kw in name_lower for kw in ['feasibility', 'fs ']):
        return 'fs'

    # PEA indicators
    if 'pea' in name_lower or 'preliminary economic' in name_lower:
        return 'pea'

    # Resource stage indicators
    if any(kw in name_lower for kw in ['resource', 'deposit']):
        return 'resource'

    # Advanced exploration indicators
    if any(kw in name_lower for kw in ['advanced', 'drill', 'drilling']):
        return 'advanced_exploration'

    # Grassroots indicators
    if any(kw in name_lower for kw in ['grassroots', 'greenfield', 'early stage']):
        return 'grassroots'

    # Default - most scraped projects are exploration stage
    return 'early_exploration'




def _classify_news(title: str) -> dict:
    """
    Classify a news release based on its title.
    Returns a dict with news_type, is_material, financing info, and drill result info.
    """
    import re
    from decimal import Decimal, InvalidOperation

    title_lower = title.lower()
    result = {
        'news_type': 'general',
        'is_material': False,
        'financing_type': 'none',
        'financing_amount': None,
        'financing_price_per_unit': None,
        'has_drill_results': False,
        'best_intercept': '',
    }

    # ===== DRILL RESULTS DETECTION =====
    drill_patterns = [
        r'drill\s*result',
        r'drilling\s*result',
        r'intersect',
        r'intercept',
        r'assay\s*result',
        r'returns?\s+\d+',  # "returns 5.2 g/t"
        r'\d+\.?\d*\s*g/t',  # grade mentions
        r'\d+\.?\d*\s*%\s*(cu|zn|pb|ni)',  # percentage grades
        r'metres?\s+of\s+\d+',  # "10 metres of 5 g/t"
        r'meters?\s+of\s+\d+',
        r'grading\s+\d+',
    ]
    for pattern in drill_patterns:
        if re.search(pattern, title_lower):
            result['news_type'] = 'drill_results'
            result['is_material'] = True
            result['has_drill_results'] = True
            # Try to extract best intercept
            intercept_match = re.search(
                r'(\d+\.?\d*)\s*(m|metres?|meters?)\s*(of|@|at)\s*(\d+\.?\d*)\s*(g/t|%)',
                title_lower
            )
            if intercept_match:
                result['best_intercept'] = intercept_match.group(0)
            break

    # ===== RESOURCE ESTIMATE DETECTION =====
    resource_patterns = [
        r'resource\s*estimate',
        r'mineral\s*resource',
        r'indicated\s*resource',
        r'inferred\s*resource',
        r'measured\s*resource',
        r'resource\s*update',
        r'ni\s*43-?101',
        r'43-?101',
        r'million\s*(oz|ounces)',
        r'moz',
        r'resource\s*of\s*\d+',
    ]
    if result['news_type'] == 'general':
        for pattern in resource_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'resource_estimate'
                result['is_material'] = True
                break

    # ===== FINANCING DETECTION =====
    financing_patterns = {
        'private_placement': [
            r'private\s*placement',
            r'non-?brokered',
            r'closes?\s*private',
            r'announces?\s*private',
        ],
        'bought_deal': [
            r'bought\s*deal',
            r'brokered\s*offering',
            r'underwritten\s*offering',
            r'prospectus\s*offering',
        ],
        'flow_through': [
            r'flow-?through',
            r'flow\s*through\s*shares?',
            r'fts\s*financing',
        ],
        'rights_offering': [
            r'rights\s*offering',
            r'rights\s*issue',
        ],
        'warrant_exercise': [
            r'warrant\s*exercise',
            r'exercises?\s*warrants?',
        ],
        'debt': [
            r'debt\s*financing',
            r'loan\s*facility',
            r'credit\s*facility',
            r'convertible\s*debenture',
        ],
    }

    for financing_type, patterns in financing_patterns.items():
        for pattern in patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'financing'
                result['is_material'] = True
                result['financing_type'] = financing_type
                # Try to extract financing amount
                amount_match = re.search(
                    r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|m\b)',
                    title_lower
                )
                if amount_match:
                    try:
                        amount_str = amount_match.group(1).replace(',', '')
                        result['financing_amount'] = Decimal(amount_str) * 1000000
                    except (ValueError, InvalidOperation, AttributeError):
                        pass
                # Try to extract price per unit
                price_match = re.search(
                    r'\$\s*(\d+\.?\d*)\s*per\s*(unit|share)',
                    title_lower
                )
                if price_match:
                    try:
                        result['financing_price_per_unit'] = Decimal(price_match.group(1))
                    except (ValueError, InvalidOperation, AttributeError):
                        pass
                break
        if result['financing_type'] != 'none':
            break

    # ===== ACQUISITION/MERGER DETECTION =====
    acquisition_patterns = [
        r'acqui(re|sition)',
        r'merger',
        r'amalgamat',
        r'take-?over',
        r'business\s*combination',
        r'purchase\s*agreement',
        r'option\s*agreement',
        r'earn-?in',
    ]
    if result['news_type'] == 'general':
        for pattern in acquisition_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'acquisition'
                result['is_material'] = True
                break

    # ===== MANAGEMENT CHANGE DETECTION =====
    management_patterns = [
        r'appoint',
        r'ceo\s*(change|transition|resign|depart)',
        r'new\s*(ceo|cfo|president|director)',
        r'board\s*(change|appointment)',
        r'management\s*change',
        r'executive\s*change',
    ]
    if result['news_type'] == 'general':
        for pattern in management_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'management'
                break

    # ===== EXPLORATION UPDATE =====
    exploration_patterns = [
        r'exploration\s*update',
        r'exploration\s*program',
        r'field\s*program',
        r'sampling\s*result',
        r'geophysic',
        r'survey\s*result',
        r'commence.*drill',
        r'start.*drill',
    ]
    if result['news_type'] == 'general':
        for pattern in exploration_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'exploration'
                break

    # ===== PRODUCTION UPDATE =====
    production_patterns = [
        r'production\s*update',
        r'production\s*result',
        r'quarterly\s*production',
        r'annual\s*production',
        r'gold\s*pour',
        r'first\s*pour',
        r'commercial\s*production',
    ]
    if result['news_type'] == 'general':
        for pattern in production_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'production'
                result['is_material'] = True
                break

    # ===== REGULATORY/PERMITTING =====
    regulatory_patterns = [
        r'permit',
        r'environmental\s*assessment',
        r'eia\b',
        r'regulatory\s*approv',
        r'license\s*grant',
        r'licence\s*grant',
    ]
    if result['news_type'] == 'general':
        for pattern in regulatory_patterns:
            if re.search(pattern, title_lower):
                result['news_type'] = 'regulatory'
                break

    return result




def _save_scraped_company_data(data: dict, source_url: str, update_existing: bool, user) -> 'Company':
    """Helper function to save scraped data to database."""
    from core.models import (
        Company, Project, CompanyPerson, CompanyDocument, CompanyNews, DocumentProcessingJob,
        NewsRelease, NewsReleaseFlag
    )

    # Validate scraped data using Claude-powered validation
    # This filters out invalid projects, news with date-only titles, and garbage descriptions
    try:
        from core.claude_validator import validate_scraped_data
        data = validate_scraped_data(data, source_url)
    except Exception as e:
        logger.warning(f"Claude validation failed, using raw data: {e}")

    company_data = data.get('company', {})

    if not company_data.get('name'):
        raise Exception("No company name extracted - cannot create record")

    # Check for existing company
    existing_company = None
    if company_data.get('ticker_symbol'):
        existing_company = Company.objects.filter(
            ticker_symbol__iexact=company_data['ticker_symbol']
        ).first()

    if not existing_company:
        existing_company = Company.objects.filter(
            name__iexact=company_data['name']
        ).first()

    if existing_company and not update_existing:
        return existing_company

    # Prepare company fields with length truncation to prevent DB errors
    company_fields = {
        'name': (company_data.get('name') or '')[:200],
        'legal_name': (company_data.get('legal_name') or company_data.get('name') or '')[:200],
        'ticker_symbol': (company_data.get('ticker_symbol') or '')[:10],
        'description': (company_data.get('description') or '')[:2000],
        'tagline': (company_data.get('tagline') or '')[:500],
        'logo_url': (company_data.get('logo_url') or '')[:200],
        'website': source_url[:200],
        'source_website_url': source_url[:200],
        'auto_populated': True,
        'last_scraped_at': timezone.now(),
        # Contact info
        'ir_contact_email': (company_data.get('ir_contact_email') or '')[:254],
        'general_email': (company_data.get('general_email') or '')[:254],
        'media_email': (company_data.get('media_email') or '')[:254],
        'general_phone': (company_data.get('general_phone') or '')[:30],
        'street_address': (company_data.get('street_address') or '')[:300],
        # Social media
        'linkedin_url': (company_data.get('linkedin_url') or '')[:200],
        'twitter_url': (company_data.get('twitter_url') or '')[:200],
        'facebook_url': (company_data.get('facebook_url') or '')[:200],
        'youtube_url': (company_data.get('youtube_url') or '')[:200],
    }

    # Map exchange
    exchange_map = {
        'TSX': 'tsx', 'TSXV': 'tsxv', 'TSX-V': 'tsxv',
        'CSE': 'cse', 'OTC': 'otc', 'ASX': 'asx', 'AIM': 'aim',
    }
    if company_data.get('exchange'):
        company_fields['exchange'] = exchange_map.get(company_data['exchange'].upper(), 'other')

    # Market data
    if company_data.get('market_cap_usd'):
        company_fields['market_cap_usd'] = company_data['market_cap_usd']
    if company_data.get('shares_outstanding'):
        company_fields['shares_outstanding'] = company_data['shares_outstanding']

    # Set status
    if company_fields.get('ticker_symbol') and company_fields.get('exchange'):
        company_fields['status'] = 'public'
    else:
        company_fields['status'] = 'private'

    # Create or update company
    if existing_company:
        for field, value in company_fields.items():
            if value:
                setattr(existing_company, field, value)
        existing_company.save()
        company = existing_company
    else:
        company = Company.objects.create(**company_fields)

    # Calculate completeness score
    company.calculate_completeness_score()
    company.save()

    # Save people
    for i, person_data in enumerate(data.get('people', [])):
        CompanyPerson.objects.update_or_create(
            company=company,
            full_name=person_data.get('full_name', '')[:200],
            defaults={
                'role_type': person_data.get('role_type', 'executive'),
                'title': person_data.get('title', '')[:200],
                'biography': person_data.get('biography', ''),
                'photo_url': person_data.get('photo_url', '')[:200],
                'linkedin_url': person_data.get('linkedin_url', '')[:200],
                'source_url': person_data.get('source_url', '')[:200],
                'extracted_at': timezone.now(),
                'display_order': i,
            }
        )

    # Save documents and create processing jobs for key document types
    from core.models import DocumentProcessingJob
    processing_job_types = ['ni43101', 'pea', 'presentation', 'fact_sheet']
    processing_jobs_created = []

    # IMPORTANT: Filter documents to only keep the most recent of each type
    # Old presentations and reports are not useful - investors want current info
    documents = data.get('documents', [])

    # Sort by year (newest first) if available, then by title containing year
    def get_doc_year(doc):
        # Try explicit year field
        if doc.get('year'):
            return int(doc['year'])
        # Try to extract year from title or URL
        import re
        text = f"{doc.get('title', '')} {doc.get('source_url', '')}"
        years = re.findall(r'20[12]\d', text)
        if years:
            return max(int(y) for y in years)
        return 0

    documents.sort(key=get_doc_year, reverse=True)

    # Filter to keep only most recent documents by type
    filtered_docs = []
    seen_types = {'presentation': 0, 'fact_sheet': 0, 'ni43101': 0, 'pea': 0}
    type_limits = {'presentation': 1, 'fact_sheet': 1, 'ni43101': 2, 'pea': 1}  # How many to keep per type

    for doc in documents:
        doc_type = doc.get('document_type', 'other')

        if doc_type in seen_types:
            # Check if we've reached the limit for this type
            if seen_types[doc_type] < type_limits.get(doc_type, 1):
                filtered_docs.append(doc)
                seen_types[doc_type] += 1
        else:
            # Keep other document types (news_release, financial_statement, etc.)
            filtered_docs.append(doc)

    logger.info(f"Filtered documents: {len(filtered_docs)} from {len(documents)} total")
    for doc_type, count in seen_types.items():
        if count > 0:
            logger.debug(f"  - {doc_type}: {count} (limit: {type_limits.get(doc_type, 1)})")

    for doc_data in filtered_docs:
        doc_type = doc_data.get('document_type', 'other')
        source_url = doc_data.get('source_url', '')

        # Skip documents with URLs that are too long (max 200 chars for source_url field)
        if len(source_url) > 200:
            continue

        # Save document record
        CompanyDocument.objects.update_or_create(
            company=company,
            source_url=source_url,
            defaults={
                'document_type': doc_type,
                'title': doc_data.get('title', 'Untitled')[:500],  # Truncate title to max length
                'year': doc_data.get('year'),
                'extracted_at': timezone.now(),
            }
        )

        # Create document processing job for key document types (if PDF)
        if doc_type in processing_job_types and source_url and '.pdf' in source_url.lower():
            # Check if job already exists for this URL
            existing_job = DocumentProcessingJob.objects.filter(url=source_url).first()
            if not existing_job:
                job = DocumentProcessingJob.objects.create(
                    url=source_url,
                    document_type=doc_type,
                    company_name=company.name,
                    status='pending',
                    created_by=user,
                )
                processing_jobs_created.append({
                    'id': job.id,
                    'type': doc_type,
                    'url': source_url
                })

    # Store processing jobs info for later use
    data['_processing_jobs_created'] = processing_jobs_created

    # Set Company.presentation field from first presentation document
    # This ensures the presentation URL is accessible via the Company model directly
    presentation_doc = CompanyDocument.objects.filter(
        company=company,
        document_type='presentation'
    ).order_by('-year', '-created_at').first()
    if presentation_doc and presentation_doc.source_url and not company.presentation:
        company.presentation = presentation_doc.source_url
        company.save(update_fields=['presentation'])
        logger.info(f"Set company.presentation from document: {presentation_doc.source_url}")

    # Save news with classification and document processing
    from datetime import datetime
    news_processing_jobs = []

    # FALLBACK: If company_scraper found no news, use website_crawler which has better extraction
    news_items = data.get('news', [])
    if not news_items and company and company.website:
        try:
            import asyncio
            from mcp_servers.website_crawler import crawl_news_releases
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                crawler_news = loop.run_until_complete(crawl_news_releases(company.website, months=12))
                news_items = []
                for item in crawler_news:
                    news_items.append({
                        'title': item.get('title', ''),
                        'source_url': item.get('url', ''),
                        'publication_date': item.get('date'),
                    })
                logger.info(f"website_crawler found {len(news_items)} news items")
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"website_crawler error: {e}")

    for news_item in news_items[:50]:
        pub_date = None
        if news_item.get('publication_date'):
            try:
                pub_date = datetime.strptime(news_item['publication_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        # Skip news without dates
        if not pub_date:
            continue

        news_url = news_item.get('source_url', '')
        news_title = news_item.get('title', 'Untitled')[:500]

        # Skip news items with URLs that are too long (max 200 chars for source_url field)
        if len(news_url) > 200:
            continue

        # Skip items with very short titles
        if len(news_title) < 10:
            continue

        # Skip titles that are just dates (e.g., "January 8, 2026", "December 23, 2025")
        import re
        date_only_pattern = re.compile(
            r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$',
            re.IGNORECASE
        )
        if date_only_pattern.match(news_title.strip()):
            continue

        is_pdf = '.pdf' in news_url.lower()

        # Classify the news item
        classification = _classify_news(news_title)

        # Create or update the news record with classification data
        news_record, created = CompanyNews.objects.update_or_create(
            company=company,
            source_url=news_url,
            defaults={
                'title': news_title,
                'publication_date': pub_date,
                'is_pdf': is_pdf,
                'news_type': classification['news_type'],
                'is_material': classification['is_material'],
                'financing_type': classification['financing_type'],
                'financing_amount': classification['financing_amount'],
                'financing_price_per_unit': classification['financing_price_per_unit'],
                'has_drill_results': classification['has_drill_results'],
                'best_intercept': classification['best_intercept'][:200] if classification['best_intercept'] else '',
            }
        )

        # Create financing flag for superuser review if financing-related AND recent (within 7 days)
        if classification['news_type'] == 'financing' and pub_date:
            # Only flag recent financing news (within 7 days) - older ones are not actionable
            from datetime import timedelta
            cutoff_date = timezone.now().date() - timedelta(days=7)
            is_recent = pub_date >= cutoff_date

            if is_recent:
                financing_keywords = [
                    'private placement', 'financing', 'funding round', 'capital raise',
                    'bought deal', 'equity financing', 'debt financing', 'flow-through',
                    'warrant', 'subscription', 'offering', 'closes', 'tranche',
                    'non-brokered', 'brokered', 'strategic investment', 'strategic partner'
                ]
                title_lower = news_title.lower()
                detected_keywords = [kw for kw in financing_keywords if kw in title_lower]

                if detected_keywords:
                    # Import NewsReleaseFlag here to ensure it's available in this scope
                    from core.models import NewsReleaseFlag
                    # Create NewsRelease record (needed for NewsReleaseFlag)
                    news_release, _ = NewsRelease.objects.get_or_create(
                        company=company,
                        url=news_url,
                        defaults={
                            'title': news_title,
                            'release_date': pub_date,
                            'is_material': True,
                        }
                    )
                    # Create the flag
                    NewsReleaseFlag.objects.get_or_create(
                        news_release=news_release,
                        defaults={
                            'detected_keywords': detected_keywords,
                            'status': 'pending'
                        }
                    )

        # Create DocumentProcessingJob for PDF news releases
        if is_pdf and news_url and not news_record.is_processed:
            existing_job = DocumentProcessingJob.objects.filter(url=news_url).first()
            if not existing_job:
                job = DocumentProcessingJob.objects.create(
                    url=news_url,
                    document_type='news_release',
                    company_name=company.name,
                    project_name='',
                    status='pending',
                    created_by=user,
                )
                news_record.processing_job = job
                news_record.save(update_fields=['processing_job'])
                news_processing_jobs.append({
                    'id': job.id,
                    'type': 'news_release',
                    'url': news_url,
                    'is_material': classification['is_material'],
                })

    # Add news processing jobs to the list
    if news_processing_jobs:
        processing_jobs_created.extend(news_processing_jobs)

    # Save projects
    for project_data in data.get('projects', []):
        if project_data.get('name'):
            project_name = project_data.get('name', '')[:200]

            # Skip invalid project names (geochemistry data, sample labels, etc.)
            if _is_invalid_project_name(project_name):
                continue

            # Check if project already exists
            existing_project = Project.objects.filter(
                company=company,
                name=project_name
            ).first()

            if existing_project:
                # Only update description and location, preserve commodity and stage
                # (to avoid overwriting manual corrections)
                if project_data.get('description'):
                    existing_project.description = (project_data.get('description') or '')[:2000]
                if project_data.get('location'):
                    existing_project.country = (project_data.get('location') or '')[:100]
                existing_project.save()
            else:
                # New project - infer commodity and stage from name
                commodity = _infer_commodity_from_name(project_name)
                stage = _infer_project_stage_from_name(project_name)
                # Use 'Unknown' as default country if not provided (NOT NULL constraint)
                country = (project_data.get('location') or project_data.get('country') or 'Unknown')[:100]
                Project.objects.create(
                    company=company,
                    name=project_name,
                    description=(project_data.get('description') or '')[:2000],
                    country=country,
                    project_stage=stage,
                    primary_commodity=commodity,
                )

    return company




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scraping_jobs(request):
    """
    List scraping jobs with pagination.

    GET /api/admin/companies/scraping-jobs/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import ScrapingJob

    jobs = ScrapingJob.objects.select_related('company', 'initiated_by').order_by('-created_at')[:50]

    results = []
    for job in jobs:
        results.append({
            'id': job.id,
            'company_name_input': job.company_name_input,
            'website_url': job.website_url,
            'status': job.status,
            'company_id': job.company_id,
            'company_name': job.company.name if job.company else None,
            'documents_found': job.documents_found,
            'people_found': job.people_found,
            'news_found': job.news_found,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'duration_seconds': job.duration_seconds,
            'initiated_by': job.initiated_by.username if job.initiated_by else None,
            'error_messages': job.error_messages,
        })

    return Response({'results': results})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_failed_discoveries(request):
    """
    List failed company discoveries.

    GET /api/admin/companies/failed-discoveries/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import FailedCompanyDiscovery

    failures = FailedCompanyDiscovery.objects.filter(resolved=False).order_by('-last_attempted_at')[:50]

    results = []
    for f in failures:
        results.append({
            'id': f.id,
            'company_name': f.company_name,
            'website_url': f.website_url,
            'failure_reason': f.failure_reason,
            'attempts': f.attempts,
            'last_attempted_at': f.last_attempted_at,
            'resolved': f.resolved,
        })

    return Response({'results': results})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scraping_job(request, job_id):
    """
    Get details of a specific scraping job.

    GET /api/admin/companies/scraping-jobs/<job_id>/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import ScrapingJob

    try:
        job = ScrapingJob.objects.get(id=job_id)
    except ScrapingJob.DoesNotExist:
        return Response(
            {'error': 'Scraping job not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'id': job.id,
        'company_name_input': job.company_name_input,
        'website_url': job.website_url,
        'status': job.status,
        'started_at': job.started_at,
        'completed_at': job.completed_at,
        'company_id': job.company_id,
        'company_name': job.company.name if job.company else None,
        'data_extracted': job.data_extracted,
        'documents_found': job.documents_found,
        'people_found': job.people_found,
        'news_found': job.news_found,
        'sections_to_process': job.sections_to_process,
        'sections_completed': job.sections_completed,
        'initiated_by': job.initiated_by.username if job.initiated_by else None,
        'error_messages': job.error_messages,
        'error_traceback': job.error_traceback,
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_failed_discovery(request, discovery_id):
    """
    Retry a failed company discovery.

    POST /api/admin/companies/failed-discoveries/<discovery_id>/retry/
    """
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )

    from core.models import FailedCompanyDiscovery, ScrapingJob
    from mcp_servers.company_scraper import scrape_company_website
    import asyncio

    try:
        discovery = FailedCompanyDiscovery.objects.get(id=discovery_id)
    except FailedCompanyDiscovery.DoesNotExist:
        return Response(
            {'error': 'Failed discovery not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Create a new scraping job
    job = ScrapingJob.objects.create(
        company_name_input=discovery.company_name,
        website_url=discovery.website_url,
        status='running',
        started_at=timezone.now(),
        initiated_by=request.user
    )

    # Increment attempt count
    discovery.attempts += 1
    discovery.last_attempted_at = timezone.now()
    discovery.save()

    try:
        # Run the scraper
        result = asyncio.run(scrape_company_website(discovery.website_url))

        data = result['data']
        errors = result['errors']

        # Save the company
        from core.management.commands.onboard_company import Command
        cmd = Command()
        company = cmd._save_company_data(data, discovery.website_url, update_existing=True)

        if company:
            job.company = company
            job.status = 'success'
            job.completed_at = timezone.now()
            job.data_extracted = data
            job.documents_found = len(data.get('documents', []))
            job.people_found = len(data.get('people', []))
            job.news_found = len(data.get('news', []))
            job.sections_completed = ['all']
            job.error_messages = errors
            job.save()

            # Mark discovery as resolved
            discovery.resolved = True
            discovery.save()

            return Response({
                'success': True,
                'company_id': company.id,
                'company_name': company.name,
                'job_id': job.id,
            })

    except Exception as e:
        logger.error(f"retry_failed_discovery error for discovery {discovery_id}: {str(e)}")
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_messages = [str(e)]
        job.error_traceback = str(e)
        job.save()

        discovery.failure_reason = str(e)
        discovery.save()

        return Response(
            {'error': 'Failed to retry discovery. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

