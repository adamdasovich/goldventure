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
    Watchlist, Alert, DocumentProcessingJob
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
