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





class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - public version without admin fields"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        # SECURITY: Do not expose is_staff/is_superuser to prevent admin enumeration
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'user_type', 'company', 'phone', 'linkedin_url', 'created_at']
        read_only_fields = ['id', 'created_at', 'full_name']

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else f"{obj.first_name} {obj.last_name}".strip() or obj.username




class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for User model - admin version with all fields"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'user_type', 'company', 'phone', 'linkedin_url', 'created_at',
                  'is_staff', 'is_superuser', 'is_active', 'last_login']
        read_only_fields = ['id', 'created_at', 'full_name', 'last_login']

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else f"{obj.first_name} {obj.last_name}".strip() or obj.username

