"""Multi-round novelty critic: whole-idea → facets → verdict; optional LLM may only tighten (W2)."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Callable

from .evidence_score import tokenize
from .llm_client import llm_meta, resolve_llm
from .novelty_check import novelty_against_corpus

VERDICT_ORDER = {"duplicate": 0, "incremental": 1, "novel": 2}
_PROBLEM_CUES = r"\b(for|on|of|to solve|to improve|towards?)\b"
_METHOD_CUES = r"\b(using|via|with|through|by|based on|leveraging)\b"
_SETTING_CUES = r"\b(in|under|across|when|at)\b"
_STOP = {"the", "a", "an", "and", "or", "of", "for", "on", "in", "to", "with", "using", "via", "by", "under", "across", "at", "when", "through", "based", "towards", "toward"}

SYSTEM_PROMPT = (
    "You are a strict novelty reviewer. Given an idea and the closest prior work, answer ONLY JSON: "
    '{"verdict": "duplicate|incremental|novel", "shared_points": [..], "distinguishing_points": [..], "confidence": 0..1}. '
    "Be critical: prefer 'incremental' when the method and problem both appear in prior work."
)


def _phrase_terms(segment: str, k: int = 6) -> list[str]:
    toks = [t for t in tokenize(segment) if t not in _STOP and len(t) > 2]
    return [t for t, _ in Counter(toks).most_common(k)]


def extract_facets(idea: str) -> dict[str, list[str]]:
    """Cue-word segmentation into problem / method / setting keyphrase buckets."""
    text = (idea or "").strip()
    facets = {"problem": [], "method": [], "setting": []}
    if not text:
        return facets
    cuts: list[tuple[int, str]] = []
    m_method = re.search(_METHOD_CUES, text, re.I)
    m_setting = re.search(_SETTING_CUES, text, re.I)
    if m_method:
        cuts.append((m_method.start(), "method"))
    if m_setting:
        cuts.append((m_setting.start(), "setting"))
    cuts.sort(key=lambda c: c[0])
    problem_seg = text[: cuts[0][0]] if cuts else text
    method_seg = setting_seg = ""
    for i, (pos, kind) in enumerate(cuts):
        end = cuts[i + 1][0] if i + 1 < len(cuts) else len(text)
        if kind == "method":
            method_seg = text[pos:end]
        else:
            setting_seg = text[pos:end]
    facets["problem"] = _phrase_terms(re.sub(_PROBLEM_CUES, " ", problem_seg, flags=re.I))
    facets["method"] = _phrase_terms(method_seg)
    facets["setting"] = _phrase_terms(setting_seg)
    if not facets["problem"]:
        facets["problem"] = _phrase_terms(text)
    return facets


def critic_rounds(idea: str, papers: list[dict[str, Any]], *, rounds: int = 3, high_overlap: float = 6.5) -> dict[str, Any]:
    rounds = max(1, min(3, int(rounds)))
    per_round: list[dict[str, Any]] = []
    r1 = novelty_against_corpus(idea, papers, high_overlap=high_overlap)
    per_round.append({"round": 1, "kind": "whole_idea", "hit_n": r1["hit_n"], "top_score": (r1["hits"][0]["score"] if r1["hits"] else 0.0)})
    nearest = r1["hits"][0] if r1["hits"] else None
    facets = extract_facets(idea)
    facet_hits: dict[str, dict[str, Any] | None] = {}
    if rounds >= 2:
        any_facet = any(facets.values())
        if not any_facet:
            per_round.append({"round": 2, "kind": "facets", "skipped": "no_facets"})
        else:
            for name, terms in facets.items():
                if not terms:
                    facet_hits[name] = None
                    continue
                fr = novelty_against_corpus(" ".join(terms), papers, high_overlap=high_overlap)
                facet_hits[name] = fr["hits"][0] if fr["hits"] else None
            per_round.append({"round": 2, "kind": "facets", "facet_top": {k: (v["score"] if v else 0.0) for k, v in facet_hits.items()}})
    shared, distinguishing = [], []
    if rounds >= 3 and facet_hits:
        for name, hit in facet_hits.items():
            score = float(hit["score"]) if hit else 0.0
            label = f"{name}: {' '.join(facets[name])}"
            if score >= 0.8 * high_overlap:
                shared.append(label + f" (~ {hit['title']})")
            elif score < 0.5 * high_overlap:
                distinguishing.append(label)
        per_round.append({"round": 3, "kind": "aggregate", "shared_n": len(shared), "distinguishing_n": len(distinguishing)})
    if not r1["novel"]:
        verdict = "duplicate"
    elif len(shared) >= 2:
        verdict = "incremental"
    else:
        verdict = "novel"
    return {
        "rounds_run": len(per_round),
        "verdict": verdict,
        "shared_points": shared,
        "distinguishing_points": distinguishing,
        "facets": facets,
        "per_round": per_round,
        "nearest": nearest,
        "policy": f"duplicate if whole-idea hit>={high_overlap}; incremental if >=2 facets hit>={0.8*high_overlap:.2f}",
    }


def llm_critique(chat: Callable[[str, str], dict[str, Any] | None], idea: str, hits: list[dict[str, Any]]) -> dict[str, Any] | None:
    prior = "\n".join(f"- {h.get('title')} ({h.get('year') or 'n.d.'}) score={h.get('score')}" for h in hits[:8]) or "- (none)"
    out = chat(SYSTEM_PROMPT, f"IDEA:\n{idea}\n\nCLOSEST PRIOR WORK:\n{prior}")
    if not isinstance(out, dict) or str(out.get("verdict")) not in VERDICT_ORDER:
        return None
    try:
        return {
            "verdict": str(out["verdict"]),
            "shared_points": [str(x) for x in (out.get("shared_points") or [])][:8],
            "distinguishing_points": [str(x) for x in (out.get("distinguishing_points") or [])][:8],
            "confidence": float(out.get("confidence") or 0.0),
        }
    except (TypeError, ValueError, AttributeError):
        return None


def merge_verdicts(heuristic: dict[str, Any], llm: dict[str, Any] | None) -> dict[str, Any]:
    """Stricter verdict wins; heuristic 'duplicate' is a hard gate; invalid LLM output is ignored."""
    final = dict(heuristic)
    if not llm or llm.get("verdict") not in VERDICT_ORDER:
        return final
    if VERDICT_ORDER[llm["verdict"]] < VERDICT_ORDER[final["verdict"]]:
        final["verdict"] = llm["verdict"]
    final["shared_points"] = list(dict.fromkeys([*final.get("shared_points", []), *llm.get("shared_points", [])]))
    final["distinguishing_points"] = list(dict.fromkeys([*final.get("distinguishing_points", []), *llm.get("distinguishing_points", [])]))
    return final


def run_novelty_critic(
    idea: str,
    papers: list[dict[str, Any]],
    *,
    rounds: int = 3,
    use_llm: str = "off",
    high_overlap: float = 6.5,
    transport=None,
) -> dict[str, Any]:
    heur = critic_rounds(idea, papers or [], rounds=rounds, high_overlap=high_overlap)
    chat, model, skip = resolve_llm(use_llm, transport=transport)  # may raise LlmUnconfigured
    llm = None
    if chat is not None:
        hits = novelty_against_corpus(idea, papers or [], high_overlap=high_overlap)["hits"]
        llm = llm_critique(chat, idea, hits)
        if llm is None:
            skip = "llm_bad_response"
    final = merge_verdicts(heur, llm)
    final["llm"] = llm_meta(llm is not None, model, skip, verdict=(llm or {}).get("verdict"))
    return final
