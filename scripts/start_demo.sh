#!/bin/bash
# CineRAG - Demo Startup Script

echo "🎬 Starting CineRAG Demo..."
echo "=================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+."
    exit 1
fi

echo "✅ Dependencies check passed"
echo ""

# Start backend API
echo "🚀 Starting Backend API (port 8001)..."
cd "$(dirname "$0")/.."
python app/simple_main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Test backend
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend API is running"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting Frontend (port 3000)..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "🎯 Demo is ready!"
echo "=================================="
echo "📱 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8001"
echo "📚 API Docs: http://localhost:8001/docs"
echo ""
echo "🎬 Features available:"
echo "  ✅ Browse 9,000+ movies"
echo "  ✅ Search functionality"
echo "  ✅ Popular movies"
echo "  ✅ Real ratings data"
echo "  ✅ Netflix-style UI"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait