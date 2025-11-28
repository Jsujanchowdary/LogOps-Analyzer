from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio
from database import get_db, LogEntry, create_tables
from config import Config
from anomaly_detector import AnomalyDetector
from telegram_alerter import TelegramAlerter

# Create FastAPI app
app = FastAPI(
    title="LogOps Analyzer API",
    description="API for log ingestion, analysis, and monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
anomaly_detector = AnomalyDetector()
telegram_alerter = TelegramAlerter()

# Pydantic models
class LogEntryRequest(BaseModel):
    timestamp: Optional[str] = None
    service: str
    severity: str
    message: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict] = None

class LogBatchRequest(BaseModel):
    logs: List[LogEntryRequest]

class LogResponse(BaseModel):
    id: int
    timestamp: str
    service: str
    severity: str
    message: str
    source_ip: Optional[str]
    user_id: Optional[str]
    request_id: Optional[str]
    metadata: Dict

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    create_tables()
    print("Database tables created")
    print("LogOps Analyzer API started")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Log ingestion endpoint
@app.post("/api/logs", response_model=Dict)
async def ingest_logs(
    log_batch: LogBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Ingest a batch of logs"""
    try:
        # Process each log entry
        processed_logs = []
        for log_data in log_batch.logs:
            # Create log entry
            log_entry = LogEntry(
                timestamp=datetime.fromisoformat(log_data.timestamp) if log_data.timestamp else datetime.utcnow(),
                service=log_data.service,
                severity=log_data.severity,
                message=log_data.message,
                source_ip=log_data.source_ip,
                user_id=log_data.user_id,
                request_id=log_data.request_id,
                log_metadata=json.dumps(log_data.metadata) if log_data.metadata else None
            )
            
            db.add(log_entry)
            processed_logs.append(log_entry)
        
        # Commit to database
        db.commit()
        
        # Refresh to get IDs
        for log_entry in processed_logs:
            db.refresh(log_entry)
        
        # Background tasks for analysis and alerting
        background_tasks.add_task(analyze_logs_for_anomalies, [log.to_dict() for log in processed_logs])
        background_tasks.add_task(check_alert_conditions, [log.to_dict() for log in processed_logs])
        
        return {
            "status": "success",
            "processed_logs": len(processed_logs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process logs: {str(e)}")

# Single log ingestion endpoint
@app.post("/api/log", response_model=LogResponse)
async def ingest_single_log(
    log_data: LogEntryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Ingest a single log entry"""
    try:
        # Create log entry
        log_entry = LogEntry(
            timestamp=datetime.fromisoformat(log_data.timestamp) if log_data.timestamp else datetime.utcnow(),
            service=log_data.service,
            severity=log_data.severity,
            message=log_data.message,
            source_ip=log_data.source_ip,
            user_id=log_data.user_id,
            request_id=log_data.request_id,
            log_metadata=json.dumps(log_data.metadata) if log_data.metadata else None
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        # Background tasks
        background_tasks.add_task(analyze_logs_for_anomalies, [log_entry.to_dict()])
        background_tasks.add_task(check_alert_conditions, [log_entry.to_dict()])
        
        return LogResponse(**log_entry.to_dict())
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process log: {str(e)}")

# Get logs endpoint
@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(
    limit: int = 100,
    offset: int = 0,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get logs with optional filtering"""
    try:
        query = db.query(LogEntry)
        
        # Apply filters
        if service:
            query = query.filter(LogEntry.service == service)
        if severity:
            query = query.filter(LogEntry.severity == severity)
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(LogEntry.timestamp >= start_dt)
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(LogEntry.timestamp <= end_dt)
        
        # Apply pagination and ordering
        logs = query.order_by(LogEntry.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [LogResponse(**log.to_dict()) for log in logs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

# Get log statistics endpoint
@app.get("/api/logs/stats")
async def get_log_stats(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get log statistics for the specified time period"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get logs in time range (limit to prevent memory issues)
        logs = db.query(LogEntry).filter(
            LogEntry.timestamp >= start_time,
            LogEntry.timestamp <= end_time
        ).limit(10000).all()  # Limit to 10k logs max
        
        # Calculate statistics
        total_logs = len(logs)
        severity_counts = {}
        service_counts = {}
        hourly_counts = {}
        
        for log in logs:
            # Severity counts
            severity_counts[log.severity] = severity_counts.get(log.severity, 0) + 1
            
            # Service counts
            service_counts[log.service] = service_counts.get(log.service, 0) + 1
            
            # Hourly counts
            hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "total_logs": total_logs,
            "severity_distribution": severity_counts,
            "service_distribution": service_counts,
            "hourly_distribution": hourly_counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate statistics: {str(e)}")

# Background task functions
async def analyze_logs_for_anomalies(logs: List[Dict]):
    """Analyze logs for anomalies in background"""
    try:
        anomalies = await anomaly_detector.detect_anomalies(logs)
        if anomalies:
            print(f"Detected {len(anomalies)} anomalies")
            # Here you could store anomalies in database or trigger alerts
    except Exception as e:
        print(f"Error in anomaly detection: {e}")

async def check_alert_conditions(logs: List[Dict]):
    """Check if logs meet alert conditions in background"""
    try:
        # Count errors and critical logs
        error_count = sum(1 for log in logs if log["severity"] == "ERROR")
        critical_count = sum(1 for log in logs if log["severity"] == "CRITICAL")
        
        # Check thresholds
        if error_count >= Config.ERROR_THRESHOLD:
            await telegram_alerter.send_alert(
                f"High error rate detected: {error_count} errors in recent logs"
            )
        
        if critical_count >= Config.CRITICAL_THRESHOLD:
            await telegram_alerter.send_alert(
                f"Critical alerts detected: {critical_count} critical logs in recent batch"
            )
            
    except Exception as e:
        print(f"Error in alert checking: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
