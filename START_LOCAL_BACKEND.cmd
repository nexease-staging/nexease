@echo off
setlocal
cd /d "%~dp0"
set APP_ENV=development
set DJANGO_DEBUG=true
set ALLOWED_HOSTS=localhost,127.0.0.1
set FRONTEND_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
set FRONTEND_BASE_URL=http://127.0.0.1:3000
set TRUST_PROXY_SSL_HEADER=false
set DJANGO_SETTINGS_MODULE=config.settings
if not exist ".venv\Scripts\python.exe" (
 echo Install dependencies and create .venv first. See OCT31_OPERATIONS_UPDATE.md.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
pause
