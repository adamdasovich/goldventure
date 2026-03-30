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
# COMPANY PORTAL SERIALIZERS (Resources, Events, Subscriptions)
# ============================================================================

class CompanyResourceSerializer(serializers.ModelSerializer):
    """Serializer for company resource files"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)

    class Meta:
        model = CompanyResource
        fields = [
            'id', 'company', 'company_name', 'resource_type', 'resource_type_display',
            'category', 'category_display', 'title', 'description',
            'file_url', 'external_url', 'thumbnail_url', 'file_size_mb', 'file_format',
            'sort_order', 'is_primary', 'is_public', 'is_featured', 'project', 'project_name',
            'uploaded_at', 'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']




class CompanyResourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating company resources"""

    class Meta:
        model = CompanyResource
        exclude = ['uploaded_by', 'uploaded_at']
        read_only_fields = ['id']




class CompanyResourceChoicesSerializer(serializers.Serializer):
    """Returns all choice options for company resource forms"""
    resource_types = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    def get_resource_types(self, obj):
        return [{'value': k, 'label': v} for k, v in CompanyResource.RESOURCE_TYPES]

    def get_categories(self, obj):
        return [{'value': k, 'label': v} for k, v in CompanyResource.RESOURCE_CATEGORIES]




class SpeakingEventSerializer(serializers.ModelSerializer):
    """Serializer for speaking events"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SpeakingEvent
        fields = [
            'id', 'company', 'company_name', 'company_ticker',
            'title', 'event_type', 'event_type_display', 'description',
            'event_name', 'location', 'is_virtual',
            'start_datetime', 'end_datetime', 'timezone',
            'registration_url', 'livestream_url', 'recording_url', 'presentation_url',
            'speakers', 'status', 'status_display', 'is_featured',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']




class SpeakingEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating speaking events"""

    class Meta:
        model = SpeakingEvent
        exclude = ['created_by', 'created_at', 'updated_at']
        read_only_fields = ['id']




class SpeakingEventListSerializer(serializers.ModelSerializer):
    """Compact serializer for event lists"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SpeakingEvent
        fields = [
            'id', 'company', 'company_name', 'company_ticker',
            'title', 'event_type', 'event_type_display',
            'event_name', 'location', 'is_virtual',
            'start_datetime', 'end_datetime', 'timezone',
            'registration_url', 'livestream_url',
            'status', 'status_display', 'is_featured'
        ]




class SpeakingEventChoicesSerializer(serializers.Serializer):
    """Returns all choice options for speaking event forms"""
    event_types = serializers.SerializerMethodField()
    statuses = serializers.SerializerMethodField()

    def get_event_types(self, obj):
        return [{'value': k, 'label': v} for k, v in SpeakingEvent.EVENT_TYPES]

    def get_statuses(self, obj):
        return [{'value': k, 'label': v} for k, v in SpeakingEvent.EVENT_STATUS]




class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for subscription invoices"""
    amount_dollars = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SubscriptionInvoice
        fields = [
            'id', 'stripe_invoice_id', 'status', 'status_display',
            'amount_cents', 'amount_dollars', 'currency',
            'invoice_date', 'due_date', 'paid_at',
            'invoice_pdf_url', 'hosted_invoice_url', 'created_at'
        ]

    def get_amount_dollars(self, obj):
        return f"${obj.amount_cents / 100:.2f}"




class CompanySubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for company subscriptions"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    price_dollars = serializers.SerializerMethodField()
    invoices = SubscriptionInvoiceSerializer(many=True, read_only=True)

    class Meta:
        model = CompanySubscription
        fields = [
            'id', 'company', 'company_name',
            'stripe_customer_id', 'stripe_subscription_id',
            'plan_type', 'plan_type_display', 'status', 'status_display',
            'price_cents', 'price_dollars',
            'trial_start', 'trial_end',
            'current_period_start', 'current_period_end',
            'cancel_at_period_end', 'canceled_at',
            'features', 'is_active', 'can_access_premium',
            'invoices', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_customer_id', 'stripe_subscription_id',
            'trial_start', 'trial_end', 'current_period_start', 'current_period_end',
            'canceled_at', 'is_active', 'can_access_premium',
            'created_at', 'updated_at'
        ]

    def get_price_dollars(self, obj):
        return f"${obj.price_cents / 100:.2f}"




class CompanySubscriptionStatusSerializer(serializers.ModelSerializer):
    """Compact serializer for subscription status checks"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = CompanySubscription
        fields = [
            'id', 'company', 'company_name', 'status', 'status_display',
            'is_active', 'can_access_premium', 'trial_end',
            'current_period_end', 'cancel_at_period_end', 'days_remaining'
        ]

    def get_days_remaining(self, obj):
        from django.utils import timezone
        if obj.current_period_end:
            delta = obj.current_period_end - timezone.now()
            return max(0, delta.days)
        return None




# ============================================================================
# COMPANY ACCESS REQUEST SERIALIZERS
# ============================================================================

class CompanyAccessRequestSerializer(serializers.ModelSerializer):
    """Full serializer for company access requests"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)

    class Meta:
        from ..models import CompanyAccessRequest
        model = CompanyAccessRequest
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'company', 'company_name', 'company_ticker',
            'status', 'status_display',
            'role', 'role_display', 'job_title',
            'justification', 'work_email',
            'reviewer', 'reviewer_name', 'review_notes', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'status', 'reviewer', 'review_notes', 'reviewed_at',
            'created_at', 'updated_at'
        ]




class CompanyAccessRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating access requests"""

    class Meta:
        from ..models import CompanyAccessRequest
        model = CompanyAccessRequest
        fields = ['company', 'role', 'job_title', 'justification', 'work_email']

    def validate_company(self, value):
        """Ensure user doesn't already have a pending request for this company"""
        user = self.context['request'].user
        from ..models import CompanyAccessRequest
        if CompanyAccessRequest.objects.filter(
            user=user,
            company=value,
            status='pending'
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending request for this company."
            )
        return value

    def validate(self, data):
        """Additional validations"""
        user = self.context['request'].user

        # Check if user is already associated with a company
        if user.company:
            raise serializers.ValidationError(
                "You are already associated with a company. "
                "Please contact support if you need to change your company."
            )

        return data

    def create(self, validated_data):
        from ..models import CompanyAccessRequest
        validated_data['user'] = self.context['request'].user
        return CompanyAccessRequest.objects.create(**validated_data)




class CompanyAccessRequestReviewSerializer(serializers.Serializer):
    """Serializer for admin review actions"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True, default='')




class CompanyAccessRequestChoicesSerializer(serializers.Serializer):
    """Return dropdown choices for forms"""
    roles = serializers.SerializerMethodField()
    statuses = serializers.SerializerMethodField()

    def get_roles(self, obj):
        from ..models import CompanyAccessRequest
        return [{'value': k, 'label': v} for k, v in CompanyAccessRequest.ROLE_CHOICES]

    def get_statuses(self, obj):
        from ..models import CompanyAccessRequest
        return [{'value': k, 'label': v} for k, v in CompanyAccessRequest.REQUEST_STATUS]

