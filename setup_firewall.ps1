# ATLASSIAN2 Access - Windows Firewall Setup Script
# This script creates firewall rules to allow external access to the application
# Run this script as Administrator

param(
    [Parameter(Mandatory=$false)]
    [string]$Port = "5000",
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteAddress = "Any",
    
    [Parameter(Mandatory=$false)]
    [switch]$Remove
)

$RuleName = "ATLASSIAN2 Access - Port $Port"

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($Remove) {
    # Remove existing firewall rule
    Write-Host "Removing firewall rule: $RuleName" -ForegroundColor Yellow
    
    $existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Remove-NetFirewallRule -DisplayName $RuleName
        Write-Host "Firewall rule removed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Firewall rule not found." -ForegroundColor Yellow
    }
    
    exit 0
}

# Create firewall rule
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ATLASSIAN2 Access - Firewall Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Remove existing rule if it exists
$existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "Removing existing firewall rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $RuleName
}

# Create new firewall rule
Write-Host "Creating firewall rule..." -ForegroundColor Green
Write-Host "  Rule Name: $RuleName" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host "  Protocol: TCP" -ForegroundColor White
Write-Host "  Direction: Inbound" -ForegroundColor White
Write-Host "  Remote Address: $RemoteAddress" -ForegroundColor White
Write-Host ""

try {
    if ($RemoteAddress -eq "Any") {
        New-NetFirewallRule -DisplayName $RuleName `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $Port `
            -Action Allow `
            -Profile Domain,Private,Public `
            -ErrorAction Stop | Out-Null
    } else {
        New-NetFirewallRule -DisplayName $RuleName `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $Port `
            -RemoteAddress $RemoteAddress `
            -Action Allow `
            -Profile Domain,Private,Public `
            -ErrorAction Stop | Out-Null
    }
    
    Write-Host "Firewall rule created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Display the created rule
    Write-Host "Firewall Rule Details:" -ForegroundColor Cyan
    Get-NetFirewallRule -DisplayName $RuleName | Format-Table -Property DisplayName, Enabled, Direction, Action
    
    Write-Host ""
    Write-Host "Your application is now accessible from:" -ForegroundColor Green
    Write-Host "  - Local:    http://127.0.0.1:$Port" -ForegroundColor White
    Write-Host "  - Network:  http://[YOUR_IP]:$Port" -ForegroundColor White
    
    if ($RemoteAddress -eq "Any") {
        Write-Host "  - External: http://[PUBLIC_IP]:$Port" -ForegroundColor White
        Write-Host ""
        Write-Host "WARNING: Port is open to all external connections!" -ForegroundColor Yellow
        Write-Host "Consider restricting access to specific IP ranges for security." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "To remove this rule later, run:" -ForegroundColor Cyan
    Write-Host "  .\setup_firewall.ps1 -Remove" -ForegroundColor White
    
} catch {
    Write-Host "ERROR: Failed to create firewall rule!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
