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

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register_user, name='register_user'),
    path('auth/login/', views.login_user, name='login_user'),
    path('auth/me/', views.get_current_user, name='current_user'),

    # Metals Pricing endpoints
    path('metals/prices/', views.metals_prices, name='metals_prices'),
    path('metals/historical/<str:symbol>/', views.metal_historical, name='metal_historical'),

    # Claude Chat endpoints
    path('claude/chat/', views.claude_chat, name='claude_chat'),
    path('claude/tools/', views.available_tools, name='available_tools'),
    path('companies/<int:company_id>/chat/', views.company_chat, name='company_chat'),

    # News Scraping endpoints
    path('companies/<int:company_id>/scrape-news/', views.scrape_company_news, name='scrape_company_news'),
    path('companies/<int:company_id>/news-releases/', views.company_news_releases, name='company_news_releases'),
    path('tasks/<str:task_id>/status/', views.check_scrape_status, name='check_scrape_status'),

    # ViewSet routes
    path('', include(router.urls)),
]
