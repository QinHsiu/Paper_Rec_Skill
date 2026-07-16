# Start Paper_Rec Wiki (API :8787 + Web :5173)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Api = Join-Path $Root "apps\wiki-api"
$Web = Join-Path $Root "apps\wiki-web"

Write-Host "Starting wiki-api on http://127.0.0.1:8787 ..."
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd `"$Api`"; python -m uvicorn app:app --reload --host 127.0.0.1 --port 8787"
)

Start-Sleep -Seconds 1
Write-Host "Starting wiki-web on http://127.0.0.1:5173 ..."
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd `"$Web`"; npm run dev -- --host 127.0.0.1 --port 5173"
)

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5173/"
Write-Host "Opened http://127.0.0.1:5173/"
