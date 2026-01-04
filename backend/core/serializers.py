"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from rest_framework import serializers
from .models import (
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
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'user_type', 'company', 'phone', 'linkedin_url', 'created_at',
                  'is_staff', 'is_superuser']
        read_only_fields = ['id', 'created_at', 'full_name', 'is_staff', 'is_superuser']

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else f"{obj.first_name} {obj.last_name}".strip() or obj.username


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'status': {'required': False},  # Make status optional for user submissions
        }

    def get_project_count(self, obj):
        return obj.projects.filter(is_active=True).count()


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)
    resource_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_resource_count(self, obj):
        return obj.resources.count()


class ResourceEstimateSerializer(serializers.ModelSerializer):
    """Serializer for ResourceEstimate model"""
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ResourceEstimate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EconomicStudySerializer(serializers.ModelSerializer):
    """Serializer for EconomicStudy model"""
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = EconomicStudy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FinancingSerializer(serializers.ModelSerializer):
    """Serializer for Financing model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Financing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestorSerializer(serializers.ModelSerializer):
    """Serializer for Investor model"""

    class Meta:
        model = Investor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarketDataSerializer(serializers.ModelSerializer):
    """Serializer for MarketData model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    ticker = serializers.CharField(source='company.ticker_symbol', read_only=True)

    class Meta:
        model = MarketData
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class NewsReleaseSerializer(serializers.ModelSerializer):
    """Serializer for NewsRelease model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = NewsRelease
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# Nested serializers for detailed views
class CompanyDetailSerializer(serializers.ModelSerializer):
    """Detailed company serializer with nested projects"""
    projects = ProjectSerializer(many=True, read_only=True)
    financings = FinancingSerializer(many=True, read_only=True)
    presentation_url = serializers.SerializerMethodField()
    fact_sheet_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

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


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed project serializer with nested resources and studies"""
    company = CompanySerializer(read_only=True)
    resources = ResourceEstimateSerializer(many=True, read_only=True)
    economic_studies = EconomicStudySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'


# Guest Speaker Event Serializers

class EventSpeakerSerializer(serializers.ModelSerializer):
    """Serializer for event speakers"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = EventSpeaker
        fields = ['id', 'user', 'user_id', 'title', 'bio', 'is_primary', 'added_at']
        read_only_fields = ['id', 'added_at']


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for event registrations"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = ['id', 'user', 'status', 'registered_at', 'joined_at', 'left_at', 'reminder_sent']
        read_only_fields = ['id', 'user', 'registered_at', 'joined_at', 'left_at', 'reminder_sent']


class EventQuestionSerializer(serializers.ModelSerializer):
    """Serializer for event questions"""
    user = UserSerializer(read_only=True)
    answered_by = UserSerializer(read_only=True)

    class Meta:
        model = EventQuestion
        fields = ['id', 'event', 'user', 'content', 'status', 'answer', 'answered_by',
                  'upvotes', 'is_featured', 'created_at', 'answered_at']
        read_only_fields = ['id', 'user', 'upvotes', 'created_at', 'answered_at']


class EventReactionSerializer(serializers.ModelSerializer):
    """Serializer for event reactions"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventReaction
        fields = ['id', 'event', 'user', 'reaction_type', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp']


class SpeakerEventListSerializer(serializers.ModelSerializer):
    """Serializer for list view of speaker events"""
    company = CompanySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    is_registered = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()

    class Meta:
        model = SpeakerEvent
        fields = [
            'id', 'company', 'created_by', 'title', 'description', 'topic',
            'scheduled_start', 'scheduled_end', 'duration_minutes', 'format',
            'status', 'max_participants', 'registered_count', 'attended_count',
            'speakers', 'is_registered', 'can_register', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'registered_count', 'attended_count', 'created_at']

    def get_is_registered(self, obj):
        """Check if current user is registered"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(user=request.user, status='registered').exists()
        return False

    def get_can_register(self, obj):
        """Check if user can register"""
        if obj.status != 'scheduled':
            return False
        if obj.max_participants and obj.registered_count >= obj.max_participants:
            return False
        return True


class SpeakerEventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for speaker events"""
    company = CompanySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    registrations = EventRegistrationSerializer(many=True, read_only=True)
    questions = EventQuestionSerializer(many=True, read_only=True)
    is_registered = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    user_registration = serializers.SerializerMethodField()

    class Meta:
        model = SpeakerEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'registered_count', 'attended_count',
                            'questions_count', 'created_at', 'updated_at']

    def get_is_registered(self, obj):
        """Check if current user is registered"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(user=request.user, status='registered').exists()
        return False

    def get_can_register(self, obj):
        """Check if user can register"""
        if obj.status != 'scheduled':
            return False
        if obj.max_participants and obj.registered_count >= obj.max_participants:
            return False
        return True

    def get_user_registration(self, obj):
        """Get current user's registration if exists"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            registration = obj.registrations.filter(user=request.user).first()
            if registration:
                return EventRegistrationSerializer(registration).data
        return None


