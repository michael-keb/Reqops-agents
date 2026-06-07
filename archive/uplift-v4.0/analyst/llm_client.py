"""OpenAI client helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LlmResult:
    text: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    wait_ms: float


def model_name(role: str = "default") -> str:
    if role == "score":
        return (
            os.environ.get("SCORE_MODEL")
            or os.environ.get("LLM_MODEL")
            or "gpt-4o"
        )
    return (
        os.environ.get("PHRASING_MODEL")
        or os.environ.get("LLM_MODEL")
        or "gpt-4o"
    )


def call_llm(
    *,
    api_key: str,
    system_prompt: str,
    user_message: str,
    role: str = "default",
    temperature: float = 0.4,
) -> LlmResult:
    import time

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = model_name(role)
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    wait_ms = (time.perf_counter() - t0) * 1000
    choice = resp.choices[0].message.content or ""
    usage = resp.usage
    return LlmResult(
        text=choice.strip(),
        model=model,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
        total_tokens=usage.total_tokens if usage else None,
        wait_ms=wait_ms,
    )
