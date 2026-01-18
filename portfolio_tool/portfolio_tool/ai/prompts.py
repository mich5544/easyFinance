from __future__ import annotations

from typing import Dict, List


SYSTEM_PROMPT = (
    "You are a financial analytics assistant. Provide neutral, concise explanations. "
    "Do not give investment advice or promises. Avoid promotional language. "
    "Format your response in Markdown with clear headings and bullet points."
)


def _base_messages(user_content: str) -> List[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def study_commentary_prompt(payload: Dict) -> List[dict]:
    user_content = (
        "Summarize the study results for a cautious investor. "
        "Highlight strengths, weaknesses, and 2-3 clear warnings (e.g., concentration, "
        "data window limits, sensitivity to assumptions). "
        "Use Markdown with headings and short bullets. "
        "Do not give investment advice.\n\n"
        f"Inputs:\n{payload}"
    )
    return _base_messages(user_content)


def benchmark_comparison_prompt(payload: Dict) -> List[dict]:
    user_content = (
        "Explain whether the portfolio beats the benchmark and at what risk cost. "
        "Be specific, use plain language, and avoid certainty. "
        "Use Markdown with headings and bullets.\n\n"
        f"Inputs:\n{payload}"
    )
    return _base_messages(user_content)


def study_comparison_prompt(payload: Dict) -> List[dict]:
    user_content = (
        "Compare Study A vs Study B. Highlight meaningful differences for an investor, "
        "including risk/return tradeoffs, concentration, and sensitivity to assumptions. "
        "Keep it short and neutral. Use Markdown headings/bullets.\n\n"
        f"Inputs:\n{payload}"
    )
    return _base_messages(user_content)
