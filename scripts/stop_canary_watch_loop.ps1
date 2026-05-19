$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $repoRoot "data\canary_watch_loop.pid"

if (-not (Test-Path $pidPath)) {
    Write-Output "canary watch loop is not running"
    exit 0
}

$pidValue = Get-Content $pidPath -ErrorAction SilentlyContinue
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }
if ($process) {
    Stop-Process -Id $process.Id -Force
    Write-Output "canary watch loop stopped"
} else {
    Write-Output "canary watch loop pid file was stale"
}

Remove-Item -LiteralPath $pidPath -Force
