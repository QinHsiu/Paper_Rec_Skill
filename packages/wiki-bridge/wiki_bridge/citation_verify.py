"""Citation verification — detect hallucinated BibTeX entries.

Adapted from aiming-lab/AutoResearchClaw ``literature/verify.py`` (stdlib only).

Layers:
  L1 arXiv id_list
  L2 CrossRef / DataCite DOI
  L3 OpenAlex title search (polite pool)

Statuses: verified | suspicious | hallucinated | skipped
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class VerifyStatus(str, Enum):
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    HALLUCINATED = "hallucinated"
    SKIPPED = "skipped"


@dataclass
class CitationResult:
    cite_key: str
    title: str
    status: VerifyStatus
    confidence: float
    method: str
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cite_key": self.cite_key,
            "title": self.title,
            "status": self.status.value,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "details": self.details,
        }


@dataclass
class VerificationReport:
    total: int = 0
    verified: int = 0
    suspicious: int = 0
    hallucinated: int = 0
    skipped: int = 0
    results: list[CitationResult] = field(default_factory=list)

    @property
    def integrity_score(self) -> float:
        verifiable = self.total - self.skipped
        if verifiable <= 0:
            return 1.0
        return round(self.verified / verifiable, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total": self.total,
                "verified": self.verified,
                "suspicious": self.suspicious,
                "hallucinated": self.hallucinated,
                "skipped": self.skipped,
                "integrity_score": self.integrity_score,
            },
            "results": [r.to_dict() for r in self.results],
        }


_ENTRY_RE = re.compile(
    r"@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\s*\}(?=\s*(?:@|\Z))",
    re.DOTALL,
)
_FIELD_RE = re.compile(
    r"(\w+)\s*=\s*"
    r"(?:"
    r"\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"
    r'|"([^"]*)"'
    r"|([^,{}\s][^,{}]*?)"
    r")\s*(?:,|$)",
    re.DOTALL,
)

_UA = "PaperRec-Skill/2.25 (citation-verify; mailto:paper-rec@local)"


def parse_bibtex_entries(bib_text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for m in _ENTRY_RE.finditer(bib_text or ""):
        entry: dict[str, str] = {"type": m.group(1).lower(), "key": m.group(2).strip()}
        for fm in _FIELD_RE.finditer(m.group(3)):
            value = fm.group(2) if fm.group(2) is not None else fm.group(3)
            if value is None:
                value = fm.group(4)
            entry[fm.group(1).lower()] = (value or "").strip()
        entries.append(entry)
    return entries


def title_similarity(a: str, b: str) -> float:
    def _words(t: str) -> set[str]:
        return set(re.sub(r"[^a-z0-9\s]", "", (t or "").lower()).split()) - {""}

    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


def _http_get(url: str, *, timeout: int = 20, accept: str = "*/*") -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": accept})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def _classify(sim: float, *, method: str, title: str, found: str, key: str) -> CitationResult:
    if sim >= 0.80:
        status, conf = VerifyStatus.VERIFIED, sim
        details = f"Confirmed via {method}: '{found}'"
    elif sim >= 0.50:
        status, conf = VerifyStatus.SUSPICIOUS, sim
        details = f"{method} title diverge (sim={sim:.2f}): '{found}'"
    else:
        status, conf = VerifyStatus.HALLUCINATED, max(sim, 0.1)
        details = f"{method} mismatch (sim={sim:.2f}): '{found}'"
    return CitationResult(key, title, status, conf, method, details)


def verify_by_arxiv_id(arxiv_id: str, expected_title: str, *, key: str = "") -> CitationResult | None:
    params = urllib.parse.urlencode({"id_list": arxiv_id, "max_results": "1"})
    raw = _http_get(f"https://export.arxiv.org/api/query?{params}")
    if raw is None:
        return None
    try:
        root = ET.fromstring(raw.decode("utf-8"))
    except ET.ParseError:
        return None
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    if not entries:
        return CitationResult(
            key, expected_title, VerifyStatus.HALLUCINATED, 0.9, "arxiv_id", f"arXiv id {arxiv_id} not found"
        )
    entry = entries[0]
    found = re.sub(r"\s+", " ", (entry.findtext("atom:title", "", ns) or "").strip())
    eid = entry.findtext("atom:id", "", ns)
    if "api/errors" in eid or not found or found.lower() == "error":
        return CitationResult(
            key, expected_title, VerifyStatus.HALLUCINATED, 0.9, "arxiv_id", f"arXiv id {arxiv_id} invalid"
        )
    return _classify(title_similarity(expected_title, found), method="arxiv_id", title=expected_title, found=found, key=key)


def verify_by_doi(doi: str, expected_title: str, *, key: str = "") -> CitationResult | None:
    doi = doi.removeprefix("https://doi.org/").strip()
    encoded = urllib.parse.quote(doi)
    raw = _http_get(f"https://api.crossref.org/works/{encoded}", accept="application/json")
    if raw is None:
        # DataCite fallback (arXiv DOIs)
        raw = _http_get(f"https://api.datacite.org/dois/{encoded}", accept="application/json")
        if raw is None:
            return None
        try:
            body = json.loads(raw.decode("utf-8"))
            attrs = (body.get("data") or {}).get("attributes") or {}
            titles = attrs.get("titles") or []
            found = str((titles[0] or {}).get("title") if titles else "") or ""
        except Exception:
            return None
        if not found:
            return CitationResult(
                key, expected_title, VerifyStatus.HALLUCINATED, 0.85, "doi", f"DOI {doi} empty title"
            )
        return _classify(title_similarity(expected_title, found), method="doi", title=expected_title, found=found, key=key)
    try:
        body = json.loads(raw.decode("utf-8"))
        msg = body.get("message") or {}
        titles = msg.get("title") or []
        found = str(titles[0]) if titles else ""
    except Exception:
        return None
    if not found:
        return CitationResult(
            key, expected_title, VerifyStatus.HALLUCINATED, 0.85, "doi", f"DOI {doi} not found / empty"
        )
    return _classify(title_similarity(expected_title, found), method="doi", title=expected_title, found=found, key=key)


def verify_by_openalex_title(expected_title: str, *, key: str = "", mailto: str = "paper-rec@local") -> CitationResult | None:
    q = urllib.parse.urlencode(
        {"search": expected_title, "per-page": "3", "mailto": mailto, "sort": "relevance_score:desc"}
    )
    raw = _http_get(f"https://api.openalex.org/works?{q}", accept="application/json")
    if raw is None:
        return None
    try:
        body = json.loads(raw.decode("utf-8"))
        results = body.get("results") or []
    except Exception:
        return None
    if not results:
        return CitationResult(
            key, expected_title, VerifyStatus.HALLUCINATED, 0.7, "openalex_title", "no OpenAlex hit"
        )
    best = results[0]
    found = str(best.get("display_name") or "")
    sim = title_similarity(expected_title, found)
    return _classify(sim, method="openalex_title", title=expected_title, found=found, key=key)


def _extract_arxiv(entry: dict[str, str]) -> str:
    for k in ("eprint", "arxiv"):
        v = (entry.get(k) or "").strip()
        if v:
            return re.sub(r"^arxiv:", "", v, flags=re.I)
    url = entry.get("url") or ""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url, re.I)
    return m.group(1) if m else ""


def verify_entry(entry: dict[str, str], *, mailto: str = "paper-rec@local") -> CitationResult:
    key = entry.get("key") or ""
    title = entry.get("title") or ""
    if not title.strip():
        return CitationResult(key, title, VerifyStatus.SKIPPED, 0.0, "skipped", "missing title")

    arxiv = _extract_arxiv(entry)
    if arxiv:
        r = verify_by_arxiv_id(arxiv, title, key=key)
        if r is not None:
            r.cite_key = key
            return r

    doi = (entry.get("doi") or "").strip()
    if doi:
        r = verify_by_doi(doi, title, key=key)
        if r is not None:
            r.cite_key = key
            return r

    r = verify_by_openalex_title(title, key=key, mailto=mailto)
    if r is not None:
        return r
    return CitationResult(key, title, VerifyStatus.SKIPPED, 0.0, "skipped", "all APIs unreachable")


def verify_bibtex(bib_text: str, *, mailto: str = "paper-rec@local") -> VerificationReport:
    report = VerificationReport()
    for entry in parse_bibtex_entries(bib_text):
        result = verify_entry(entry, mailto=mailto)
        report.results.append(result)
        report.total += 1
        if result.status == VerifyStatus.VERIFIED:
            report.verified += 1
        elif result.status == VerifyStatus.SUSPICIOUS:
            report.suspicious += 1
        elif result.status == VerifyStatus.HALLUCINATED:
            report.hallucinated += 1
        else:
            report.skipped += 1
    return report


def filter_bibtex(bib_text: str, report: VerificationReport, *, drop: set[str] | None = None) -> str:
    """Keep entries that are not hallucinated (default)."""
    drop = drop or {VerifyStatus.HALLUCINATED.value}
    bad_keys = {r.cite_key for r in report.results if r.status.value in drop}
    if not bad_keys:
        return bib_text
    kept: list[str] = []
    for m in _ENTRY_RE.finditer(bib_text or ""):
        key = m.group(2).strip()
        if key not in bad_keys:
            kept.append(m.group(0).strip())
    return ("\n\n".join(kept) + ("\n" if kept else ""))


def verify_bib_file(
    path: Path,
    *,
    out_json: Path | None = None,
    filtered_bib: Path | None = None,
    mailto: str = "paper-rec@local",
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    report = verify_bibtex(text, mailto=mailto)
    payload = report.to_dict()
    payload["source"] = str(path)
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if filtered_bib is not None:
        filtered_bib.parent.mkdir(parents=True, exist_ok=True)
        filtered_bib.write_text(filter_bibtex(text, report), encoding="utf-8")
    return payload
