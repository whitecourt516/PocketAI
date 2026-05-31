@echo off
chcp 65001 > nul
title Pocket Shutdown
set "ROOT=%~dp0"

echo.
echo  Stopping Pocket...
REM Scoped shutdown: close the two Pocket windows by title and tree-kill their
REM children (cmd -> npm -> electron). Does NOT touch other Electron apps,
REM unlike the old "taskkill /im electron.exe".
taskkill /fi "WINDOWTITLE eq Pocket Engine*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Pocket Avatar*" /t /f >nul 2>&1
echo  Avatar and engine windows closed.
echo.

choice /C YN /M "Also stop the Docker containers"
if %errorlevel% equ 1 (
    docker compose -p pocketai -f "%ROOT%docker-compose.yml" down
    echo  Containers stopped.
)
echo.
echo  Done. Later user.
pause