class SpeakerEventSpeakerCreateSerializer(serializers.Serializer):
    """Nested serializer for creating speakers during event creation"""
    name = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255)
    bio = serializers.CharField(allow_blank=True)
    is_primary = serializers.BooleanField(default=False)


class SpeakerEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating speaker events"""
    speakers = SpeakerEventSpeakerCreateSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = SpeakerEvent
        fields = [
            'id', 'company', 'title', 'description', 'topic', 'scheduled_start',
            'scheduled_end', 'duration_minutes', 'format', 'max_participants',
            'status', 'stream_url', 'is_recorded', 'speakers'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        speakers_data = validated_data.pop('speakers', [])
        event = SpeakerEvent.objects.create(**validated_data)

        # Create speakers with auto-generated user accounts
        for speaker_data in speakers_data:
            name = speaker_data['name']
            title = speaker_data['title']
            bio = speaker_data.get('bio', '')
            is_primary = speaker_data.get('is_primary', False)

            # Generate username from name (lowercase, replace spaces with underscores)
            username = name.lower().replace(' ', '_').replace('.', '')
            email = f"{username}@speakers.goldventure.com"

            # Try to get or create user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': name.split()[0] if name.split() else name,
                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                }
            )

            # If user was just created, set a random password
            if created:
                import secrets
                user.set_password(secrets.token_urlsafe(16))
                user.save()

            # Create event speaker entry (avoid duplicates)
            EventSpeaker.objects.get_or_create(
                event=event,
                user=user,
                defaults={
                    'title': title,
                    'bio': bio,
                    'is_primary': is_primary,
                }
            )

        return event

    def to_representation(self, instance):
        """Use the full detail serializer for the response"""
        return SpeakerEventDetailSerializer(instance, context=self.context).data


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
        fields = '__all__'
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


# ============================================================================
# PROSPECTOR PROPERTY EXCHANGE SERIALIZERS
# ============================================================================

class ProspectorProfileSerializer(serializers.ModelSerializer):
    """Serializer for prospector profiles"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    listings_count = serializers.SerializerMethodField()
    can_list_properties = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProspectorProfile
        fields = [
            'id', 'user', 'username', 'email', 'display_name', 'company_name',
            'bio', 'years_experience', 'specializations', 'regions_active',
            'certifications', 'website_url', 'phone', 'is_verified',
            'verification_date', 'profile_image_url', 'total_listings',
            'active_listings', 'successful_transactions', 'average_rating',
            'listings_count', 'commission_agreement_accepted', 'commission_agreement_date',
            'can_list_properties', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'verification_date',
                          'total_listings', 'active_listings', 'successful_transactions',
                          'average_rating', 'commission_agreement_accepted',
                          'commission_agreement_date', 'can_list_properties',
                          'created_at', 'updated_at']

    def get_listings_count(self, obj):
        return obj.listings.filter(status='active').count()


class ProspectorCommissionAgreementSerializer(serializers.ModelSerializer):
    """Serializer for commission agreement acceptance"""
    agreement_text = serializers.SerializerMethodField()
    prospector_name = serializers.CharField(source='prospector.display_name', read_only=True)

    class Meta:
        model = ProspectorCommissionAgreement
        fields = [
            'id', 'prospector', 'prospector_name', 'version', 'commission_rate',
            'full_legal_name', 'accepted_at', 'ip_address', 'user_agent',
            'agreement_text', 'is_active'
        ]
        read_only_fields = ['id', 'prospector', 'version', 'commission_rate',
                          'accepted_at', 'ip_address', 'user_agent', 'is_active']

    def get_agreement_text(self, obj):
        return obj.agreement_text if obj.pk else ProspectorCommissionAgreement.get_agreement_text()


