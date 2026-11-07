param([switch]$WithWorker)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$backendPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path $backendPython)) { throw 'Create .venv and install requirements.txt first. See REFERENCE_UI_UPDATE.md.' }
if (!(Test-Path (Join-Path $PSScriptRoot '.env'))) { throw 'Copy your working .env here first. See REFERENCE_UI_UPDATE.md.' }
# Local-only process settings; saved secrets and Render settings are not modified.
$env:APP_ENV = 'development'
$env:DJANGO_DEBUG = 'true'
$env:ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:FRONTEND_ORIGINS = 'http://127.0.0.1:3000,http://localhost:3000'
$env:FRONTEND_BASE_URL = 'http://127.0.0.1:3000'
$env:TRUST_PROXY_SSL_HEADER = 'false'
$env:NEXT_PUBLIC_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'
& $backendPython manage.py check
if ($LASTEXITCODE -ne 0) { throw 'Backend check failed. Fix the error above first.' }
Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot'; & '$backendPython' manage.py runserver 127.0.0.1:8000 --noreload"
Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot\frontend'; npm.cmd run dev"
if ($WithWorker) {
    Write-Warning 'The worker processes pending jobs in the database selected by .env.'
    Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot'; & '$backendPython' manage.py run_background_worker --sleep 2 --lease-seconds 300"
}
Write-Host 'Open http://127.0.0.1:3000 after the frontend says Ready.'
