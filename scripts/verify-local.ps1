param(
    [switch]$SkipFrontend,
    [switch]$CheckDatabase,
    [switch]$CheckModel,
    [switch]$CheckRunning,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$requiredApiCapabilities = @("model_status_error", "report_pdf_export")

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
}

function Assert-NativeSuccess {
    param([string]$CommandName)
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "$CommandName 执行失败，退出码：$LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Resolve-FrontendRunner {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npm) {
        return @($npm.Source, "run")
    }

    $pnpm = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
    if ($pnpm) {
        return @($pnpm.Source, "run")
    }

    throw "未找到 npm.cmd 或 pnpm.cmd，无法执行前端检查。"
}

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

function Assert-RunningStack {
    $backendUrl = "http://127.0.0.1:$BackendPort"
    $frontendUrl = "http://127.0.0.1:$FrontendPort"
    try {
        $health = Invoke-RestMethod -Uri "$backendUrl/api/health" -TimeoutSec 2
    }
    catch {
        throw "API 未就绪：$backendUrl/api/health"
    }
    if ($health.status -ne "ok") {
        throw "API 健康检查状态异常：$($health.status)"
    }
    foreach ($capability in $requiredApiCapabilities) {
        if ($health.capabilities -notcontains $capability) {
            throw "API 缺少能力标记 $capability。当前 8000 端口可能仍是旧后端进程，请重启。"
        }
    }
    if (-not (Test-HttpOk $frontendUrl)) {
        throw "Web 未就绪：$frontendUrl"
    }
    Write-Host "API/Web 运行中，且 API 能力标记匹配当前代码。" -ForegroundColor Green
}

Invoke-Step "后端测试" {
    Push-Location (Join-Path $root "backend")
    try {
        python -m pytest
        Assert-NativeSuccess "python -m pytest"
    }
    finally {
        Pop-Location
    }
}

if ($CheckDatabase) {
    Invoke-Step "数据库连接与表结构自检" {
        Push-Location (Join-Path $root "backend")
        try {
            python .\scripts\database_smoke.py
            Assert-NativeSuccess "python .\scripts\database_smoke.py"
        }
        finally {
            Pop-Location
        }
    }
}

if ($CheckModel) {
    Invoke-Step "本地 Ollama 模型连通性自检" {
        Push-Location (Join-Path $root "backend")
        try {
            python .\scripts\ollama_smoke.py
            Assert-NativeSuccess "python .\scripts\ollama_smoke.py"
        }
        finally {
            Pop-Location
        }
    }
}

if ($CheckRunning) {
    Invoke-Step "运行中服务能力自检" {
        Assert-RunningStack
    }
}

if (-not $SkipFrontend) {
    $runner = Resolve-FrontendRunner
    Invoke-Step "前端 lint" {
        Push-Location (Join-Path $root "frontend")
        try {
            & $runner[0] $runner[1] lint
            Assert-NativeSuccess "前端 lint"
        }
        finally {
            Pop-Location
        }
    }

    Invoke-Step "前端生产构建" {
        Push-Location (Join-Path $root "frontend")
        try {
            & $runner[0] $runner[1] build
            Assert-NativeSuccess "前端生产构建"
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "本地验收通过。" -ForegroundColor Green
