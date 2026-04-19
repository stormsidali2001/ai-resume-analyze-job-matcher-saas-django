"""
interfaces/websocket/routing.py

WebSocket URL patterns for Django Channels.
"""

from django.urls import re_path

from interfaces.websocket.consumers import ResumeStatusConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/resume/(?P<resume_id>[0-9a-f-]{36})/$",
        ResumeStatusConsumer.as_asgi(),
    ),
]
