<#
Script to install the ZDownloadManager native messaging host on Windows.

Run this PowerShell script with an environment variable ZDM_EXT_ID set to your
extension ID. It writes a manifest file into the user's native
messaging hosts directory and points the path to the Python entrypoint.
>

$ErrorActionPreference = 'Stop'

if (-not $env:ZDM_EXT_ID) {
    Write-Error "Please set ZDM_EXT_ID environment variable to the extension ID"
    exit 1
}

# Determine paths
$manifestDir = Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data\NativeMessagingHosts"
if (-not (Test-Path $manifestDir)) {
    New-Item -ItemType Directory -Path $manifestDir | Out-Null
}
$manifestPath = Join-Path $manifestDir "com.zdownloadmanager.host.json"
# Template path relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$template = Get-Content (Join-Path $scriptDir "host.json.template") -Raw
# Replace placeholders
$exePath = (Join-Path $scriptDir "..\zdownloadmanager\integration\native_messaging_host.py")
$template = $template -replace '__EXT_ID__', $env:ZDM_EXT_ID
$template = $template -replace '__HOST_PATH__', $exePath.Replace('\\','\\\\')
$template | Out-File -Encoding utf8 -FilePath $manifestPath
Write-Output "Installed host manifest at $manifestPath"
