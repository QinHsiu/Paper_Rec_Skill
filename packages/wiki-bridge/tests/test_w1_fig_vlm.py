from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.fig_review import (
    VlmUnconfigured,
    make_vlm_callback,
    review_figures,
    vlm_config_from_env,
)

MD = "As shown in Figure 1, accuracy increases.\n\n![f1](fig1.png)\n**Figure 1.** Accuracy over epochs.\n"


def _png(tmp_path: Path) -> Path:
    p = tmp_path / "fig1.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 16)
    return p


def test_config_none_without_key():
    assert vlm_config_from_env({}) is None


def test_config_defaults_and_overrides():
    c = vlm_config_from_env({"OPENAI_API_KEY": "k"})
    assert c["api_key"] == "k" and c["model"] == "gpt-4o-mini" and c["base_url"].endswith("/v1")
    c2 = vlm_config_from_env({"PAPER_REC_VLM_API_KEY": "p", "OPENAI_API_KEY": "k", "PAPER_REC_VLM_MODEL": "m", "PAPER_REC_VLM_BASE_URL": "https://h/v1/"})
    assert c2 == {"api_key": "p", "model": "m", "base_url": "https://h/v1"}


def test_callback_posts_image_and_parses_json(tmp_path):
    png = _png(tmp_path)
    seen = {}

    def transport(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.get_header("Authorization")
        body = json.loads(req.data.decode())
        seen["model"] = body["model"]
        parts = body["messages"][0]["content"]
        seen["img"] = [p for p in parts if p.get("type") == "image_url"][0]["image_url"]["url"]
        content = json.dumps({"Img_description": "line up", "Img_review": "ok", "Caption_review": "mismatch: says flat", "Figrefs_review": "ok", "alignment_ok": False, "issues": ["caption_mismatch"]})
        return 200, json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    cb = make_vlm_callback({"api_key": "k", "base_url": "https://h/v1", "model": "m"}, transport=transport)
    out = cb({"figure": "1", "path": str(png), "prompt": "P"})
    assert seen["url"] == "https://h/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert seen["model"] == "m"
    assert seen["img"].startswith("data:image/png;base64,")
    assert base64.b64decode(seen["img"].split(",", 1)[1]) == png.read_bytes()
    assert out["figure"] == "1" and out["alignment_ok"] is False and "caption_mismatch" in out["issues"]


def test_callback_http_error_is_sanitised(tmp_path):
    png = _png(tmp_path)
    cb = make_vlm_callback({"api_key": "SECRET", "base_url": "https://h/v1", "model": "m"}, transport=lambda r, t: (500, b"SECRET"))
    out = cb({"figure": "1", "path": str(png), "prompt": "P"})
    assert out["alignment_ok"] is False
    assert any(i.startswith("vlm_error:HttpStatusError") for i in out["issues"])
    assert "SECRET" not in json.dumps(out)


def test_callback_missing_image_skips(tmp_path):
    cb = make_vlm_callback({"api_key": "k", "base_url": "https://h/v1", "model": "m"}, transport=lambda r, t: (200, b"{}"))
    out = cb({"figure": "1", "path": str(tmp_path / "nope.png"), "prompt": "P"})
    assert out["skipped"] is True and out["skip_reason"] == "image_unreadable"


def test_review_auto_without_key_skips(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PAPER_REC_VLM_API_KEY", raising=False)
    out = review_figures(MD, use_vlm="auto")
    assert out["vlm_applied"] is False and out["vlm_skipped"] is True and out["vlm_skip_reason"] == "no_api_key"


def test_review_required_without_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PAPER_REC_VLM_API_KEY", raising=False)
    with pytest.raises(VlmUnconfigured):
        review_figures(MD, use_vlm="required")


def test_review_auto_with_key_applies_and_blocks(tmp_path, monkeypatch):
    png = _png(tmp_path)
    monkeypatch.setenv("PAPER_REC_VLM_API_KEY", "k")
    md = MD.replace("fig1.png", str(png).replace("\\", "/"))

    def transport(req, timeout):
        content = json.dumps({"Img_description": "flat", "Img_review": "ok", "Caption_review": "mismatch", "Figrefs_review": "ok", "alignment_ok": False, "issues": ["plot_flat_caption_claims_increase"]})
        return 200, json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    out = review_figures(md, use_vlm="auto", vlm_transport=transport)
    assert out["vlm_applied"] is True and out["vlm_skipped"] is False and out["vlm_model"] == "gpt-4o-mini"
    assert out["ok"] is False
    assert any(i["issue"] == "plot_flat_caption_claims_increase" for i in out["issues"])


def test_review_off_is_unchanged():
    out = review_figures(MD, use_vlm="off")
    assert out["vlm_applied"] is False and out["vlm_skipped"] is True and out["vlm_skip_reason"] == "disabled"


def test_unknown_suffix_never_sent_to_vlm(tmp_path):
    p = tmp_path / "secret.txt"
    p.write_text("not an image")
    calls = []

    def transport(req, timeout):
        calls.append(req)
        return 200, b"{}"

    cb = make_vlm_callback({"api_key": "k", "base_url": "https://h/v1", "model": "m"}, transport=transport)
    out = cb({"figure": "Figure 1", "path": str(p), "prompt": "x"})
    assert out["skipped"] and out["skip_reason"] == "image_unreadable"
    assert calls == []
