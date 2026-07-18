"""One-shot MCP client config writer for Paper_Rec Thread Memory MCP.

Default is dry-run / project-local example. Use --apply to write client configs.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


SERVER_KEY = "paper-rec-threads"


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    # packages/thread-mcp/thread_mcp -> Paper_Rec_Skill
    env = os.environ.get("PAPER_REC_ROOT")
    if env:
        return Path(env).resolve()
    return here.parents[2].resolve()


def mcp_server_block(repo: Path, *, python_exe: str | None = None) -> dict[str, Any]:
    py = python_exe or sys.executable
    return {
        "command": py,
        "args": ["-m", "thread_mcp.server"],
        "env": {"PAPER_REC_ROOT": str(repo).replace("\\", "/")},
    }


def cursor_user_mcp_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / ".cursor" / "mcp.json"
    if system == "Windows":
        return home / ".cursor" / "mcp.json"
    return home / ".cursor" / "mcp.json"


def cursor_project_mcp_path(repo: Path) -> Path:
    return repo / ".cursor" / "mcp.json"


def claude_desktop_path() -> Path | None:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    # Linux: unofficial / Continue-style paths vary; document only
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def continue_config_hint() -> str:
    return (
        "VS Code Continue: merge into ~/.continue/config.json under mcpServers "
        f"(same block as {SERVER_KEY}). See docs/MCP.md."
    )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def merge_mcp_servers(existing: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    out = dict(existing)
    servers = dict(out.get("mcpServers") or {})
    servers[SERVER_KEY] = block
    out["mcpServers"] = servers
    return out


def write_json_backup(path: Path, data: dict[str, Any], *, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if not force:
            raise FileExistsError(f"{path} exists; pass --force to overwrite after backup")
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def discover_targets(repo: Path) -> list[dict[str, Any]]:
    targets = [
        {
            "id": "project-example",
            "label": "Project example (safe default)",
            "path": repo / "docs" / "mcp.example.json",
            "kind": "example",
        },
        {
            "id": "cursor-project",
            "label": "Cursor project .cursor/mcp.json",
            "path": cursor_project_mcp_path(repo),
            "kind": "cursor",
        },
        {
            "id": "cursor-user",
            "label": "Cursor user ~/.cursor/mcp.json",
            "path": cursor_user_mcp_path(),
            "kind": "cursor",
        },
    ]
    cd = claude_desktop_path()
    if cd:
        targets.append(
            {
                "id": "claude-desktop",
                "label": "Claude Desktop config",
                "path": cd,
                "kind": "claude",
            }
        )
    return targets


def plan_writes(
    repo: Path,
    *,
    targets: list[str] | None = None,
    python_exe: str | None = None,
) -> list[dict[str, Any]]:
    block = mcp_server_block(repo, python_exe=python_exe)
    wanted = set(targets) if targets else {"project-example", "cursor-project"}
    plans = []
    for t in discover_targets(repo):
        if t["id"] not in wanted and "all" not in wanted:
            continue
        existing = _load_json(t["path"])
        merged = merge_mcp_servers(existing, block)
        plans.append(
            {
                **t,
                "exists": t["path"].is_file(),
                "block": block,
                "merged": merged,
                "would_change": existing.get("mcpServers", {}).get(SERVER_KEY) != block
                or SERVER_KEY not in (existing.get("mcpServers") or {}),
            }
        )
    return plans


def format_diff(plan: dict[str, Any]) -> str:
    path = plan["path"]
    status = "UPDATE" if plan["exists"] else "CREATE"
    change = "changed" if plan["would_change"] else "unchanged"
    return f"[{status}/{change}] {plan['label']}\n  → {path}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="paper-rec-configure",
        description="Configure Paper_Rec Thread Memory MCP for Cursor / Claude Desktop",
    )
    p.add_argument(
        "--root",
        default="",
        help="PAPER_REC_ROOT (default: env or auto-detect repo)",
    )
    p.add_argument(
        "--python",
        default="",
        help="Python executable for MCP command (default: current interpreter)",
    )
    p.add_argument(
        "--target",
        action="append",
        default=[],
        help=(
            "Target id (repeatable): project-example, cursor-project, cursor-user, "
            "claude-desktop, all. Default: project-example + cursor-project"
        ),
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Write files (default is dry-run print only)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Backup .bak and overwrite existing mcp.json entries",
    )
    p.add_argument("--list-targets", action="store_true", help="List detectable targets")
    args = p.parse_args(argv)

    repo = Path(args.root).resolve() if args.root else _repo_root()
    os.environ.setdefault("PAPER_REC_ROOT", str(repo))

    if args.list_targets:
        for t in discover_targets(repo):
            mark = "✓" if t["path"].is_file() else "·"
            print(f"{mark} {t['id']:18} {t['path']}")
        print(continue_config_hint())
        return 0

    targets = args.target or None
    if targets and "all" in targets:
        targets = ["all"]
    plans = plan_writes(repo, targets=targets, python_exe=args.python or None)

    print(f"PAPER_REC_ROOT={repo}")
    print(f"Mode={'APPLY' if args.apply else 'DRY-RUN'}")
    print()
    for plan in plans:
        print(format_diff(plan))
        print(json.dumps({SERVER_KEY: plan["block"]}, ensure_ascii=False, indent=2))
        print()

    if not args.apply:
        print("Dry-run only. Re-run with --apply [--force] to write.")
        print(continue_config_hint())
        return 0

    for plan in plans:
        path: Path = plan["path"]
        try:
            if plan["kind"] == "example" or not path.is_file():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(plan["merged"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            else:
                write_json_backup(path, plan["merged"], force=args.force or True)
            print(f"Wrote {path}")
        except FileExistsError as e:
            print(f"Skip: {e}", file=sys.stderr)
            return 1
    print(continue_config_hint())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
