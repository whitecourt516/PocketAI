@echo off
chcp 65001 > nul
title Pocket Engine
color 0E
cd /d "%~dp0"

REM --- Virtual environment (recommended - see audit finding A8) --------------
REM Pocket currently runs on global Python. To make requirements.txt
REM reproducible, create a venv once:
REM     py -m venv .venv
REM     .venv\Scripts\pip install -r requirements.txt
REM then uncomment the next line so the engine always uses it:
REM call ".venv\Scripts\activate.bat"
REM ---------------------------------------------------------------------------

echo.
echo  Pocket Engine - pocket.py
echo  Close this window to stop ONLY the engine. The avatar keeps running.
echo.
python pocket.py
echo.
echo  Engine stopped.
pause
