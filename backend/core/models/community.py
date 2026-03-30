from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .users import User, Company
from .mining import Investor




class InvestorCommunication(models.Model):
    """Track communications with investors"""
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'In-Person Meeting'),
        ('video_call', 'Video Call'),
        ('conference', 'Conference Meeting'),
        ('site_visit', 'Site Visit'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='investor_comms')
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='communications')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text="Company user who logged this")

    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    communication_date = models.DateTimeField()

    subject = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    followup_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investor_communications'
        ordering = ['-communication_date']


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================




# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

class CompanyMetrics(models.Model):
    """Quarterly/Annual metrics snapshot"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='metrics')
    period_end_date = models.DateField()

    # Financial
    cash_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    working_capital_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    burn_rate_monthly_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    runway_months = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # Operations
    meters_drilled_period = models.IntegerField(null=True, blank=True)

    # Valuation metrics
    ev_per_resource_oz = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_metrics'
        ordering = ['-period_end_date']
        unique_together = ['company', 'period_end_date']


# ============================================================================
# WATCHLISTS & ALERTS
# ============================================================================




# ============================================================================
# WATCHLISTS & ALERTS
# ============================================================================

class Watchlist(models.Model):
    """User watchlists for tracking companies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    companies = models.ManyToManyField(Company, related_name='in_watchlists')

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'watchlists'
        ordering = ['name']




class Alert(models.Model):
    """Price alerts, news alerts, etc."""
    ALERT_TYPES = [
        ('price_above', 'Price Above'),
        ('price_below', 'Price Below'),
        ('volume_spike', 'Volume Spike'),
        ('news_release', 'News Release'),
        ('financing', 'New Financing'),
        ('resource_update', 'Resource Update'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='alerts')

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    threshold_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'




# ============================================================================
# REAL-TIME FORUM MODELS
# ============================================================================

class ForumDiscussion(models.Model):
    """Discussion thread for a company"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='forum_discussions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_discussions')

    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    # Stats
    message_count = models.IntegerField(default=0)
    participant_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'forum_discussions'
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['company', 'is_active', '-updated_at']),
            models.Index(fields=['company', 'is_archived']),
            models.Index(fields=['-is_pinned', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.company.name}: {self.title}"




class ForumMessage(models.Model):
    """Individual message in a discussion"""
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_messages')
    content = models.TextField()

    # Threading support
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')

    # Moderation
    is_pinned = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'forum_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['discussion', 'created_at']),
            models.Index(fields=['discussion', 'is_pinned', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['discussion', 'is_deleted', 'created_at']),
        ]

    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.user.username}: {content_preview}"




class GuestSpeakerSession(models.Model):
    """Scheduled Q&A session with guest speakers"""
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='guest_sessions')
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='guest_sessions')
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')

    # Settings
    is_moderated = models.BooleanField(default=True)
    allow_anonymous_questions = models.BooleanField(default=False)
    max_participants = models.IntegerField(null=True, blank=True)

    # Stats
    total_questions = models.IntegerField(default=0)
    total_participants = models.IntegerField(default=0)

    # Archive
    is_archived = models.BooleanField(default=False)
    archive_url = models.URLField(blank=True)
    transcript_url = models.URLField(blank=True)
    transcript_content = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'guest_speaker_sessions'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['company', 'scheduled_start']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['company', 'status', '-scheduled_start']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"




class SessionSpeaker(models.Model):
    """Guest speakers for a session"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='speakers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='speaker_sessions')

    # Speaker details
    role = models.CharField(max_length=100, blank=True)  # e.g., "CEO", "CFO", "Geologist"
    bio = models.TextField(blank=True)

    # Status
    is_primary = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)

    # Stats
    questions_answered = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_speakers'
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"




