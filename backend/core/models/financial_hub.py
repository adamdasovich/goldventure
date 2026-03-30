from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .users import User, Company
from .mining import Financing




# ============================================================================
# FINANCIAL HUB - INVESTOR EDUCATION & QUALIFICATION
# ============================================================================

class EducationalModule(models.Model):
    """Educational content modules for investor education"""
    MODULE_TYPES = [
        ('basics', 'Mining Financing Basics'),
        ('regulations', 'Canadian Securities Regulations'),
        ('investor_rights', 'Investor Rights & Obligations'),
        ('risk_disclosure', 'Risk Disclosures'),
        ('subscription_agreement', 'Subscription Agreement Guide'),
        ('drs', 'Direct Registration System (DRS)'),
    ]

    module_type = models.CharField(max_length=30, choices=MODULE_TYPES, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Content
    content = models.TextField(help_text="HTML/Markdown content")
    estimated_read_time_minutes = models.IntegerField(default=5)

    # Ordering
    sort_order = models.IntegerField(default=0)

    # Status
    is_published = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False, help_text="Required for accreditation process")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'educational_modules'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title




class ModuleCompletion(models.Model):
    """Track user completion of educational modules"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_completions')
    module = models.ForeignKey(EducationalModule, on_delete=models.CASCADE, related_name='completions')

    # Tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)

    # Quiz/Assessment (optional)
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        db_table = 'module_completions'
        unique_together = ['user', 'module']
        indexes = [
            models.Index(fields=['user', 'completed_at']),
            models.Index(fields=['module', '-completed_at']),
        ]

    def __str__(self):
        status = "Completed" if self.completed_at else "In Progress"
        return f"{self.user.username} - {self.module.title} ({status})"




class AccreditedInvestorQualification(models.Model):
    """Store accredited investor qualification results"""
    QUALIFICATION_STATUS = [
        ('pending', 'Pending Review'),
        ('qualified', 'Qualified'),
        ('not_qualified', 'Not Qualified'),
        ('expired', 'Expired'),
    ]

    QUALIFICATION_CRITERIA = [
        ('income_individual', 'Individual Income >$200k'),
        ('income_combined', 'Combined Income >$300k'),
        ('financial_assets', 'Financial Assets ≥$1M'),
        ('net_assets', 'Net Assets ≥$5M'),
        ('entity_assets', 'Entity with Assets ≥$5M'),
        ('professional', 'Registered Dealer/Adviser'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accreditation_qualifications')

    # Qualification Details
    status = models.CharField(max_length=20, choices=QUALIFICATION_STATUS, default='pending')
    criteria_met = models.CharField(max_length=30, choices=QUALIFICATION_CRITERIA, null=True, blank=True)

    # Questionnaire Responses (JSON)
    questionnaire_responses = models.JSONField(default=dict, help_text="Stores all questionnaire answers")

    # Supporting Documentation
    documents_submitted = models.BooleanField(default=False)
    documents_verified = models.BooleanField(default=False)

    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_qualifications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Validity
    qualified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accredited_investor_qualifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


# ============================================================================
# FINANCIAL HUB - SUBSCRIPTION AGREEMENTS & INVESTMENTS
# ============================================================================




# ============================================================================
# FINANCIAL HUB - SUBSCRIPTION AGREEMENTS & INVESTMENTS
# ============================================================================

class SubscriptionAgreement(models.Model):
    """Subscription agreement for financing participation"""
    AGREEMENT_STATUS = [
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('accepted', 'Accepted by Company'),
        ('funded', 'Funded'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    # Parties
    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='subscription_agreements')
    financing = models.ForeignKey(Financing, on_delete=models.PROTECT, related_name='subscription_agreements')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='subscription_agreements')

    # Investment Details
    num_shares = models.BigIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=4)
    total_investment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Warrants (if applicable)
    includes_warrants = models.BooleanField(default=False)
    warrant_shares = models.BigIntegerField(null=True, blank=True)
    warrant_strike_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    warrant_expiry_date = models.DateField(null=True, blank=True)

    # Agreement Status
    status = models.CharField(max_length=30, choices=AGREEMENT_STATUS, default='draft')

    # Document Management
    agreement_pdf_url = models.URLField(blank=True)
    docusign_envelope_id = models.CharField(max_length=255, blank=True)

    # Signature Tracking
    investor_signed_at = models.DateTimeField(null=True, blank=True)
    investor_ip_address = models.GenericIPAddressField(null=True, blank=True)
    company_accepted_at = models.DateTimeField(null=True, blank=True)
    company_accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_agreements'
    )

    # Payment Tracking
    payment_instructions_sent_at = models.DateTimeField(null=True, blank=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)

    # DRS & Share Issuance
    shares_issued = models.BooleanField(default=False)
    shares_issued_at = models.DateTimeField(null=True, blank=True)
    drs_statement_sent_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)

    # Legal & Compliance
    accreditation_verified = models.BooleanField(default=False)
    kyc_completed = models.BooleanField(default=False)
    aml_check_completed = models.BooleanField(default=False)

    # Notes
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_subscription_agreements'
    )

    class Meta:
        db_table = 'subscription_agreements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['docusign_envelope_id']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.investor.username} - {self.company.name} - ${self.total_investment_amount:,.2f}"

    def soft_delete(self, user=None):
        """Soft delete this subscription agreement record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted subscription agreement record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])




