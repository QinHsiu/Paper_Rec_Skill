# Start Wiki API (:8787) + Web (:5173) on Windows
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Root "packages"))) {
  $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
  if (-not (Test-Path (Join-Path $Root "packages"))) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  }
}
$env:PAPER_REC_ROOT = if ($env:PAPER_REC_ROOT) { $env:PAPER_REC_ROOT } else { $Root }
$env:PYTHONPATH = "$Root\packages\wiki-bridge;$Root\apps\wiki-api"

Write-Host "PAPER_REC_ROOT=$env:PAPER_REC_ROOT"
Write-Host "Starting API :8787 ..."
Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app:app","--host","127.0.0.1","--port","8787" -WorkingDirectory "$Root\apps\wiki-api" -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "Starting Web :5173 ..."
Start-Process -FilePath "npm" -ArgumentList "run","dev","--","--host","127.0.0.1","--port","5173" -WorkingDirectory "$Root\apps\wiki-web" -WindowStyle Normal
Write-Host "Open http://127.0.0.1:5173/"
