@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "APP_HOST=127.0.0.1"
set "APP_PORT=8000"
set "FRONTEND_PORT=5173"
set "APP_VERSION=2.0"
set "RUN_MODE=%~1"
if "%RUN_MODE%"=="" set "RUN_MODE=local"

for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "MACHINE_PATH=%%B"
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%B"
if defined MACHINE_PATH set "PATH=%MACHINE_PATH%;%PATH%"
if defined USER_PATH set "PATH=%USER_PATH%;%PATH%"
if exist "%ProgramFiles%\Docker\Docker\resources\bin" set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"

echo Prompt Optimizer V%APP_VERSION% startup mode: %RUN_MODE%
if /i "%RUN_MODE%"=="docker" goto docker_mode
if /i not "%RUN_MODE%"=="local" (
  echo ERROR: Unknown startup mode "%RUN_MODE%".
  echo Usage: start.bat [local^|docker]
  pause
  exit /b 1
)

echo [1/7] Stopping old local app processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=@(%APP_PORT%,%FRONTEND_PORT%); $ownerPids=Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($ownerPid in $ownerPids) { if ($ownerPid -and $ownerPid -ne $PID) { $proc=Get-Process -Id $ownerPid -ErrorAction SilentlyContinue; if ($proc -and $proc.ProcessName -notmatch 'docker') { Write-Host ('Stopping PID {0} ({1}) on app port' -f $ownerPid,$proc.ProcessName); Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue } } }"
if errorlevel 1 (
  echo WARN: Could not inspect or stop old port processes. Continuing...
)
echo [2/7] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.12+ is required but was not found in PATH.
  pause
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.12+ is required.
  python --version
  pause
  exit /b 1
)
python --version

echo [3/7] Checking Node.js...
where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 18+ is required but was not found in PATH.
  pause
  exit /b 1
)
for /f "usebackq delims=" %%v in (`node -p "process.versions.node.split('.')[0]"`) do set NODE_MAJOR=%%v
if %NODE_MAJOR% LSS 18 (
  echo ERROR: Node.js 18+ is required. Current version:
  node --version
  pause
  exit /b 1
)
node --version

echo [4/7] Preparing Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create Python virtual environment.
    pause
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -e "backend[dev]"
if errorlevel 1 (
  echo ERROR: Failed to install backend dependencies.
  pause
  exit /b 1
)

echo [5/7] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
  call npm.cmd install
  if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
  )
)

echo [6/7] Building frontend...
call npm.cmd run build
if errorlevel 1 (
  echo ERROR: Failed to build frontend.
  pause
  exit /b 1
)
cd ..

echo [7/7] Starting Prompt Optimizer...
echo Open http://%APP_HOST%:%APP_PORT% in your browser.
python -m prompt_optimizer.cli serve --host %APP_HOST% --port %APP_PORT%

goto end_success

:docker_mode
echo [1/4] Checking Docker Desktop...
where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker CLI was not found. Install and start Docker Desktop first.
  pause
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker engine is not running. Start Docker Desktop and try again.
  pause
  exit /b 1
)
docker --version

echo [2/4] Stopping old Prompt Optimizer Docker container...
docker rm -f prompt-optimizer-v2 >nul 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=@(%APP_PORT%); $ownerPids=Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($ownerPid in $ownerPids) { if ($ownerPid -and $ownerPid -ne $PID) { $proc=Get-Process -Id $ownerPid -ErrorAction SilentlyContinue; if ($proc -and $proc.ProcessName -match 'python|node') { Write-Host ('Stopping PID {0} ({1}) on app port' -f $ownerPid,$proc.ProcessName); Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue } } }"

echo [3/4] Building V2.0 Docker image...
docker build -t prompt-optimizer:v2.0 -t prompt-optimizer:local .
if errorlevel 1 (
  echo ERROR: Docker image build failed.
  pause
  exit /b 1
)

echo [4/4] Starting Prompt Optimizer V2.0 Docker container...
echo Open http://%APP_HOST%:%APP_PORT% in your browser.
docker run --rm --name prompt-optimizer-v2 -p %APP_PORT%:8000 prompt-optimizer:v2.0

:end_success
endlocal
