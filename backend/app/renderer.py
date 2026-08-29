"""
Presentation-stage renderer for reverse-engineering phase results.

The analysis stage is responsible for repository exploration and reasoning.
The rendering stage is repository-blind and receives the complete raw output
returned by OpenCode. Its only responsibility is to improve presentation
without reducing or changing the substantive analysis.
"""

from typing import Optional

import time

import requests

from .config import settings
from .render_prompt import build_render_prompt


_PROVIDER_ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}


def _render_with_openai_compatible_api(
    *,
    endpoint: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    }

    max_attempts = 4
    base_delay = 2

    for attempt in range(max_attempts):
        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        if response.status_code != 429:
            response.raise_for_status()
            break

        if attempt == max_attempts - 1:
            response.raise_for_status()

        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = base_delay * (2 ** attempt)
        else:
            delay = base_delay * (2 ** attempt)

        time.sleep(delay)

    data = response.json()
    rendered = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    if not isinstance(rendered, str) or not rendered.strip():
        raise RuntimeError("Renderer returned an empty response")

    return rendered.strip()


def _render_with_anthropic(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int,
) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        json={
            "model": model,
            "max_tokens": 32768,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        },
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )

    response.raise_for_status()

    data = response.json()
    content = data.get("content", [])

    rendered_parts = [
        item.get("text", "")
        for item in content
        if item.get("type") == "text"
    ]

    rendered = "\n".join(
        part for part in rendered_parts if isinstance(part, str)
    ).strip()

    if not rendered:
        raise RuntimeError("Renderer returned an empty response")

    return rendered


def _render_with_google(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int,
) -> str:
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent?key={api_key}"
    )

    response = requests.post(
        endpoint,
        json={
            "system_instruction": {
                "parts": [
                    {
                        "text": system_prompt,
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": user_prompt,
                        }
                    ],
                }
            ],
        },
        headers={
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )

    response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])

    rendered_parts = []

    if candidates:
        content = candidates[0].get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str):
                rendered_parts.append(text)

    rendered = "\n".join(rendered_parts).strip()

    if not rendered:
        raise RuntimeError("Renderer returned an empty response")

    return rendered


def render_analysis(
    phase: str,
    analysis: str,
    provider: str = "openrouter",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Transform the complete raw OpenCode output into presentation-ready Markdown.

    The renderer deliberately has no repository access and does not receive the
    repository URL. It must preserve the substantive content supplied by the
    analysis stage rather than performing a second analysis.
    """
    if not analysis or not analysis.strip():
        raise ValueError("analysis cannot be empty")

    provider_name = (provider or "openrouter").strip().lower()

    if not model or not model.strip():
        model = settings.opencode_model

    # The generic OpenRouter free router can select specialist models such as
    # content-safety classifiers. For rendering, use a general-purpose model
    # instead when the user selected openrouter/free.
    if provider_name == "openrouter" and model.strip().lower() in {
        "free",
        "openrouter/free",
    }:
        model = "openrouter/free"

    if not api_key or not api_key.strip():
        raise ValueError(
            f"An API key is required for renderer provider '{provider_name}'."
        )

    system_prompt, user_prompt = build_render_prompt(
        phase,
        analysis,
    )

    if provider_name in _PROVIDER_ENDPOINTS:
        return _render_with_openai_compatible_api(
            endpoint=_PROVIDER_ENDPOINTS[provider_name],
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
        )

    if provider_name == "anthropic":
        return _render_with_anthropic(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
        )

    if provider_name == "google":
        return _render_with_google(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
        )

    raise ValueError(
        f"Unsupported renderer provider: {provider_name}. "
        "Supported providers are: openrouter, openai, anthropic, google"
    )