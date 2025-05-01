@echo off
setlocal

:: Replace this with your real Netmaker token
set NETMAKER_TOKEN=XX

:: Step 1: Download netclientbundle.exe
echo Downloading netclientbundle.exe...
curl -L -o netclientbundle.exe https://fileserver.netmaker.io/releases/download/v0.90.0/netclientbundle.exe
if %errorlevel% neq 0 (
    echo Failed to download netclientbundle.exe
    exit /b 1
)

:: Step 2: Install netclientbundle.exe silently
echo Installing Netclient...
netclientbundle.exe /S
if %errorlevel% neq 0 (
    echo Netclient installation failed
    exit /b 1
)

:: Step 3: Wait a bit in case the installer needs time
timeout /t 5 > nul

:: Step 4: Run netclient join
echo Joining Netmaker network...
netclient join -t %NETMAKER_TOKEN% --static-port -p 51821
if %errorlevel% neq 0 (
    echo Netclient join command failed
    exit /b 1
)

:: Step 5: Start Docker Compose
echo Starting worker with Docker Compose...
docker compose -f worker.yaml up -d
if %errorlevel% neq 0 (
    echo Docker Compose failed
    exit /b 1
)

echo All steps completed successfully!
endlocal
pause