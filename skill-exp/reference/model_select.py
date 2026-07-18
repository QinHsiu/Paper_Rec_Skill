"""
Model selection helpers for /exp_* solution plans.

Roles: clean_closed / clean_open / train_base / distill_teacher / distill_student.
Family drill-down (e.g. Qwen) → comparison table markdown (scores filled by agent).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


ROLES = (
    "clean_closed",
    "clean_open",
    "train_base",
    "distill_teacher",
    "distill_student",
    "embed_rerank",
)

# role → board ids (see model_leaderboards.md)
ROLE_BOARDS: dict[str, list[str]] = {
    "clean_closed": ["lmarena", "artificial_analysis", "superclue", "llmrank"],
    "clean_open": ["hf_open_llm", "opencompass", "livebench", "superclue"],
    "train_base": ["hf_open_llm", "opencompass", "livebench", "task_specialty"],
    "distill_teacher": ["artificial_analysis", "lmarena", "superclue", "hf_open_llm"],
    "distill_student": ["hf_open_llm", "opencompass", "task_specialty"],
    "embed_rerank": ["mteb", "hf_models"],
}

BOARD_URLS: dict[str, str] = {
    "artificial_analysis": "https://artificialanalysis.ai/",
    "lmarena": "https://lmarena.ai/",
    "livebench": "https://livebench.ai/",
    "benchlm": "https://benchlm.ai/",
    "hf_open_llm": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    "hf_models": "https://huggingface.co/models",
    "superclue": "https://www.superclueai.com/",
    "llmrank": "https://llmrank.top/",
    "opencompass": "https://opencompass.org.cn/",
    "mteb": "https://huggingface.co/spaces/mteb/leaderboard",
    "task_specialty": "(code→Aider/SuperCLUE-SWE; math→MathArena; agent→OpenCompass; vlm→SuperCLUE-VLM)",
}


@dataclass
class ModelCandidate:
    name: str
    open_closed: str  # open | closed
    size: str = ""
    scores: str = ""  # free text: "OpenLLM 65.2; SuperCLUE …" or "unavailable"
    cost_vram: str = ""
    decision: str = ""  # primary | backup | reject
    source_urls: list[str] = field(default_factory=list)


@dataclass
class ModelSelectSpec:
    role: str
    task_hint: str
    family: Optional[str] = None  # e.g. "Qwen"
    boards: list[str] = field(default_factory=list)
    candidates: list[ModelCandidate] = field(default_factory=list)
    retrieved: str = ""

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"unknown role {self.role}; expected one of {ROLES}")
        if not self.boards:
            self.boards = list(ROLE_BOARDS.get(self.role, ["hf_open_llm"]))
        if not self.retrieved:
            self.retrieved = date.today().isoformat()


def boards_for_role(role: str) -> list[tuple[str, str]]:
    ids = ROLE_BOARDS.get(role, ["hf_open_llm"])
    return [(bid, BOARD_URLS.get(bid, "")) for bid in ids]


def needs_model_select(plan_text: str) -> bool:
    t = (plan_text or "").lower()
    keys = (
        "模型",
        "基座",
        "backbone",
        "base model",
        "蒸馏",
        "distill",
        "清洗",
        "label_clean",
        "label_noise",
        "relabel",
        "use_other_model",
        "consensus",
        "teacher",
        "student",
        "train_base",
        "finetune",
        "sft",
        "qwen",
        "llama",
        "gpt-",
        "claude",
        "选型",
    )
    return any(k in t for k in keys)


def infer_roles_from_actions(actions: list[str]) -> list[str]:
    roles: list[str] = []
    blob = " ".join(actions).lower()
    if any(
        k in blob
        for k in (
            "label_clean",
            "label_noise",
            "relabel",
            "use_other_model",
            "清洗",
            "consensus",
            "teacher",
        )
    ):
        roles.append("clean_closed")
        roles.append("clean_open")
    if any(k in blob for k in ("train", "finetune", "sft", "基座", "backbone", "pretrain", "train_recipe")):
        roles.append("train_base")
    if "distill" in blob or "蒸馏" in blob:
        roles.extend(["distill_teacher", "distill_student"])
    # dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for r in roles:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out or ["train_base"]


def render_model_select_md(spec: ModelSelectSpec) -> str:
    """Markdown block for plans/P*.md — agent fills candidate scores from live boards."""
    board_lines = []
    for bid in spec.boards:
        url = BOARD_URLS.get(bid, "")
        board_lines.append(f"- `{bid}`: {url}" if url else f"- `{bid}`")

    rows = [
        "| candidate | open/closed | size | key scores | VRAM/cost | decision |",
        "|-----------|-------------|------|------------|-----------|----------|",
    ]
    if spec.candidates:
        for c in spec.candidates:
            rows.append(
                f"| {c.name} | {c.open_closed} | {c.size} | {c.scores or 'TBD'} | "
                f"{c.cost_vram or 'TBD'} | {c.decision or 'TBD'} |"
            )
    else:
        rows.append("| _(agent: fill ≥3 candidates after board lookup)_ | | | | | |")

    family = spec.family or "(none yet)"
    primary = next((c.name for c in spec.candidates if c.decision == "primary"), "TBD")
    backup = next((c.name for c in spec.candidates if c.decision == "backup"), "TBD")

    return "\n".join(
        [
            "## Model selection",
            f"- role: `{spec.role}`",
            f"- task_hint: {spec.task_hint}",
            f"- family drill-down: {family}",
            f"- boards consulted (retrieved: {spec.retrieved}):",
            *board_lines,
            "",
            *rows,
            "",
            f"- primary: {primary}",
            f"- backup: {backup}",
            "- notes: do not invent scores; cite board + date; prefer official HF org checkpoints",
            "",
        ]
    )


def family_search_hints(family: str) -> list[str]:
    f = family.strip()
    return [
        f"HF models search: https://huggingface.co/models?search={f}",
        f"Open LLM Leaderboard filter / search: {f}",
        f"OpenCompass / SuperCLUE rows containing {f}",
        f"Official org cards (e.g. Qwen → https://huggingface.co/Qwen)",
        "Compare ≥3 open instruct variants; include size vs GPU from tool/function.notes",
    ]
