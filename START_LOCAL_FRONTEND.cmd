@echo off
setlocal
cd /d "%~dp0frontend"
set NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
call npm.cmd run dev -- --hostname 127.0.0.1
pause
