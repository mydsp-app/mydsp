@echo off
title MY DSP Platform
echo.
echo  ============================================
echo    MY DSP Business Platform
echo  ============================================
echo.

cd /d "%~dp0"

:: Stop any old instance running on port 5000
echo  Stopping any previous instance...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5000 "') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Initialise/update the database
echo  Updating database...
python -c "from db import init_db; init_db()" 2>nul

echo  Starting app...
echo.
echo  Opening: http://localhost:5000
echo  Login:   admin / Admin@123
echo.
echo  Keep this window open. Press Ctrl+C to stop.
echo  ============================================
echo.

start "" http://localhost:5000
python app.py
pause
