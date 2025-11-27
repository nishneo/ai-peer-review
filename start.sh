#!/bin/bash

# AI Peer Review - Start script

echo "Starting AI Peer Review..."
echo ""

# Kill any existing processes on the ports
echo "Checking for existing processes..."

if lsof -ti:8001 > /dev/null 2>&1; then
    echo "  Killing existing backend process on port 8001..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -ti:5173 > /dev/null 2>&1; then
    echo "  Killing existing frontend process on port 5173..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo ""

# Start backend
echo "Starting backend on http://localhost:8001..."
uv run python -m backend.main &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ AI Peer Review is running!"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
