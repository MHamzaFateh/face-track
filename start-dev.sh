#!/bin/bash

echo "========================================"
echo " Face Recognition System - Development"
echo "========================================"
echo ""

echo "Starting Backend Server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

sleep 3

echo "Starting Frontend Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "Both servers are running!"
echo ""
echo "Backend:  http://localhost:8003"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8003/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "========================================"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

