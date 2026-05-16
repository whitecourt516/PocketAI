@echo off
title Pocket Launcher
color 0A

echo.
echo  ===================================
echo   Pocket - Starting up...
echo  ===================================
echo.

REM ── Start Docker containers ──────────────────────────────────────────────
echo  [1/3] Starting Docker containers...
docker compose -p pocketai -f C:\Users\white\PocketAI\docker-compose.yml up -d

if %errorlevel% neq 0 (
    echo.
    echo  [!] Docker failed to start. Is Docker Desktop running?
    echo      Open Docker Desktop first, wait for it to load, then try again.
    echo.
    pause
    exit /b 1
)

echo  Containers up.
echo.

REM ── Wait for Ollama to be ready ──────────────────────────────────────────
echo  [2/3] Waiting for Ollama to be ready...
:wait_ollama
curl -s http://localhost:11434 > nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak > nul
    goto wait_ollama
)
echo  Ollama ready.
echo.

REM ── Start the Electron avatar app ────────────────────────────────────────
echo  [3/3] Starting Pocket...
start "Pocket Avatar" /D "%~dp0app" cmd /c "npm start"

REM ── Wait for avatar WebSocket server to come up ──────────────────────────
timeout /t 3 /nobreak > nul

REM ── Start the unified Pocket engine ─────────────────────────────────────
cd /D "%~dp0expression-engine"
python pocket.py

REM ── Cleanup on exit ──────────────────────────────────────────────────────
echo.
echo  Pocket has stopped.
echo.
choice /C YN /M "Shut down Docker containers too?"
if %errorlevel% equ 1 (
    docker compose -p pocketai -f C:\Users\white\PocketAI\docker-compose.yml down
    echo  Containers stopped.
)

taskkill /f /im electron.exe > nul 2>&1
echo  Done. Later user.
pause
