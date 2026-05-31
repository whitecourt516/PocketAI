@echo off
chcp 65001 > nul
title Pocket Avatar
color 0B
cd /d "%~dp0app"
echo.
echo  Pocket Avatar - Electron + WebSocket server (port 7845)
echo  Close this window to stop ONLY the avatar. The engine keeps running
echo  and will reconnect automatically* when the avatar comes back.
echo.
npm start
echo.
echo  Avatar stopped.
pause
