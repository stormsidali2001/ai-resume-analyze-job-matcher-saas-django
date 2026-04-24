"""
interfaces/websocket/chat_consumer.py

RAG-powered AI chat consumer for Django Channels.

Clients connect to:
    ws://localhost:8000/ws/chat/?token=<jwt>

Flow per message:
  1. JWT is validated; user role determines which search tool is exposed.
  2. First Gemini call (non-streaming, tools enabled): the model decides
     whether to invoke the search tool or answer directly.
  3. If the model calls the tool → Elasticsearch hybrid search runs →
     result is fed back as a FunctionResponse.
  4. Second Gemini call (streaming): the model generates its final answer
     using the retrieved context and streams it chunk-by-chunk.
  5. If the model answered directly (no tool call) → stream that text.
  6. Source cards are sent in the `done` frame so the frontend can render them.
  7. Conversation history is kept in-memory per connection (last 20 turns).
"""

from __future__ import annotations

import json
import logging

import google.genai as genai
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from google.genai import types as genai_types
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-lite"  # 10 RPM on this project's free tier

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_CANDIDATE_SYSTEM = (
    "You are a job search assistant on ResumeAI. "
    "When the user asks about jobs, roles, companies, or anything related to finding work, "
    "call the search_jobs tool with a concise search query. "
    "Use the tool results to give a specific, helpful answer. "
    "For greetings or off-topic questions, answer directly without calling the tool. "
    "Never make up job listings — only reference what the tool returns."
)

_RECRUITER_SYSTEM = (
    "You are a talent discovery assistant on ResumeAI. "
    "When the recruiter asks about candidates, skills, or finding talent, "
    "call the search_candidates tool with a concise search query. "
    "Use the tool results to give a specific, helpful answer. "
    "Refer to candidates by their skills and location — never expose personal contact details. "
    "For greetings or off-topic questions, answer directly without calling the tool. "
    "Never make up candidate profiles — only reference what the tool returns."
)

# ---------------------------------------------------------------------------
# Tool definitions (one per role)
# ---------------------------------------------------------------------------

_CANDIDATE_TOOL = genai_types.Tool(
    function_declarations=[
        genai_types.FunctionDeclaration(
            name="search_jobs",
            description=(
                "Search the job listings database for roles matching the query. "
                "Call this whenever the user asks about available jobs, companies hiring, "
                "role requirements, or anything related to job opportunities."
            ),
            parameters=genai_types.Schema(
                type="OBJECT",
                properties={
                    "query": genai_types.Schema(
                        type="STRING",
                        description="Concise search query capturing the user's intent, e.g. 'Python engineer remote'",
                    )
                },
                required=["query"],
            ),
        )
    ]
)