class InvestmentTransaction(models.Model):
    """Track individual investment transactions and their lifecycle"""
    TRANSACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('payment_pending', 'Payment Pending'),
        ('payment_received', 'Payment Received'),
        ('shares_issued', 'Shares Issued'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='investment_transactions')
    financing = models.ForeignKey(Financing, on_delete=models.PROTECT, related_name='investment_transactions')

    # Transaction Details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')

    # Payment Details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    # Share Allocation
    shares_allocated = models.BigIntegerField(null=True, blank=True)
    price_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_investment_transactions'
    )

    class Meta:
        db_table = 'investment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.financing.company.name} - ${self.amount:,.2f}"

    def soft_delete(self, user=None):
        """Soft delete this investment transaction record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted investment transaction record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])




class FinancingAggregate(models.Model):
    """Aggregate investment data for financing rounds"""
    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    financing = models.OneToOneField(Financing, on_delete=models.PROTECT, related_name='aggregate_data')

    # Subscription Metrics
    total_subscriptions = models.IntegerField(default=0)
    total_subscribers = models.IntegerField(default=0)

    # Amount Metrics
    total_committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_funded_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_shares_allocated = models.BigIntegerField(default=0)

    # Status Breakdown (JSON)
    status_breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown by agreement status: {draft: 2, signed: 5, funded: 10}"
    )

    # Investor Type Breakdown (JSON)
    investor_type_breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown by investor type: {individual: 8, institutional: 2}"
    )

    # Last Updated
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financing_aggregates'

    def __str__(self):
        return f"{self.financing.company.name} - {self.financing.financing_type} Aggregate"




class PaymentInstruction(models.Model):
    """Payment instructions for financing participations"""
    PAYMENT_METHOD = [
        ('wire', 'Wire Transfer'),
        ('ach', 'ACH Transfer'),
        ('check', 'Check'),
        ('crypto', 'Cryptocurrency'),
    ]

    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    subscription_agreement = models.OneToOneField(
        SubscriptionAgreement,
        on_delete=models.PROTECT,
        related_name='payment_instruction'
    )
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='payment_instructions')

    # Payment Method
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)

    # Banking Details (encrypted in production)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=255, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)

    # Additional Instructions
    reference_code = models.CharField(max_length=100, help_text="Unique reference for payment tracking")
    special_instructions = models.TextField(blank=True)

    # Tracking
    sent_to_investor_at = models.DateTimeField(null=True, blank=True)
    viewed_by_investor_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_payment_instructions'
    )

    class Meta:
        db_table = 'payment_instructions'
        indexes = [
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.subscription_agreement.investor.username} - {self.get_payment_method_display()}"

    def soft_delete(self, user=None):
        """Soft delete this payment instruction record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted payment instruction record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])




