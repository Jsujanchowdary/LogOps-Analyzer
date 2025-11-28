from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from config import Config

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service = Column(String(50), index=True)
    severity = Column(String(20), index=True)
    message = Column(Text)
    source_ip = Column(String(45))
    user_id = Column(String(100))
    request_id = Column(String(100))
    log_metadata = Column(Text)  # JSON string for additional data
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "service": self.service,
            "severity": self.severity,
            "message": self.message,
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "metadata": json.loads(self.log_metadata) if self.log_metadata else {}
        }

class AnomalyDetection(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    anomaly_type = Column(String(50))
    severity = Column(String(20))
    description = Column(Text)
    confidence_score = Column(Float)
    affected_service = Column(String(50))
    anomaly_metadata = Column(Text)

# Database setup
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
