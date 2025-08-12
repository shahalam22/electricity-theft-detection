@echo off
echo ===============================================
echo  Electricity Theft Detection System Launcher
echo ===============================================
echo.
echo Starting the application...
echo.

REM Start backend API
echo [1/2] Starting Backend API Server...
start "Backend API" cmd /c "python run_simple.py"
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] Starting Frontend Dashboard...
start "Frontend Dashboard" cmd /c "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ===============================================
echo  Application is starting up...
echo ===============================================
echo.
echo Backend API:       http://localhost:8000
echo Frontend Dashboard: http://localhost:3000
echo API Documentation: http://localhost:8000/api/docs
echo.
echo Please wait a few seconds for both servers to start,
echo then open http://localhost:3000 in your browser.
echo.
echo Press any key to open the dashboard in your browser...
pause >nul

REM Open browser
start http://localhost:3000

echo.
echo Application is now running!
echo Close this window when you want to stop the application.
echo.
pause