@echo off
echo ========================================
echo  Face Recognition System - Development
echo ========================================
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo.
echo Backend:  http://localhost:8003
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8003/docs
echo.
echo Press any key to close this window...
echo ========================================
pause >nul

