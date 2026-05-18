$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $repoRoot "data\ws_snapshot_recorder.pid"
$snapshotPath = Join-Path $repoRoot "data\ws_orderbook_snapshots.csv"

$pidValue = if (Test-Path $pidPath) { Get-Content $pidPath -ErrorAction SilentlyContinue } else { $null }
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }

$env:PYTHONPATH = Join-Path $repoRoot "src"
$status = python -m btc5m_bot.snapshot_status --snapshots $snapshotPath

[pscustomobject]@{
    running = [bool]$process
    pid = if ($process) { $process.Id } else { "" }
    data = $status
}
