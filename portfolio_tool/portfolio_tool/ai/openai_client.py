from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import List, Optional

from ..utils import get_logger

logger = get_logger()


@dataclass
class OpenAIConfig:
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    timeout_seconds: float = 20.0
    max_retries: int = 2


class OpenAIClient:
    def __init__(self, config: OpenAIConfig | None = None) -> None:
        self._config = config or OpenAIConfig()
        if not self._config.api_key:
            self._config.api_key = os.getenv("OPENAI_API_KEY")
        if not self._config.api_key:
            try:
                from dotenv import load_dotenv
            except Exception:
                return
            load_dotenv()
            self._config.api_key = os.getenv("OPENAI_API_KEY")

    def is_configured(self) -> bool:
        return bool(self._config.api_key)

    def _build_client(self):
        try:
            from openai import OpenAI
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("OpenAI SDK not installed. Install `openai`.") from exc
        return OpenAI(api_key=self._config.api_key, timeout=self._config.timeout_seconds)

    def generate(self, messages: List[dict], temperature: float = 0.2, max_tokens: int = 400) -> str:
        if not self.is_configured():
            raise RuntimeError("OpenAI API key not configured.")

        client = self._build_client()
        last_error = None
        for attempt in range(self._config.max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self._config.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("OpenAI request failed (attempt %s): %s", attempt + 1, exc)
                time.sleep(0.5 * (attempt + 1))

        raise RuntimeError(f"OpenAI request failed: {last_error}") from last_error
