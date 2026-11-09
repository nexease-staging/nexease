param([string]$Output = (Join-Path $env:USERPROFILE 'Downloads\NexEase-Singapore.apk'))
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $env:NEXT_PUBLIC_API_BASE_URL = 'https://nexease-backend-singapore.onrender.com/api/v1'
    $env:NPM_CONFIG_INCLUDE = 'dev'
    if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
    if (-not (Test-Path $env:ANDROID_HOME)) { throw 'Android SDK missing. Set ANDROID_HOME to your SDK folder.' }
    if ($env:JAVA_HOME) { $env:Path = (Join-Path $env:JAVA_HOME 'bin') + ';' + $env:Path }
    & java -version
    if ($LASTEXITCODE -ne 0) { throw 'Configure JDK 21 or newer.' }
    & npm ci --include=dev
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    & npm run mobile:build
    if ($LASTEXITCODE -ne 0) { throw 'Mobile web build failed.' }
    & npx cap sync android
    if ($LASTEXITCODE -ne 0) { throw 'Capacitor sync failed.' }
    Push-Location android
    try {
        & .\gradlew.bat assembleDebug
        if ($LASTEXITCODE -ne 0) { throw 'Android Gradle build failed.' }
        Copy-Item -LiteralPath '.\app\build\outputs\apk\debug\app-debug.apk' -Destination $Output -Force
    } finally { Pop-Location }
    Write-Host "APK ready: $Output" -ForegroundColor Green
} finally { Pop-Location }
