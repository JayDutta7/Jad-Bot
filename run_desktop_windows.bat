@echo off
REM ==============================================================================
REM 🌅 Daily 6:00 AM Wake Up & Morning Assistant Bot - Windows Desktop Launcher
REM ==============================================================================
chcp 65001 >nul
cd /d "%~dp0"
title 🌅 Wake Up Bot (Daily 6:00 AM IST)

echo =======================================================
echo 🌅 Launching Wake Up Bot on Windows Desktop
echo ⏰ Daily Alarm Time: 6:00 AM IST (GMT+5:30)
echo 🔋 Automatic sleep prevention (SetThreadExecutionState) enabled
echo =======================================================
echo.

python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Notice] Python exited with error code %ERRORLEVEL%.
    echo Please make sure Python 3.9+ is installed and added to your system PATH.
    pause
)
