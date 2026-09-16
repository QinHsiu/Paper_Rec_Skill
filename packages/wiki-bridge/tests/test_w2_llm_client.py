from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.llm_client import (
    LlmUnconfigured,
    first_json_object,
    llm_config_from_env,
    make_json_chat,
    resolve_llm,
)


def _ok_transport(content: str, seen: list):
    def transport(req, timeout):
        seen.append(req)
        return 200, json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    return transport


def test_config_none_without_key():
    assert llm_config_from_env({}) is None


def test_config_precedence_and_defaults():
    c = llm_config_from_env({"OPENAI_API_KEY": "k"})
    assert c.api_key == "k" and c.model == "gpt-4o-mini" and c.base_url == "https://api.openai.com/v1"
    c2 = llm_config_from_env({"PAPER_REC_LLM_API_KEY": "p", "OPENAI_API_KEY": "k", "PAPER_REC_LLM_MODEL": "m", "PAPER_REC_LLM_BASE_URL": "https://h/v1/"})
    assert (c2.api_key, c2.model, c2.base_url) == ("p", "m", "https://h/v1")


def test_json_chat_posts_and_parses():
    seen = []
    chat = make_json_chat(llm_config_from_env({"OPENAI_API_KEY": "k"}), transport=_ok_transport('{"a": 1}', seen))
    assert chat("sys", "user") == {"a": 1}
    req = seen[0]
    assert req.full_url == "https://api.openai.com/v1/chat/completions"
    assert req.get_header("Authorization") == "Bearer k"
    body = json.loads(req.data.decode())
    assert body["temperature"] == 0 and body["messages"][0]["role"] == "system"


def test_json_chat_returns_none_on_http_error_and_bad_shape():
    cfg = llm_config_from_env({"OPENAI_API_KEY": "k"})
    assert make_json_chat(cfg, transport=lambda r, t: (500, b""))("s", "u") is None
    assert make_json_chat(cfg, transport=lambda r, t: (200, b'{"choices": []}'))("s", "u") is None
    assert make_json_chat(cfg, transport=_ok_transport("not json", []))("s", "u") is None


def test_first_json_object_extracts_embedded():
    assert first_json_object('text before {"x": [1]} after') == {"x": [1]}
    assert first_json_object("[1,2]") is None


def test_resolve_llm_modes(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PAPER_REC_LLM_API_KEY", raising=False)
    assert resolve_llm("off") == (None, None, "disabled")
    assert resolve_llm("auto") == (None, None, "no_api_key")
    with pytest.raises(LlmUnconfigured):
        resolve_llm("required")
    monkeypatch.setenv("PAPER_REC_LLM_API_KEY", "k")
    chat, model, reason = resolve_llm("auto", transport=_ok_transport("{}", []))
    assert callable(chat) and model == "gpt-4o-mini" and reason is None
    with pytest.raises(ValueError):
        resolve_llm("sometimes")
