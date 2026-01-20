from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'resources', views.ResourceEstimateViewSet, basename='resource')
router.register(r'financings', views.FinancingViewSet, basename='financing')
router.register(r'events', views.SpeakerEventViewSet, basename='event')
router.register(r'event-questions', views.EventQuestionViewSet, basename='event-question')
router.register(r'event-reactions', views.EventReactionViewSet, basename='event-reaction')

# Financial Hub ViewSets
router.register(r'education/modules', views.EducationalModuleViewSet, basename='educational-module')
router.register(r'education/completions', views.ModuleCompletionViewSet, basename='module-completion')
router.register(r'qualifications', views.AccreditedInvestorQualificationViewSet, basename='qualification')
router.register(r'agreements', views.SubscriptionAgreementViewSet, basename='agreement')
router.register(r'investments/transactions', views.InvestmentTransactionViewSet, basename='transaction')
router.register(r'investments/aggregates', views.FinancingAggregateViewSet, basename='aggregate')
router.register(r'investments/payment-instructions', views.PaymentInstructionViewSet, basename='payment-instruction')
router.register(r'drs/documents', views.DRSDocumentViewSet, basename='drs-document')

# Property Exchange ViewSets
router.register(r'properties/prospectors', views.ProspectorProfileViewSet, basename='prospector-profile')
router.register(r'properties/listings', views.PropertyListingViewSet, basename='property-listing')
router.register(r'properties/media', views.PropertyMediaViewSet, basename='property-media')
router.register(r'properties/inquiries', views.PropertyInquiryViewSet, basename='property-inquiry')
router.register(r'properties/watchlist', views.PropertyWatchlistViewSet, basename='property-watchlist')
router.register(r'properties/saved-searches', views.SavedPropertySearchViewSet, basename='saved-property-search')

# Company Portal ViewSets
router.register(r'company-portal/resources', views.CompanyResourceViewSet, basename='company-resource')
router.register(r'company-portal/events', views.SpeakingEventViewSet, basename='speaking-event')
router.register(r'company-portal/subscriptions', views.CompanySubscriptionViewSet, basename='company-subscription')
router.register(r'company-portal/access-requests', views.CompanyAccessRequestViewSet, basename='company-access-request')

# Store ViewSets
router.register(r'store/categories', views.StoreCategoryViewSet, basename='store-category')
router.register(r'store/products', views.StoreProductViewSet, basename='store-product')
router.register(r'store/cart', views.StoreCartViewSet, basename='store-cart')
router.register(r'store/orders', views.StoreOrderViewSet, basename='store-order')
router.register(r'store/shipping-rates', views.StoreShippingRateViewSet, basename='store-shipping-rate')

# Store Admin ViewSets
router.register(r'admin/store/categories', views.StoreAdminCategoryViewSet, basename='admin-store-category')
router.register(r'admin/store/products', views.StoreAdminProductViewSet, basename='admin-store-product')
router.register(r'admin/store/images', views.StoreAdminImageViewSet, basename='admin-store-image')
router.register(r'admin/store/variants', views.StoreAdminVariantViewSet, basename='admin-store-variant')
router.register(r'admin/store/digital-assets', views.StoreAdminDigitalAssetViewSet, basename='admin-store-digital-asset')
router.register(r'admin/store/orders', views.StoreAdminOrderViewSet, basename='admin-store-order')

# Glossary ViewSet (order matters - more specific routes first)
router.register(r'glossary/submissions', views.GlossaryTermSubmissionViewSet, basename='glossary-submission')
router.register(r'glossary', views.GlossaryTermViewSet, basename='glossary')

