# PowerShell script to manage Docker containers
# Requires administrative privileges

# Function to check if Docker is installed
function Test-DockerInstallation {
    try {
        $dockerVersion = docker --version
        if ($dockerVersion) {
            Write-Host "Docker is installed: $dockerVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "Docker is not installed." -ForegroundColor Red
        return $false
    }
}

# Function to install Docker Desktop for Windows
function Install-DockerDesktop {
    Write-Host "Installing Docker Desktop for Windows..." -ForegroundColor Yellow
    
    # Download Docker Desktop installer
    $installerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $installerPath = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    
    # Run the installer
    Start-Process -Wait -FilePath $installerPath -ArgumentList "install --quiet"
    
    # Clean up
    Remove-Item $installerPath
    
    Write-Host "Docker Desktop has been installed. Please restart your computer to complete the installation." -ForegroundColor Green
    exit
}

# Function to check if containers are running
function Test-ContainersRunning {
    $composeFile = "docker-compose.yml"
    if (-not (Test-Path $composeFile)) {
        Write-Host "Error: docker-compose.yml not found in the current directory." -ForegroundColor Red
        exit 1
    }
    
    $containers = docker compose ps --format json | ConvertFrom-Json
    return $containers.Count -gt 0
}

# Main script
Write-Host "Docker Container Management Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if running with administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrative privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Check Docker installation
if (-not (Test-DockerInstallation)) {
    $installDocker = Read-Host "Docker is not installed. Would you like to install Docker Desktop? (Y/N)"
    if ($installDocker -eq 'Y') {
        Install-DockerDesktop
    }
    else {
        Write-Host "Please install Docker Desktop manually to use this script." -ForegroundColor Yellow
        exit 1
    }
}

# Check if containers are running
$containersRunning = Test-ContainersRunning

if ($containersRunning) {
    Write-Host "Containers are currently running." -ForegroundColor Yellow
    $action = Read-Host "Would you like to stop the containers? (Y/N)"
    if ($action -eq 'Y') {
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker compose down
        Write-Host "Containers have been stopped." -ForegroundColor Green
    }
}
else {
    Write-Host "No containers are currently running." -ForegroundColor Yellow
    $action = Read-Host "Would you like to start the containers? (Y/N)"
    if ($action -eq 'Y') {
        Write-Host "Starting containers..." -ForegroundColor Yellow
        docker compose up -d
        Write-Host "Containers have been started." -ForegroundColor Green
    }
}

Write-Host "`nScript completed." -ForegroundColor Cyan 