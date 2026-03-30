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
    User,

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




@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_my_investment_interest(request, interest_id):
    """
    Update investment interest (user can update their own if status is pending).

    PATCH /api/investment-interest/<interest_id>/update/

    Body:
    - shares_requested: number of shares (optional)
    - investment_amount: amount in USD (optional)
    """
    try:
        interest = InvestmentInterest.objects.get(id=interest_id, user=request.user)
    except InvestmentInterest.DoesNotExist:
        return Response(
            {'error': 'Investment interest not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Only allow updates if status is pending
    if interest.status != 'pending':
        return Response(
            {'error': 'Cannot update interest at this stage. Please contact support.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update fields
    shares_requested = request.data.get('shares_requested')
    investment_amount = request.data.get('investment_amount')

    if shares_requested is not None:
        interest.shares_requested = int(shares_requested)

    if investment_amount is not None:
        from decimal import Decimal
        interest.investment_amount = Decimal(str(investment_amount))

    interest.save()

    # Recalculate aggregate
    InvestmentInterestAggregate.update_for_financing(interest.financing)

    return Response({
        'message': 'Investment interest updated successfully',
        'interest_id': interest.id,
        'shares_requested': interest.shares_requested,
        'investment_amount': str(interest.investment_amount),
        'status': interest.status
    })




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

    # Get all active financing rounds with interests (announced or closing status)
    active_financings = Financing.objects.filter(
        status__in=['announced', 'closing']
    ).select_related('company').prefetch_related('investment_interests')

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

