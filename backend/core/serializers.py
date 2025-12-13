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
    PropertyWatchlist, SavedPropertySearch, ProspectorCommissionAgreement
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

    class Meta:
        model = Company
        fields = '__all__'


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
            'inquiry_type', 'inquiry_type_display', 'message',
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
        fields = ['listing', 'inquiry_type', 'message', 'contact_preference', 'phone_number']


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
