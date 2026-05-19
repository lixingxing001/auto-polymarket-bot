param(
    [string]$Workspace = "F:\AI\Project\auto-polymarket-bot"
)

$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $Workspace
$env:PYTHONPATH = "src"

$logDir = Join-Path $Workspace "data"
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$runLog = Join-Path $logDir "scheduled_canary_watchdog.log"
$errLog = Join-Path $logDir "scheduled_canary_watchdog.err.log"
$stamp = (Get-Date).ToUniversalTime().ToString("o")
Add-Content -LiteralPath $runLog -Value "[$stamp] scheduled watchdog start"

function Invoke-Step {
    param(
        [string]$Name,
        [string[]]$ArgsList
    )
    $stepStamp = (Get-Date).ToUniversalTime().ToString("o")
    Add-Content -LiteralPath $runLog -Value "[$stepStamp] step=$Name start"
    $output = & python @ArgsList 2>&1
    $exitCode = $LASTEXITCODE
    $outputItems = @($output)
    if ($outputItems.Count -gt 0) {
        $firstLine = $outputItems[0].ToString()
        if ($firstLine.Length -gt 240) {
            $firstLine = $firstLine.Substring(0, 240) + "..."
        }
        Add-Content -LiteralPath $runLog -Encoding utf8 -Value "[$Name] output_lines=$($outputItems.Count) first=$firstLine"
    }
    if ($exitCode -ne 0 -and $outputItems.Count -gt 0) {
        $outputItems | ForEach-Object { "[$Name] $($_.ToString())" } | Add-Content -LiteralPath $errLog -Encoding utf8
    }
    $doneStamp = (Get-Date).ToUniversalTime().ToString("o")
    Add-Content -LiteralPath $runLog -Value "[$doneStamp] step=$Name exit=$exitCode"
    return $exitCode
}

Invoke-Step -Name "canary_monitor" -ArgsList @("-m", "btc5m_bot.canary_monitor_cli", "--monitor-output", "canary_monitor_report.md", "--readiness-output", "canary_readiness_report.md") | Out-Null
Invoke-Step -Name "strategy_guardrail" -ArgsList @("-m", "btc5m_bot.strategy_guardrail_cli") | Out-Null
Invoke-Step -Name "candidate_evidence" -ArgsList @("-m", "btc5m_bot.candidate_evidence_cli") | Out-Null
Invoke-Step -Name "candidate_change_review" -ArgsList @("-m", "btc5m_bot.candidate_change_review_cli") | Out-Null
Invoke-Step -Name "candidate_evidence_progress" -ArgsList @("-m", "btc5m_bot.candidate_evidence_progress_cli", "--output", "candidate_evidence_progress_report.md") | Out-Null
Invoke-Step -Name "canary_watch_once" -ArgsList @("-m", "btc5m_bot.canary_watch_loop", "--iterations", "1", "--continue-on-error") | Out-Null
Invoke-Step -Name "canary_dashboard" -ArgsList @("-m", "btc5m_bot.canary_dashboard_cli", "--output", "canary_dashboard.html") | Out-Null

$finish = (Get-Date).ToUniversalTime().ToString("o")
Add-Content -LiteralPath $runLog -Value "[$finish] scheduled watchdog finish"
