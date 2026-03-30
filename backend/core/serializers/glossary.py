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
# GLOSSARY SERIALIZERS
# ============================================================================

class GlossaryTermSerializer(serializers.ModelSerializer):
    """Serializer for glossary terms"""
    first_letter = serializers.CharField(read_only=True)

    class Meta:
        model = GlossaryTerm
        fields = [
            'id', 'term', 'definition', 'category',
            'related_links', 'keywords', 'first_letter',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']




class GlossaryTermSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for listing glossary term submissions"""
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GlossaryTermSubmission
        fields = [
            'id', 'term', 'definition', 'category',
            'related_links', 'keywords',
            'submitted_by', 'submitted_by_username', 'submitted_at',
            'status', 'status_display',
            'reviewed_by', 'reviewed_by_username', 'reviewed_at',
            'rejection_reason', 'approved_term'
        ]
        read_only_fields = [
            'submitted_by', 'submitted_at',
            'reviewed_by', 'reviewed_at',
            'status', 'rejection_reason', 'approved_term'
        ]




class GlossaryTermSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new glossary term submissions"""

    class Meta:
        model = GlossaryTermSubmission
        fields = ['term', 'definition', 'category', 'related_links', 'keywords']

    def validate_term(self, value):
        """Ensure term doesn't already exist in glossary"""
        if GlossaryTerm.objects.filter(term__iexact=value).exists():
            raise serializers.ValidationError('This term already exists in the glossary.')
        return value

    def create(self, validated_data):
        """Create submission with current user as submitter"""
        validated_data['submitted_by'] = self.context['request'].user
        return super().create(validated_data)

