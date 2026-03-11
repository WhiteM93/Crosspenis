# Запуск, остановка и статус TgBot + Ollama
# Использование: .\run_bot.ps1 start | stop | status | restart

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "restart")]
    [string]$Command = "status"
)

$ScriptDir = $PSScriptRoot
$BotScript = Join-Path $ScriptDir "bot.py"
$PythonExe = if (Test-Path (Join-Path $ScriptDir "venv\Scripts\python.exe")) { Join-Path $ScriptDir "venv\Scripts\python.exe" } else { "python" }
$OllamaBase = "http://localhost:11434"
$ModelName = "gemma2:9b"

function Get-BotProcesses {
    Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*bot.py*" }
}

function Get-OllamaStatus {
    try {
        $r = Invoke-RestMethod -Uri "$OllamaBase/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
        $models = $r.models | ForEach-Object { $_.name }
        $hasModel = $models | Where-Object { $_ -like "${ModelName}*" -or $_ -eq $ModelName }
        if ($hasModel) {
            return @{ ok = $true; models = $models; modelFound = $true }
        }
        return @{ ok = $true; models = $models; modelFound = $false }
    } catch {
        return @{ ok = $false; error = $_.Exception.Message }
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "=== TgBot status ===" -ForegroundColor Cyan

    $procs = Get-BotProcesses
    if ($procs) {
        Write-Host "Bot:        " -NoNewline
        Write-Host "running" -ForegroundColor Green -NoNewline
        Write-Host " (PID: $($procs.ProcessId -join ', '))"
    } else {
        Write-Host "Bot:        " -NoNewline
        Write-Host "not running" -ForegroundColor Red
    }

    $ollama = Get-OllamaStatus
    if ($ollama.ok) {
        Write-Host "Ollama:     " -NoNewline
        Write-Host "running" -ForegroundColor Green
        if ($ollama.modelFound) {
            Write-Host "Model:      " -NoNewline
            Write-Host "$ModelName OK" -ForegroundColor Green
        } else {
            Write-Host "Model:      " -NoNewline
            Write-Host "$ModelName not found (ollama pull $ModelName)" -ForegroundColor Yellow
            if ($ollama.models) {
                Write-Host "Available:  $($ollama.models -join ', ')"
            }
        }
    } else {
        Write-Host "Ollama:     " -NoNewline
        Write-Host "not available" -ForegroundColor Red
        Write-Host "  (start Ollama or check localhost:11434)"
    }

    Write-Host ""
}

function Stop-Bot {
    $procs = Get-BotProcesses
    if (-not $procs) {
        Write-Host "Bot is not running." -ForegroundColor Yellow
        return
    }
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped bot (PID $($p.ProcessId))."
    }
}

function Start-Bot {
    if (-not (Test-Path $BotScript)) {
        Write-Host "Not found: $BotScript" -ForegroundColor Red
        exit 1
    }
    $procs = Get-BotProcesses
    if ($procs) {
        Write-Host "Bot already running (PID: $($procs.ProcessId -join ', ')). Use stop then start, or restart." -ForegroundColor Yellow
        return
    }
    Set-Location $ScriptDir
    Start-Process $PythonExe -ArgumentList "bot.py" -WorkingDirectory $ScriptDir -WindowStyle Normal
    Write-Host "Bot started in new window."
}

switch ($Command) {
    "status"  { Show-Status }
    "stop"    { Stop-Bot; Show-Status }
    "start"   { Start-Bot; Start-Sleep -Seconds 2; Show-Status }
    "restart" { Stop-Bot; Start-Sleep -Seconds 1; Start-Bot; Start-Sleep -Seconds 2; Show-Status }
}
