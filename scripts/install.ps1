# Paper_Rec one-shot install (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $Root "packages")) {
  # script in repo root
} else {
  $Root = Split-Path -Parent $Root  # scripts/install.ps1
}
Set-Location $Root

Write-Host "== Paper_Rec install =="
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw "Need Python 3.10+ on PATH" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Need Node 18+ (npm)" }

Write-Host "-- pip editable packages"
python -m pip install -e packages/wiki-bridge -e packages/thread-mcp
python -m pip install -r apps/wiki-api/requirements.txt
python -m pip install "mcp>=1.0"
try { python -m pip install pymupdf } catch { Write-Host "(optional) pymupdf skipped" }

Write-Host "-- wiki-web npm"
Push-Location apps/wiki-web
npm install
Pop-Location

Write-Host ""
Write-Host "Done. Next: .\scripts\start-wiki.ps1"
Write-Host "Set PAPER_REC_ROOT=$Root for MCP."
