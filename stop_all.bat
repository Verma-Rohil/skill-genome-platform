@echo off
title Skill Genome Platform - Stopping All Services
echo ============================================================
echo    Skill Genome Platform - Stopping All Services
echo ============================================================
echo.

:: Kill processes on the three ports
echo Stopping FastAPI on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo Stopping MLflow on port 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo Stopping Vite on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo.
echo All services stopped.
echo ============================================================
pause