class ProspectorCommissionAgreementCreateSerializer(serializers.Serializer):
    """Serializer for accepting the commission agreement"""
    full_legal_name = serializers.CharField(max_length=300, help_text="Your full legal name as electronic signature")

    def validate_full_legal_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Please enter your full legal name")
        return value.strip()


class ProspectorProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prospector profiles during registration"""

    class Meta:
        model = ProspectorProfile
        fields = [
            'display_name', 'company_name', 'bio', 'years_experience',
            'specializations', 'regions_active', 'website_url', 'phone'
        ]


class PropertyMediaSerializer(serializers.ModelSerializer):
    """Serializer for property media files"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = PropertyMedia
        fields = [
            'id', 'listing', 'media_type', 'category', 'title', 'description',
            'file_url', 'thumbnail_url', 'file_size_mb', 'file_format',
            'sort_order', 'is_primary', 'uploaded_at', 'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']


class PropertyListingListSerializer(serializers.ModelSerializer):
    """Compact serializer for property listing lists/search results"""
    prospector_name = serializers.CharField(source='prospector.display_name', read_only=True)
    prospector_verified = serializers.BooleanField(source='prospector.is_verified', read_only=True)
    primary_mineral_display = serializers.CharField(source='get_primary_mineral_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    exploration_stage_display = serializers.CharField(source='get_exploration_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    country_display = serializers.CharField(source='get_country_display', read_only=True)
    hero_image = serializers.SerializerMethodField()
    is_watchlisted = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = [
            'id', 'slug', 'title', 'summary', 'property_type', 'property_type_display',
            'country', 'country_display', 'province_state', 'region_district',
            'primary_mineral', 'primary_mineral_display', 'exploration_stage',
            'exploration_stage_display', 'listing_type', 'listing_type_display',
            'asking_price', 'price_currency', 'price_negotiable',
            'total_hectares', 'total_acres', 'total_claims',
            'status', 'status_display', 'is_featured',
            'prospector', 'prospector_name', 'prospector_verified',
            'views_count', 'inquiries_count', 'watchlist_count',
            'hero_image', 'is_watchlisted',
            'created_at', 'published_at'
        ]

    def get_hero_image(self, obj):
        hero = obj.media.filter(is_primary=True).first()
        if hero:
            return hero.file_url
        # Fall back to first image
        first_image = obj.media.filter(media_type='image').first()
        return first_image.file_url if first_image else None

    def get_is_watchlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.watchlisted_by.filter(user=request.user).exists()
        return False


class PropertyListingDetailSerializer(serializers.ModelSerializer):
    """Full serializer for property listing detail view"""
    prospector = ProspectorProfileSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)

    # Display values
    primary_mineral_display = serializers.CharField(source='get_primary_mineral_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    exploration_stage_display = serializers.CharField(source='get_exploration_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    country_display = serializers.CharField(source='get_country_display', read_only=True)
    mineral_rights_type_display = serializers.CharField(source='get_mineral_rights_type_display', read_only=True)
    deposit_type_display = serializers.CharField(source='get_deposit_type_display', read_only=True)
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)

    is_watchlisted = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'prospector', 'views_count', 'inquiries_count',
                          'watchlist_count', 'created_at', 'updated_at', 'published_at']

    def get_is_watchlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.watchlisted_by.filter(user=request.user).exists()
        return False

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.prospector.user == request.user
            except:
                return False
        return False


class PropertyListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating property listings"""
    # Allow null for total_claims - will use default value of 1 if not provided
    total_claims = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    # Allow empty description
    description = serializers.CharField(required=False, allow_blank=True)
    # Allow empty summary
    summary = serializers.CharField(required=False, allow_blank=True, max_length=500)

    class Meta:
        model = PropertyListing
        exclude = ['prospector', 'slug', 'views_count', 'inquiries_count',
                  'watchlist_count', 'published_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Generate slug from title
        from django.utils.text import slugify
        import uuid
        base_slug = slugify(validated_data.get('title', 'property'))
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        validated_data['slug'] = unique_slug

        # Set default for total_claims if null or not provided
        if validated_data.get('total_claims') is None:
            validated_data['total_claims'] = 1

        return super().create(validated_data)


class PropertyInquirySerializer(serializers.ModelSerializer):
    """Serializer for property inquiries"""
    inquirer_name = serializers.CharField(source='inquirer.username', read_only=True)
    inquirer_email = serializers.EmailField(source='inquirer.email', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_slug = serializers.SlugField(source='listing.slug', read_only=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PropertyInquiry
        fields = [
            'id', 'listing', 'listing_title', 'listing_slug',
            'inquirer', 'inquirer_name', 'inquirer_email',
            'inquiry_type', 'inquiry_type_display', 'subject', 'message',
            'contact_preference', 'phone_number',
            'status', 'status_display', 'response', 'responded_at',
            'is_nda_signed', 'nda_signed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'inquirer', 'status', 'response', 'responded_at',
                          'created_at', 'updated_at']


class PropertyInquiryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new inquiries"""

    class Meta:
        model = PropertyInquiry
        fields = ['listing', 'inquiry_type', 'subject', 'message', 'contact_preference', 'phone_number']


class PropertyInquiryResponseSerializer(serializers.Serializer):
    """Serializer for responding to inquiries"""
    response = serializers.CharField()


class PropertyWatchlistSerializer(serializers.ModelSerializer):
    """Serializer for watchlist items"""
    listing = PropertyListingListSerializer(read_only=True)

    class Meta:
        model = PropertyWatchlist
        fields = ['id', 'listing', 'notes', 'price_alert', 'added_at']
        read_only_fields = ['id', 'added_at']


class PropertyWatchlistCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding to watchlist"""

    class Meta:
        model = PropertyWatchlist
        fields = ['listing', 'notes', 'price_alert']


class SavedPropertySearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches"""

    class Meta:
        model = SavedPropertySearch
        fields = [
            'id', 'name', 'search_criteria', 'email_alerts',
            'alert_frequency', 'created_at', 'last_alerted_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_alerted_at']


# Choice list serializers for frontend dropdowns
class PropertyChoicesSerializer(serializers.Serializer):
    """Returns all choice options for property forms"""
    property_types = serializers.SerializerMethodField()
    mineral_types = serializers.SerializerMethodField()
    mineral_rights_types = serializers.SerializerMethodField()
    deposit_types = serializers.SerializerMethodField()
    exploration_stages = serializers.SerializerMethodField()
    listing_types = serializers.SerializerMethodField()
    access_types = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    canadian_provinces = serializers.SerializerMethodField()

    def get_property_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.PROPERTY_TYPES]

    def get_mineral_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.MINERAL_TYPES]

    def get_mineral_rights_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.MINERAL_RIGHTS_TYPES]

    def get_deposit_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.DEPOSIT_TYPES]

    def get_exploration_stages(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.EXPLORATION_STAGES]

    def get_listing_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.LISTING_TYPES]

    def get_access_types(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.ACCESS_TYPES]

    def get_countries(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.COUNTRIES]

    def get_canadian_provinces(self, obj):
        return [{'value': k, 'label': v} for k, v in PropertyListing.CANADIAN_PROVINCES]


# ============================================================================
# INQUIRY MESSAGE SERIALIZERS (Conversation Thread)
# ============================================================================

