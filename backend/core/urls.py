from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'resources', views.ResourceEstimateViewSet, basename='resource')
router.register(r'financings', views.FinancingViewSet, basename='financing')

urlpatterns = [
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

    # ViewSet routes
    path('', include(router.urls)),
]
