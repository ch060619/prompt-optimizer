@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "APP_HOST=127.0.0.1"
set "APP_PORT=8000"
set "APP_VERSION=2.0"
set "RUNTIME_DIR=%CD%\.runtime"
set "LOCAL_PID_FILE=%RUNTIME_DIR%\backend.pid"
set "DOCKER_CONTAINER=prompt-optimizer-v2"
set "RUN_MODE=%~1"
if "%RUN_MODE%"=="" set "RUN_MODE=local"

if /i "%RUN_MODE%"=="local" goto local
if /i "%RUN_MODE%"=="docker" goto docker
if /i "%RUN_MODE%"=="stop" goto stop
if /i "%RUN_MODE%"=="status" goto status
echo ERROR: Unknown command "%RUN_MODE%".
echo Usage: start.bat [local^|docker^|stop^|status]
exit /b 1

:local
set "PROMPT_OPTIMIZER_ENV=development"
echo [local] stopping previous instance
call :stop_local
if errorlevel 1 exit /b 1
echo [local] checking port
call :require_free_port
if errorlevel 1 exit /b 1
echo [local] preparing runtime
call :prepare_local
if errorlevel 1 exit /b 1
if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"
echo Starting Prompt Optimizer V%APP_VERSION% locally...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Get-Location).Path; $runtime=Join-Path $root '.runtime'; $python=Join-Path $root '.venv\Scripts\python.exe'; $process=Start-Process -FilePath $python -ArgumentList @('-m','prompt_optimizer.cli','serve','--host','127.0.0.1','--port','8000') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'backend.log') -RedirectStandardError (Join-Path $runtime 'backend-error.log') -PassThru; Set-Content -LiteralPath (Join-Path $runtime 'backend.pid') -Value $process.Id -NoNewline; exit 0"
if errorlevel 1 (
  echo ERROR: Failed to start the local backend. Check .runtime\backend-error.log.
  exit /b 1
)
echo Running at http://%APP_HOST%:%APP_PORT%
echo Logs: .runtime\backend.log
exit /b 0

:docker
where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker CLI was not found.
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running.
  exit /b 1
)
if "%PROMPT_OPTIMIZER_JWT_SECRET%"=="" (
  echo ERROR: Set PROMPT_OPTIMIZER_JWT_SECRET to a random value of at least 32 bytes.
  exit /b 1
)
call :require_free_port
if errorlevel 1 exit /b 1
echo Building and starting Prompt Optimizer API and Worker...
docker compose up -d --build
if errorlevel 1 exit /b 1
echo Running at http://%APP_HOST%:%APP_PORT%
echo Logs: docker logs -f %DOCKER_CONTAINER%
exit /b 0

:stop
call :stop_local
if errorlevel 1 exit /b 1
docker compose down >nul 2>nul
echo Prompt Optimizer stopped.
exit /b 0

:status
call :local_status
docker ps --filter "label=com.docker.compose.service=api" --format "Docker API: {{.Status}}" 2>nul
docker ps --filter "label=com.docker.compose.service=worker" --format "Docker Worker: {{.Status}}" 2>nul
exit /b 0

:prepare_local
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.12+ is required.
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.12+ is required.
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 18+ is required.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 exit /b 1
  ".venv\Scripts\python.exe" -m pip install -e "backend[dev]"
  if errorlevel 1 exit /b 1
)
if not exist "frontend\node_modules" (
  pushd frontend
  call npm.cmd ci
  popd
  if errorlevel 1 exit /b 1
)
pushd frontend
call npm.cmd run build
popd
if errorlevel 1 exit /b 1
exit /b 0

:require_free_port
powershell -NoProfile -ExecutionPolicy Bypass -Command "$listener=Get-NetTCPConnection -State Listen -LocalPort %APP_PORT% -ErrorAction SilentlyContinue ^| Select-Object -First 1; if ($listener) { Write-Error ('Port %APP_PORT% is in use by PID {0}. Stop that process or use another port.' -f $listener.OwningProcess); exit 1 }; exit 0"
exit /b !errorlevel!

:stop_local
if not exist "%LOCAL_PID_FILE%" exit /b 0
if exist "%LOCAL_PID_FILE%" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$pidFile='%LOCAL_PID_FILE%'; $raw=(Get-Content -LiteralPath $pidFile -Raw).Trim(); if ($raw -notmatch '^\d+$') { Write-Error 'Invalid Prompt Optimizer PID file.'; exit 1 }; $process=Get-CimInstance Win32_Process -Filter ('ProcessId={0}' -f $raw) -ErrorAction SilentlyContinue; if ($null -eq $process) { Remove-Item -LiteralPath $pidFile -Force; exit 0 }; if ($process.CommandLine -notlike '*prompt_optimizer.cli*serve*') { Write-Error ('PID file points to a different process: {0}' -f $process.Name); exit 1 }; Stop-Process -Id ([int]$raw) -ErrorAction Stop; Wait-Process -Id ([int]$raw) -Timeout 10 -ErrorAction Stop; Remove-Item -LiteralPath $pidFile -Force"
  exit /b !errorlevel!
)

:local_status
if not exist "%LOCAL_PID_FILE%" (
  echo Local: stopped
  exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$pidFile='%LOCAL_PID_FILE%'; $raw=(Get-Content -LiteralPath $pidFile -Raw).Trim(); $process=Get-CimInstance Win32_Process -Filter ('ProcessId={0}' -f $raw) -ErrorAction SilentlyContinue; if ($process -and $process.CommandLine -like '*prompt_optimizer.cli*serve*') { Write-Host ('Local: running (PID {0})' -f $raw) } else { Write-Host 'Local: stale PID file' }"
exit /b 0
