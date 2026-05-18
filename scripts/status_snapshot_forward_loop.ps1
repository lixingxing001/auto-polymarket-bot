$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $repoRoot "data\snapshot_forward_loop.pid"
$evaluationPath = Join-Path $repoRoot "data\forward_snapshot_evaluations.csv"
$archivePath = Join-Path $repoRoot "data\settled_snapshot_windows.csv"
$candidateDir = Join-Path $repoRoot "data\candidate_comparisons"

$pidValue = if (Test-Path $pidPath) { Get-Content $pidPath -ErrorAction SilentlyContinue } else { $null }
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }

$archiveRows = if (Test-Path $archivePath) { (Import-Csv $archivePath).Count } else { 0 }
$evaluationRows = if (Test-Path $evaluationPath) { (Import-Csv $evaluationPath).Count } else { 0 }
$candidateFiles = if (Test-Path $candidateDir) { Get-ChildItem $candidateDir -Filter *.csv } else { @() }
$env:PYTHONPATH = Join-Path $repoRoot "src"
$guardrail = python -m btc5m_bot.strategy_guardrail_cli

[pscustomobject]@{
    running = [bool]$process
    pid = if ($process) { $process.Id } else { "" }
    archived_windows = $archiveRows
    evaluations = $evaluationRows
    candidate_files = $candidateFiles.Count
    guardrail = $guardrail
}
