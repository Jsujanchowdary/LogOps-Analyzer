#!/bin/bash

echo "🚀 Starting LogOps Analyzer (Fast Mode)..."
echo "=================================="

# Kill any existing processes
pkill -f "streamlit run" 2>/dev/null
pkill -f "python api.py" 2>/dev/null
pkill -f "python log_generator.py" 2>/dev/null

# Wait a moment
sleep 2

# Start API
echo "🔧 Starting API server..."
python api.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 5

# Start log generator
echo "📝 Starting log generator..."
python log_generator.py &
GENERATOR_PID=$!

# Wait a moment
sleep 2

# Start simple dashboard
echo "📊 Starting simple dashboard..."
echo ""
echo "🎉 LogOps Analyzer is starting!"
echo "📊 Dashboard: http://localhost:8501"
echo "🔧 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping LogOps Analyzer..."
    kill $API_PID $GENERATOR_PID 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start Streamlit with simple dashboard
streamlit run dashboard_simple.py --server.port=8501 --server.address=0.0.0.0




