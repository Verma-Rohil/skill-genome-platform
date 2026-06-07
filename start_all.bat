@echo off
title Skill Genome Platform - All Services
echo ============================================================
echo    Skill Genome Platform - Starting All Services
echo ============================================================
echo.

:: Start MLflow Tracking Server (port 5000)
echo [1/3] Starting MLflow Tracking Server on port 5000...
start "MLflow Server" /min cmd /c "cd /d C:\Project_2\skill-genome-platform\backend && .\venv\Scripts\mlflow server --host 127.0.0.1 --port 5000"

:: Start FastAPI Backend (port 8000)
echo [2/3] Starting FastAPI Backend on port 8000...
start "FastAPI Backend" /min cmd /c "cd /d C:\Project_2\skill-genome-platform\backend && .\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: Start Vite Frontend (port 5173)
echo [3/3] Starting Vite Frontend Dashboard on port 5173...
start "Vite Frontend" /min cmd /c "cd /d C:\Project_2\skill-genome-platform\frontend && npm run dev"

echo.
echo ============================================================
echo    All services are starting in minimized windows!
echo ============================================================
echo.
echo    Dashboard UI:      http://localhost:5173/
echo    API Docs:          http://localhost:8000/docs
echo    API Health:        http://localhost:8000/api/health
echo    MLflow Tracking:   http://localhost:5000/
echo.
echo    Close this window anytime. The servers run independently.
echo ============================================================
echo.
timeout /t 20 /nobreak >nul

:: Open dashboard in browser after giving servers time to boot
start http://localhost:5173/
