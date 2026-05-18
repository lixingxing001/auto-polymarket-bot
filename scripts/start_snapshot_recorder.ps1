$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $repoRoot "data"
$pidPath = Join-Path $dataDir "snapshot_recorder.pid"
$stdoutPath = Join-Path $dataDir "snapshot_recorder.log"
$stderrPath = Join-Path $dataDir "snapshot_recorder.err.log"

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if (Test-Path $pidPath) {
    $existingPid = Get-Content $pidPath -ErrorAction SilentlyContinue
    if ($existingPid) {
        $existing = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Output "snapshot recorder already running with PID $existingPid"
            exit 0
        }
    }
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
$arguments = @(
    "-m", "btc5m_bot.snapshot_recorder",
    "--iterations", "0",
    "--interval-seconds", "5",
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
Write-Output "snapshot recorder started with PID $($process.Id)"
