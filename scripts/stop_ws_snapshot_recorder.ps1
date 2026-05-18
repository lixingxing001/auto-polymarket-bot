$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $repoRoot "data\ws_snapshot_recorder.pid"

if (-not (Test-Path $pidPath)) {
    Write-Output "ws snapshot recorder is not running"
    exit 0
}

$pidValue = Get-Content $pidPath -ErrorAction SilentlyContinue
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }
if ($process) {
    Stop-Process -Id $process.Id -Force
    Write-Output "ws snapshot recorder stopped"
} else {
    Write-Output "ws snapshot recorder pid file was stale"
}

Remove-Item -LiteralPath $pidPath -Force
