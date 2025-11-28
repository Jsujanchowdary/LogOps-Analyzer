# LogOps Analyzer

**LogOps Analyzer** is a real-time log ingestion, analysis, and monitoring system powered by AI. It leverages **Google Gemini** for intelligent insights, **FastAPI** for high-performance log ingestion, and **Streamlit** for an interactive dashboard. The system is designed to detect anomalies, visualize log patterns, and send alerts via Telegram.

## 🚀 Features

-   **Real-time Log Ingestion**: High-throughput API for ingesting logs (single or batch).
-   **AI-Powered Insights**: Utilizes Google Gemini to analyze log patterns, explain anomalies, and suggest optimizations.
-   **Anomaly Detection**: Multi-layered detection using:
    -   **Isolation Forest** for pattern anomalies.
    -   **Statistical Analysis** for volume spikes and severity shifts.
    -   **Service-specific** error rate monitoring.
-   **Interactive Dashboard**:
    -   Real-time metrics (Error Rate, Critical Rate, Health Score).
    -   Visualizations (Severity Distribution, Service Volume, Timeline).
    -   Searchable log table.
-   **Alerting System**: Instant notifications via Telegram for critical events and high error rates.
-   **Containerized**: Fully Dockerized for easy deployment.

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
-   **Frontend**: Streamlit, Plotly
-   **AI/ML**: Google Gemini Pro, Scikit-learn (Isolation Forest, DBSCAN)
-   **Database**: SQLite (default), extensible to PostgreSQL
-   **DevOps**: Docker, Docker Compose

## 📋 Prerequisites

-   Docker & Docker Compose
-   Python 3.9+ (for local development)
-   Google Gemini API Key
-   Telegram Bot Token & Chat ID

## ⚙️ Installation & Setup

### Option 1: Using Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd log-test
    ```

2.  **Configure Environment Variables**:
    Create a `.env` file in the root directory:
    ```bash
    GEMINI_API_KEY=your_gemini_api_key
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_telegram_chat_id
    ```

3.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```

4.  **Access the Application**:
    -   **Dashboard**: [http://localhost:8501](http://localhost:8501)
    -   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Local Development

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Environment Variables**:
    Export the required variables in your terminal or use a `.env` file.

3.  **Run the API**:
    ```bash
    uvicorn api:app --reload --port 8000
    ```

4.  **Run the Dashboard**:
    ```bash
    streamlit run dashboard.py
    ```

## 🔌 API Usage

### Ingest Logs
**POST** `/api/logs`

```json
{
  "logs": [
    {
      "service": "auth-service",
      "severity": "ERROR",
      "message": "Invalid credentials provided",
      "timestamp": "2023-11-28T10:00:00Z",
      "metadata": {"user_id": "12345"}
    }
  ]
}
```

### Health Check
**GET** `/health`

## 📊 Dashboard

The Streamlit dashboard provides a comprehensive view of your system's health:
-   **Metrics**: View total logs, error rates, and a calculated "Health Score".
-   **Charts**: Analyze log distribution by severity and service.
-   **AI Insights**: Click on the "AI Insights" tabs to get explanations for anomalies and optimization tips.

## 📂 Project Structure

```
.
├── api.py                 # FastAPI backend
├── dashboard.py           # Streamlit dashboard
├── anomaly_detector.py    # ML-based anomaly detection logic
├── gemini_insights.py     # Gemini AI integration
├── telegram_alerter.py    # Telegram alerting service
├── database.py            # Database models and connection
├── config.py              # Configuration management
├── docker-compose.yml     # Docker orchestration
└── requirements.txt       # Python dependencies
```

## 👤 Author

**Jujjavarapu Sujan Chowdary**

---
*Built with ❤️ using Python and AI.*
