$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $repoRoot "data"
$pidPath = Join-Path $dataDir "ws_snapshot_recorder.pid"
$stdoutPath = Join-Path $dataDir "ws_snapshot_recorder.log"
$stderrPath = Join-Path $dataDir "ws_snapshot_recorder.err.log"

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if (Test-Path $pidPath) {
    $existingPid = Get-Content $pidPath -ErrorAction SilentlyContinue
    if ($existingPid) {
        $existing = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Output "ws snapshot recorder already running with PID $existingPid"
            exit 0
        }
    }
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
$arguments = @(
    "-m", "btc5m_bot.ws_snapshot_recorder",
    "--output", "data\ws_orderbook_snapshots.csv",
    "--summary-output", "data\ws_orderbook_window_summary.csv",
    "--max-windows", "0",
    "--min-write-interval-seconds", "1",
    "--continue-on-error"
)
$process = Start-Process `
    -FilePath "python" `
    -ArgumentList $arguments `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -WindowStyle Hidden `
    -PassThru

$process.Id | Set-Content $pidPath
Write-Output "ws snapshot recorder started with PID $($process.Id)"
