"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from rest_framework import serializers
from .users import UserSerializer
from .companies import CompanySerializer, FinancingSerializer
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
# FINANCIAL HUB SERIALIZERS
# ============================================================================

class EducationalModuleSerializer(serializers.ModelSerializer):
    """Serializer for Educational Modules"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    completion_status = serializers.SerializerMethodField()

    class Meta:
        model = EducationalModule
        fields = [
            'id', 'module_type', 'title', 'description', 'content',
            'estimated_read_time_minutes', 'sort_order', 'is_published',
            'is_required', 'created_by_name', 'completion_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_completion_status(self, obj):
        """Get completion status for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            completion = obj.completions.filter(user=request.user).first()
            if completion:
                return {
                    'completed': bool(completion.completed_at),
                    'completed_at': completion.completed_at,
                    'time_spent_seconds': completion.time_spent_seconds,
                    'passed': completion.passed
                }
        return None




class ModuleCompletionSerializer(serializers.ModelSerializer):
    """Serializer for Module Completion tracking"""
    module_title = serializers.CharField(source='module.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ModuleCompletion
        fields = [
            'id', 'user', 'user_name', 'module', 'module_title',
            'started_at', 'completed_at', 'time_spent_seconds',
            'quiz_score', 'passed'
        ]
        read_only_fields = ['id', 'started_at']




class AccreditedInvestorQualificationSerializer(serializers.ModelSerializer):
    """Serializer for Accredited Investor Qualification"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    criteria_display = serializers.CharField(source='get_criteria_met_display', read_only=True)

    class Meta:
        model = AccreditedInvestorQualification
        fields = [
            'id', 'user', 'user_name', 'status', 'status_display',
            'criteria_met', 'criteria_display', 'questionnaire_responses',
            'documents_submitted', 'documents_verified', 'reviewed_by',
            'reviewed_by_name', 'reviewed_at', 'review_notes',
            'qualified_at', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']




class SubscriptionAgreementSerializer(serializers.ModelSerializer):
    """Serializer for Subscription Agreements"""
    investor_name = serializers.CharField(source='investor.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    financing_type = serializers.CharField(source='financing.financing_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    financing_detail = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionAgreement
        fields = [
            'id', 'investor', 'investor_name', 'financing', 'financing_type', 'financing_detail',
            'company', 'company_name', 'num_shares', 'price_per_share',
            'total_investment_amount', 'currency', 'includes_warrants',
            'warrant_shares', 'warrant_strike_price', 'warrant_expiry_date',
            'status', 'status_display', 'agreement_pdf_url', 'docusign_envelope_id',
            'investor_signed_at', 'company_accepted_at', 'payment_received_at',
            'shares_issued', 'shares_issued_at', 'drs_statement_sent_at',
            'accreditation_verified', 'kyc_completed', 'aml_check_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_financing_detail(self, obj):
        """Return financing details for frontend"""
        return {
            'id': obj.financing.id,
            'company': {
                'id': obj.company.id,
                'name': obj.company.name,
                'ticker_symbol': obj.company.ticker_symbol if hasattr(obj.company, 'ticker_symbol') else None,
            },
            'price_per_share': str(obj.financing.price_per_share) if obj.financing.price_per_share else '0.00',
            'financing_type': obj.financing.financing_type,
        }




class SubscriptionAgreementDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Subscription Agreements with all related data"""
    investor = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    financing = FinancingSerializer(read_only=True)
    transactions = serializers.SerializerMethodField()
    payment_instruction = serializers.SerializerMethodField()
    drs_documents = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionAgreement
        fields = [
            'id', 'investor', 'financing', 'company',
            'num_shares', 'price_per_share', 'total_investment_amount', 'currency',
            'includes_warrants', 'warrant_shares', 'warrant_strike_price', 'warrant_expiry_date',
            'status', 'agreement_pdf_url', 'docusign_envelope_id',
            'investor_signed_at', 'investor_ip_address',
            'company_accepted_at', 'company_accepted_by',
            'payment_instructions_sent_at', 'payment_received_at', 'payment_reference',
            'shares_issued', 'shares_issued_at', 'drs_statement_sent_at', 'certificate_number',
            'accreditation_verified', 'kyc_completed', 'aml_check_completed',
            'notes', 'rejection_reason',
            'created_at', 'updated_at',
            # Nested serializers
            'transactions', 'payment_instruction', 'drs_documents',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_transactions(self, obj):
        transactions = obj.transactions.all()
        return InvestmentTransactionSerializer(transactions, many=True).data

    def get_payment_instruction(self, obj):
        try:
            return PaymentInstructionSerializer(obj.payment_instruction).data
        except PaymentInstruction.DoesNotExist:
            return None

    def get_drs_documents(self, obj):
        documents = obj.drs_documents.all()
        return DRSDocumentSerializer(documents, many=True).data




class InvestmentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Investment Transactions"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='financing.company.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InvestmentTransaction
        fields = [
            'id', 'subscription_agreement', 'user', 'user_name', 'financing',
            'company_name', 'amount', 'currency', 'status', 'status_display',
            'payment_method', 'payment_reference', 'payment_date',
            'shares_allocated', 'price_per_share', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']




class FinancingAggregateSerializer(serializers.ModelSerializer):
    """Serializer for Financing Aggregates"""
    financing_info = FinancingSerializer(source='financing', read_only=True)

    class Meta:
        model = FinancingAggregate
        fields = [
            'id', 'financing', 'financing_info', 'total_subscriptions',
            'total_subscribers', 'total_committed_amount', 'total_funded_amount',
            'total_shares_allocated', 'status_breakdown', 'investor_type_breakdown',
            'last_calculated_at'
        ]
        read_only_fields = ['id', 'last_calculated_at']




class PaymentInstructionSerializer(serializers.ModelSerializer):
    """Serializer for Payment Instructions"""
    investor_name = serializers.CharField(source='subscription_agreement.investor.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = PaymentInstruction
        fields = [
            'id', 'subscription_agreement', 'investor_name', 'company',
            'company_name', 'payment_method', 'payment_method_display',
            'bank_name', 'bank_account_name', 'bank_account_number',
            'routing_number', 'swift_code', 'reference_code',
            'special_instructions', 'sent_to_investor_at',
            'viewed_by_investor_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']




class DRSDocumentSerializer(serializers.ModelSerializer):
    """Serializer for DRS Documents"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    delivery_status_display = serializers.CharField(source='get_delivery_status_display', read_only=True)

    class Meta:
        model = DRSDocument
        fields = [
            'id', 'subscription_agreement', 'user', 'user_name', 'company',
            'company_name', 'document_type', 'document_type_display',
            'document_url', 'document_hash', 'num_shares', 'certificate_number',
            'issue_date', 'delivery_status', 'delivery_status_display',
            'delivery_method', 'sent_at', 'delivered_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

