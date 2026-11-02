@echo off
setlocal
cd /d "%~dp0"
if not exist "frontend\vitest.config.mts" (
  echo Extract the complete update before running this script.
  exit /b 1
)
rem Remove the superseded test configuration, never environment files.
if exist "frontend\vitest.config.ts" del "frontend\vitest.config.ts"
if not exist ".venv\Scripts\python.exe" (
  echo Existing virtual environment not found. Run: py -m venv .venv
  echo Then run: .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)
.venv\Scripts\python.exe manage.py upgrade_workforce
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe manage.py check
if errorlevel 1 exit /b 1
cd frontend
call npm ci
if errorlevel 1 exit /b 1
set "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1"
call npm run test:run
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
echo Local checks completed. Restart the frontend and backend.
endlocal
