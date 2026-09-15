# packages/wiki-bridge/wiki_bridge/http_client.py
"""Stdlib HTTP helper with injectable transport and key redaction (W1)."""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable

Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]

_SENSITIVE = {"authorization", "x-api-key"}


class HttpError(Exception):
    """Base HTTP error; never carries secrets or raw bodies."""


class HttpTimeout(HttpError):
    pass


class HttpRateLimited(HttpError):
    pass


class HttpStatusError(HttpError):
    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP {status} for {url}")
        self.status = status


class HttpBadJson(HttpError):
    pass


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: ("***" if k.lower() in _SENSITIVE else v) for k, v in (headers or {}).items()}


def _default_transport(req: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), b""


def _request(
    req: urllib.request.Request,
    *,
    timeout: float,
    transport: Transport | None,
) -> Any:
    tr = transport or _default_transport
    try:
        status, body = tr(req, timeout)
    except (socket.timeout, TimeoutError) as exc:
        raise HttpTimeout(f"timeout after {timeout}s for {req.full_url}") from None
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc, "reason", None), (socket.timeout, TimeoutError)):
            raise HttpTimeout(f"timeout after {timeout}s for {req.full_url}") from None
        raise HttpStatusError(0, req.full_url) from None
    if status == 429:
        raise HttpRateLimited(f"rate limited (429) for {req.full_url}")
    if status < 200 or status >= 300:
        raise HttpStatusError(status, req.full_url)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HttpBadJson(f"non-JSON response for {req.full_url}") from None


def get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
    transport: Transport | None = None,
) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    return _request(req, timeout=timeout, transport=transport)


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    transport: Transport | None = None,
) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})},
    )
    return _request(req, timeout=timeout, transport=transport)
