"""OpenRouter (OpenAI-compatible) client — httpx, one retry on 429/5xx (docs/06 §1)."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class OpenRouterError(Exception):
    """Raised on network/HTTP failure so the chat loop can persist a friendly turn."""


def call_openrouter(
    messages: list[dict],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    tools: list[dict] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools
    headers = {
        "Authorization": f"Bearer {api_key or settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "TransitOps",
    }
    url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"

    last: Exception | None = None
    for _attempt in range(2):  # initial call + one retry
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=45)
        except httpx.HTTPError as exc:
            last = exc
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            last = OpenRouterError(f"OpenRouter returned {resp.status_code}")
            continue
        if resp.status_code >= 400:
            raise OpenRouterError(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")
        return resp.json()
    raise OpenRouterError(str(last) if last else "OpenRouter unavailable")
