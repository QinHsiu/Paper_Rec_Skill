#!/usr/bin/env bash
# Start Wiki API (:8787) + Web (:5173)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PAPER_REC_ROOT="${PAPER_REC_ROOT:-$ROOT}"
export PYTHONPATH="${ROOT}/packages/wiki-bridge:${ROOT}/apps/wiki-api${PYTHONPATH:+:$PYTHONPATH}"

cd "$ROOT/apps/wiki-api"
python -m uvicorn app:app --host 127.0.0.1 --port 8787 &
API_PID=$!
cd "$ROOT/apps/wiki-web"
npm run dev -- --host 127.0.0.1 --port 5173 &
WEB_PID=$!

echo "API http://127.0.0.1:8787  (pid $API_PID)"
echo "Web http://127.0.0.1:5173  (pid $WEB_PID)"
echo "Ctrl+C stops this shell only — kill pids if needed."
wait
