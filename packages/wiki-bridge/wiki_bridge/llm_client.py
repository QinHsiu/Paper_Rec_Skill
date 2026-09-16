"""Text-only OpenAI-compatible JSON chat helper (W2). Errors never carry secrets."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .http_client import HttpError, Transport, post_json

USE_LLM_MODES = ("off", "auto", "required")


@dataclass(frozen=True)
class LlmConfig:
    api_key: str
    base_url: str
    model: str


class LlmUnconfigured(RuntimeError):
    pass


def llm_config_from_env(env: Mapping[str, str] | None = None) -> LlmConfig | None:
    e = os.environ if env is None else env
    key = e.get("PAPER_REC_LLM_API_KEY") or e.get("OPENAI_API_KEY")
    if not key:
        return None
    return LlmConfig(
        api_key=key,
        base_url=(e.get("PAPER_REC_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
        model=e.get("PAPER_REC_LLM_MODEL") or "gpt-4o-mini",
    )


def first_json_object(text: str) -> dict[str, Any] | None:
    text = text or ""
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def make_json_chat(
    config: LlmConfig,
    *,
    transport: Transport | None = None,
    timeout: float = 60.0,
) -> Callable[[str, str], dict[str, Any] | None]:
    url = config.base_url + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}"}

    def chat(system: str, user: str) -> dict[str, Any] | None:
        payload = {
            "model": config.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            resp = post_json(url, payload, headers=headers, timeout=timeout, transport=transport)
        except HttpError:
            return None
        try:
            content = resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        return first_json_object(str(content))

    return chat


def resolve_llm(
    use_llm: str,
    *,
    transport: Transport | None = None,
) -> tuple[Callable[[str, str], dict[str, Any] | None] | None, str | None, str | None]:
    """-> (chat, model, skip_reason). Raises LlmUnconfigured for required-without-key."""
    if use_llm not in USE_LLM_MODES:
        raise ValueError(f"use_llm must be one of {USE_LLM_MODES}")
    if use_llm == "off":
        return None, None, "disabled"
    cfg = llm_config_from_env()
    if cfg is None:
        if use_llm == "required":
            raise LlmUnconfigured("llm_required_but_unconfigured: set PAPER_REC_LLM_API_KEY or OPENAI_API_KEY")
        return None, None, "no_api_key"
    return make_json_chat(cfg, transport=transport), cfg.model, None


def llm_meta(applied: bool, model: str | None, skip_reason: str | None, **extra: Any) -> dict[str, Any]:
    """Uniform block every engine embeds under key "llm"."""
    return {"applied": applied, "skipped": not applied, "skip_reason": None if applied else skip_reason, "model": model if applied else None, **extra}