_RECRUITER_TOOL = genai_types.Tool(
    function_declarations=[
        genai_types.FunctionDeclaration(
            name="search_candidates",
            description=(
                "Search the candidate profiles database for resumes matching the query. "
                "Call this whenever the recruiter asks about finding candidates, "
                "skills availability, experience levels, or talent discovery."
            ),
            parameters=genai_types.Schema(
                type="OBJECT",
                properties={
                    "query": genai_types.Schema(
                        type="STRING",
                        description="Concise search query capturing the recruiter's intent, e.g. 'React developer 3 years'",
                    )
                },
                required=["query"],
            ),
        )
    ]
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_job_results(sources: list[dict]) -> str:
    if not sources:
        return "No relevant job listings found in the database."
    parts = []
    for i, s in enumerate(sources, 1):
        skills = ", ".join(s.get("skills", [])) or "N/A"
        exp = s.get("required_experience_months", 0)
        parts.append(
            f"[{i}] {s.get('title', 'Unknown')} at {s.get('company', 'Unknown')}\n"
            f"    Location: {s.get('location', 'N/A')} | Type: {s.get('employment_type', 'N/A')}\n"
            f"    Required experience: {exp} months | Skills: {skills}\n"
            f"    Description: {s.get('description', '')[:400]}"
        )
    return "\n\n".join(parts)


def _format_resume_results(sources: list[dict]) -> str:
    if not sources:
        return "No relevant candidate profiles found in the database."
    parts = []
    for i, s in enumerate(sources, 1):
        skills = ", ".join(s.get("skills", [])) or "N/A"
        exp = s.get("total_experience_months", 0)
        parts.append(
            f"[{i}] Candidate\n"
            f"    Location: {s.get('location', 'N/A')} | Experience: {exp} months\n"
            f"    Skills: {skills}"
        )
    return "\n\n".join(parts)


def _format_source_card(source: dict, role: str) -> dict:
    if role == "candidate":
        return {
            "id": source.get("job_id", ""),
            "title": source.get("title", "Unknown position"),
            "subtitle": source.get("company", "Unknown company"),
            "detail": source.get("location", ""),
        }
    skills = source.get("skills", [])
    skill_preview = ", ".join(skills[:4]) + ("…" if len(skills) > 4 else "")
    return {
        "id": source.get("resume_id", ""),
        "title": "Candidate profile",
        "subtitle": skill_preview or "No skills listed",
        "detail": source.get("location", ""),
    }


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _friendly_error(exc: Exception) -> str:
    """Convert known API errors into user-readable messages."""
    name = type(exc).__name__
    text = str(exc)

    # Gemini 429 — extract retry delay if present
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        import re
        match = re.search(r"retry.*?(\d+)s", text, re.IGNORECASE)
        wait = f" Please try again in {match.group(1)} seconds." if match else " Please try again shortly."
        return f"The AI service is temporarily rate-limited.{wait}"

    if "404" in text or "NOT_FOUND" in text:
        return "The AI model is unavailable. Please contact support."

    return "An error occurred while processing your request. Please try again."


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

class ChatConsumer(AsyncWebsocketConsumer):
    """Role-aware tool-calling RAG chat consumer. One connection = one session."""

    async def connect(self) -> None:
        token = self._extract_token()
        user = await self._authenticate(token)
        if user is None:
            logger.warning("ChatConsumer: auth failed — closing 4001")
            await self.close(code=4001)
            return

        self.user = user
        # History stores plain Content objects for the non-tool turns only.
        # Tool call/response pairs are ephemeral — they're not kept across turns
        # to keep history compact and avoid stale context.
        self.history: list[genai_types.Content] = []
        await self.accept()
        logger.debug("ChatConsumer connected: user=%s role=%s", user.id, user.role)

    async def disconnect(self, close_code: int) -> None:
        logger.debug("ChatConsumer disconnected: code=%s", close_code)

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        user_message = (data.get("message") or "").strip()
        if not user_message:
            return

        await self._handle_message(user_message)

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    async def _handle_message(self, user_message: str) -> None:
        try:
            from django.conf import settings

            is_candidate = self.user.role == "candidate"
            system_prompt = _CANDIDATE_SYSTEM if is_candidate else _RECRUITER_SYSTEM
            tool = _CANDIDATE_TOOL if is_candidate else _RECRUITER_TOOL

            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            # Current user turn
            user_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            )
            contents = list(self.history) + [user_content]

            # ── Turn 1: let Gemini decide whether to call the search tool ──
            first_response = await client.aio.models.generate_content(
                model=_MODEL,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[tool],
                ),
            )

            sources: list[dict] = []
            full_text = ""
            model_content = first_response.candidates[0].content

            # Check for a function call in the response parts
            function_call = next(
                (p.function_call for p in model_content.parts if p.function_call),
                None,
            )

            if function_call:
                # ── Execute the tool ──
                query = (function_call.args or {}).get("query", user_message)
                logger.debug("Tool call: %s(query=%r)", function_call.name, query)

                if is_candidate:
                    from infrastructure.search.retriever import search_jobs
                    sources = await sync_to_async(search_jobs)(query)
                    tool_result_text = _format_job_results(sources)
                else:
                    from infrastructure.search.retriever import search_resumes
                    sources = await sync_to_async(search_resumes)(query)
                    tool_result_text = _format_resume_results(sources)

                # Build the tool result content to feed back
                function_response_content = genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part.from_function_response(
                            name=function_call.name,
                            response={"result": tool_result_text},
                        )
                    ],
                )

                # ── Turn 2: stream the final answer with tool results ──
                final_contents = contents + [model_content, function_response_content]

                async for chunk in await client.aio.models.generate_content_stream(
                    model=_MODEL,
                    contents=final_contents,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        # No tools here — prevents the model looping back into tool calls
                    ),
                ):
                    if chunk.text:
                        full_text += chunk.text
                        await self.send(json.dumps({"type": "chunk", "content": chunk.text}))

            else:
                # ── No tool call — model answered directly ──
                # (greetings, follow-up questions on prior context, etc.)
                direct_text = "".join(
                    p.text for p in model_content.parts if p.text
                )
                full_text = direct_text
                if full_text:
                    await self.send(json.dumps({"type": "chunk", "content": full_text}))

            # ── Update conversation history (user + model turns only) ──
            model_reply_content = genai_types.Content(
                role="model",
                parts=[genai_types.Part(text=full_text)],
            )
            self.history.append(user_content)
            self.history.append(model_reply_content)
            # Keep last 20 turns (10 exchanges)
            if len(self.history) > 20:
                self.history = self.history[-20:]

            # ── Done frame with source cards ──
            source_cards = [_format_source_card(s, self.user.role) for s in sources]
            await self.send(json.dumps({"type": "done", "sources": source_cards}))

        except Exception as exc:
            message = _friendly_error(exc)
            logger.exception("ChatConsumer._handle_message error: %s", exc)
            try:
                await self.send(json.dumps({"type": "error", "message": message}))
            except Exception as send_exc:
                logger.warning("ChatConsumer: failed to send error frame: %s", send_exc)

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _extract_token(self) -> str | None:
        raw_qs: str = self.scope.get("query_string", b"").decode()
        for pair in raw_qs.split("&"):
            if "=" in pair:
                key, _, value = pair.partition("=")
                if key == "token":
                    return value
        return None

    async def _authenticate(self, token: str | None):
        if not token:
            return None
        try:
            validated = await sync_to_async(UntypedToken)(token)
            user_id = validated.payload.get("user_id")
            if not user_id:
                return None
            from infrastructure.models.user import CustomUser
            return await CustomUser.objects.aget(id=user_id)
        except (InvalidToken, TokenError, Exception):
            return None
