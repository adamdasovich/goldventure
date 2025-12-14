"""
WebSocket URL routing for real-time forum features.
"""

from django.urls import re_path
from core import consumers

websocket_urlpatterns = [
    # Forum discussion WebSocket
    re_path(r'^ws/forum/(?P<discussion_id>\d+)/$', consumers.ForumConsumer.as_asgi()),

    # Guest speaker session WebSocket
    re_path(r'^ws/session/(?P<session_id>\d+)/$', consumers.SessionConsumer.as_asgi()),

    # Speaker event WebSocket
    re_path(r'^ws/event/(?P<event_id>\d+)/$', consumers.SpeakerEventConsumer.as_asgi()),

    # Property inquiry inbox WebSocket (real-time messaging)
    re_path(r'^ws/inbox/$', consumers.InquiryConsumer.as_asgi()),
]
