@echo off
echo Starting Traffic Flow Optimization System (MAU Yola)...

:: Step 1: Ensure database exists
start "Database Check" cmd /c "cd /d C:\Users\Administrator\traffic-flow-system && if not exist traffic.db (python database.py)"
timeout /t 2 /nobreak >nul

:: Step 2: Start Flask Application
start "Traffic Flow System - Web Server (Flask)" cmd /k "cd /d C:\Users\Administrator\traffic-flow-system && python app.py"
timeout /t 3 /nobreak >nul

:: Step 3: Launch Web Browser
start http://127.0.0.1:5000/
