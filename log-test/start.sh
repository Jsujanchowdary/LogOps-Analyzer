#!/bin/bash

# LogOps Analyzer Startup Script
echo "🚀 Starting LogOps Analyzer..."
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
# Gemini API Configuration
GEMINI_API_KEY=AIzaSyCF7ZF63ss7KSxGAP_WQorsWr2iEHb_ix4

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8099428200:AAH2nsScHbbagxhhDOSzOicxduH-efNTqKk
TELEGRAM_CHAT_ID=5040089366

# Application Configuration
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./logs.db
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501

# Alerting Configuration
ERROR_THRESHOLD=2
CRITICAL_THRESHOLD=3
ANOMALY_THRESHOLD=0.8
EOF
    echo "✅ Created .env file. Please edit it with your API keys."
fi

# Create necessary directories
mkdir -p data logs

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container..."
    exec python api.py &
    API_PID=$!
    sleep 5
    exec python log_generator.py &
    GENERATOR_PID=$!
    exec streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
else
    echo "💻 Running in development mode..."
    
    # Check if Python dependencies are installed
    if ! python -c "import streamlit, fastapi, pandas" 2>/dev/null; then
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    # Start API in background
    echo "🔧 Starting API server..."
    python api.py &
    API_PID=$!
    
    # Wait for API to start
    echo "⏳ Waiting for API to start..."
    sleep 5
    
    # Start log generator in background
    echo "📝 Starting log generator..."
    python log_generator.py &
    GENERATOR_PID=$!
    
    # Start Streamlit dashboard
    echo "📊 Starting dashboard..."
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
        echo "✅ All services stopped"
        exit 0
    }
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Start Streamlit
    streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
fi




