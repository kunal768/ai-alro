"""
LLM provider abstraction for the Reasoner Agent.

Supported providers (set via LLM_PROVIDER env var):
  anthropic  — Claude API          (requires ANTHROPIC_API_KEY)
  openai     — OpenAI API          (requires OPENAI_API_KEY)
  ollama     — Local Ollama server, OpenAI-compatible endpoint
               Start with: ollama serve && ollama pull llama3.2
               No API key required.

Provider + model are read at import time so the health endpoint can report them.
"""
import os
from typing import AsyncIterator

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic").lower()
LLM_MODEL: str = os.getenv("LLM_MODEL", "")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Sensible defaults per provider
_DEFAULTS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "ollama": "llama3.2",
}


def _effective_model() -> str:
    return LLM_MODEL or _DEFAULTS.get(LLM_PROVIDER, "claude-sonnet-4-6")


# ── Anthropic ──────────────────────────────────────────────────────────────────

async def _stream_anthropic(system: str, user: str, model: str) -> AsyncIterator[str]:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    async with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
        temperature=LLM_TEMPERATURE,
    ) as stream:
        async for text in stream.text_stream:
            if text:
                yield text


# ── OpenAI / Ollama (OpenAI-compatible) ───────────────────────────────────────

async def _stream_openai_compatible(
    system: str,
    user: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> AsyncIterator[str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key or "placeholder",
        base_url=base_url,
    )
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        stream=True,
        max_tokens=2048,
        temperature=LLM_TEMPERATURE,
    )
    async for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            yield text


# ── Public interface ───────────────────────────────────────────────────────────

async def stream_llm(system: str, user: str) -> AsyncIterator[str]:
    """Stream completions from the configured LLM provider."""
    model = _effective_model()

    if LLM_PROVIDER == "anthropic":
        async for chunk in _stream_anthropic(system, user, model):
            yield chunk

    elif LLM_PROVIDER == "openai":
        async for chunk in _stream_openai_compatible(
            system, user, model, api_key=OPENAI_API_KEY
        ):
            yield chunk

    elif LLM_PROVIDER == "ollama":
        async for chunk in _stream_openai_compatible(
            system, user, model, api_key="ollama", base_url=OLLAMA_BASE_URL
        ):
            yield chunk

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER={LLM_PROVIDER!r}. "
            "Valid options: anthropic | openai | ollama"
        )


def provider_summary() -> dict:
    return {"provider": LLM_PROVIDER, "model": _effective_model(), "temperature": LLM_TEMPERATURE}
