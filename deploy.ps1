# Local deploy wrapper for EV Charger Discord Bot
# Calls CentralDeployTools with preconfigured server and username

param(
    [string]$ServerIP = "10.0.0.225",
    [string]$Username = "kali",
    [string]$RemoteDir = "discord-car-charger-bot",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$CentralScript = "F:\Games\Python\Coinbase\Grid bot\CentralDeployTools\deploy.ps1"
$ProjectPath = $PSScriptRoot

if (Test-Path $CentralScript) {
    Write-Host "Deploying to $Username@$ServerIP (Remote: ~/$RemoteDir)..." -ForegroundColor Cyan
    & $CentralScript -ProjectPath $ProjectPath -Username $Username -ServerIP $ServerIP -RemoteDir $RemoteDir -DryRun:$DryRun
} else {
    Write-Error "Central deployment script not found at: $CentralScript"
}
