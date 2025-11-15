from django.urls import path
from . import views

urlpatterns = [
    # Claude Chat
    path('claude/chat/', views.claude_chat, name='claude_chat'),
    path('claude/tools/', views.available_tools, name='available_tools'),

    # TODO: Add CRUD endpoints for companies, projects, etc.
    # These will be added as we build out the API
]
