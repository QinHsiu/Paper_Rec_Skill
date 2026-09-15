# packages/wiki-bridge/tests/test_w1_http_client.py
from __future__ import annotations

import json
import socket
import sys
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wiki_bridge.http_client import (
    HttpBadJson,
    HttpRateLimited,
    HttpStatusError,
    HttpTimeout,
    get_json,
    post_json,
    redact_headers,
)


def _ok(body: dict):
    def transport(req: urllib.request.Request, timeout: float):
        return 200, json.dumps(body).encode("utf-8")
    return transport


def test_get_json_parses_and_sends_headers():
    seen = {}

    def transport(req, timeout):
        seen["url"] = req.full_url
        seen["key"] = req.get_header("X-api-key")
        seen["timeout"] = timeout
        return 200, b'{"a": 1}'

    out = get_json("https://x.test/p", headers={"x-api-key": "SECRET"}, timeout=7.5, transport=transport)
    assert out == {"a": 1}
    assert seen["url"] == "https://x.test/p"
    assert seen["key"] == "SECRET"
    assert seen["timeout"] == 7.5


def test_post_json_sends_body():
    seen = {}

    def transport(req, timeout):
        seen["body"] = json.loads(req.data.decode("utf-8"))
        seen["ct"] = req.get_header("Content-type")
        return 200, b'{"ok": true}'

    out = post_json("https://x.test/c", {"q": 1}, transport=transport)
    assert out == {"ok": True}
    assert seen["body"] == {"q": 1}
    assert "application/json" in seen["ct"]


def test_429_maps_to_rate_limited():
    with pytest.raises(HttpRateLimited):
        get_json("https://x.test", transport=lambda r, t: (429, b"slow"))


def test_500_maps_to_status_error_without_body():
    with pytest.raises(HttpStatusError) as ei:
        get_json("https://x.test", headers={"Authorization": "Bearer SECRET"}, transport=lambda r, t: (500, b"SECRET-BODY"))
    msg = str(ei.value)
    assert "500" in msg
    assert "SECRET" not in msg


def test_bad_json():
    with pytest.raises(HttpBadJson):
        get_json("https://x.test", transport=lambda r, t: (200, b"<html>"))


def test_timeout_maps():
    def transport(r, t):
        raise socket.timeout("t")
    with pytest.raises(HttpTimeout):
        get_json("https://x.test", transport=transport)


def test_redact_headers():
    out = redact_headers({"Authorization": "Bearer k", "x-api-key": "k", "Accept": "a"})
    assert out == {"Authorization": "***", "x-api-key": "***", "Accept": "a"}