# News Release Financing Flags ViewSet
router.register(r'news-flags', views.NewsReleaseFlagViewSet, basename='news-flag')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register_user, name='register_user'),
    path('auth/login/', views.login_user, name='login_user'),
    path('auth/me/', views.get_current_user, name='current_user'),

    # Metals Pricing endpoints
    path('metals/prices/', views.metals_prices, name='metals_prices'),
    path('metals/historical/<str:symbol>/', views.metal_historical, name='metal_historical'),

    # Stock Quote endpoint
    path('companies/<int:company_id>/stock-quote/', views.stock_quote, name='stock_quote'),

    # Company Forum Discussion endpoint
    path('companies/<int:company_id>/discussion/', views.get_company_discussion, name='get_company_discussion'),

    # Claude Chat endpoints
    path('claude/chat/', views.claude_chat, name='claude_chat'),
    path('claude/tools/', views.available_tools, name='available_tools'),
    path('companies/<int:company_id>/chat/', views.company_chat, name='company_chat'),

    # News Scraping endpoints
    path('companies/<int:company_id>/scrape-news/', views.scrape_company_news, name='scrape_company_news'),
    path('companies/<int:company_id>/news-releases/', views.company_news_releases, name='company_news_releases'),
    path('tasks/<str:task_id>/status/', views.check_scrape_status, name='check_scrape_status'),

    # Hero Section endpoints (homepage cards)
    path('hero-section/', views.hero_section_data, name='hero_section_data'),
    path('hero-section/set-featured/', views.set_featured_property, name='set_featured_property'),
    path('hero-section/reset-featured/', views.reset_featured_property, name='reset_featured_property'),

    # News Articles endpoints
    path('news/articles/', views.news_articles_list, name='news_articles_list'),
    path('news/sources/', views.news_sources_list, name='news_sources_list'),
    path('news/sources/admin/', views.news_sources_admin, name='news_sources_admin'),
    path('news/sources/admin/<int:source_id>/', views.news_sources_admin, name='news_sources_admin_detail'),
    path('news/sources/admin/<int:source_id>/update/', views.news_source_update, name='news_source_update'),
    path('news/scrape/', views.news_scrape_trigger, name='news_scrape_trigger'),
    path('news/scrape/status/', views.news_scrape_status, name='news_scrape_status'),
    path('news/scrape/status/<int:job_id>/', views.news_scrape_status, name='news_scrape_status_detail'),

    # Company Portal - Stripe Subscription endpoints
    path('company-portal/subscriptions/create-checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('company-portal/subscriptions/billing-portal/', views.create_billing_portal, name='create_billing_portal'),
    path('company-portal/subscriptions/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('company-portal/subscriptions/reactivate/', views.reactivate_subscription, name='reactivate_subscription'),
    path('company-portal/webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Investment Interest endpoints
    path('investment-interest/register/', views.register_investment_interest, name='register_investment_interest'),
    path('investment-interest/my-interest/<int:financing_id>/', views.get_my_investment_interest, name='get_my_investment_interest'),
    path('investment-interest/aggregate/<int:financing_id>/', views.get_financing_interest_aggregate, name='get_financing_interest_aggregate'),
    path('investment-interest/list/<int:financing_id>/', views.list_investment_interests, name='list_investment_interests'),
    path('investment-interest/<int:interest_id>/status/', views.update_investment_interest_status, name='update_investment_interest_status'),
    path('investment-interest/<int:interest_id>/withdraw/', views.withdraw_investment_interest, name='withdraw_investment_interest'),
    path('investment-interest/<int:interest_id>/update/', views.update_my_investment_interest, name='update_my_investment_interest'),
    path('investment-interest/export/<int:financing_id>/', views.export_investment_interests, name='export_investment_interests'),
    path('investment-interest/admin/dashboard/', views.admin_investment_interest_dashboard, name='admin_investment_interest_dashboard'),

    # Store endpoints
    path('store/ticker/', views.store_ticker, name='store_ticker'),
    path('store/badges/', views.user_store_badges, name='user_store_badges'),
    path('store/checkout/', views.store_checkout, name='store_checkout'),
    path('store/webhook/', views.store_webhook, name='store_webhook'),

    # Company Scraping/Onboarding endpoints
    path('admin/companies/scrape-preview/', views.scrape_company_preview, name='scrape_company_preview'),
    path('admin/companies/scrape-save/', views.scrape_company_save, name='scrape_company_save'),
    path('admin/companies/scraping-jobs/', views.list_scraping_jobs, name='list_scraping_jobs'),
    path('admin/companies/scraping-jobs/<int:job_id>/', views.get_scraping_job, name='get_scraping_job'),
    path('admin/companies/failed-discoveries/', views.list_failed_discoveries, name='list_failed_discoveries'),
    path('admin/companies/failed-discoveries/<int:discovery_id>/retry/', views.retry_failed_discovery, name='retry_failed_discovery'),

    # Document Processing Summary (Superuser Dashboard)
    path('admin/document-summary/', views.document_processing_summary, name='document_processing_summary'),

    # Closed Financings (public page for displaying recently closed financings)
    path('closed-financings/', views.closed_financings_list, name='closed_financings_list'),
    path('closed-financings/create/', views.create_closed_financing, name='create_closed_financing'),
    path('closed-financings/<int:financing_id>/update/', views.update_closed_financing, name='update_closed_financing'),

    # ViewSet routes
    path('', include(router.urls)),
]
