"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from rest_framework import serializers
from ..models import (
    User, Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, MarketData, NewsRelease, Document,
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    # Financial Hub models
    EducationalModule, ModuleCompletion, AccreditedInvestorQualification,
    SubscriptionAgreement, InvestmentTransaction, FinancingAggregate,
    PaymentInstruction, DRSDocument,
    # Property Exchange models
    ProspectorProfile, PropertyListing, PropertyMedia, PropertyInquiry,
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement,
    InquiryMessage,
    # Company Portal models
    CompanyResource, SpeakingEvent, CompanySubscription, SubscriptionInvoice,
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





# ============================================================================
# INVESTMENT INTEREST SERIALIZERS
# ============================================================================

class InvestmentInterestSerializer(serializers.ModelSerializer):
    """Full serializer for investment interests (admin/company view)"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    financing_type = serializers.CharField(source='financing.financing_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InvestmentInterest
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'financing', 'financing_type', 'company', 'company_name',
            'is_accredited_investor', 'accreditation_confirmed_at',
            'shares_requested', 'price_per_share', 'investment_amount', 'currency',
            'term_sheet_confirmed', 'term_sheet_confirmed_at',
            'subscription_agreement_confirmed', 'subscription_agreement_confirmed_at',
            'contact_email', 'contact_phone',
            'risk_acknowledged', 'risk_acknowledged_at',
            'status', 'status_display', 'status_notes',
            'subscription_agreement',
            'ip_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username




class InvestmentInterestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating investment interest registrations"""

    class Meta:
        model = InvestmentInterest
        fields = [
            'financing', 'is_accredited_investor',
            'shares_requested',
            'term_sheet_confirmed',
            'subscription_agreement_confirmed',
            'contact_email', 'contact_phone',
            'risk_acknowledged',
        ]

    def validate_is_accredited_investor(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm that you are an accredited investor to participate."
            )
        return value

    def validate_term_sheet_confirmed(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm that you have read the term sheet."
            )
        return value

    def validate_subscription_agreement_confirmed(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must confirm that you have read the subscription agreement."
            )
        return value

    def validate_risk_acknowledged(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must acknowledge the investment risks."
            )
        return value

    def validate_shares_requested(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Number of shares must be greater than zero."
            )
        return value

    def validate(self, data):
        """Additional validation"""
        user = self.context['request'].user
        financing = data.get('financing')

        # Check if user already expressed interest in this financing
        if InvestmentInterest.objects.filter(
            user=user,
            financing=financing
        ).exists():
            raise serializers.ValidationError(
                "You have already registered interest in this financing round."
            )

        # Verify financing is open (announced or closing status)
        if financing.status not in ['announced', 'closing']:
            raise serializers.ValidationError(
                "This financing round is not currently accepting new interests."
            )

        return data

    def create(self, validated_data):
        from django.utils import timezone

        user = self.context['request'].user
        request = self.context.get('request')
        financing = validated_data['financing']

        # Set timestamps for confirmations
        now = timezone.now()
        if validated_data.get('term_sheet_confirmed'):
            validated_data['term_sheet_confirmed_at'] = now
        if validated_data.get('subscription_agreement_confirmed'):
            validated_data['subscription_agreement_confirmed_at'] = now
        if validated_data.get('risk_acknowledged'):
            validated_data['risk_acknowledged_at'] = now

        # Set additional fields
        validated_data['user'] = user
        validated_data['company'] = financing.company
        validated_data['price_per_share'] = financing.price_per_share
        validated_data['investment_amount'] = validated_data['shares_requested'] * financing.price_per_share

        # Track IP address and user agent
        # SECURITY: Use get_client_ip() to prevent X-Forwarded-For spoofing
        if request:
            from core.security_utils import get_client_ip
            validated_data['ip_address'] = get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        interest = InvestmentInterest.objects.create(**validated_data)

        # Update aggregate data
        InvestmentInterestAggregate.update_for_financing(financing)

        return interest




class InvestmentInterestAggregateSerializer(serializers.ModelSerializer):
    """Public serializer for investment interest aggregates (NO PII)"""
    financing_id = serializers.IntegerField(source='financing.id', read_only=True)
    company_name = serializers.CharField(source='financing.company.name', read_only=True)
    target_amount = serializers.DecimalField(
        source='financing.amount_raised_usd',
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    financing_status = serializers.CharField(source='financing.status', read_only=True)

    class Meta:
        model = InvestmentInterestAggregate
        fields = [
            'id', 'financing_id', 'company_name', 'financing_status',
            'total_interest_count', 'total_shares_requested',
            'total_amount_interested', 'percentage_filled',
            'target_amount', 'last_calculated_at'
        ]




class InvestmentInterestStatusSerializer(serializers.Serializer):
    """Serializer for checking user's investment interest status"""
    has_interest = serializers.BooleanField()
    interest_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    shares_requested = serializers.IntegerField(allow_null=True)
    investment_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, allow_null=True
    )
    created_at = serializers.DateTimeField(allow_null=True)

