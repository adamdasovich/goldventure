"""
DRF Serializers for GoldVenture Platform
Convert Django models to/from JSON
"""

from rest_framework import serializers
from .users import UserSerializer
from .companies import CompanySerializer
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
        fields = [
            'id', 'company', 'created_by',
            'title', 'description', 'topic', 'agenda',
            'scheduled_start', 'scheduled_end', 'timezone', 'duration_minutes',
            'format', 'max_participants',
            'status', 'actual_start', 'actual_end',
            'stream_url', 'is_recorded', 'recording_url', 'transcript_url',
            'registered_count', 'attended_count', 'questions_count',
            'created_at', 'updated_at',
            # Nested serializers
            'speakers', 'registrations', 'questions',
            # Method fields
            'is_registered', 'can_register', 'user_registration',
        ]
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

