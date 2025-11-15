from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Company, Project, ResourceEstimate, EconomicStudy,
    Financing, Investor, InvestorPosition, MarketData, CommodityPrice,
    NewsRelease, Document, InvestorCommunication, CompanyMetrics,
    Watchlist, Alert
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
