"""
interfaces/websocket/consumers.py

WebSocket consumer for real-time resume analysis status updates.

Clients connect to:
    ws://localhost:8000/ws/resume/{resume_id}/?token=<jwt>

The consumer:
  1. Validates the JWT from the query string (uses SimpleJWT UntypedToken)
  2. Joins the channel group "resume_{resume_id}"
  3. Forwards any "resume.status.update" group messages to the browser

The Celery task broadcasts to the group after each status transition
(processing → done / failed), so connected clients receive updates
without any polling.
"""

from __future__ import annotations

import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

logger = logging.getLogger(__name__)


class ResumeStatusConsumer(AsyncWebsocketConsumer):
    """Push analysis_status updates to a single connected browser tab."""

    async def connect(self) -> None:
        self.resume_id: str = self.scope["url_route"]["kwargs"]["resume_id"]
        self.group_name: str = f"resume_{self.resume_id}"

        token = self._extract_token()
        if not token or not await self._token_valid(token):
            logger.warning(
                "WebSocket auth failed for resume %s — closing with 4001",
                self.resume_id,
            )
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WebSocket connected: resume=%s channel=%s", self.resume_id, self.channel_name)

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WebSocket disconnected: resume=%s code=%s", self.resume_id, close_code)

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        # Server-push only; client messages are ignored.
        pass

    # ------------------------------------------------------------------
    # Group message handler — called by channel layer when the Celery
    # task sends a group_send with type "resume.status.update"
    # ------------------------------------------------------------------

    async def resume_status_update(self, event: dict) -> None:
        """Forward a status update event to the connected WebSocket client."""
        await self.send(json.dumps({
            "type": "status_update",
            "analysis_status": event["analysis_status"],
            "resume_id": event["resume_id"],
        }))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_token(self) -> str | None:
        """Parse the JWT from ?token=<value> in the WebSocket query string."""
        raw_qs: str = self.scope.get("query_string", b"").decode()
        for pair in raw_qs.split("&"):
            if "=" in pair:
                key, _, value = pair.partition("=")
                if key == "token":
                    return value
        return None

    @staticmethod
    async def _token_valid(token: str) -> bool:
        """Validate token using SimpleJWT (sync call wrapped in sync_to_async)."""
        try:
            await sync_to_async(UntypedToken)(token)
            return True
        except (InvalidToken, TokenError):
            return False
