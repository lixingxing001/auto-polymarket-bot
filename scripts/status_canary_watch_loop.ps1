$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $repoRoot "data\canary_watch_loop.pid"
$reportPath = Join-Path $repoRoot "canary_watch_report.md"
$stdoutPath = Join-Path $repoRoot "data\canary_watch_loop.log"
$stderrPath = Join-Path $repoRoot "data\canary_watch_loop.err.log"

$pidValue = if (Test-Path $pidPath) { Get-Content $pidPath -ErrorAction SilentlyContinue } else { $null }
$process = if ($pidValue) { Get-Process -Id $pidValue -ErrorAction SilentlyContinue } else { $null }
$report = if (Test-Path $reportPath) { Get-Item $reportPath } else { $null }
$stdout = if (Test-Path $stdoutPath) { Get-Item $stdoutPath } else { $null }
$stderr = if (Test-Path $stderrPath) { Get-Item $stderrPath } else { $null }

[pscustomobject]@{
    running = [bool]$process
    pid = if ($process) { $process.Id } else { "" }
    report_last_write = if ($report) { $report.LastWriteTime } else { "" }
    stdout_last_write = if ($stdout) { $stdout.LastWriteTime } else { "" }
    stderr_last_write = if ($stderr) { $stderr.LastWriteTime } else { "" }
}
