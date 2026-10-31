"""Application configuration and unified LLM client helper.

Loads environment variables, defines typed Settings via pydantic-settings,
and provides a resilient LLM invocation fallback chain:
Groq (Llama-3.3-70B) -> Google Gemini (2.5-Flash) -> Deterministic Fallback.
"""

from collections.abc import Callable
from functools import lru_cache
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Load .env relative to the backend root directory
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_ROOT / ".env"
load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    base_dir: Path = _BACKEND_ROOT
    data_dir: Path = _BACKEND_ROOT / "data"
    chroma_db_dir: Path = Path(
        os.getenv("CHROMA_DB_DIR", str(_BACKEND_ROOT / "data" / "chroma_db"))
    )
    fastembed_cache_path: str = os.getenv(
        "FASTEMBED_CACHE_PATH", str(_BACKEND_ROOT / ".cache" / "fastembed")
    )
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    gemini_model: str = "gemini-3-flash-preview"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None
    google_calendar_id: str = "primary"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "Settings":
        """Anchor relative storage paths to the backend root directory."""
        if not self.chroma_db_dir.is_absolute():
            self.chroma_db_dir = self.base_dir / self.chroma_db_dir
        cache_path = Path(self.fastembed_cache_path)
        if not cache_path.is_absolute():
            self.fastembed_cache_path = str(self.base_dir / cache_path)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def has_valid_key(key: str | None) -> bool:
    """Check if an API key is set, non-empty, and not a placeholder."""
    if not key:
        return False
    stripped = key.strip()
    if not stripped or stripped.startswith("your_"):
        return False
    return True


def generate_json_with_llm(
    system_prompt: str,
    user_prompt: str,
    fallback_fn: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Execute JSON generation using Groq, falling back to Gemini, then deterministic function.

    Returns:
        tuple[dict[str, Any], str]: The parsed JSON dictionary and the provider name used
        ("groq", "gemini", or "deterministic_fallback").
    """
    settings = get_settings()

    # 1. Attempt Groq if a valid key is provided
    if has_valid_key(settings.groq_api_key):
        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key, timeout=15.0)
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content or ""
            parsed = json.loads(raw_text)
            return parsed, "groq"
        except Exception as exc:
            logger.warning("Groq JSON generation failed; falling back: %s", exc)

    # 2. Attempt Google Gemini if a valid key is provided
    if has_valid_key(settings.gemini_api_key):
        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            combined_prompt = f"System Instructions:\n{system_prompt}\n\nTask:\n{user_prompt}"
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=combined_prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = response.text or ""
            parsed = json.loads(raw_text)
            return parsed, "gemini"
        except Exception as exc:
            logger.warning("Gemini JSON generation failed; falling back: %s", exc)

    # 3. Deterministic local fallback
    logger.info("Using deterministic fallback function for JSON generation")
    return fallback_fn(), "deterministic_fallback"


def generate_text_with_llm(
    system_prompt: str,
    user_prompt: str,
    fallback_fn: Callable[[], str],
) -> tuple[str, str]:
    """Execute text generation using Groq, falling back to Gemini, then deterministic function.

    Returns:
        tuple[str, str]: The generated text string and the provider name used
        ("groq", "gemini", or "deterministic_fallback").
    """
    settings = get_settings()

    # 1. Attempt Groq if a valid key is provided
    if has_valid_key(settings.groq_api_key):
        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key, timeout=15.0)
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                return text, "groq"
        except Exception as exc:
            logger.warning("Groq text generation failed; falling back: %s", exc)

    # 2. Attempt Google Gemini if a valid key is provided
    if has_valid_key(settings.gemini_api_key):
        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            combined_prompt = f"System Instructions:\n{system_prompt}\n\nTask:\n{user_prompt}"
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=combined_prompt,
            )
            text = (response.text or "").strip()
            if text:
                return text, "gemini"
        except Exception as exc:
            logger.warning("Gemini text generation failed; falling back: %s", exc)

    # 3. Deterministic local fallback
    logger.info("Using deterministic fallback function for text generation")
    return fallback_fn(), "deterministic_fallback"
