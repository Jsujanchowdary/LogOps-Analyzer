# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Expose ports
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting LogOps Analyzer..."\n\
\n\
# Start API in background\n\
python api.py &\n\
API_PID=$!\n\
\n\
# Wait for API to start\n\
sleep 5\n\
\n\
# Start log generator in background\n\
python log_generator.py &\n\
GENERATOR_PID=$!\n\
\n\
# Start Streamlit dashboard\n\
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true\n\
\n\
# Cleanup on exit\n\
trap "kill $API_PID $GENERATOR_PID" EXIT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["/app/start.sh"]




