"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from django.db.models import Max
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







class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    project_count = serializers.SerializerMethodField()
    latest_news_date = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'legal_name', 'former_names', 'ticker_symbol', 'exchange', 'status',
            'incorporation_date', 'jurisdiction', 'website', 'news_url',
            'headquarters_city', 'headquarters_country',
            'ceo_name', 'cfo_name', 'ir_contact_name', 'ir_contact_email', 'ir_contact_phone',
            'market_cap_usd', 'shares_outstanding', 'current_price',
            'description', 'logo_url', 'is_active',
            'tagline', 'logo_file', 'data_completeness_score',
            'general_email', 'media_email', 'general_phone',
            'linkedin_url', 'twitter_url', 'facebook_url', 'youtube_url',
            'street_address', 'postal_code',
            'approval_status', 'company_size', 'industry', 'contact_email',
            'brief_description', 'is_user_submitted',
            'created_at', 'updated_at', 'project_count', 'latest_news_date',
        ]
        read_only_fields = ['id', 'slug', 'former_names', 'created_at', 'updated_at', 'data_completeness_score']
        extra_kwargs = {
            'status': {'required': False},  # Make status optional for user submissions
        }

    def get_project_count(self, obj):
        if hasattr(obj, '_project_count'):
            return obj._project_count
        return obj.projects.filter(is_active=True).count()

    def get_latest_news_date(self, obj):
        """Date of the most recent press release, or None.

        Exists so the sitemap can emit a truthful `lastmod`. `updated_at` is
        rewritten by the daily scrape regardless of whether anything changed,
        which makes every company page look modified every day — the pattern
        that causes Google to distrust and ignore lastmod entirely.
        """
        if hasattr(obj, '_latest_news_date'):
            latest = obj._latest_news_date
        else:
            latest = obj.news_releases.aggregate(d=Max('release_date'))['d']
        return latest.isoformat() if latest else None








class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)
    resource_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'company', 'company_name', 'company_ticker',
            'name', 'project_stage', 'primary_commodity',
            'country', 'province_state', 'latitude', 'longitude',
            'description', 'ownership_percentage',
            'acquisition_date', 'last_drill_program',
            'is_flagship', 'is_active',
            'created_at', 'updated_at', 'resource_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_resource_count(self, obj):
        if hasattr(obj, '_resource_count'):
            return obj._resource_count
        return obj.resources.count()






