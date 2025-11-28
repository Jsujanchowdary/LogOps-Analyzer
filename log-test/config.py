import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Application Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./logs.db")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Alerting Configuration
    ERROR_THRESHOLD = int(os.getenv("ERROR_THRESHOLD", "10"))
    CRITICAL_THRESHOLD = int(os.getenv("CRITICAL_THRESHOLD", "5"))
    ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.8"))
    
    # Log Generation Configuration
    LOG_GENERATION_INTERVAL = 5  # seconds
    MAX_LOGS_PER_BATCH = 15
    
    # Severity levels and their weights for realistic distribution
    SEVERITY_WEIGHTS = {
        "INFO": 0.80,      # 80% - most logs are info
        "WARNING": 0.12,   # 12% - some warnings
        "ERROR": 0.05,     # 5% - fewer errors
        "CRITICAL": 0.03   # 3% - very few critical
    }
    
    # Service types for log generation
    SERVICES = [
        "database", "authentication", "access", "server", 
        "api", "cache", "queue", "storage", "monitoring"
    ]