class SessionModerator(models.Model):
    """Moderators for a guest speaker session"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='moderators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderated_sessions')

    # Permissions
    can_approve_questions = models.BooleanField(default=True)
    can_reject_questions = models.BooleanField(default=True)
    can_delete_messages = models.BooleanField(default=True)
    can_control_session = models.BooleanField(default=False)  # Start/end session

    # Stats
    questions_approved = models.IntegerField(default=0)
    questions_rejected = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_moderators'
        unique_together = [['session', 'user']]

    def __str__(self):
        return f"{self.user.username} - Moderator for {self.session.title}"




class SessionQuestion(models.Model):
    """Questions asked during guest speaker sessions"""
    QUESTION_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
    ]

    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='questions')
    message = models.ForeignKey(ForumMessage, on_delete=models.CASCADE, related_name='session_question')
    asked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')

    # Status
    status = models.CharField(max_length=20, choices=QUESTION_STATUS, default='pending')
    priority = models.IntegerField(default=0)  # Higher = more important

    # Moderation
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_questions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Engagement
    upvote_count = models.IntegerField(default=0)

    # Answer tracking
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )
    answered_at = models.DateTimeField(null=True, blank=True)
    answer_message = models.ForeignKey(
        ForumMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answer_to_question'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_questions'
        ordering = ['-priority', '-upvote_count', 'created_at']
        indexes = [
            models.Index(fields=['session', 'status', '-priority']),
            models.Index(fields=['session', '-upvote_count']),
            models.Index(fields=['asked_by', '-created_at']),
        ]

    def __str__(self):
        content = self.message.content[:50] + '...' if len(self.message.content) > 50 else self.message.content
        return f"Q: {content} ({self.get_status_display()})"




class QuestionUpvote(models.Model):
    """Track which users upvoted which questions"""
    question = models.ForeignKey(SessionQuestion, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_upvotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'question_upvotes'
        unique_together = [['question', 'user']]
        indexes = [
            models.Index(fields=['question', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} upvoted question {self.question.id}"




class UserPresence(models.Model):
    """Track user online/offline status in discussions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presences')
    discussion = models.ForeignKey(ForumDiscussion, on_delete=models.CASCADE, related_name='user_presences')

    # Status
    is_online = models.BooleanField(default=False)
    is_typing = models.BooleanField(default=False)

    # Connection tracking
    connection_id = models.CharField(max_length=255, blank=True)  # WebSocket connection ID

    # Timestamps
    last_seen = models.DateTimeField(auto_now=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_presence'
        unique_together = [['user', 'discussion']]
        indexes = [
            models.Index(fields=['discussion', 'is_online']),
            models.Index(fields=['user', 'discussion']),
            models.Index(fields=['discussion', 'is_typing']),
        ]

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        typing = " (typing)" if self.is_typing else ""
        return f"{self.user.username} - {status}{typing}"




class SessionNotification(models.Model):
    """User notifications for guest speaker sessions"""
    NOTIFICATION_TYPE = [
        ('session_reminder_24h', '24 Hour Reminder'),
        ('session_reminder_1h', '1 Hour Reminder'),
        ('session_starting', 'Session Starting'),
        ('session_live', 'Session Live Now'),
        ('session_ended', 'Session Ended'),
        ('question_approved', 'Question Approved'),
        ('question_answered', 'Question Answered'),
        ('speaker_response', 'Speaker Responded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_notifications')
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE)

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.URLField(blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # Related objects
    related_question = models.ForeignKey(
        SessionQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Timestamps
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['session', 'notification_type']),
            models.Index(fields=['is_sent', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"




class SessionParticipant(models.Model):
    """Track participants in guest speaker sessions"""
    session = models.ForeignKey(GuestSpeakerSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attended_sessions')

    # Participation tracking
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_currently_active = models.BooleanField(default=True)

    # Engagement stats
    messages_sent = models.IntegerField(default=0)
    questions_asked = models.IntegerField(default=0)
    questions_upvoted = models.IntegerField(default=0)

    class Meta:
        db_table = 'session_participants'
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session', 'is_currently_active']),
            models.Index(fields=['user', '-joined_at']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.session.title}"


# ============================================================================
# GUEST SPEAKER EVENT MODELS
# ============================================================================




# ============================================================================
# GUEST SPEAKER EVENT MODELS
# ============================================================================

class SpeakerEvent(models.Model):
    """Scheduled guest speaker event for companies"""
    EVENT_FORMAT = [
        ('video', 'Video Stream'),
        ('text', 'Text Chat'),
    ]
    EVENT_STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='speaker_events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')

    # Event Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    topic = models.CharField(max_length=255)
    agenda = models.TextField(blank=True)

    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    duration_minutes = models.IntegerField()

    # Format & Capacity
    format = models.CharField(max_length=10, choices=EVENT_FORMAT, default='text')
    max_participants = models.IntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='draft')
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Streaming & Recording
    stream_url = models.URLField(blank=True, help_text="Live stream embed URL (YouTube, Twitch, etc.)")
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    transcript_url = models.URLField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats (denormalized for performance)
    registered_count = models.IntegerField(default=0)
    attended_count = models.IntegerField(default=0)
    questions_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['-scheduled_start']),
        ]

    def __str__(self):
        return f"{self.title} - {self.company.name}"




class EventSpeaker(models.Model):
    """Speaker assigned to an event"""
    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='speakers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='speaking_events')
    title = models.CharField(max_length=255)  # CEO, CFO, Lead Geologist, etc.
    bio = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"




class EventRegistration(models.Model):
    """User registration for an event"""
    REGISTRATION_STATUS = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='registered')

    # Notifications
    reminder_sent = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', '-registered_at']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"




class EventQuestion(models.Model):
    """Question submitted during event"""
    QUESTION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_questions')

    content = models.TextField()
    status = models.CharField(max_length=20, choices=QUESTION_STATUS, default='pending')
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='answered_event_questions')

    upvotes = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-upvotes', '-created_at']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['-upvotes', '-created_at']),
        ]

    def __str__(self):
        return f"Q: {self.content[:50]}..."




