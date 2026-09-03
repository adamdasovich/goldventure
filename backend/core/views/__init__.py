"""
Core views package - re-exports all views.
"""

from .companies import (  # noqa: F401
    FlexiblePagePagination,
    CompanyViewSet,
)
from .metals import (  # noqa: F401
    metals_prices,
    metal_historical,
)
from .stocks import (  # noqa: F401
    stock_quote,
    top_movers,
)
from .ai_chat import (  # noqa: F401
    check_prompt_injection,
    get_or_create_ai_usage,
    claude_chat,
    company_chat,
    available_tools,
)
from .company_news import (  # noqa: F401
    scrape_company_news,
    check_scrape_status,
    company_news_releases,
)
from .projects import (  # noqa: F401
    ProjectViewSet,
)
from .financings import (  # noqa: F401
    ResourceEstimateViewSet,
    FinancingViewSet,
)
from .events import (  # noqa: F401
    SpeakerEventViewSet,
    EventQuestionViewSet,
    EventReactionViewSet,
)
from .auth import (  # noqa: F401
    register_user,
    login_user,
    get_current_user,
)
from .financial_hub import (  # noqa: F401
    EducationalModuleViewSet,
    ModuleCompletionViewSet,
    AccreditedInvestorQualificationViewSet,
    SubscriptionAgreementViewSet,
    InvestmentTransactionViewSet,
    FinancingAggregateViewSet,
    PaymentInstructionViewSet,
    DRSDocumentViewSet,
)
from .properties import (  # noqa: F401
    ProspectorProfileViewSet,
    PropertyListingViewSet,
    PropertyMediaViewSet,
    PropertyInquiryViewSet,
    PropertyWatchlistViewSet,
    SavedPropertySearchViewSet,
)
from .homepage import (  # noqa: F401
    platform_stats,
    hero_section_data,
    set_featured_property,
    reset_featured_property,
)
from .news_articles import (  # noqa: F401
    news_articles_list,
    news_sources_list,
    news_sources_admin,
    news_source_update,
    news_scrape_trigger,
    news_scrape_status,
)
from .company_portal import (  # noqa: F401
    CompanyResourceViewSet,
    SpeakingEventViewSet,
    CompanyAccessRequestViewSet,
)
from .investment_interest import (  # noqa: F401
    register_investment_interest,
    get_my_investment_interest,
    get_financing_interest_aggregate,
    list_investment_interests,
    update_investment_interest_status,
    withdraw_investment_interest,
    update_my_investment_interest,
    export_investment_interests,
    admin_investment_interest_dashboard,
)
from .store import (  # noqa: F401
    StoreCategoryViewSet,
    StoreProductViewSet,
    StoreCartViewSet,
    StoreOrderViewSet,
    StoreShippingRateViewSet,
    store_ticker,
    user_store_badges,
    get_company_discussion,
    get_company_forum_preview,
    store_checkout,
    store_webhook,
)
from .store_admin import (  # noqa: F401
    IsAdminUser,
    StoreAdminCategoryViewSet,
    StoreAdminProductViewSet,
    StoreAdminImageViewSet,
    StoreAdminVariantViewSet,
    StoreAdminDigitalAssetViewSet,
    StoreAdminOrderViewSet,
)
from .onboarding import (  # noqa: F401
    scrape_company_preview,
    scrape_company_save,
    _infer_commodity_from_name,
    _is_invalid_project_name,
    _infer_project_stage_from_name,
    _classify_news,
    _save_scraped_company_data,
    list_scraping_jobs,
    list_failed_discoveries,
    get_scraping_job,
    retry_failed_discovery,
)
from .glossary import (  # noqa: F401
    GlossaryTermViewSet,
    GlossaryTermSubmissionViewSet,
)
from .news_flags import (  # noqa: F401
    NewsReleaseFlagViewSet,
)
from .news_report_flags import (  # noqa: F401
    NewsReportFlagViewSet,
)
from .document_queue import (  # noqa: F401
    DocumentQueueViewSet,
)
from .closed_financings import (  # noqa: F401
    closed_financings_list,
    create_closed_financing,
    update_closed_financing,
)
from .open_financings import (  # noqa: F401
    open_financings_list,
)
from .document_processing import (  # noqa: F401
    document_processing_summary,
)
from .investor_tools import (  # noqa: F401
    grade_ranker,
    peer_comparison,
    financing_flow,
    sector_pulse,
    drill_scanner,
    catalyst_calendar,
    portfolio_xray,
    property_valuation,
    stock_comparison,
    resource_growth,
    dilution_tracker,
    unusual_activity,
    catalyst_impact,
    due_diligence,
    metal_correlation,
)
from .warrant_radar import (  # noqa: F401
    warrant_radar,
)
from .market_quality import (  # noqa: F401
    liquidity_screener,
    signal_to_noise,
)
from .platform_subscriptions import (  # noqa: F401
    platform_subscription_tiers,
    platform_signup_offer,
    platform_subscription_status,
    platform_create_checkout,
    platform_confirm_checkout,
    platform_billing_portal,
    platform_cancel_subscription,
    platform_reactivate_subscription,
    platform_stripe_webhook,
)
from .company_subscriptions import (  # noqa: F401
    company_plan,
    company_subscription_status,
    company_create_checkout,
    company_confirm_checkout,
    company_billing_portal,
    company_stripe_webhook,
)
from .dashboard import (  # noqa: F401
    watchlist_detail,
    watchlist_toggle,
    daily_briefing,
    briefing_email_toggle,
    briefing_email_unsubscribe,
)
from .reports import (  # noqa: F401
    weekly_report_list,
    weekly_report_detail,
    weekly_report_pdf,
    weekly_report_latest,
    weekly_financings_list,
    weekly_financings_detail,
)

from .exports import (  # noqa: F401
    export_companies_csv,
)
