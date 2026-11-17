param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$SkipInstall,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$logDir = Join-Path $root ".local\logs"
$backendUrl = "http://127.0.0.1:$BackendPort"
$frontendUrl = "http://127.0.0.1:$FrontendPort"
$requiredApiCapabilities = @("model_status_error", "report_pdf_export")

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Test-ApiCapabilities {
    param([string]$Url)
    try {
        $payload = Invoke-RestMethod -Uri $Url -TimeoutSec 2
        if ($payload.status -ne "ok") {
            return $false
        }
        foreach ($capability in $requiredApiCapabilities) {
            if ($payload.capabilities -notcontains $capability) {
                Write-Host "WARN API 缺少能力标记：$capability。请重启后端以加载最新代码。" -ForegroundColor Yellow
                return $false
            }
        }
        return $true
    }
    catch {
        return $false
    }
}

function Wait-HttpOk {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Seconds = 45
    )

    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $ready = if ($Name -eq "API") { Test-ApiCapabilities $Url } else { Test-HttpOk $Url }
        if ($ready) {
            Write-Host "OK  $Name $Url" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Host "WARN $Name 暂未就绪：$Url" -ForegroundColor Yellow
    return $false
}

if ($CheckOnly) {
    $apiReady = Wait-HttpOk "API" "$backendUrl/api/health" 3
    $webReady = Wait-HttpOk "Web" $frontendUrl 3
    if ($apiReady -and $webReady) {
        exit 0
    }
    exit 1
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "未找到 Python。请安装 Python 3 并加入 PATH。"
}

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "未找到 npm.cmd。请安装 Node.js，或确认 npm 已加入 PATH。"
}

$backendLog = Join-Path $logDir "backend.log"
$frontendLog = Join-Path $logDir "frontend.log"
Remove-Item -Force -ErrorAction SilentlyContinue $backendLog, $frontendLog

Write-Host "启动 AI 共创官本地开发环境" -ForegroundColor Cyan
Write-Host "API: $backendUrl"
Write-Host "Web: $frontendUrl"
Write-Host "日志: $logDir"
Write-Host ""

$backendJob = Start-Job -Name "fyg-api" -ArgumentList $backendDir, $BackendPort, $SkipInstall.IsPresent, $python.Source, $backendLog -ScriptBlock {
    param($backendDir, $port, $skipInstall, $pythonExe, $logPath)
    $ErrorActionPreference = "Stop"
    Set-Location $backendDir
    $venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        & $pythonExe -m venv .venv *>> $logPath
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    $pip = Join-Path $backendDir ".venv\Scripts\pip.exe"
    if (-not $skipInstall) {
        & $pip install -r requirements.txt *>> $logPath
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    & $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port *>> $logPath
    exit $LASTEXITCODE
}

$frontendJob = Start-Job -Name "fyg-web" -ArgumentList $frontendDir, $FrontendPort, $BackendPort, $SkipInstall.IsPresent, $npm.Source, $frontendLog -ScriptBlock {
    param($frontendDir, $port, $backendPort, $skipInstall, $npmExe, $logPath)
    $ErrorActionPreference = "Stop"
    Set-Location $frontendDir
    if (-not $skipInstall -and -not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        & $npmExe install *>> $logPath
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    $env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$backendPort"
    & $npmExe run dev -- --host 127.0.0.1 --port $port *>> $logPath
    exit $LASTEXITCODE
}

try {
    $apiReady = Wait-HttpOk "API" "$backendUrl/api/health" 60
    $webReady = Wait-HttpOk "Web" $frontendUrl 60
    if (-not ($apiReady -and $webReady)) {
        throw "本地环境未全部就绪，请查看日志：$logDir"
    }
    Write-Host ""
    Write-Host "本地环境已启动。" -ForegroundColor Green
    Write-Host "打开：$frontendUrl"
    Write-Host "健康检查：$backendUrl/api/health"
    Write-Host "运行状态：$backendUrl/api/system/status"
    Write-Host "按 Ctrl+C 停止 API 和 Web。"
    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($job in @($backendJob, $frontendJob)) {
            if ($job.State -in @("Failed", "Completed", "Stopped")) {
                Receive-Job $job -ErrorAction SilentlyContinue | Out-Host
                throw "$($job.Name) 已停止，请查看日志：$logDir"
            }
        }
    }
}
finally {
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "已停止本地开发环境。" -ForegroundColor Yellow
}