class EventReaction(models.Model):
    """Participant engagement reactions"""
    REACTION_TYPE = [
        ('applause', 'Applause'),
        ('thumbs_up', 'Thumbs Up'),
        ('fire', 'Fire'),
        ('heart', 'Heart'),
    ]

    event = models.ForeignKey(SpeakerEvent, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event', 'reaction_type']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.reaction_type}"


# ============================================================================
# FINANCIAL HUB - INVESTOR EDUCATION & QUALIFICATION
# ============================================================================




# ============================================================================
# GLOSSARY MODEL
# ============================================================================

class GlossaryTerm(models.Model):
    """Mining industry glossary terms for SEO and chatbot knowledge"""

    CATEGORY_CHOICES = [
        ('reporting', 'Reporting & Standards'),
        ('geology', 'Geology & Resources'),
        ('finance', 'Finance & Investment'),
        ('regulatory', 'Regulatory & Legal'),
        ('operations', 'Mining Operations'),
        ('general', 'General Terms'),
    ]

    term = models.CharField(max_length=200, unique=True, db_index=True)
    definition = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    related_links = models.JSONField(default=list, blank=True, help_text='List of related links with text and url fields')

    # SEO fields
    keywords = models.CharField(max_length=500, blank=True, help_text='Comma-separated keywords for SEO')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='glossary_terms_created')

    class Meta:
        db_table = 'glossary_terms'
        ordering = ['term']
        verbose_name = 'Glossary Term'
        verbose_name_plural = 'Glossary Terms'

    def __str__(self):
        return self.term

    @property
    def first_letter(self):
        """Get the first letter of the term for alphabetical grouping"""
        return self.term[0].upper() if self.term else ''




class GlossaryTermSubmission(models.Model):
    """User-submitted glossary terms pending superuser approval"""

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Submission data (matches GlossaryTerm fields)
    term = models.CharField(max_length=200, db_index=True)
    definition = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=GlossaryTerm.CATEGORY_CHOICES,
        default='general'
    )
    related_links = models.JSONField(
        default=list,
        blank=True,
        help_text='List of related links with text and url fields'
    )
    keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated keywords for SEO'
    )

    # Submission metadata
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='glossary_submissions'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Approval workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='glossary_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Reference to approved term (if approved)
    approved_term = models.ForeignKey(
        GlossaryTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_submission'
    )

    # Audit
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'glossary_term_submissions'
        ordering = ['-submitted_at']
        verbose_name = 'Glossary Term Submission'
        verbose_name_plural = 'Glossary Term Submissions'
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['submitted_by', '-submitted_at']),
        ]

    def __str__(self):
        return f"{self.term} - {self.get_status_display()}"

    def approve(self, reviewer):
        """Approve submission and create GlossaryTerm"""
        from django.utils import timezone

        # Create the approved glossary term
        approved_term = GlossaryTerm.objects.create(
            term=self.term,
            definition=self.definition,
            category=self.category,
            related_links=self.related_links,
            keywords=self.keywords,
            created_by=self.submitted_by
        )

        # Update submission status
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.approved_term = approved_term
        self.save()

        return approved_term

    def reject(self, reviewer, reason=''):
        """Reject submission"""
        from django.utils import timezone

        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()




class UserAIUsage(models.Model):
    """
    Track AI chat usage per user for cost control.
    Prevents unlimited API spend by enforcing daily limits.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='ai_usage'
    )

    # Daily counters (reset at midnight)
    messages_today = models.IntegerField(default=0, help_text="Messages sent today")
    tokens_today = models.IntegerField(default=0, help_text="Total tokens used today (input + output)")
    last_reset_date = models.DateField(auto_now_add=True, help_text="Date of last counter reset")

    # Lifetime stats
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    # Limits (can be customized per user)
    daily_message_limit = models.IntegerField(default=50, help_text="Max messages per day (0 = unlimited)")
    daily_token_limit = models.IntegerField(default=100000, help_text="Max tokens per day (0 = unlimited)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_ai_usage'
        verbose_name = 'User AI Usage'
        verbose_name_plural = 'User AI Usage'

    def __str__(self):
        return f"{self.user.username}: {self.messages_today} msgs today"

    def reset_if_new_day(self):
        """Reset daily counters if it's a new day."""
        from datetime import date
        today = date.today()
        if self.last_reset_date < today:
            self.messages_today = 0
            self.tokens_today = 0
            self.last_reset_date = today
            self.save(update_fields=['messages_today', 'tokens_today', 'last_reset_date'])

    def can_send_message(self) -> tuple:
        """Check if user can send a message. Returns (allowed, error_message)."""
        self.reset_if_new_day()

        if self.daily_message_limit > 0 and self.messages_today >= self.daily_message_limit:
            return False, f"Daily message limit reached ({self.daily_message_limit} messages). Resets at midnight."

        if self.daily_token_limit > 0 and self.tokens_today >= self.daily_token_limit:
            return False, f"Daily token limit reached ({self.daily_token_limit:,} tokens). Resets at midnight."

        return True, None

    def record_usage(self, tokens_used: int = 0):
        """Record a message and token usage."""
        self.reset_if_new_day()
        self.messages_today += 1
        self.tokens_today += tokens_used
        self.total_messages += 1
        self.total_tokens += tokens_used
        self.save()


# ============================================================================
# FAILED TASK LOG - Dead Letter Queue for Celery
# ============================================================================

