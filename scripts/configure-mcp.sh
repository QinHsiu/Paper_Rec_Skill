#!/usr/bin/env bash
# Configure Paper_Rec Thread Memory MCP (dry-run by default).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PAPER_REC_ROOT="${PAPER_REC_ROOT:-$ROOT}"
cd "$ROOT/packages/thread-mcp"
if [[ "${1:-}" == "--apply" ]]; then
  shift
  python -m thread_mcp.configure --root "$PAPER_REC_ROOT" --apply "$@"
else
  python -m thread_mcp.configure --root "$PAPER_REC_ROOT" "$@"
fi
