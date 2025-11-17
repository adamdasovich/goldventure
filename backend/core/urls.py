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
    # Claude Chat endpoints
    path('claude/chat/', views.claude_chat, name='claude_chat'),
    path('claude/tools/', views.available_tools, name='available_tools'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
