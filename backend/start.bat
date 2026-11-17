@echo off
setlocal
REM 始终在 backend 目录执行；自动创建 .venv 并安装依赖后启动 AI 共创官 API。
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul || set "PY=py"

if not exist ".venv\Scripts\python.exe" (
  echo [%~n0] 正在创建虚拟环境 .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [%~n0] 失败：未找到 Python。请安装 Python 3 并加入 PATH，或在 backend 目录手动执行:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    exit /b 1
  )
)

if not exist ".venv\Scripts\uvicorn.exe" (
  echo [%~n0] 正在安装依赖 requirements.txt ...
  ".venv\Scripts\pip.exe" install -r requirements.txt
  if errorlevel 1 exit /b 1
)

echo [%~n0] 启动 AI 共创官 API http://127.0.0.1:8000 （工作目录: %CD%）
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
