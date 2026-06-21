@echo off
chcp 65001 > nul
title Pocket Engine
color 0E
cd /d "%~dp0"

REM --- Virtual environment (A8) ----------------------------------------------
REM Pocket runs in a local Python 3.13 venv (.venv) for reproducibility.
REM Activate it so the engine never silently falls back to global Python.
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo  [warning] .venv not found - running on global Python.
    echo            Create it:  py -3.13 -m venv .venv  then  pip install -r requirements.txt
)
REM ---------------------------------------------------------------------------

echo.
echo  Pocket Engine - pocket.py
echo  Close this window to stop ONLY the engine. The avatar keeps running.
echo.
python pocket.py
echo.
echo  Engine stopped.
pause