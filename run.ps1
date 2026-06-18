# Crosspenis — start | stop | status | restart

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "restart")]
    [string]$Command = "status"
)

$ScriptDir = $PSScriptRoot
$AppScript = Join-Path $ScriptDir "app.py"
$PythonExe = if (Test-Path (Join-Path $ScriptDir "venv\Scripts\python.exe")) { Join-Path $ScriptDir "venv\Scripts\python.exe" } else { "python" }

function Get-AppProcesses {
    Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*app.py*" }
}

function Show-Status {
    Write-Host ""
    Write-Host "=== Crosspenis ===" -ForegroundColor Cyan

    $procs = Get-AppProcesses
    if ($procs) {
        Write-Host "Status: " -NoNewline
        Write-Host "running" -ForegroundColor Green -NoNewline
        Write-Host " (PID: $($procs.ProcessId -join ', '))"
    } else {
        Write-Host "Status: " -NoNewline
        Write-Host "stopped" -ForegroundColor Red
    }

    Write-Host ""
}

function Stop-App {
    $procs = Get-AppProcesses
    if (-not $procs) {
        Write-Host "Already stopped." -ForegroundColor Yellow
        return
    }
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped (PID $($p.ProcessId))."
    }
}

function Start-App {
    if (-not (Test-Path $AppScript)) {
        Write-Host "Not found: $AppScript" -ForegroundColor Red
        exit 1
    }
    $procs = Get-AppProcesses
    if ($procs) {
        Write-Host "Already running (PID: $($procs.ProcessId -join ', ')). Use stop or restart." -ForegroundColor Yellow
        return
    }
    Set-Location $ScriptDir
    Start-Process $PythonExe -ArgumentList "app.py" -WorkingDirectory $ScriptDir -WindowStyle Normal
    Write-Host "Started."
}

switch ($Command) {
    "status"  { Show-Status }
    "stop"    { Stop-App; Show-Status }
    "start"   { Start-App; Start-Sleep -Seconds 2; Show-Status }
    "restart" { Stop-App; Start-Sleep -Seconds 1; Start-App; Start-Sleep -Seconds 2; Show-Status }
}
