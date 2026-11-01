$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk" }
if (-not $env:JAVA_HOME) {
    $jdk = Get-ChildItem 'C:\Program Files\Eclipse Adoptium' -Directory -Filter 'jdk-21*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
    if ($jdk) { $env:JAVA_HOME = $jdk.FullName }
}
function Run-Step([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed (exit $LASTEXITCODE). Build stopped." }
}
try {
    Run-Step 'node' @('scripts/check-java.mjs')
    Write-Host 'Stop the NexEase web frontend before continuing: npm ci replaces node_modules.'
    Run-Step 'npm.cmd' @('ci')
    Run-Step 'npm.cmd' @('run','mobile:build')
    Run-Step 'npx.cmd' @('cap','sync','android')
    Set-Location android
    Run-Step '.\gradlew.bat' @('assembleDebug')
    Write-Host "APK: $PWD\app\build\outputs\apk\debug\app-debug.apk"
    explorer.exe '.\app\build\outputs\apk\debug'
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
