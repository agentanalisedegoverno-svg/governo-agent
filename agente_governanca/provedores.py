"""Adaptadores independentes para os provedores do painel de governanca."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


DEFAULT_PROVIDER_TIMEOUT_SECONDS = 180


@dataclass
class ProviderReview:
    provider: str
    model: str
    result: dict
    usage: dict


@dataclass
class ProviderFailure:
    provider: str
    error_type: str
    message: str


PROVIDER_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def provider_timeout_seconds() -> float:
    raw = os.getenv("AI_GOVERNOR_PROVIDER_TIMEOUT_SECONDS")
    if not raw:
        return float(DEFAULT_PROVIDER_TIMEOUT_SECONDS)
    try:
        timeout = float(raw)
    except ValueError:
        return float(DEFAULT_PROVIDER_TIMEOUT_SECONDS)
    return timeout if timeout > 0 else float(DEFAULT_PROVIDER_TIMEOUT_SECONDS)


def configured_providers(requested: list[str]) -> tuple[list[str], list[ProviderFailure]]:
    configured = []
    skipped = []
    for provider in requested:
        env_name = PROVIDER_KEYS[provider]
        if os.getenv(env_name):
            configured.append(provider)
        else:
            skipped.append(
                ProviderFailure(
                    provider=provider,
                    error_type="missing_credentials",
                    message=f"{env_name} nao configurada.",
                )
            )
    return configured, skipped


def _anthropic_review(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    knowledge_pull: bool,
    allowed_domains: list[str],
) -> ProviderReview:
    import anthropic

    model = os.getenv(
        "AI_GOVERNOR_ANTHROPIC_MODEL",
        os.getenv("AI_GOVERNOR_MODEL", "claude-sonnet-5"),
    )
    kwargs = {
        "model": model,
        "max_tokens": 16_000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "output_config": {
            "effort": "high",
            "format": {"type": "json_schema", "schema": schema},
        },
    }
    if knowledge_pull:
        kwargs["tools"] = [
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "allowed_domains": allowed_domains,
            }
        ]
    response = anthropic.Anthropic(timeout=provider_timeout_seconds()).messages.create(
        **kwargs
    )
    text = next(
        (block.text for block in response.content if getattr(block, "type", None) == "text"),
        None,
    )
    if not text:
        raise RuntimeError("Anthropic nao retornou bloco textual estruturado.")
    usage = response.usage
    return ProviderReview(
        provider="anthropic",
        model=response.model,
        result=json.loads(text),
        usage={
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
        },
    )


def _openai_review(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    knowledge_pull: bool,
    allowed_domains: list[str],
) -> ProviderReview:
    from openai import OpenAI

    model = os.getenv("AI_GOVERNOR_OPENAI_MODEL", "gpt-5.6-terra")
    kwargs = {
        "model": model,
        "instructions": system_prompt,
        "input": user_prompt,
        "max_output_tokens": 16_000,
        "reasoning": {"effort": "high"},
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "governance_analysis",
                "strict": True,
                "schema": schema,
            }
        },
    }
    if knowledge_pull:
        kwargs.update(
            {
                "tools": [
                    {
                        "type": "web_search",
                        "filters": {"allowed_domains": allowed_domains[:100]},
                    }
                ],
                "tool_choice": "required",
                "include": ["web_search_call.action.sources"],
            }
        )
    response = OpenAI(timeout=provider_timeout_seconds()).responses.create(**kwargs)
    if not response.output_text:
        raise RuntimeError("OpenAI nao retornou texto estruturado.")
    usage = response.usage
    return ProviderReview(
        provider="openai",
        model=response.model,
        result=json.loads(response.output_text),
        usage={
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
        },
    )


def _gemini_review(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    knowledge_pull: bool,
) -> ProviderReview:
    from google import genai

    model = os.getenv("AI_GOVERNOR_GEMINI_MODEL", "gemini-3.7-flash")
    timeout = provider_timeout_seconds()
    try:
        from google.genai import types

        client = genai.Client(
            http_options=types.HttpOptions(timeout=int(timeout * 1000))
        )
    except Exception:
        client = genai.Client()
    interaction = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=user_prompt,
        store=False,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": schema,
        },
    )
    if not interaction.output_text:
        raise RuntimeError("Gemini nao retornou texto estruturado.")
    usage = getattr(interaction, "usage", None)
    result = json.loads(interaction.output_text)
    if knowledge_pull:
        # A busca do Gemini ainda nao permite restringir dominios na propria API.
        result["knowledge_updates"] = []
        result["proposed_patches"] = []
    return ProviderReview(
        provider="gemini",
        model=model,
        result=result,
        usage={
            "input_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
            "output_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
        },
    )


def _run_provider(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    knowledge_pull: bool,
    allowed_domains: list[str],
) -> ProviderReview:
    if provider == "anthropic":
        return _anthropic_review(
            system_prompt,
            user_prompt,
            schema,
            knowledge_pull,
            allowed_domains,
        )
    if provider == "openai":
        return _openai_review(
            system_prompt,
            user_prompt,
            schema,
            knowledge_pull,
            allowed_domains,
        )
    if provider == "gemini":
        return _gemini_review(system_prompt, user_prompt, schema, knowledge_pull)
    raise ValueError(f"Provedor desconhecido: {provider}")


def run_panel(
    providers: list[str],
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    knowledge_pull: bool,
    allowed_domains: list[str],
) -> tuple[list[ProviderReview], list[ProviderFailure]]:
    configured, failures = configured_providers(providers)
    reviews = []
    with ThreadPoolExecutor(max_workers=max(1, len(configured))) as executor:
        futures = {
            executor.submit(
                _run_provider,
                provider,
                system_prompt,
                user_prompt,
                schema,
                knowledge_pull,
                allowed_domains,
            ): provider
            for provider in configured
        }
        for future in as_completed(futures):
            provider = futures[future]
            try:
                reviews.append(future.result())
            except Exception as exc:  # A falha de um provedor nao oculta os demais.
                failures.append(
                    ProviderFailure(
                        provider=provider,
                        error_type=type(exc).__name__,
                        message=str(exc)[:500],
                    )
                )
    reviews.sort(key=lambda item: providers.index(item.provider))
    failures.sort(key=lambda item: providers.index(item.provider))
    return reviews, failures
