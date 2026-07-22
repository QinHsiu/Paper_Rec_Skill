"""Statistical rigor gate for Results / Experiments prose.

Blocks single-run claims that lack variance (std/CI/±), seed count, or
multi-run language — complements float whitelist (number-verify).
"""
from __future__ import annotations

import re
from typing import Any

_SECTION = re.compile(
    r"(?im)^(?:\#+\s*)?(?:\d+(\.\d+)*\s+)?(results?|experiments?|evaluation|实验结果|实验|结果)\b.*$"
)
_NEXT_H = re.compile(r"(?im)^\#+\s+")
_VARIANCE = re.compile(
    r"(?i)(\±|\+/-|std\.?|standard deviation|confidence interval|\bCI\b|"
    r"95\s*%|error bar|IQR|seed[s]?\s*[=:]|\bn\s*=\s*\d+|runs?\s*=\s*\d+|"
    r"平均|标准差|置信区间|三次|五次|多次运行|多随机种子)"
)
_POINT_CLAIM = re.compile(
    r"(?i)(achieve[sd]?|obtain[sd]?|reach(?:es|ed)?|report[sd]?|improve[sd]?|"
    r"outperform[sd]?|SOTA|state-of-the-art|准确率|达到|提升|优于)\b"
)
_FLOAT = re.compile(r"\d+\.\d+")


def extract_results_sections(text: str) -> str:
    lines = (text or "").splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        if _SECTION.search(line.strip()):
            capture = True
            out.append(line)
            continue
        if capture and _NEXT_H.match(line) and not _SECTION.search(line.strip()):
            # stop at next major heading that isn't results
            if line.strip().startswith("#"):
                break
        if capture:
            out.append(line)
    return "\n".join(out) if out else (text or "")


def check_stats_rigor(text: str, *, require_section: bool = False) -> dict[str, Any]:
    """Return ok=False when numeric Results claims lack variance/seed evidence."""
    body = extract_results_sections(text)
    if require_section and body == (text or "") and not _SECTION.search(text or ""):
        return {
            "ok": True,
            "skipped": True,
            "reason": "no_results_section",
            "issues": [],
            "claim_sentences": 0,
        }

    issues: list[dict[str, Any]] = []
    claims = 0
    for sent in re.split(r"(?<=[.!?。！？])\s+", body):
        sent = sent.strip()
        if len(sent) < 25:
            continue
        if not _FLOAT.search(sent):
            continue
        if not _POINT_CLAIM.search(sent):
            continue
        claims += 1
        if not _VARIANCE.search(sent) and not _VARIANCE.search(body):
            # allow if section-level variance exists once; else flag sentence
            issues.append(
                {
                    "sentence": sent[:300],
                    "issue": "numeric_claim_without_variance_or_seeds",
                }
            )

    # If whole Results has variance somewhere, only flag sentences that look absolute
    section_has_var = bool(_VARIANCE.search(body))
    if section_has_var:
        # keep only claims that assert a lone float without nearby ± in same sentence
        filtered = []
        for it in issues:
            s = it["sentence"]
            if not _VARIANCE.search(s) and len(_FLOAT.findall(s)) >= 1:
                # still an issue if sentence itself has no variance
                filtered.append(it)
        # soften: if ≥1 variance mention in section, require per-sentence only when many claims
        if claims <= 2 and section_has_var:
            issues = []
        else:
            issues = filtered

    return {
        "ok": len(issues) == 0,
        "skipped": False,
        "claim_sentences": claims,
        "issues": issues,
        "issue_n": len(issues),
        "section_has_variance_cue": section_has_var,
        "policy": "Results numeric claims should include ±/std/CI/seeds or multi-run wording.",
    }
