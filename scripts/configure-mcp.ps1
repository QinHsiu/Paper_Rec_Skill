# Configure Paper_Rec Thread Memory MCP (dry-run by default).
# Usage:
#   .\scripts\configure-mcp.ps1
#   .\scripts\configure-mcp.ps1 -Apply -Force
#   .\scripts\configure-mcp.ps1 -Target all -Apply
param(
  [switch]$Apply,
  [switch]$Force,
  [string[]]$Target = @(),
  [string]$Root = ""
)
$ErrorActionPreference = "Stop"
$repo = if ($Root) { Resolve-Path $Root } else { Resolve-Path (Join-Path $PSScriptRoot "..") }
$env:PAPER_REC_ROOT = "$repo"
Push-Location (Join-Path $repo "packages\thread-mcp")
try {
  $args = @("-m", "thread_mcp.configure", "--root", "$repo")
  if ($Apply) { $args += "--apply" }
  if ($Force) { $args += "--force" }
  foreach ($t in $Target) { $args += @("--target", $t) }
  python @args
} finally {
  Pop-Location
}
