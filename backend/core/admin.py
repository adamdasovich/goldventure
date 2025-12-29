from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    User, Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, InvestorPosition, MarketData, CommodityPrice,
    NewsRelease, Document, InvestorCommunication, CompanyMetrics,
    Watchlist, Alert, DocumentProcessingJob,
    SpeakerEvent, EventSpeaker, EventRegistration, EventQuestion, EventReaction,
    # Financial Hub models
    EducationalModule, ModuleCompletion, AccreditedInvestorQualification,
    SubscriptionAgreement, InvestmentTransaction, FinancingAggregate,
    PaymentInstruction, DRSDocument,
    # Company Portal models
    CompanyResource, SpeakingEvent, CompanySubscription, SubscriptionInvoice,
    CompanyAccessRequest,
    # Company Onboarding models
    CompanyPerson, CompanyDocument, CompanyNews, ScrapingJob, FailedCompanyDiscovery
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'company', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'company', 'phone', 'linkedin_url', 'bio')}),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'ticker_symbol', 'exchange', 'status', 'is_active']
    list_filter = ['status', 'exchange', 'is_active']
    search_fields = ['name', 'ticker_symbol']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'project_stage', 'primary_commodity', 'country', 'is_flagship']
    list_filter = ['project_stage', 'primary_commodity', 'country', 'is_flagship']
    search_fields = ['name', 'company__name']


@admin.register(ResourceEstimate)
class ResourceEstimateAdmin(admin.ModelAdmin):
    list_display = ['project', 'category', 'gold_ounces', 'tonnes', 'report_date']
    list_filter = ['category', 'standard']
    search_fields = ['project__name']


@admin.register(EconomicStudy)
class EconomicStudyAdmin(admin.ModelAdmin):
    list_display = ['project', 'study_type', 'npv_5_usd', 'irr_percent', 'release_date']
    list_filter = ['study_type']
    search_fields = ['project__name']


@admin.register(Financing)
class FinancingAdmin(admin.ModelAdmin):
    list_display = ['company', 'financing_type', 'amount_raised_usd', 'announced_date', 'status']
    list_filter = ['financing_type', 'status']
    search_fields = ['company__name']


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'investor_type', 'city', 'country', 'relationship_strength']
    list_filter = ['investor_type', 'country']
    search_fields = ['first_name', 'last_name', 'company_name', 'email']


@admin.register(InvestorPosition)
class InvestorPositionAdmin(admin.ModelAdmin):
    list_display = ['investor', 'company', 'shares_held', 'percentage_ownership', 'position_date']
    list_filter = ['is_insider']
    search_fields = ['investor__company_name', 'company__name']


@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'close_price', 'volume']
    list_filter = ['company', 'date']
    search_fields = ['company__name']


@admin.register(CommodityPrice)
class CommodityPriceAdmin(admin.ModelAdmin):
    list_display = ['commodity', 'date', 'price']
    list_filter = ['commodity']


