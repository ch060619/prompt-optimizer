@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "MACHINE_PATH=%%B"
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%B"
if defined MACHINE_PATH set "PATH=%MACHINE_PATH%;%PATH%"
if defined USER_PATH set "PATH=%USER_PATH%;%PATH%"

echo [1/6] Checking Python...
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

echo [2/6] Checking Node.js...
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

echo [3/6] Preparing Python virtual environment...
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

echo [4/6] Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
  call npm.cmd install
  if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
  )
)

echo [5/6] Building frontend...
call npm.cmd run build
if errorlevel 1 (
  echo ERROR: Failed to build frontend.
  pause
  exit /b 1
)
cd ..

echo [6/6] Starting Prompt Optimizer...
echo Open http://127.0.0.1:8000 in your browser.
python -m prompt_optimizer.cli serve --host 127.0.0.1 --port 8000

endlocal
