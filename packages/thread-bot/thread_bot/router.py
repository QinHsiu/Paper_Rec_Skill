"""Unified Thread conversation bot — channel adapters call the same command router."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Ensure wiki_bridge importable when run as package
_PKG = Path(__file__).resolve().parents[2] / "wiki-bridge"
if _PKG.is_dir() and str(_PKG) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_PKG))

from wiki_bridge import thread_store as ts  # noqa: E402
from wiki_bridge.thread_delta import run_delta  # noqa: E402
from wiki_bridge.thread_templates import (  # noqa: E402
    ensure_builtin_templates,
    import_template,
    list_templates,
)


@dataclass
class BotContext:
    root: Path
    channel: str
    user_id: str = ""
    chat_id: str = ""
    active_thread: str = ""


HELP = """Paper_Rec Thread Bot
命令：
  /help
  /threads              列出研究主线
  /thread <id>          查看主线摘要
  /use <id>             设置当前主线
  /delta [mode]         运行 Watch/Delta（默认 auto）
  /templates            模板市场列表
  /import <template_id> [new_id]  从模板创建主线
  /feedback <accept|skip|pin> <path>
  /query <问题>         返回检索提示（需配合 Skill/检索 MCP）
"""


def _root() -> Path:
    return Path(os.environ.get("PAPER_REC_ROOT") or ".").resolve()


def parse_command(text: str) -> tuple[str, list[str]]:
    text = (text or "").strip()
    if not text:
        return "", []
    # Feishu sometimes wraps @bot
    text = re.sub(r"^@_user_\d+\s+", "", text)
    if not text.startswith("/"):
        # natural language shortcuts
        low = text.lower()
        if low in ("帮助", "help", "菜单"):
            return "help", []
        if low.startswith("主线") or low.startswith("threads"):
            return "threads", []
        return "chat", [text]
    parts = text.split()
    cmd = parts[0][1:].lower()
    return cmd, parts[1:]


def handle_message(ctx: BotContext, text: str) -> str:
    """Return plain-text reply for any channel."""
    cmd, args = parse_command(text)
    root = ctx.root

    if cmd in ("help", "start", ""):
        active = ctx.active_thread or "(未设置，用 /use <id>)"
        return HELP + f"\n当前主线: {active}\n渠道: {ctx.channel}"

    if cmd == "threads":
        rows = ts.list_threads(root)
        if not rows:
            return "暂无主线。可用 /import multimodal-alignment 从模板创建。"
        lines = ["研究主线："]
        for t in rows[:30]:
            lines.append(
                f"- `{t.get('thread_id')}` · {t.get('title') or ''} · {t.get('status')} · "
                f"papers={t.get('paper_count', 0)}"
            )
        return "\n".join(lines)

    if cmd == "thread":
        if not args:
            return "用法: /thread <id>"
        tid = args[0]
        try:
            data = ts.load_thread(root, tid)
        except FileNotFoundError:
            return f"未找到主线 `{tid}`"
        claims = data.get("claims") or []
        gaps = data.get("evidence_gaps") or []
        return (
            f"**{data.get('title')}** (`{tid}`)\n"
            f"假设: {data.get('hypothesis') or '—'}\n"
            f"claims={len(claims)} gaps={len(gaps)} papers={len(data.get('paper_paths') or [])}\n"
            f"seeds: {', '.join((data.get('seed_terms') or [])[:8])}"
        )

    if cmd == "use":
        if not args:
            return "用法: /use <thread_id>"
        tid = args[0]
        try:
            ts.load_thread(root, tid)
        except FileNotFoundError:
            return f"未找到主线 `{tid}`"
        ctx.active_thread = tid
        _save_session(ctx)
        return f"已切换当前主线 → `{tid}`"

    if cmd == "delta":
        tid = ctx.active_thread or (args[0] if args and args[0] not in ("auto", "gap_focus", "diff_brief", "new_digest", "exp_bridge") else "")
        mode = "auto"
        for a in args:
            if a in ("auto", "gap_focus", "diff_brief", "new_digest", "exp_bridge"):
                mode = a
            elif not tid:
                tid = a
        if not tid:
            return "请先 /use <id> 或 /delta <id> [mode]"
        try:
            result = run_delta(root, tid, mode=mode, persist=True)
        except FileNotFoundError:
            return f"未找到主线 `{tid}`"
        except Exception as e:
            return f"Delta 失败: {e}"
        cands = result.get("candidates") or []
        lines = [f"Delta `{tid}` mode={mode} · 候选 {len(cands)}"]
        for c in cands[:8]:
            lines.append(f"- R={c.get('R')} · {c.get('title') or c.get('path')}")
        if result.get("delta_path"):
            lines.append(f"文件: `{result.get('delta_path')}`")
        return "\n".join(lines)

    if cmd == "templates":
        ensure_builtin_templates(root)
        items = list_templates(root)
        if not items:
            return "模板市场为空。"
        lines = ["主线模板市场："]
        for t in items:
            lines.append(
                f"- `{t.get('template_id')}` · {t.get('title')} · claims={t.get('claims_n', '?')} "
                f"{'(builtin)' if t.get('builtin') else ''}"
            )
        lines.append("导入: /import <template_id> [new_thread_id]")
        return "\n".join(lines)

    if cmd == "import":
        if not args:
            return "用法: /import <template_id> [new_thread_id]"
        ensure_builtin_templates(root)
        tpl = args[0]
        new_id = args[1] if len(args) > 1 else ""
        try:
            out = import_template(root, tpl, new_thread_id=new_id)
        except FileNotFoundError:
            return f"模板不存在: `{tpl}`。先 /templates"
        except FileExistsError:
            return f"主线已存在，换一个 new_id 再试。"
        except Exception as e:
            return f"导入失败: {e}"
        ctx.active_thread = out["thread_id"]
        _save_session(ctx)
        return f"已从模板 `{tpl}` 创建主线 `{out['thread_id']}`，并设为当前主线。"

    if cmd == "feedback":
        if len(args) < 2:
            return "用法: /feedback <accept|skip|pin|read> <paper_path>"
        action, path = args[0], args[1]
        tid = ctx.active_thread
        if not tid:
            return "请先 /use <thread_id>"
        try:
            out = ts.record_feedback(root, tid, action=action, path=path, by=f"bot:{ctx.channel}")
        except Exception as e:
            return f"反馈失败: {e}"
        return f"已记录 {action} → `{path}`（seeds={len(out.get('seed_terms') or [])}）"

    if cmd == "query":
        q = " ".join(args).strip()
        if not q:
            return "用法: /query <研究问题>"
        tid = ctx.active_thread
        hints = []
        if tid:
            try:
                data = ts.load_thread(root, tid)
                hints = list(data.get("seed_queries") or [])[:3]
            except FileNotFoundError:
                pass
        return (
            f"检索提示（请在 Cursor/Skill 执行 `/query_*` 或外接 scholar-mcp）：\n"
            f"问题: {q}\n"
            f"主线: {tid or '—'}\n"
            f"建议 queries: {hints or [q]}"
        )

    if cmd == "chat":
        # free text → treat as query hint when thread active
        return handle_message(ctx, "/query " + " ".join(args))

    return f"未知命令 `/{cmd}`。发送 /help"


def session_path(ctx: BotContext) -> Path:
    d = ctx.root / "content" / "_bot_sessions"
    d.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{ctx.channel}_{ctx.chat_id or ctx.user_id}")[:80]
    return d / f"{key}.json"


def _save_session(ctx: BotContext) -> None:
    session_path(ctx).write_text(
        json.dumps(
            {
                "channel": ctx.channel,
                "user_id": ctx.user_id,
                "chat_id": ctx.chat_id,
                "active_thread": ctx.active_thread,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_session(ctx: BotContext) -> BotContext:
    p = session_path(ctx)
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            ctx.active_thread = str(data.get("active_thread") or "")
        except json.JSONDecodeError:
            pass
    return ctx


def make_context(channel: str, *, user_id: str = "", chat_id: str = "", root: Path | None = None) -> BotContext:
    ctx = BotContext(root=root or _root(), channel=channel, user_id=user_id, chat_id=chat_id)
    return load_session(ctx)
