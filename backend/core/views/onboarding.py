"""
API Views for GoldVenture Platform
"""

import logging
from django.utils import timezone

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

    Fallback only -- company_scraper.score_commodity reads the page itself and
    should be preferred. Returns '' when the name gives no signal; it must not
    guess, because a wrong commodity puts the company on the wrong landing page.

    Whichever commodity is named FIRST wins. Mining convention orders a project
    name by contribution, so "Gold-Copper" is a gold project and "Copper-Gold"
    is a copper one. Fixed-order checking got this backwards: silver was tested
    before copper and gold, so "Cerro Bayo Gold-Silver Project" came out silver
    and "Bright Angel Gold - Copper Project" came out copper.
    """
    import re  # module-level import is absent here; the file imports locally

    name_lower = name.lower()

    # (pattern, commodity). Matched as regexes so a word boundary can be
    # required where a bare substring would over-match.
    #
    # 'ree' needs a boundary. As a bare substring it matches inside "Creek",
    # "Green" and "Three", and because that check once ran before the gold
    # check, "Gold Creek", "Burro Creek Gold" and "Coyote Creek" were all filed
    # as rare earths -- 25 of the 28 ree-tagged projects on 2026-08-24, which
    # was very nearly the entire rare-earths landing page.
    patterns = [
        (r'rare earth|\bree\b|\btreo\b', 'ree'),
        (r'\bbase metals?\b', 'base metals'),
        (r'\bgold\b|\bau\b', 'gold'),
        (r'\bsilver\b|\bag\b', 'silver'),
        (r'\bcopper\b|\bcu\b', 'copper'),
        (r'\bzinc\b', 'zinc'),
        (r'\bnickel\b', 'nickel'),
        (r'\blithium\b', 'lithium'),
        (r'\buranium\b|u3o8', 'uranium'),
        (r'\bcobalt\b', 'cobalt'),
        (r'\bgraphite\b', 'graphite'),
        (r'\btungsten\b', 'tungsten'),
        (r'\bantimony\b', 'antimony'),
        (r'\bmolybdenum\b|\bmoly\b', 'moly'),
        (r'\bvanadium\b', 'vanadium'),
        (r'\bmanganese\b', 'manganese'),
        (r'\bpotash\b', 'potash'),
        (r'\btin\b', 'tin'),
        (r'\blead\b', 'lead'),
        (r'\biron ore\b', 'iron_ore'),
        (r'platinum|palladium|\bpgm\b|\bpge\b', 'pgm'),
    ]

    best_pos = None
    best_commodity = ''
    for pattern, commodity in patterns:
        match = re.search(pattern, name_lower)
        if match and (best_pos is None or match.start() < best_pos):
            best_pos = match.start()
            best_commodity = commodity

    if best_commodity:
        return best_commodity

    # Unknown. Do NOT default to gold.
    #
    # This used to `return 'gold'` on the grounds that most juniors are gold
    # companies. The effect was that any project whose NAME lacked a commodity
    # word -- "Acacia", "Bulldog", "Coyote Creek" -- was recorded as gold as
    # though it had been detected. On 2026-08-24 that accounted for 594 of the
    # 720 gold-tagged projects, 82% of them, and it put companies on the gold
    # commodity landing page on no evidence at all. Skyharbour, an Athabasca
    # uranium explorer, was tagged gold this way.
    #
    # Blank is honest and the commodity filter simply skips it. The page-content
    # scorer in company_scraper.score_commodity is what should supply a real
    # value; this name-based guess is only a fallback for when it cannot.
    return ''




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
    from core.models import Company
    from core.claude_validator import validate_scraped_data

    try:
        data = validate_scraped_data(data, source_url)
    except Exception as e:
        logger.warning(f"Claude validation failed, using raw data: {e}")

    company = _create_or_update_company(data, source_url, update_existing)
    _save_people(company, data.get('people', []))
    processing_jobs = _save_documents(company, data.get('documents', []), user)
    data['_processing_jobs_created'] = processing_jobs
    _set_presentation_url(company)
    news_jobs = _save_news(company, data.get('news', []), user)
    processing_jobs.extend(news_jobs)
    _save_projects(company, data.get('projects', []))
    return company


def _create_or_update_company(data: dict, source_url: str, update_existing: bool):
    """Find or create company from scraped data."""
    from core.models import Company
    # Imported lazily, like scrape_company_website below -- company_scraper
    # pulls in crawl4ai at module level.
    from mcp_servers.company_scraper import clean_company_name

    company_data = data.get('company', {})
    if not company_data.get('name'):
        raise Exception("No company name extracted - cannot create record")

    # Second line of defence. The scraper already cleans what it extracts,
    # but this is the single point every code path saves a company through,
    # and a page <title> reaching the database here ends up in the <h1>,
    # the <title>, the JSON-LD and the URL slug all at once.
    cleaned_name = clean_company_name(company_data['name'])
    if cleaned_name and cleaned_name != company_data['name']:
        logger.info(
            f"[ONBOARD] cleaned company name "
            f"{company_data['name']!r} -> {cleaned_name!r}"
        )
        company_data['name'] = cleaned_name

    # Check for existing company
    existing = None
    if company_data.get('ticker_symbol'):
        existing = Company.objects.filter(ticker_symbol__iexact=company_data['ticker_symbol']).first()
    if not existing:
        existing = Company.find_by_exact_name(company_data['name'])
    if existing and not update_existing:
        return existing

    # Prepare fields with length truncation
    fields = {
        'name': (company_data.get('name') or '')[:200],
        # Deliberately NOT falling back to name: a display name is not a
        # legal name, and mirroring the two left no clean value to recover
        # from when the scraper wrote a page title into both.
        'legal_name': (company_data.get('legal_name') or '')[:200],
        'ticker_symbol': (company_data.get('ticker_symbol') or '')[:10],
        'description': (company_data.get('description') or '')[:2000],
        'tagline': (company_data.get('tagline') or '')[:500],
        'logo_url': (company_data.get('logo_url') or '')[:200],
        'website': source_url[:200],
        'source_website_url': source_url[:200],
        'auto_populated': True,
        'last_scraped_at': timezone.now(),
        'ir_contact_email': (company_data.get('ir_contact_email') or '')[:254],
        'general_email': (company_data.get('general_email') or '')[:254],
        'media_email': (company_data.get('media_email') or '')[:254],
        'general_phone': (company_data.get('general_phone') or '')[:30],
        'street_address': (company_data.get('street_address') or '')[:300],
        'linkedin_url': (company_data.get('linkedin_url') or '')[:200],
        'twitter_url': (company_data.get('twitter_url') or '')[:200],
        'facebook_url': (company_data.get('facebook_url') or '')[:200],
        'youtube_url': (company_data.get('youtube_url') or '')[:200],
    }

    exchange_map = {
        'TSX': 'tsx', 'TSXV': 'tsxv', 'TSX-V': 'tsxv',
        'CSE': 'cse', 'OTC': 'otc', 'ASX': 'asx', 'AIM': 'aim',
    }
    if company_data.get('exchange'):
        fields['exchange'] = exchange_map.get(company_data['exchange'].upper(), 'other')
    if company_data.get('market_cap_usd'):
        fields['market_cap_usd'] = company_data['market_cap_usd']
    if company_data.get('shares_outstanding'):
        fields['shares_outstanding'] = company_data['shares_outstanding']
    fields['status'] = 'public' if fields.get('ticker_symbol') and fields.get('exchange') else 'private'

    if existing:
        for field, value in fields.items():
            if value:
                setattr(existing, field, value)
        existing.save()
        company = existing
    else:
        company = Company.objects.create(**fields)

    company.calculate_completeness_score()
    company.save()
    return company


def _save_people(company, people_data: list):
    """Save scraped people to database."""
    from core.models import CompanyPerson
    for i, person in enumerate(people_data):
        CompanyPerson.objects.update_or_create(
            company=company,
            full_name=person.get('full_name', '')[:200],
            defaults={
                'role_type': person.get('role_type', 'executive'),
                'title': person.get('title', '')[:200],
                'biography': person.get('biography', ''),
                'photo_url': person.get('photo_url', '')[:200],
                'linkedin_url': person.get('linkedin_url', '')[:200],
                'source_url': person.get('source_url', '')[:200],
                'extracted_at': timezone.now(),
                'display_order': i,
            }
        )


def _save_documents(company, documents: list, user) -> list:
    """Save scraped documents, create processing jobs for key types. Returns list of created jobs."""
    import re
    from core.models import CompanyDocument, DocumentProcessingJob

    processing_job_types = ['ni43101', 'pea', 'presentation', 'fact_sheet']
    jobs_created = []

    def get_doc_year(doc):
        if doc.get('year'):
            return int(doc['year'])
        text = f"{doc.get('title', '')} {doc.get('source_url', '')}"
        years = re.findall(r'20[12]\d', text)
        return max(int(y) for y in years) if years else 0

    documents.sort(key=get_doc_year, reverse=True)

    # Keep only most recent of each key type
    seen_types = {'presentation': 0, 'fact_sheet': 0, 'ni43101': 0, 'pea': 0}
    type_limits = {'presentation': 1, 'fact_sheet': 1, 'ni43101': 2, 'pea': 1}
    filtered = []
    for doc in documents:
        doc_type = doc.get('document_type', 'other')
        if doc_type in seen_types:
            if seen_types[doc_type] < type_limits.get(doc_type, 1):
                filtered.append(doc)
                seen_types[doc_type] += 1
        else:
            filtered.append(doc)

    logger.info(f"Filtered documents: {len(filtered)} from {len(documents)} total")

    for doc_data in filtered:
        doc_type = doc_data.get('document_type', 'other')
        doc_url = doc_data.get('source_url', '')
        if len(doc_url) > 200:
            continue

        CompanyDocument.objects.update_or_create(
            company=company, source_url=doc_url,
            defaults={
                'document_type': doc_type,
                'title': doc_data.get('title', 'Untitled')[:500],
                'year': doc_data.get('year'),
                'extracted_at': timezone.now(),
            }
        )

        if doc_type in processing_job_types and doc_url and '.pdf' in doc_url.lower():
            if not DocumentProcessingJob.objects.filter(url=doc_url).exists():
                job = DocumentProcessingJob.objects.create(
                    url=doc_url, document_type=doc_type, company_name=company.name,
                    status='pending', created_by=user,
                )
                jobs_created.append({'id': job.id, 'type': doc_type, 'url': doc_url})

    return jobs_created


def _set_presentation_url(company):
    """Set Company.presentation field from most recent presentation document."""
    from core.models import CompanyDocument
    doc = CompanyDocument.objects.filter(
        company=company, document_type='presentation'
    ).order_by('-year', '-created_at').first()
    if doc and doc.source_url and not company.presentation:
        company.presentation = doc.source_url
        company.save(update_fields=['presentation'])


def _save_news(company, news_items: list, user) -> list:
    """Save scraped news with classification and financing flags. Returns processing jobs."""
    import re
    from datetime import datetime, timedelta
    from core.models import CompanyNews, DocumentProcessingJob, NewsRelease, NewsReleaseFlag

    jobs = []

    # Fallback: use website_crawler if no news from company_scraper
    if not news_items and company and company.website:
        try:
            import asyncio
            from mcp_servers.website_crawler import crawl_news_releases
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                crawler_news = loop.run_until_complete(crawl_news_releases(company.website, months=12))
                news_items = [{'title': n.get('title', ''), 'source_url': n.get('url', ''),
                               'publication_date': n.get('date')} for n in crawler_news]
                logger.info(f"website_crawler found {len(news_items)} news items")
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"website_crawler error: {e}")

    date_only_re = re.compile(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$',
        re.IGNORECASE
    )

    for news_item in news_items[:50]:
        pub_date = None
        if news_item.get('publication_date'):
            try:
                pub_date = datetime.strptime(news_item['publication_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        if not pub_date:
            continue

        news_url = news_item.get('source_url', '')
        news_title = news_item.get('title', 'Untitled')[:500]
        if len(news_url) > 200 or len(news_title) < 10 or date_only_re.match(news_title.strip()):
            continue

        is_pdf = '.pdf' in news_url.lower()
        classification = _classify_news(news_title)

        news_record, _ = CompanyNews.objects.update_or_create(
            company=company, source_url=news_url,
            defaults={
                'title': news_title, 'publication_date': pub_date, 'is_pdf': is_pdf,
                'news_type': classification['news_type'], 'is_material': classification['is_material'],
                'financing_type': classification['financing_type'],
                'financing_amount': classification['financing_amount'],
                'financing_price_per_unit': classification['financing_price_per_unit'],
                'has_drill_results': classification['has_drill_results'],
                'best_intercept': classification['best_intercept'][:200] if classification['best_intercept'] else '',
            }
        )

        # Create financing flag for recent financing news
        if classification['news_type'] == 'financing' and pub_date:
            cutoff = timezone.now().date() - timedelta(days=7)
            if pub_date >= cutoff:
                _create_financing_flag(company, news_url, news_title, pub_date)

        # Create processing job for PDF news
        if is_pdf and news_url and not news_record.is_processed:
            if not DocumentProcessingJob.objects.filter(url=news_url).exists():
                job = DocumentProcessingJob.objects.create(
                    url=news_url, document_type='news_release', company_name=company.name,
                    project_name='', status='pending', created_by=user,
                )
                news_record.processing_job = job
                news_record.save(update_fields=['processing_job'])
                jobs.append({'id': job.id, 'type': 'news_release', 'url': news_url,
                            'is_material': classification['is_material']})

    return jobs


def _create_financing_flag(company, news_url, news_title, pub_date):
    """Create NewsReleaseFlag for financing-related news."""
    from core.models import NewsRelease, NewsReleaseFlag

    financing_keywords = [
        'private placement', 'financing', 'funding round', 'capital raise',
        'bought deal', 'equity financing', 'debt financing', 'flow-through',
        'warrant', 'subscription', 'offering', 'closes', 'tranche',
        'non-brokered', 'brokered', 'strategic investment', 'strategic partner'
    ]
    detected = [kw for kw in financing_keywords if kw in news_title.lower()]
    if not detected:
        return

    news_release, _ = NewsRelease.objects.get_or_create(
        company=company, url=news_url,
        defaults={'title': news_title, 'release_date': pub_date, 'is_material': True}
    )
    NewsReleaseFlag.objects.get_or_create(
        news_release=news_release,
        defaults={'detected_keywords': detected, 'status': 'pending'}
    )


def _save_projects(company, projects_data: list):
    """Save scraped projects to database."""
    from core.models import Project

    import re  # module-level import is absent here; the file imports locally

    def _norm(s):
        return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()

    # Listing pages put the company's own name in the same markup as the
    # project cards, so it gets collected as a property. Skyharbour Resources
    # was stored as a Skyharbour project.
    company_norm = _norm(company.name)
    company_bare = re.sub(
        r'\b(resources?|minerals?|mining|metals?|gold|silver|corp|corporation|'
        r'inc|ltd|limited|plc|company|co)\b', ' ', company_norm
    ).strip()

    for project_data in projects_data:
        name = (project_data.get('name') or '')[:200]
        if not name or _is_invalid_project_name(name):
            continue
        name_norm = _norm(name)
        if name_norm == company_norm or (company_bare and name_norm == company_bare):
            continue

        # Prefer what was actually read off the page. The name-based guess is
        # only a fallback: score_commodity() weighs how often each metal is
        # mentioned and counts assay notation heavily, whereas a name tells you
        # nothing unless it happens to contain the word.
        scraped_commodity = (project_data.get('commodity') or '').strip().lower()
        commodity = scraped_commodity or _infer_commodity_from_name(name)

        existing = Project.objects.filter(company=company, name=name).first()
        if existing:
            if project_data.get('description'):
                existing.description = (project_data.get('description') or '')[:2000]
            if project_data.get('location'):
                existing.country = (project_data.get('location') or '')[:100]
            # Only fill a blank; never overwrite a commodity already on record
            # with a fresh guess.
            if scraped_commodity and not existing.primary_commodity:
                existing.primary_commodity = scraped_commodity[:50]
            existing.save()
        else:
            country = (project_data.get('location') or project_data.get('country') or 'Unknown')[:100]
            Project.objects.create(
                company=company, name=name,
                description=(project_data.get('description') or '')[:2000],
                country=country,
                project_stage=_infer_project_stage_from_name(name),
                primary_commodity=commodity[:50],
            )




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

