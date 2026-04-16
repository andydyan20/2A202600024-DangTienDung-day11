"""
Local Ollama AI Client
Provides an interface to run LLMs locally via Ollama server.
"""

import os
import uuid
import aiohttp
from typing import Optional

from google.genai import types
from core.config import get_config


class OllamaClient:
    """Client for interacting with local Ollama LLM server."""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        config = get_config()
        self.model = model or config.OLLAMA_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.chat_endpoint = f"{self.base_url}/api/chat"

    async def chat(self, messages: list) -> str:
        """Chat with the model using a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.chat_endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Ollama API error ({response.status}): {error_text}"
                    )

                result = await response.json()
                return result.get("message", {}).get("content", "").strip()


def get_ollama_client() -> OllamaClient:
    """Get a configured Ollama client instance."""
    return OllamaClient()


# ============================================================
# Agent & Runner for Ollama (ADK-compatible interfaces)
# ============================================================


class OllamaAgent:
    """Simple agent container compatible with ADK's LlmAgent interface."""

    def __init__(self, model: str, name: str, instruction: str):
        self.model = model
        self.name = name
        self.instruction = instruction


class SimpleSession:
    """Minimal session object with an id."""

    def __init__(self, session_id: str):
        self.id = session_id


class InMemorySessionService:
    """Simple in-memory session storage, mimicking ADK's session service."""

    def __init__(self):
        self.sessions = {}

    async def get_session(self, app_name: str, user_id: str, session_id: str):
        return self.sessions.get((app_name, user_id, session_id))

    async def create_session(self, app_name: str, user_id: str, session_id: str = None):
        if session_id is None:
            session_id = str(uuid.uuid4())
        session = SimpleSession(session_id)
        self.sessions[(app_name, user_id, session_id)] = session
        return session


class SimpleEvent:
    """Simple event object with a content attribute."""

    def __init__(self, content: types.Content):
        self.content = content


class OllamaRunner:
    """Runner that mimics ADK's InMemoryRunner but uses Ollama backend."""

    def __init__(self, agent: OllamaAgent, app_name: str, session_service=None):
        from core.config import get_config

        config = get_config()
        self.agent = agent
        self.app_name = app_name
        self.session_service = session_service or InMemorySessionService()
        self.client = OllamaClient(model=agent.model, base_url=config.OLLAMA_BASE_URL)

    async def run_async(
        self, user_id: str, session_id: str, new_message: types.Content
    ):
        """Run the agent with the given message, yielding a single event."""
        # Get or create session
        session = await self.session_service.get_session(
            self.app_name, user_id, session_id
        )
        if session is None:
            session = await self.session_service.create_session(
                self.app_name, user_id, session_id
            )

        # Build message list
        messages = []
        if self.agent.instruction:
            messages.append({"role": "system", "content": self.agent.instruction})

        user_text = ""
        if new_message and new_message.parts:
            for part in new_message.parts:
                if hasattr(part, "text"):
                    user_text += part.text
        messages.append({"role": "user", "content": user_text})

        # Call Ollama
        response_text = await self.client.chat(messages)

        # Create event with response
        content = types.Content(
            role="model", parts=[types.Part.from_text(text=response_text)]
        )
        yield SimpleEvent(content=content)
