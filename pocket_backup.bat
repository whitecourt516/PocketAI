@echo off
title Pocket Backup
color 0A

REM ── Configuration ────────────────────────────────────────────────────────
set COMPOSE_FILE=C:\Users\white\PocketAI\docker-compose.yml
set PROJECT_NAME=pocketai
set CHROMA_SOURCE=C:\Users\white\PocketAI\chroma_data
set BACKUP_ROOT=C:\Users\white\pocket_backups
set RETENTION_DAYS=30

REM ── Timestamp ─────────────────────────────────────────────────────────────
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set DATE_STR=%%c-%%a-%%b
for /f "tokens=1-3 delims=:." %%a in ("%time: =0%") do set TIME_STR=%%a%%b%%c
set TIMESTAMP=%DATE_STR%_%TIME_STR%
set BACKUP_DIR=%BACKUP_ROOT%\%TIMESTAMP%

echo.
echo  ===================================
echo   Pocket Backup - %TIMESTAMP%
echo  ===================================
echo.

REM ── Create backup directory ───────────────────────────────────────────────
echo  [1/6] Creating backup directory...
mkdir "%BACKUP_DIR%" 2>nul
if not exist "%BACKUP_DIR%" (
    echo  [!] Failed to create backup directory: %BACKUP_DIR%
    echo      Check that C:\Users\white\pocket_backups exists and is writable.
    pause
    exit /b 1
)
echo  Directory: %BACKUP_DIR%
echo.

REM ── Stop containers ───────────────────────────────────────────────────────
echo  [2/6] Stopping Pocket containers...
docker compose -p %PROJECT_NAME% -f "%COMPOSE_FILE%" stop memory-chat n8n
if %errorlevel% neq 0 (
    echo  [!] Failed to stop containers. Is Docker running?
    pause
    exit /b 1
)
echo  Containers stopped.
echo.

REM ── Back up chroma_data ───────────────────────────────────────────────────
echo  [3/6] Backing up chroma_data...
if not exist "%CHROMA_SOURCE%" (
    echo  [!] chroma_data folder not found at %CHROMA_SOURCE%
    echo      Skipping — check path in configuration block at top of script.
) else (
    xcopy "%CHROMA_SOURCE%" "%BACKUP_DIR%\chroma_data\" /E /I /H /Q
    if %errorlevel% neq 0 (
        echo  [!] chroma_data backup failed.
    ) else (
        echo  chroma_data backed up.
    )
)
echo.

REM ── Back up n8n_data volume ───────────────────────────────────────────────
echo  [4/6] Backing up n8n_data volume...
docker run --rm ^
    -v pocketai_n8n_data:/source:ro ^
    -v "%BACKUP_DIR%":/backup ^
    alpine tar czf /backup/n8n_data.tar.gz -C /source .
if %errorlevel% neq 0 (
    echo  [!] n8n_data backup failed.
) else (
    echo  n8n_data backed up.
)
echo.

REM ── Restart containers ────────────────────────────────────────────────────
echo  [5/6] Restarting containers...
docker compose -p %PROJECT_NAME% -f "%COMPOSE_FILE%" start memory-chat n8n
if %errorlevel% neq 0 (
    echo  [!] Containers failed to restart. Run Start Pocket.bat manually.
) else (
    echo  Containers restarted.
)
echo.

REM ── Prune old backups ─────────────────────────────────────────────────────
echo  [6/6] Pruning backups older than %RETENTION_DAYS% days...
forfiles /p "%BACKUP_ROOT%" /d -%RETENTION_DAYS% /c "cmd /c if @isdir==TRUE rd /s /q @path" 2>nul
echo  Pruning complete.
echo.

REM ── Summary ───────────────────────────────────────────────────────────────
echo  ===================================
echo   Backup complete.
echo   Location: %BACKUP_DIR%
echo  ===================================
echo.
pause
