"""
Lab 11 — Configuration & API Key Setup
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class Config:
    """Configuration for the LLM provider and models."""

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google").lower()
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_config() -> Config:
    """Get configuration singleton."""
    return Config()


def setup_api_key():
    """Load API key from environment or prompt."""
    config = get_config()

    if config.LLM_PROVIDER == "google":
        if not config.GOOGLE_API_KEY:
            config.GOOGLE_API_KEY = input("Enter Google API Key: ")
            os.environ["GOOGLE_API_KEY"] = config.GOOGLE_API_KEY
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
        print("API key loaded for Google provider.")
    elif config.LLM_PROVIDER == "ollama":
        print(
            f"Using local Ollama at {config.OLLAMA_BASE_URL} with model {config.OLLAMA_MODEL}"
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking",
    "account",
    "transaction",
    "transfer",
    "loan",
    "interest",
    "savings",
    "credit",
    "deposit",
    "withdrawal",
    "balance",
    "payment",
    "tai khoan",
    "giao dich",
    "tiet kiem",
    "lai suat",
    "chuyen tien",
    "the tin dung",
    "so du",
    "vay",
    "ngan hang",
    "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack",
    "exploit",
    "weapon",
    "drug",
    "illegal",
    "violence",
    "gambling",
    "bomb",
    "kill",
    "steal",
]
