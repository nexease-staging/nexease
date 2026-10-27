$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$backendPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path $backendPython)) { throw 'Run the setup steps in START_HERE_SAAS.md first.' }
Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot'; & '$backendPython' manage.py runserver 127.0.0.1:8000"
Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot\frontend'; npm.cmd run dev"
Start-Process powershell.exe -ArgumentList '-NoExit','-Command',"Set-Location '$PSScriptRoot'; & '$backendPython' manage.py run_background_worker --sleep 2 --lease-seconds 300"
Write-Host 'Open http://127.0.0.1:3000 after the frontend is ready. Owner: http://127.0.0.1:3000/owner'
