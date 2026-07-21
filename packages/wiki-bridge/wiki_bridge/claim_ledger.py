"""Report-level claim → citation ledger (PaperPilot-inspired).

Scans Markdown (or claim JSON) and marks sentences without citations as
``material_gap``. Complements BibTeX ``citation-verify`` (existence) with
draft-level grounding checks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# [Author2024], \cite{key}, (Author et al., 2024)
_CITE_BRACKET = re.compile(r"\[([A-Za-z][A-Za-z0-9_:\-]{0,64})\]")
_CITE_LATEX = re.compile(r"\\cite[tp]?\{([^}]+)\}")
_CITE_PAREN = re.compile(
    r"\(([A-Z][A-Za-z\-]+(?:\s+et\s+al\.)?(?:\s*&\s*[A-Z][A-Za-z\-]+)?,?\s*\d{4}[a-z]?)\)"
)
_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def extract_citations(text: str) -> list[str]:
    found: list[str] = []
    for m in _CITE_LATEX.finditer(text or ""):
        for part in m.group(1).split(","):
            key = part.strip()
            if key:
                found.append(key)
    for m in _CITE_BRACKET.finditer(text or ""):
        found.append(m.group(1))
    for m in _CITE_PAREN.finditer(text or ""):
        found.append(m.group(1).strip())
    return list(dict.fromkeys(found))


def _looks_like_claim(sentence: str) -> bool:
    s = sentence.strip()
    if len(s) < 40:
        return False
    # skip headings / list markers only
    if s.startswith("#") or s.startswith("|"):
        return False
    claimish = (
        "show",
        "demonstrate",
        "propose",
        "achieve",
        "outperform",
        "state-of-the-art",
        "sota",
        "we ",
        "our ",
        "表明",
        "提出",
        "优于",
        "首次",
        "证明",
    )
    low = s.lower()
    return any(c in low for c in claimish) or bool(re.search(r"\d", s))


def claims_from_markdown(text: str) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    # strip code fences lightly
    body = re.sub(r"```[\s\S]*?```", " ", text or "")
    for i, para in enumerate(re.split(r"\n\s*\n", body), start=1):
        para = para.strip()
        if not para or para.startswith("#"):
            continue
        for j, sent in enumerate(_SENT_SPLIT.split(para), start=1):
            sent = sent.strip()
            if not _looks_like_claim(sent):
                continue
            cites = extract_citations(sent)
            gap = not cites
            claims.append(
                {
                    "claim_id": f"md.{i}.{j}",
                    "text": sent[:500],
                    "citations": cites,
                    "evidence_strength": "gap" if gap else "moderate",
                    "evidence_basis": "draft_sentence",
                    "status": "material_gap" if gap else "grounded",
                }
            )
    return claims


def claims_from_json_list(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, raw in enumerate(items or [], start=1):
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or raw.get("claim") or "").strip()
        if not text:
            continue
        cites = list(raw.get("citations") or raw.get("refs") or [])
        if not cites:
            cites = extract_citations(text)
        gap = not cites or "MATERIAL GAP" in text.upper()
        out.append(
            {
                "claim_id": str(raw.get("claim_id") or f"json.{idx}"),
                "text": text,
                "citations": cites,
                "evidence_strength": "gap" if gap else str(raw.get("evidence_strength") or "moderate"),
                "evidence_basis": str(raw.get("evidence_basis") or "provided"),
                "status": "material_gap" if gap else "grounded",
            }
        )
    return out


def build_claim_ledger(
    *,
    markdown: str = "",
    claims: list[dict[str, Any]] | None = None,
    known_keys: list[str] | None = None,
) -> dict[str, Any]:
    rows = list(claims_from_json_list(claims or []))
    if markdown:
        rows.extend(claims_from_markdown(markdown))
    known = {k.strip() for k in (known_keys or []) if k and str(k).strip()}
    unknown_cite = 0
    if known:
        for row in rows:
            bad = [c for c in row.get("citations") or [] if c not in known]
            if bad:
                unknown_cite += 1
                row["unknown_citations"] = bad
                if row.get("status") == "grounded":
                    row["status"] = "unknown_cite"
    grounded = sum(1 for r in rows if r.get("status") == "grounded")
    gaps = sum(1 for r in rows if r.get("status") == "material_gap")
    return {
        "version": "1.0",
        "policy": (
            "Each report-level claim should cite papers or be marked MATERIAL GAP "
            "when evidence is insufficient."
        ),
        "claim_count": len(rows),
        "grounded": grounded,
        "material_gap": gaps,
        "unknown_cite": unknown_cite,
        "claims": rows,
    }


def build_claim_ledger_from_paths(
    paths: list[Path],
    *,
    known_keys: list[str] | None = None,
) -> dict[str, Any]:
    chunks: list[str] = []
    json_claims: list[dict[str, Any]] = []
    for p in paths:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".json":
            data = json.loads(text)
            if isinstance(data, list):
                json_claims.extend(data)
            elif isinstance(data, dict):
                json_claims.extend(list(data.get("claims") or []))
        else:
            chunks.append(text)
    return build_claim_ledger(
        markdown="\n\n".join(chunks),
        claims=json_claims,
        known_keys=known_keys,
    )