class ResourceEstimateSerializer(serializers.ModelSerializer):
    """Serializer for ResourceEstimate model"""
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ResourceEstimate
        fields = [
            'id', 'project', 'project_name',
            'category', 'standard',
            'tonnes', 'gold_grade_gpt', 'gold_ounces',
            'silver_grade_gpt', 'silver_ounces', 'copper_grade_pct',
            'report_date', 'cutoff_grade', 'effective_date',
            'qualified_person', 'report_url',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']






class EconomicStudySerializer(serializers.ModelSerializer):
    """Serializer for EconomicStudy model"""
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = EconomicStudy
        fields = [
            'id', 'project', 'project_name',
            'study_type', 'release_date',
            'npv_5_usd', 'irr_percent', 'payback_years',
            'annual_production_oz', 'mine_life_years',
            'aisc_per_oz', 'initial_capex_usd',
            'gold_price_assumption', 'exchange_rate_assumption',
            'report_url', 'qualified_person', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']






class FinancingSerializer(serializers.ModelSerializer):
    """Serializer for Financing model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Financing
        fields = [
            'id', 'company', 'company_name',
            'financing_type', 'status',
            'announced_date', 'closing_date',
            'amount_raised_usd', 'price_per_share', 'shares_issued',
            'has_warrants', 'warrant_strike_price', 'warrant_expiry_date',
            'use_of_proceeds', 'lead_agent',
            'press_release_url', 'notes',
            'is_closed', 'closed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'closed_at']






class InvestorSerializer(serializers.ModelSerializer):
    """Serializer for Investor model"""

    class Meta:
        model = Investor
        fields = [
            'id', 'investor_type',
            'first_name', 'last_name', 'company_name',
            'email', 'phone', 'linkedin_url',
            'city', 'country',
            'focus_regions', 'focus_commodities', 'preferred_project_stages',
            'typical_check_size_min_usd', 'typical_check_size_max_usd',
            'relationship_strength', 'notes', 'tags',
            'user', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']






class MarketDataSerializer(serializers.ModelSerializer):
    """Serializer for MarketData model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)

    class Meta:
        model = MarketData
        fields = [
            'id', 'company', 'company_name', 'ticker',
            'date', 'open_price', 'high_price', 'low_price', 'close_price',
            'volume', 'change_amount', 'change_percent',
            'currency', 'source', 'market_cap_usd',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']






class NewsReleaseSerializer(serializers.ModelSerializer):
    """Serializer for NewsRelease model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = NewsRelease
        fields = [
            'id', 'company', 'company_name', 'project',
            'title', 'release_type', 'release_date',
            'summary', 'full_text', 'url',
            'is_material',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']






class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'company', 'company_name', 'project',
            'title', 'document_type', 'document_date',
            'file_url', 'file_size_mb',
            'description', 'is_public',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']






class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed project serializer with nested resources and studies"""
    company = CompanySerializer(read_only=True)
    resources = ResourceEstimateSerializer(many=True, read_only=True)
    economic_studies = EconomicStudySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'company',
            'name', 'project_stage', 'primary_commodity',
            'country', 'province_state', 'latitude', 'longitude',
            'description', 'ownership_percentage',
            'acquisition_date', 'last_drill_program',
            'is_flagship', 'is_active',
            'created_at', 'updated_at',
            # Nested serializers
            'resources', 'economic_studies',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']










# Nested serializers for detailed views
class CompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed company serializer with nested projects"""
    projects = ProjectSerializer(many=True, read_only=True)
    financings = FinancingSerializer(many=True, read_only=True)
    # Mirrors CompanySerializer so callers can read the same field off either
    # endpoint — the frontend's indexability check relied on it being here.
    project_count = serializers.SerializerMethodField()
    presentation_url = serializers.SerializerMethodField()
    fact_sheet_url = serializers.SerializerMethodField()
    technical_report_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'legal_name', 'former_names', 'ticker_symbol', 'exchange', 'status',
            'incorporation_date', 'jurisdiction', 'website', 'news_url',
            'headquarters_city', 'headquarters_country',
            'ceo_name', 'cfo_name', 'ir_contact_name', 'ir_contact_email', 'ir_contact_phone',
            'market_cap_usd', 'shares_outstanding', 'current_price',
            'description', 'logo_url', 'is_active',
            'tagline', 'logo_file', 'data_completeness_score',
            'general_email', 'media_email', 'general_phone',
            'linkedin_url', 'twitter_url', 'facebook_url', 'youtube_url',
            'street_address', 'postal_code',
            'approval_status', 'company_size', 'industry', 'contact_email',
            'brief_description', 'is_user_submitted',
            'created_at', 'updated_at',
            # Nested serializers
            'projects', 'financings',
            # Method fields
            'project_count',
            'presentation_url', 'fact_sheet_url', 'technical_report_url',
        ]
        read_only_fields = ['id', 'slug', 'former_names', 'created_at', 'updated_at', 'data_completeness_score']

    def get_project_count(self, obj):
        if hasattr(obj, '_project_count'):
            return obj._project_count
        return obj.projects.filter(is_active=True).count()

    def get_presentation_url(self, obj):
        """Get the latest corporate presentation URL"""
        doc = obj.scraped_documents.filter(
            document_type='presentation'
        ).order_by('-year', '-created_at').first()
        return doc.source_url if doc else None

    def get_fact_sheet_url(self, obj):
        """Get the latest fact sheet URL"""
        doc = obj.scraped_documents.filter(
            document_type='fact_sheet'
        ).order_by('-year', '-created_at').first()
        return doc.source_url if doc else None

    def get_technical_report_url(self, obj):
        """Get the latest NI 43-101 technical report URL"""
        doc = obj.scraped_documents.filter(
            document_type='ni43101'
        ).order_by('-year', '-created_at').first()
        return doc.source_url if doc else None