@admin.register(NewsRelease)
class NewsReleaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'release_type', 'release_date', 'is_material']
    list_filter = ['release_type', 'is_material']
    search_fields = ['title', 'company__name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'document_type', 'document_date', 'is_public']
    list_filter = ['document_type', 'is_public']
    search_fields = ['title', 'company__name']


@admin.register(InvestorCommunication)
class InvestorCommunicationAdmin(admin.ModelAdmin):
    list_display = ['investor', 'company', 'communication_type', 'communication_date', 'requires_followup']
    list_filter = ['communication_type', 'requires_followup', 'followup_completed']
    search_fields = ['investor__company_name', 'company__name', 'subject']


@admin.register(CompanyMetrics)
class CompanyMetricsAdmin(admin.ModelAdmin):
    list_display = ['company', 'period_end_date', 'cash_usd', 'burn_rate_monthly_usd', 'runway_months']
    list_filter = ['period_end_date']
    search_fields = ['company__name']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name', 'user__username']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'alert_type', 'is_active', 'last_triggered']
    list_filter = ['alert_type', 'is_active']
    search_fields = ['user__username', 'company__name']


@admin.register(DocumentProcessingJob)
class DocumentProcessingJobAdmin(admin.ModelAdmin):
    """Admin interface for document processing with batch capabilities"""

    list_display = [
        'id', 'status_badge', 'url_display', 'document_type',
        'company_name', 'duration_display', 'results_display', 'created_at'
    ]
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['url', 'company_name', 'project_name', 'error_message']
    readonly_fields = [
        'status', 'progress_message', 'error_message',
        'document', 'resources_created', 'chunks_created',
        'started_at', 'completed_at', 'processing_time_seconds',
        'created_at', 'created_by'
    ]

    fieldsets = (
        ('Job Details', {
            'fields': ('url', 'document_type', 'company_name', 'project_name')
        }),
        ('Status', {
            'fields': ('status', 'progress_message', 'error_message')
        }),
        ('Results', {
            'fields': ('document', 'resources_created', 'chunks_created')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at', 'processing_time_seconds')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('batch-add/', self.batch_add_view, name='core_documentprocessingjob_batch_add'),
            path('process-queue/', self.process_queue_view, name='core_documentprocessingjob_process_queue'),
        ]
        return custom_urls + urls

    def batch_add_view(self, request):
        """View for adding multiple URLs at once"""
        if request.method == 'POST':
            urls_text = request.POST.get('urls', '')
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]

            company_name = request.POST.get('company_name', '').strip()
            project_name = request.POST.get('project_name', '').strip()
            document_type = request.POST.get('document_type', 'ni43101')

            created_count = 0
            for url in urls:
                DocumentProcessingJob.objects.create(
                    url=url,
                    document_type=document_type,
                    company_name=company_name,
                    project_name=project_name,
                    created_by=request.user
                )
                created_count += 1

            messages.success(request, f'Created {created_count} processing jobs. Click "Process Queue" to start processing.')
            return redirect('..')

        context = {
            'title': 'Batch Add Document URLs',
            'opts': self.model._meta,
            'has_permission': True,
        }
        return render(request, 'admin/core/documentprocessingjob/batch_add.html', context)

    def process_queue_view(self, request):
        """Process all pending jobs"""
        from .tasks import process_document_queue

        pending_jobs = DocumentProcessingJob.objects.filter(status='pending').count()

        if request.method == 'POST':
            # Start processing in background
            process_document_queue()
            messages.success(request, f'Started processing {pending_jobs} pending jobs.')
            return redirect('..')

        context = {
            'title': 'Process Document Queue',
            'pending_jobs': pending_jobs,
            'opts': self.model._meta,
            'has_permission': True,
        }
        return render(request, 'admin/core/documentprocessingjob/process_queue.html', context)

    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 10px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def url_display(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:60] + '...')
    url_display.short_description = 'URL'

    def results_display(self, obj):
        if obj.status == 'completed':
            return format_html(
                '{} resources, {} chunks',
                obj.resources_created, obj.chunks_created
            )
        return '-'
    results_display.short_description = 'Results'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['pending_count'] = DocumentProcessingJob.objects.filter(status='pending').count()
        extra_context['processing_count'] = DocumentProcessingJob.objects.filter(status='processing').count()
        return super().changelist_view(request, extra_context=extra_context)


# ============================================================================
# GUEST SPEAKER EVENT ADMIN
# ============================================================================

class EventSpeakerInline(admin.TabularInline):
    """Inline admin for event speakers"""
    model = EventSpeaker
    extra = 1
    fields = ['user', 'title', 'bio', 'is_primary']


@admin.register(SpeakerEvent)
class SpeakerEventAdmin(admin.ModelAdmin):
    """Admin interface for speaker events"""
    list_display = [
        'title', 'company', 'status', 'format', 'scheduled_start',
        'registered_count', 'attended_count', 'created_by'
    ]
    list_filter = ['status', 'format', 'company', 'scheduled_start']
    search_fields = ['title', 'description', 'topic', 'company__name']
    readonly_fields = ['created_by', 'registered_count', 'attended_count', 'questions_count', 'created_at', 'updated_at']
    inlines = [EventSpeakerInline]

    fieldsets = (
        ('Event Details', {
            'fields': ('company', 'title', 'description', 'topic')
        }),
        ('Scheduling', {
            'fields': ('scheduled_start', 'scheduled_end', 'duration_minutes', 'registration_deadline')
        }),
        ('Format & Capacity', {
            'fields': ('format', 'max_participants', 'video_url', 'banner_image')
        }),
        ('Status', {
            'fields': ('status', 'actual_start', 'actual_end')
        }),
        ('Statistics', {
            'fields': ('registered_count', 'attended_count', 'questions_count')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventSpeaker)
class EventSpeakerAdmin(admin.ModelAdmin):
    """Admin interface for event speakers"""
    list_display = ['user', 'event', 'title', 'is_primary']
    list_filter = ['is_primary', 'event']
    search_fields = ['user__username', 'event__title', 'title']


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    """Admin interface for event registrations"""
    list_display = ['user', 'event', 'status', 'registered_at', 'reminder_sent']
    list_filter = ['status', 'reminder_sent', 'registered_at']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['registered_at', 'joined_at', 'left_at']


@admin.register(EventQuestion)
class EventQuestionAdmin(admin.ModelAdmin):
    """Admin interface for event questions"""
    list_display = ['content_preview', 'event', 'user', 'status', 'upvotes', 'is_featured', 'created_at']
    list_filter = ['status', 'is_featured', 'event']
    search_fields = ['content', 'user__username', 'event__title']
    readonly_fields = ['upvotes', 'created_at', 'answered_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Question'


@admin.register(EventReaction)
class EventReactionAdmin(admin.ModelAdmin):
    """Admin interface for event reactions"""
    list_display = ['user', 'event', 'reaction_type', 'timestamp']
    list_filter = ['reaction_type', 'event', 'timestamp']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['timestamp']


# ============================================================================
# FINANCIAL HUB ADMIN
# ============================================================================

@admin.register(EducationalModule)
class EducationalModuleAdmin(admin.ModelAdmin):
    """Admin interface for educational modules"""
    list_display = ['title', 'module_type', 'is_published', 'is_required', 'sort_order', 'estimated_read_time_minutes']
    list_filter = ['module_type', 'is_published', 'is_required']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Module Details', {
            'fields': ('module_type', 'title', 'description')
        }),
        ('Content', {
            'fields': ('content', 'estimated_read_time_minutes')
        }),
        ('Settings', {
            'fields': ('is_published', 'is_required', 'sort_order')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModuleCompletion)
class ModuleCompletionAdmin(admin.ModelAdmin):
    """Admin interface for module completions"""
    list_display = ['user', 'module', 'started_at', 'completed_at', 'time_spent_seconds', 'passed']
    list_filter = ['module', 'passed', 'completed_at']
    search_fields = ['user__username', 'module__title']
    readonly_fields = ['started_at']


@admin.register(AccreditedInvestorQualification)
class AccreditedInvestorQualificationAdmin(admin.ModelAdmin):
    """Admin interface for accredited investor qualifications"""
    list_display = ['user', 'status', 'criteria_met', 'qualified_at', 'expires_at', 'reviewed_by']
    list_filter = ['status', 'criteria_met', 'documents_verified']
    search_fields = ['user__username', 'review_notes']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User & Status', {
            'fields': ('user', 'status', 'criteria_met')
        }),
        ('Questionnaire', {
            'fields': ('questionnaire_responses',)
        }),
        ('Documentation', {
            'fields': ('documents_submitted', 'documents_verified')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Validity', {
            'fields': ('qualified_at', 'expires_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SubscriptionAgreement)
class SubscriptionAgreementAdmin(admin.ModelAdmin):
    """Admin interface for subscription agreements"""
    list_display = [
        'investor', 'company', 'financing', 'total_investment_amount',
        'num_shares', 'status', 'investor_signed_at', 'shares_issued'
    ]
    list_filter = ['status', 'company', 'accreditation_verified', 'kyc_completed', 'shares_issued']
    search_fields = ['investor__username', 'company__name', 'docusign_envelope_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Parties', {
            'fields': ('investor', 'financing', 'company')
        }),
        ('Investment Details', {
            'fields': ('num_shares', 'price_per_share', 'total_investment_amount', 'currency')
        }),
        ('Warrants', {
            'fields': ('includes_warrants', 'warrant_shares', 'warrant_strike_price', 'warrant_expiry_date'),
            'classes': ('collapse',)
        }),
        ('Agreement Status', {
            'fields': ('status', 'agreement_pdf_url', 'docusign_envelope_id')
        }),
        ('Signatures', {
            'fields': ('investor_signed_at', 'investor_ip_address', 'company_accepted_at', 'company_accepted_by')
        }),
        ('Payment', {
            'fields': ('payment_instructions_sent_at', 'payment_received_at', 'payment_reference')
        }),
        ('Share Issuance', {
            'fields': ('shares_issued', 'shares_issued_at', 'drs_statement_sent_at', 'certificate_number')
        }),
        ('Compliance', {
            'fields': ('accreditation_verified', 'kyc_completed', 'aml_check_completed')
        }),
        ('Notes', {
            'fields': ('notes', 'rejection_reason')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    """Admin interface for investment transactions"""
    list_display = ['user', 'financing', 'amount', 'status', 'payment_date', 'shares_allocated']
    list_filter = ['status', 'financing', 'payment_date']
    search_fields = ['user__username', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FinancingAggregate)
class FinancingAggregateAdmin(admin.ModelAdmin):
    """Admin interface for financing aggregates"""
    list_display = [
        'financing', 'total_subscriptions', 'total_subscribers',
        'total_committed_amount', 'total_funded_amount', 'last_calculated_at'
    ]
    list_filter = ['last_calculated_at']
    search_fields = ['financing__company__name']
    readonly_fields = ['last_calculated_at']


@admin.register(PaymentInstruction)
class PaymentInstructionAdmin(admin.ModelAdmin):
    """Admin interface for payment instructions"""
    list_display = ['subscription_agreement', 'company', 'payment_method', 'sent_to_investor_at', 'viewed_by_investor_at']
    list_filter = ['payment_method', 'company']
    search_fields = ['reference_code', 'bank_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Agreement & Company', {
            'fields': ('subscription_agreement', 'company', 'payment_method')
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'bank_account_name', 'bank_account_number', 'routing_number', 'swift_code'),
            'description': 'These details should be encrypted in production'
        }),
        ('Instructions', {
            'fields': ('reference_code', 'special_instructions')
        }),
        ('Tracking', {
            'fields': ('sent_to_investor_at', 'viewed_by_investor_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DRSDocument)
class DRSDocumentAdmin(admin.ModelAdmin):
    """Admin interface for DRS documents"""
    list_display = [
        'user', 'company', 'document_type', 'num_shares',
        'delivery_status', 'sent_at', 'delivered_at'
    ]
    list_filter = ['document_type', 'delivery_status', 'company']
    search_fields = ['user__username', 'certificate_number', 'document_hash']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Document & Parties', {
            'fields': ('subscription_agreement', 'user', 'company', 'document_type')
        }),
        ('Document Details', {
            'fields': ('document_url', 'document_hash')
        }),
        ('Share Details', {
            'fields': ('num_shares', 'certificate_number', 'issue_date')
        }),
        ('Delivery', {
            'fields': ('delivery_status', 'delivery_method', 'sent_at', 'delivered_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ============================================================================
# COMPANY PORTAL ADMIN
# ============================================================================

@admin.register(CompanyResource)
class CompanyResourceAdmin(admin.ModelAdmin):
    """Admin interface for company resources"""
    list_display = ['title', 'company', 'resource_type', 'category', 'is_public', 'uploaded_at']
    list_filter = ['resource_type', 'category', 'is_public', 'company']
    search_fields = ['title', 'description', 'company__name']
    readonly_fields = ['uploaded_at', 'uploaded_by']


@admin.register(SpeakingEvent)
class SpeakingEventAdmin(admin.ModelAdmin):
    """Admin interface for speaking events"""
    list_display = ['title', 'company', 'event_type', 'start_datetime', 'status', 'is_featured']
    list_filter = ['event_type', 'status', 'is_featured', 'company']
    search_fields = ['title', 'description', 'company__name', 'location']
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(CompanySubscription)
class CompanySubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for company subscriptions"""
    list_display = ['company', 'status', 'is_active', 'trial_end', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['status', 'cancel_at_period_end']
    search_fields = ['company__name', 'stripe_customer_id', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    """Admin interface for subscription invoices"""
    list_display = ['subscription', 'status', 'amount_cents', 'invoice_date', 'paid_at']
    list_filter = ['status', 'invoice_date']
    search_fields = ['stripe_invoice_id', 'subscription__company__name']
    readonly_fields = ['created_at']


@admin.register(CompanyAccessRequest)
class CompanyAccessRequestAdmin(admin.ModelAdmin):
    """Admin interface for company access requests with approval workflow"""
    list_display = [
        'user', 'company', 'status_badge', 'role', 'job_title',
        'work_email', 'created_at', 'reviewer'
    ]
    list_filter = ['status', 'role', 'company', 'created_at']
    search_fields = ['user__username', 'user__email', 'company__name', 'job_title', 'work_email']
    readonly_fields = ['user', 'created_at', 'updated_at', 'reviewed_at']
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        ('Request Details', {
            'fields': ('user', 'company', 'status', 'role', 'job_title')
        }),
        ('Justification', {
            'fields': ('work_email', 'justification')
        }),
        ('Review', {
            'fields': ('reviewer', 'review_notes', 'reviewed_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',    # amber
            'approved': '#10b981',   # green
            'rejected': '#ef4444',   # red
            'cancelled': '#6b7280',  # gray
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 10px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    @admin.action(description='Approve selected requests')
    def approve_requests(self, request, queryset):
        pending = queryset.filter(status='pending')
        count = 0
        for access_request in pending:
            access_request.approve(reviewer=request.user, notes='Bulk approved via admin')
            count += 1
        self.message_user(request, f'{count} request(s) approved.')

    @admin.action(description='Reject selected requests')
    def reject_requests(self, request, queryset):
        pending = queryset.filter(status='pending')
        count = pending.update(
            status='rejected',
            reviewer=request.user,
            review_notes='Bulk rejected via admin'
        )
        self.message_user(request, f'{count} request(s) rejected.')


# ============================================================================
# COMPANY ONBOARDING ADMIN
# ============================================================================

@admin.register(CompanyPerson)
class CompanyPersonAdmin(admin.ModelAdmin):
    """Admin interface for company people (scraped)"""
    list_display = ['full_name', 'company', 'role_type', 'title', 'display_order', 'extracted_at']
    list_filter = ['role_type', 'company', 'extracted_at']
    search_fields = ['full_name', 'title', 'company__name']
    readonly_fields = ['extracted_at']


@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    """Admin interface for company documents (scraped)"""
    list_display = ['title', 'company', 'document_type', 'year', 'extracted_at']
    list_filter = ['document_type', 'company', 'year']
    search_fields = ['title', 'company__name']
    readonly_fields = ['extracted_at']


@admin.register(CompanyNews)
class CompanyNewsAdmin(admin.ModelAdmin):
    """Admin interface for company news (scraped)"""
    list_display = ['title', 'company', 'publication_date', 'is_pdf', 'extracted_at']
    list_filter = ['company', 'is_pdf', 'publication_date']
    search_fields = ['title', 'company__name']
    readonly_fields = ['extracted_at']


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    """Admin interface for scraping jobs"""
    list_display = [
        'company_name_input', 'status_badge', 'company',
        'people_found', 'documents_found', 'news_found',
        'started_at', 'initiated_by'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['company_name_input', 'website_url', 'company__name']
    readonly_fields = [
        'started_at', 'completed_at', 'company',
        'data_extracted', 'error_traceback'
    ]

    fieldsets = (
        ('Job Details', {
            'fields': ('company_name_input', 'website_url', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Results', {
            'fields': ('company', 'people_found', 'documents_found', 'news_found')
        }),
        ('Sections', {
            'fields': ('sections_to_process', 'sections_completed')
        }),
        ('Errors', {
            'fields': ('error_messages', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('data_extracted',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('initiated_by',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280',
            'running': '#3b82f6',
            'success': '#10b981',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 10px; border-radius:3px;">{}</span>',
            color, obj.status.title()
        )
    status_badge.short_description = 'Status'


@admin.register(FailedCompanyDiscovery)
class FailedCompanyDiscoveryAdmin(admin.ModelAdmin):
    """Admin interface for failed company discoveries"""
    list_display = ['company_name', 'website_url', 'attempts', 'resolved', 'last_attempted_at']
    list_filter = ['resolved', 'last_attempted_at']
    search_fields = ['company_name', 'website_url']
    readonly_fields = ['created_at', 'last_attempted_at']

    fieldsets = (
        ('Company Details', {
            'fields': ('company_name', 'website_url')
        }),
        ('Failure Info', {
            'fields': ('failure_reason', 'attempts')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_attempted_at')
        }),
    )