class DRSDocument(models.Model):
    """DRS (Direct Registration System) documents and delivery tracking"""
    DOCUMENT_TYPE = [
        ('statement', 'DRS Statement'),
        ('certificate', 'Share Certificate'),
        ('confirmation', 'Issuance Confirmation'),
        ('educational', 'DRS Educational Material'),
    ]

    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.PROTECT,
        related_name='drs_documents',
        null=True,
        blank=True
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='drs_documents')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='drs_documents')

    # Document Details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE)
    document_url = models.URLField(blank=True)
    document_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash for verification")

    # Share Details (for statements/certificates)
    num_shares = models.BigIntegerField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(null=True, blank=True)

    # Delivery Tracking
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=50, blank=True, help_text="email, postal, etc")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_drs_documents'
    )

    class Meta:
        db_table = 'drs_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['subscription_agreement', '-created_at']),
            models.Index(fields=['delivery_status', '-created_at']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()} - {self.company.name}"

    def soft_delete(self, user=None):
        """Soft delete this DRS document record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted DRS document record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


# ============================================================================
# PROSPECTOR PROPERTY EXCHANGE MODELS
# ============================================================================




# ============================================================================
# INVESTMENT INTEREST REGISTRATION
# ============================================================================

class InvestmentInterest(models.Model):
    """
    Tracks investor interest in financing rounds.
    This is the initial registration step before formal subscription agreements.
    Used for lead generation and investor qualification.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('qualified', 'Qualified'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted to Subscription'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    # Core relationships
    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='investment_interests')
    financing = models.ForeignKey(Financing, on_delete=models.PROTECT, related_name='investment_interests')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='investment_interests')

    # Accreditation
    is_accredited_investor = models.BooleanField(
        help_text="User confirmed they are an accredited investor"
    )
    accreditation_confirmed_at = models.DateTimeField(auto_now_add=True)

    # Investment details
    shares_requested = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares the investor is interested in"
    )
    price_per_share = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Price per share at time of interest registration"
    )
    investment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total investment amount (shares * price)"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Document confirmations
    term_sheet_confirmed = models.BooleanField(default=False)
    term_sheet_confirmed_at = models.DateTimeField(null=True, blank=True)
    subscription_agreement_confirmed = models.BooleanField(default=False)
    subscription_agreement_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Contact information
    contact_email = models.EmailField(
        help_text="Email for follow-up communications"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for follow-up"
    )

    # Risk acknowledgment
    risk_acknowledged = models.BooleanField(
        default=False,
        help_text="User acknowledged investment risks"
    )
    risk_acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    status_notes = models.TextField(blank=True)

    # Linked subscription agreement (if converted)
    subscription_agreement = models.ForeignKey(
        SubscriptionAgreement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interest_registrations'
    )

    # Tracking/audit fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete fields (financial records should never be hard deleted)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_investment_interests'
    )

    class Meta:
        db_table = 'investment_interests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'financing']),
            models.Index(fields=['financing', 'status']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_accredited_investor']),
            models.Index(fields=['is_deleted']),
        ]
        # Prevent duplicate interests from same user for same financing
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'financing'],
                name='unique_user_financing_interest'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.company.name} - ${self.investment_amount:,.2f}"

    def save(self, *args, **kwargs):
        # Auto-calculate investment amount
        if self.shares_requested and self.price_per_share:
            self.investment_amount = self.shares_requested * self.price_per_share
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """Soft delete this investment interest record."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted investment interest record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])




class InvestmentInterestAggregate(models.Model):
    """
    Aggregated public statistics for investment interests.
    This is the PUBLIC-FACING data shown on company pages.
    Contains NO personally identifiable information.
    """
    # SECURITY: Use PROTECT for financial records - they must never be auto-deleted
    financing = models.OneToOneField(
        Financing,
        on_delete=models.PROTECT,
        related_name='interest_aggregate'
    )

    # Public metrics (NO PII)
    total_interest_count = models.IntegerField(
        default=0,
        help_text="Number of investors who expressed interest"
    )
    total_shares_requested = models.BigIntegerField(
        default=0,
        help_text="Total shares requested across all interests"
    )
    total_amount_interested = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total investment amount interested"
    )

    # Percentage metrics
    percentage_filled = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Percentage of financing goal filled by interests"
    )

    # Last updated
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investment_interest_aggregates'

    def __str__(self):
        return f"{self.financing.company.name} - Interest Aggregate"

    def recalculate(self):
        """Recalculate aggregate statistics from investment interests"""
        from django.db.models import Sum, Count
        from django.utils import timezone

        # Get aggregated data from active interests (not withdrawn/rejected)
        stats = self.financing.investment_interests.filter(
            status__in=['pending', 'qualified', 'contacted', 'converted']
        ).aggregate(
            count=Count('id'),
            total_shares=Sum('shares_requested'),
            total_amount=Sum('investment_amount')
        )

        self.total_interest_count = stats['count'] or 0
        self.total_shares_requested = stats['total_shares'] or 0
        self.total_amount_interested = stats['total_amount'] or Decimal('0.00')

        # Calculate percentage of financing goal filled (use amount_raised_usd as target)
        if self.financing.amount_raised_usd and self.financing.amount_raised_usd > 0:
            self.percentage_filled = min(
                (self.total_amount_interested / self.financing.amount_raised_usd) * 100,
                Decimal('100.00')
            )
        else:
            self.percentage_filled = Decimal('0.00')

        self.last_calculated_at = timezone.now()
        self.save()

    @classmethod
    def update_for_financing(cls, financing):
        """Get or create aggregate and recalculate"""
        aggregate, created = cls.objects.get_or_create(financing=financing)
        aggregate.recalculate()
        return aggregate


# ============================================================================
# STORE MODULE - E-COMMERCE FOR GOLDVENTURE
# ============================================================================

