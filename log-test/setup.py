#!/usr/bin/env python3
"""
Setup script for LogOps Analyzer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'ssl']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file from template"""
    env_content = """# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Application Configuration
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./logs.db
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501

# Alerting Configuration
ERROR_THRESHOLD=10
CRITICAL_THRESHOLD=5
ANOMALY_THRESHOLD=0.8
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("ℹ️  .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def check_docker():
    """Check if Docker is installed and running"""
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        print("✅ Docker and Docker Compose are available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker or Docker Compose not found")
        print("   Please install Docker and Docker Compose to use containerized deployment")
        return False

def create_startup_scripts():
    """Create startup scripts"""
    
    # Development startup script
    dev_script = """#!/bin/bash
echo "Starting LogOps Analyzer in development mode..."

# Start API in background
python api.py &
API_PID=$!

# Wait for API to start
sleep 5

# Start log generator in background
python log_generator.py &
GENERATOR_PID=$!

# Start Streamlit dashboard
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0

# Cleanup on exit
trap "kill $API_PID $GENERATOR_PID" EXIT
"""
    
    with open('start_dev.sh', 'w') as f:
        f.write(dev_script)
    os.chmod('start_dev.sh', 0o755)
    print("✅ Created start_dev.sh")
    
    # Production startup script
    prod_script = """#!/bin/bash
echo "Starting LogOps Analyzer in production mode..."

# Build and start with Docker Compose
docker-compose up --build -d

echo "LogOps Analyzer is starting..."
echo "API: http://localhost:8000"
echo "Dashboard: http://localhost:8501"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
"""
    
    with open('start_prod.sh', 'w') as f:
        f.write(prod_script)
    os.chmod('start_prod.sh', 0o755)
    print("✅ Created start_prod.sh")

def create_readme():
    """Create README.md file"""
    readme_content = """# LogOps Analyzer

A comprehensive log monitoring and analysis system with real-time insights, anomaly detection, and AI-powered recommendations.

## Features

- 🔄 **Real-time Log Ingestion**: Continuously collect logs from various services
- 📊 **Interactive Dashboard**: Beautiful Streamlit dashboard with visualizations
- 🤖 **AI-Powered Insights**: Gemini LLM integration for intelligent analysis
- 🔍 **Anomaly Detection**: Machine learning-based anomaly detection
- 🚨 **Telegram Alerts**: Real-time notifications via Telegram bot
- 🐳 **Docker Support**: Easy deployment with Docker and docker-compose
- 📈 **Log Simulation**: Realistic log generator for testing

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Gemini API key
- Telegram Bot token and chat ID

### Setup

1. **Clone and setup**:
   ```bash
   python setup.py
   ```

2. **Configure environment**:
   Edit `.env` file with your API keys:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

3. **Start the application**:

   **Development mode**:
   ```bash
   ./start_dev.sh
   ```

   **Production mode**:
   ```bash
   ./start_prod.sh
   ```

4. **Access the dashboard**:
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key for AI insights | Required |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for alerts | Required |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for alerts | Required |
| `LOG_LEVEL` | Logging level | INFO |
| `ERROR_THRESHOLD` | Error count threshold for alerts | 10 |
| `CRITICAL_THRESHOLD` | Critical count threshold for alerts | 5 |
| `ANOMALY_THRESHOLD` | Anomaly detection confidence threshold | 0.8 |

### Log Generation

The system includes a realistic log generator that creates logs with:
- 60% INFO logs
- 25% WARNING logs
- 12% ERROR logs
- 3% CRITICAL logs

Services include: database, authentication, access, server, api, cache, queue, storage, monitoring.

## API Endpoints

- `GET /health` - Health check
- `POST /api/logs` - Ingest log batch
- `POST /api/log` - Ingest single log
- `GET /api/logs` - Retrieve logs with filtering
- `GET /api/logs/stats` - Get log statistics

## Docker Deployment

### Basic Deployment
```bash
docker-compose up -d
```

### With Additional Services
```bash
# With Redis caching
docker-compose --profile cache up -d

# With PostgreSQL database
docker-compose --profile database up -d

# Production setup with Nginx
docker-compose --profile production up -d
```

## Development

### Running Individual Components

1. **API Server**:
   ```bash
   python api.py
   ```

2. **Log Generator**:
   ```bash
   python log_generator.py
   ```

3. **Dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

### Testing

Test individual components:
```bash
# Test Telegram alerts
python -c "import asyncio; from telegram_alerter import TelegramAlerter; asyncio.run(TelegramAlerter().test_connection())"

# Test Gemini insights
python -c "import asyncio; from gemini_insights import GeminiInsights; print('Gemini configured:', GeminiInsights().model is not None)"
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Log Generator │───▶│   FastAPI       │───▶│   SQLite DB     │
│                 │    │   Backend       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Anomaly        │
                       │  Detection      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Telegram       │    │  Gemini LLM     │
                       │  Alerts         │    │  Insights       │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Streamlit      │
                       │  Dashboard      │
                       └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at http://localhost:8000/docs
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created README.md")

def main():
    """Main setup function"""
    print("🚀 Setting up LogOps Analyzer...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create environment file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return False
    
    # Check Docker
    docker_available = check_docker()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Create README
    create_readme()
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("")
    print("Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run ./start_dev.sh for development")
    if docker_available:
        print("3. Run ./start_prod.sh for production")
    print("")
    print("Dashboard will be available at: http://localhost:8501")
    print("API will be available at: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




