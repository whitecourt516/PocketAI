@echo off
chcp 65001 > nul
title Pocket Launcher
color 0A
set "ROOT=%~dp0"
set "WS_PORT=7845"

echo.
echo  ===================================
echo   Pocket - Starting up...
echo  ===================================
echo.

echo  [1/4] Starting Docker containers...
docker compose -p pocketai -f "%ROOT%docker-compose.yml" up -d
if %errorlevel% neq 0 (
    echo  [!] Docker failed to start. Is Docker Desktop running?
    pause
    exit /b 1
)
echo        Containers up.
echo.

echo  [2/4] Waiting for Ollama...
:wait_ollama
curl -s http://localhost:11434 >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto wait_ollama
)
echo        Ollama ready.
echo.

echo  [3/4] Launching avatar in its own window...
start "Pocket Avatar" /D "%ROOT%" Start-Avatar.bat
echo        Waiting for avatar WebSocket on port %WS_PORT% (not a blind sleep)...
:wait_ws
netstat -an | findstr "LISTENING" | findstr ":%WS_PORT%" >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto wait_ws
)
echo        Avatar WebSocket up.
echo.

echo  [4/4] Launching engine in its own window...
start "Pocket Engine" /D "%ROOT%" Start-Engine.bat

echo.
echo  ===================================
echo   Pocket is up - two independent windows:
echo     - Pocket Avatar  (Electron + WebSocket server, port %WS_PORT%)
echo     - Pocket Engine  (pocket.py CLI)
echo.
echo   Relaunch either alone:  Start-Avatar.bat  /  Start-Engine.bat
echo   Stop everything:        Stop-Pocket.bat
echo.
echo   Closing THIS window will NOT stop Pocket.
echo  ===================================
echo.
pause
