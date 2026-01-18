from __future__ import annotations

from typing import Dict, Optional

from .openai_client import OpenAIClient
from .prompts import (
    benchmark_comparison_prompt,
    study_commentary_prompt,
    study_comparison_prompt,
)
from ..utils import get_logger

logger = get_logger()


def _safe_generate(client: OpenAIClient, messages: list[dict]) -> Dict[str, Optional[str]]:
    try:
        text = client.generate(messages)
        return {"text": text, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI insight failed: %s", exc)
        return {"text": None, "error": str(exc)}


def comment_study(
    client: OpenAIClient,
    assets: list[str],
    min_var: dict,
    max_sharpe: dict,
    benchmark: dict,
    constraints: dict,
) -> Dict[str, Optional[str]]:
    payload = {
        "assets": assets,
        "min_variance": min_var,
        "max_sharpe": max_sharpe,
        "benchmark": benchmark,
        "constraints": constraints,
    }
    return _safe_generate(client, study_commentary_prompt(payload))


def compare_to_benchmark(
    client: OpenAIClient,
    portfolio: dict,
    benchmark: dict,
) -> Dict[str, Optional[str]]:
    payload = {
        "portfolio": portfolio,
        "benchmark": benchmark,
    }
    return _safe_generate(client, benchmark_comparison_prompt(payload))


def compare_studies(
    client: OpenAIClient,
    study_a: dict,
    study_b: dict,
) -> Dict[str, Optional[str]]:
    payload = {
        "study_a": study_a,
        "study_b": study_b,
    }
    return _safe_generate(client, study_comparison_prompt(payload))
