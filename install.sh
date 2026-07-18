#!/usr/bin/env bash
# Paper_Rec one-shot install (Unix / Git Bash / WSL)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== Paper_Rec install =="
command -v python3 >/dev/null || command -v python >/dev/null || { echo "Need Python 3.10+"; exit 1; }
command -v npm >/dev/null || { echo "Need Node 18+ (npm)"; exit 1; }
PY="$(command -v python3 || command -v python)"

echo "-- pip editable packages"
"$PY" -m pip install -e packages/wiki-bridge -e packages/thread-mcp
"$PY" -m pip install -r apps/wiki-api/requirements.txt
"$PY" -m pip install "mcp>=1.0" || true
"$PY" -m pip install pymupdf || echo "(optional) pymupdf not installed — PDF ingest needs it"

echo "-- wiki-web npm"
(cd apps/wiki-web && npm install)

echo
echo "Done. Next:"
echo "  ./scripts/start-wiki.sh"
echo "  or: see README / CONTRIBUTING"
echo "Set PAPER_REC_ROOT=$ROOT for MCP."
