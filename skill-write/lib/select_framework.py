"""Framework auto-selection (STAR / CO-STAR / …)."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Optional

# id → methods/<file>.md (paths relative to this skill package root)
FRAMEWORKS: dict[str, dict[str, str]] = {
    "icio": {
        "name": "ICIO",
        "file": "methods/icio.md",
        "aliases": ("icio",),
    },
    "star": {
        "name": "STAR",
        "file": "methods/star.md",
        "aliases": ("star",),
    },
    "costar": {
        "name": "CO-STAR",
        "file": "methods/costar.md",
        "aliases": ("costar", "co-star", "co_star"),
    },
    "crispe": {
        "name": "CRISPE",
        "file": "methods/crispe.md",
        "aliases": ("crispe",),
    },
    "broke": {
        "name": "BROKE",
        "file": "methods/broke.md",
        "aliases": ("broke",),
    },
    "rascef": {
        "name": "RASCEF",
        "file": "methods/rascef.md",
        "aliases": ("rascef",),
    },
    "racef": {
        "name": "RACEF",
        "file": "methods/racef.md",
        "aliases": ("racef",),
    },
    "spf": {
        "name": "SPF",
        "file": "methods/spf.md",
        "aliases": ("spf",),
    },
}

_ALIAS_TO_ID: dict[str, str] = {}
for _fid, _meta in FRAMEWORKS.items():
    _ALIAS_TO_ID[_fid] = _fid
    for _a in _meta["aliases"]:
        _ALIAS_TO_ID[_a.lower()] = _fid


@dataclass
class FrameworkDecision:
    framework_id: str
    name: str
    method_file: str
    reason: str
    source: str  # user | auto


def resolve_alias(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    key = token.strip().lower().replace(" ", "-")
    return _ALIAS_TO_ID.get(key)


def select_framework(brief: str, forced: Optional[str] = None) -> FrameworkDecision:
    """Pick a writing methodology from user flag or brief text."""
    forced_id = resolve_alias(forced)
    if forced_id:
        meta = FRAMEWORKS[forced_id]
        return FrameworkDecision(
            framework_id=forced_id,
            name=meta["name"],
            method_file=meta["file"],
            reason="user-specified",
            source="user",
        )

    text = brief or ""
    d = text.lower()

    def hit(*needles: str) -> bool:
        return any(n.lower() in text.lower() or n.lower() in d for n in needles)

    # Order: narrow transforms → role → iterate → step → fast → content default
    if hit(
        "翻译",
        "译成",
        "摘要",
        "总结一下",
        "格式转换",
        "改写成",
        "润色成英文",
        "translate",
        "summarize",
        "summary",
        "rewrite into",
        "format as",
    ):
        return _auto("icio", "变换任务（翻译/摘要/改写/格式）")

    if hit("角色扮演", "人设", "模拟面试", "以…口吻", "以你的身份", "role-play", "roleplay", "persona", "as a "):
        return _auto("crispe", "需要人设/角色口吻")

    if hit("直到满意", "多轮迭代", "kpi", "okr", "关键结果", "evolve", "iterate until", "目标导向"):
        return _auto("broke", "目标/KPI 导向多轮任务")

    if hit("分步", "一步步", "逐步", "step by step", "step-by-step", "按步骤"):
        return _auto("rascef", "明确要求分步执行")

    if hit("尽快", "快速出一版", "先出一版", "速成", "quick draft", "asap"):
        return _auto("racef", "要求快速轻量出稿")

    if hit("教学", "演示提示词", "结构化提示课", "吴恩达", "spf"):
        return _auto("spf", "教学/结构化提示演示")

    if hit("新手", "先给个结构", "入门提示词", "golden formula", "黄金公式"):
        return _auto("star", "新手/快速结构化（STAR）")

    if hit(
        "文案",
        "文章",
        "脚本",
        "小红书",
        "种草",
        "公众号",
        "推文",
        "博客",
        "营销",
        "推广",
        "copy",
        "article",
        "script",
        "blog",
        "newsletter",
        "landing",
    ):
        return _auto("costar", "内容创作默认（CO-STAR）")

    # Soft STAR: short one-shot without channel cues
    if len(text.strip()) < 40 and not hit("写一篇", "长文"):
        return _auto("star", "短请求，先用 STAR 四段结构")

    return _auto("costar", "模糊内容请求，回退 CO-STAR")


def _auto(fid: str, reason: str) -> FrameworkDecision:
    meta = FRAMEWORKS[fid]
    return FrameworkDecision(
        framework_id=fid,
        name=meta["name"],
        method_file=meta["file"],
        reason=reason,
        source="auto",
    )


def parse_write_argv(tokens: list[str]) -> tuple[Optional[str], str]:
    """Parse tokens after /write: optional framework flag + brief."""
    if not tokens:
        return None, ""
    first = tokens[0].lower().replace("_", "-")
    if first == "prompt" and len(tokens) > 1:
        # /write prompt costar ...
        maybe = resolve_alias(tokens[1])
        if maybe:
            return maybe, " ".join(tokens[2:]).strip()
        return None, " ".join(tokens[1:]).strip()
    if first == "help":
        return None, "help"
    forced = resolve_alias(first)
    if forced:
        return forced, " ".join(tokens[1:]).strip()
    return None, " ".join(tokens).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Select AIGC writing framework")
    parser.add_argument("brief", nargs="*", help="User brief (tokens after /write)")
    parser.add_argument("--forced", "-f", default=None, help="Force framework id/alias")
    parser.add_argument("--json", action="store_true", help="Print JSON decision")
    args = parser.parse_args()
    forced, brief = parse_write_argv(args.brief)
    if args.forced:
        forced = args.forced
    decision = select_framework(brief, forced=forced)
    if args.json:
        print(json.dumps(asdict(decision), ensure_ascii=False, indent=2))
    else:
        print(f"{decision.name}\t{decision.framework_id}\t{decision.method_file}\t{decision.reason}\t{decision.source}")


if __name__ == "__main__":
    main()