class InquiryMessageSerializer(serializers.ModelSerializer):
    """Serializer for inquiry conversation messages"""
    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    is_from_prospector = serializers.SerializerMethodField()

    class Meta:
        model = InquiryMessage
        fields = [
            'id', 'inquiry', 'sender', 'sender_name', 'sender_email',
            'message', 'is_read', 'is_from_prospector', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

    def get_is_from_prospector(self, obj):
        """Check if message is from the property owner (prospector)"""
        return obj.sender == obj.inquiry.listing.prospector.user


class InquiryMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new inquiry messages"""

    class Meta:
        model = InquiryMessage
        fields = ['message']

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class PropertyInquiryWithMessagesSerializer(serializers.ModelSerializer):
    """Serializer for inquiry detail with full conversation thread"""
    inquirer_name = serializers.CharField(source='inquirer.username', read_only=True)
    inquirer_email = serializers.EmailField(source='inquirer.email', read_only=True)
    inquirer_full_name = serializers.SerializerMethodField()
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_slug = serializers.SlugField(source='listing.slug', read_only=True)
    inquiry_type_display = serializers.CharField(source='get_inquiry_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    messages = InquiryMessageSerializer(many=True, read_only=True)
    prospector_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = PropertyInquiry
        fields = [
            'id', 'listing', 'listing_title', 'listing_slug',
            'inquirer', 'inquirer_name', 'inquirer_email', 'inquirer_full_name',
            'inquiry_type', 'inquiry_type_display', 'subject', 'message',
            'contact_preference', 'phone_number',
            'status', 'status_display', 'response', 'responded_at',
            'is_nda_signed', 'nda_signed_at',
            'messages', 'prospector_name', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'inquirer', 'status', 'response', 'responded_at',
                          'created_at', 'updated_at']

    def get_inquirer_full_name(self, obj):
        return obj.inquirer.get_full_name() or obj.inquirer.username

    def get_prospector_name(self, obj):
        return obj.listing.prospector.display_name or obj.listing.prospector.user.username

    def get_unread_count(self, obj):
        """Count unread messages for the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


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
        from .models import CompanyAccessRequest
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
        from .models import CompanyAccessRequest
        model = CompanyAccessRequest
        fields = ['company', 'role', 'job_title', 'justification', 'work_email']

    def validate_company(self, value):
        """Ensure user doesn't already have a pending request for this company"""
        user = self.context['request'].user
        from .models import CompanyAccessRequest
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
        from .models import CompanyAccessRequest
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
        from .models import CompanyAccessRequest
        return [{'value': k, 'label': v} for k, v in CompanyAccessRequest.ROLE_CHOICES]

    def get_statuses(self, obj):
        from .models import CompanyAccessRequest
        return [{'value': k, 'label': v} for k, v in CompanyAccessRequest.REQUEST_STATUS]


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
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                validated_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
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


# ============================================================================
# STORE MODULE SERIALIZERS
# ============================================================================

class StoreCategorySerializer(serializers.ModelSerializer):
    """Serializer for store categories"""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'slug', 'description', 'display_order',
                  'icon', 'is_active', 'product_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class StoreProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""

    class Meta:
        model = StoreProductImage
        fields = ['id', 'image_url', 'alt_text', 'display_order', 'is_primary']
        read_only_fields = ['id']


class StoreProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants"""
    effective_price_cents = serializers.SerializerMethodField()
    effective_price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreProductVariant
        fields = ['id', 'name', 'sku', 'price_cents_override', 'inventory_count',
                  'is_active', 'display_order', 'effective_price_cents',
                  'effective_price_dollars']
        read_only_fields = ['id']

    def get_effective_price_cents(self, obj):
        return obj.price_cents

    def get_effective_price_dollars(self, obj):
        return obj.price_cents / 100


class StoreDigitalAssetSerializer(serializers.ModelSerializer):
    """Serializer for digital assets (admin view)"""
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = StoreDigitalAsset
        fields = ['id', 'file_name', 'file_size_bytes', 'file_size_mb',
                  'download_limit', 'expiry_hours']
        read_only_fields = ['id']

    def get_file_size_mb(self, obj):
        return round(obj.file_size_bytes / (1024 * 1024), 2) if obj.file_size_bytes else 0


class StoreProductListSerializer(serializers.ModelSerializer):
    """Compact serializer for product list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'short_description', 'price_cents',
                  'price_dollars', 'compare_at_price_cents', 'compare_at_price_dollars',
                  'product_type', 'inventory_count', 'is_featured', 'badges',
                  'total_sold', 'is_on_sale', 'in_stock', 'category_name',
                  'category_slug', 'primary_image', 'created_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        if primary:
            return StoreProductImageSerializer(primary).data
        return None

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None


class StoreProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail views"""
    category = StoreCategorySerializer(read_only=True)
    images = StoreProductImageSerializer(many=True, read_only=True)
    variants = StoreProductVariantSerializer(many=True, read_only=True)
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    requires_inquiry = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'price_cents', 'price_dollars', 'compare_at_price_cents',
                  'compare_at_price_dollars', 'product_type', 'sku',
                  'inventory_count', 'weight_grams', 'is_active', 'is_featured',
                  'badges', 'provenance_info', 'authentication_docs',
                  'total_sold', 'is_on_sale', 'in_stock', 'requires_inquiry',
                  'category', 'images', 'variants', 'created_at', 'updated_at']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None


class StoreCartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = StoreProductListSerializer(read_only=True)
    variant = StoreProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    unit_price_cents = serializers.IntegerField(read_only=True)
    line_total_cents = serializers.IntegerField(read_only=True)
    line_total_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreCartItem
        fields = ['id', 'product', 'variant', 'product_id', 'variant_id',
                  'quantity', 'unit_price_cents', 'line_total_cents',
                  'line_total_dollars', 'added_at']
        read_only_fields = ['id', 'added_at']

    def get_line_total_dollars(self, obj):
        return obj.line_total_cents / 100


class StoreCartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = StoreCartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    subtotal_cents = serializers.IntegerField(read_only=True)
    subtotal_dollars = serializers.SerializerMethodField()
    has_physical_items = serializers.BooleanField(read_only=True)
    has_digital_items = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreCart
        fields = ['id', 'user', 'items', 'item_count', 'subtotal_cents',
                  'subtotal_dollars', 'has_physical_items', 'has_digital_items',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100


class StoreOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    line_total_cents = serializers.IntegerField(read_only=True)
    line_total_dollars = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrderItem
        fields = ['id', 'product_name', 'variant_name', 'quantity',
                  'price_cents', 'price_dollars', 'line_total_cents',
                  'line_total_dollars', 'digital_download_url',
                  'download_count', 'download_expires_at']

    def get_line_total_dollars(self, obj):
        return obj.line_total_cents / 100

    def get_price_dollars(self, obj):
        return obj.price_cents / 100


class StoreOrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    items = StoreOrderItemSerializer(many=True, read_only=True)
    total_dollars = serializers.SerializerMethodField()
    subtotal_dollars = serializers.SerializerMethodField()
    shipping_dollars = serializers.SerializerMethodField()
    tax_dollars = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StoreOrder
        fields = ['id', 'status', 'status_display', 'subtotal_cents',
                  'subtotal_dollars', 'shipping_cents', 'shipping_dollars',
                  'tax_cents', 'tax_dollars', 'total_cents', 'total_dollars',
                  'currency', 'shipping_address', 'shipping_rate_name',
                  'tracking_number', 'items', 'created_at', 'paid_at',
                  'shipped_at', 'delivered_at']
        read_only_fields = ['id', 'created_at']

    def get_total_dollars(self, obj):
        return obj.total_cents / 100

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100

    def get_shipping_dollars(self, obj):
        return obj.shipping_cents / 100

    def get_tax_dollars(self, obj):
        return obj.tax_cents / 100


class StoreShippingRateSerializer(serializers.ModelSerializer):
    """Serializer for shipping rates"""
    price_dollars = serializers.SerializerMethodField()
    delivery_estimate = serializers.SerializerMethodField()

    class Meta:
        model = StoreShippingRate
        fields = ['id', 'name', 'description', 'price_cents', 'price_dollars',
                  'estimated_days_min', 'estimated_days_max', 'delivery_estimate',
                  'countries']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_delivery_estimate(self, obj):
        if obj.estimated_days_min == obj.estimated_days_max:
            return f"{obj.estimated_days_min} business days"
        return f"{obj.estimated_days_min}-{obj.estimated_days_max} business days"


class StoreRecentPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for The Ticker recent purchases"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    amount_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreRecentPurchase
        fields = ['id', 'product_name', 'product_slug', 'product_image',
                  'location', 'amount_dollars', 'is_anonymous', 'created_at']

    def get_product_image(self, obj):
        primary = obj.product.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.product.images.first()
        return primary.image_url if primary else None

    def get_location(self, obj):
        if obj.city and obj.country:
            return f"{obj.city}, {obj.country}"
        return obj.country or "Unknown"

    def get_amount_dollars(self, obj):
        return obj.amount_cents / 100


class StoreProductShareSerializer(serializers.ModelSerializer):
    """Serializer for product shares"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StoreProductShare
        fields = ['id', 'user', 'username', 'product', 'product_name',
                  'shared_to', 'destination_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class StoreProductInquirySerializer(serializers.ModelSerializer):
    """Serializer for product inquiries (high-value items)"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StoreProductInquiry
        fields = ['id', 'user', 'user_email', 'product', 'product_name',
                  'status', 'status_display', 'message', 'phone',
                  'preferred_contact', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class StoreProductInquiryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product inquiries"""

    class Meta:
        model = StoreProductInquiry
        fields = ['product', 'message', 'phone', 'preferred_contact']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserStoreBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user store badges"""
    badge_display = serializers.CharField(source='get_badge_type_display', read_only=True)
    total_spent_dollars = serializers.SerializerMethodField()

    class Meta:
        model = UserStoreBadge
        fields = ['id', 'badge_type', 'badge_display', 'earned_at',
                  'total_spent_cents', 'total_spent_dollars', 'order_count']

    def get_total_spent_dollars(self, obj):
        return obj.total_spent_cents / 100


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        try:
            product = StoreProduct.objects.get(id=value, is_active=True)
            if not product.in_stock:
                raise serializers.ValidationError("This product is out of stock")
            if product.requires_inquiry:
                raise serializers.ValidationError(
                    "This item requires an inquiry. Please use the inquiry form."
                )
        except StoreProduct.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        return value

    def validate(self, data):
        product = StoreProduct.objects.get(id=data['product_id'])
        variant_id = data.get('variant_id')

        if variant_id:
            try:
                variant = product.variants.get(id=variant_id, is_active=True)
                if variant.inventory_count < data['quantity']:
                    raise serializers.ValidationError(
                        {"quantity": f"Only {variant.inventory_count} available"}
                    )
            except StoreProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"variant_id": "Variant not found for this product"}
                )
        else:
            if product.product_type == 'physical' and product.inventory_count < data['quantity']:
                raise serializers.ValidationError(
                    {"quantity": f"Only {product.inventory_count} available"}
                )

        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=0)


class CheckoutSerializer(serializers.Serializer):
    """Serializer for initiating checkout"""
    shipping_address = serializers.JSONField(required=False)
    shipping_rate_id = serializers.IntegerField(required=False, allow_null=True)
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()

    def validate_shipping_address(self, value):
        if value:
            required_fields = ['name', 'line1', 'city', 'state', 'postal_code', 'country']
            missing = [f for f in required_fields if not value.get(f)]
            if missing:
                raise serializers.ValidationError(
                    f"Missing required fields: {', '.join(missing)}"
                )
            # Validate North America only
            if value.get('country') not in ['US', 'CA']:
                raise serializers.ValidationError(
                    "Shipping is only available to the United States and Canada"
                )
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Get or create cart for user
            cart = StoreCart.objects.filter(user=request.user).first()
            if not cart or not cart.items.exists():
                raise serializers.ValidationError("Your cart is empty")

            # Check if shipping info needed
            if cart.has_physical_items and not data.get('shipping_address'):
                raise serializers.ValidationError(
                    {"shipping_address": "Shipping address required for physical items"}
                )

            if cart.has_physical_items and not data.get('shipping_rate_id'):
                raise serializers.ValidationError(
                    {"shipping_rate_id": "Please select a shipping option"}
                )

        return data


# ============================================================================
# Store Admin Serializers
# ============================================================================

class StoreProductImageAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for product images - allows full CRUD"""

    class Meta:
        model = StoreProductImage
        fields = ['id', 'image_url', 'alt_text', 'display_order', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class StoreProductVariantAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for product variants - allows full CRUD"""
    effective_price_cents = serializers.SerializerMethodField()

    class Meta:
        model = StoreProductVariant
        fields = ['id', 'name', 'sku', 'price_cents_override', 'inventory_count',
                  'is_active', 'display_order', 'effective_price_cents', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_effective_price_cents(self, obj):
        return obj.price_cents


class StoreDigitalAssetAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for digital assets"""
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = StoreDigitalAsset
        fields = ['id', 'file_url', 'file_name', 'file_size_bytes', 'file_size_mb',
                  'download_limit', 'expiry_hours', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_file_size_mb(self, obj):
        return round(obj.file_size_bytes / (1024 * 1024), 2) if obj.file_size_bytes else 0


class StoreCategoryAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for categories - allows full CRUD"""
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreCategory
        fields = ['id', 'name', 'slug', 'description', 'display_order',
                  'icon', 'is_active', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_product_count(self, obj):
        return obj.products.count()


class StoreProductAdminListSerializer(serializers.ModelSerializer):
    """Admin serializer for product list view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_dollars = serializers.SerializerMethodField()
    variant_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'price_cents',
                  'price_dollars', 'product_type', 'inventory_count', 'is_active',
                  'is_featured', 'badges', 'total_sold', 'primary_image',
                  'variant_count', 'image_count', 'created_at', 'updated_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        return primary.image_url if primary else None

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_variant_count(self, obj):
        return obj.variants.count()

    def get_image_count(self, obj):
        return obj.images.count()


class StoreProductAdminDetailSerializer(serializers.ModelSerializer):
    """Admin serializer for product detail/edit view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = StoreProductImageAdminSerializer(many=True, read_only=True)
    variants = StoreProductVariantAdminSerializer(many=True, read_only=True)
    digital_assets = StoreDigitalAssetAdminSerializer(many=True, read_only=True)
    price_dollars = serializers.SerializerMethodField()
    compare_at_price_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'category', 'category_name', 'price_cents', 'price_dollars',
                  'compare_at_price_cents', 'compare_at_price_dollars',
                  'product_type', 'sku', 'inventory_count', 'weight_grams',
                  'is_active', 'is_featured', 'badges', 'provenance_info',
                  'authentication_docs', 'min_price_for_inquiry', 'total_sold',
                  'images', 'variants', 'digital_assets', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_sold', 'created_at', 'updated_at']

    def get_price_dollars(self, obj):
        return obj.price_cents / 100

    def get_compare_at_price_dollars(self, obj):
        return obj.compare_at_price_cents / 100 if obj.compare_at_price_cents else None


class StoreProductAdminCreateSerializer(serializers.ModelSerializer):
    """Admin serializer for creating/updating products"""
    images = StoreProductImageAdminSerializer(many=True, required=False)
    variants = StoreProductVariantAdminSerializer(many=True, required=False)

    class Meta:
        model = StoreProduct
        fields = ['id', 'name', 'slug', 'description', 'short_description',
                  'category', 'price_cents', 'compare_at_price_cents',
                  'product_type', 'sku', 'inventory_count', 'weight_grams',
                  'is_active', 'is_featured', 'badges', 'provenance_info',
                  'authentication_docs', 'min_price_for_inquiry',
                  'images', 'variants']
        read_only_fields = ['id']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])

        product = StoreProduct.objects.create(**validated_data)

        # Create images
        for idx, image_data in enumerate(images_data):
            StoreProductImage.objects.create(
                product=product,
                display_order=idx,
                **image_data
            )

        # Create variants
        for idx, variant_data in enumerate(variants_data):
            StoreProductVariant.objects.create(
                product=product,
                display_order=idx,
                **variant_data
            )

        return product

    def update(self, instance, validated_data):
        # Remove nested data - these are handled separately
        validated_data.pop('images', None)
        validated_data.pop('variants', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class StoreOrderAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for viewing orders"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    items = serializers.SerializerMethodField()
    subtotal_dollars = serializers.SerializerMethodField()
    shipping_dollars = serializers.SerializerMethodField()
    tax_dollars = serializers.SerializerMethodField()
    total_dollars = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrder
        fields = ['id', 'user', 'user_email', 'user_name', 'status',
                  'subtotal_cents', 'subtotal_dollars', 'shipping_cents',
                  'shipping_dollars', 'tax_cents', 'tax_dollars',
                  'total_cents', 'total_dollars', 'shipping_address',
                  'customer_email', 'tracking_number', 'shipped_at',
                  'delivered_at', 'paid_at', 'items', 'created_at']

    def get_items(self, obj):
        return [{
            'id': item.id,
            'product_name': item.product_name,
            'variant_name': item.variant_name,
            'quantity': item.quantity,
            'price_cents': item.price_cents,
            'price_dollars': item.price_cents / 100,
        } for item in obj.items.all()]

    def get_subtotal_dollars(self, obj):
        return obj.subtotal_cents / 100

    def get_shipping_dollars(self, obj):
        return obj.shipping_cents / 100

    def get_tax_dollars(self, obj):
        return obj.tax_cents / 100

    def get_total_dollars(self, obj):
        return obj.total_cents / 100


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
