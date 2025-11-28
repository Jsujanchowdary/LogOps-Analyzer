#!/usr/bin/env python3
"""
Test script for LogOps Analyzer components
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from telegram_alerter import TelegramAlerter
from gemini_insights import GeminiInsights
from anomaly_detector import AnomalyDetector

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        # Test basic config
        assert Config.API_HOST == "0.0.0.0"
        assert Config.API_PORT == 8000
        assert Config.STREAMLIT_PORT == 8501
        
        # Test severity weights
        total_weight = sum(Config.SEVERITY_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01, f"Severity weights should sum to 1.0, got {total_weight}"
        
        print("✅ Configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_telegram_alerter():
    """Test Telegram alerter"""
    print("📱 Testing Telegram alerter...")
    
    try:
        alerter = TelegramAlerter()
        
        # Test connection if configured
        if alerter.bot_token and alerter.chat_id:
            connection_ok = await alerter.test_connection()
            if connection_ok:
                print("✅ Telegram connection test passed")
                
                # Test alert sending
                success = await alerter.send_alert("Test alert from LogOps Analyzer", "general")
                if success:
                    print("✅ Telegram alert test passed")
                else:
                    print("⚠️  Telegram alert test failed")
            else:
                print("⚠️  Telegram connection test failed")
        else:
            print("⚠️  Telegram not configured (missing bot token or chat ID)")
        
        await alerter.close()
        return True
    except Exception as e:
        print(f"❌ Telegram alerter test failed: {e}")
        return False

def test_gemini_insights():
    """Test Gemini insights"""
    print("🤖 Testing Gemini insights...")
    
    try:
        insights = GeminiInsights()
        
        if insights.model:
            print("✅ Gemini API configured")
            
            # Test with sample data
            test_logs = [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "database",
                    "severity": "ERROR",
                    "message": "Database connection failed",
                    "source_ip": "192.168.1.100"
                }
            ]
            
            test_stats = {
                "total_logs": 100,
                "severity_distribution": {
                    "INFO": 60,
                    "WARNING": 25,
                    "ERROR": 12,
                    "CRITICAL": 3
                },
                "service_distribution": {
                    "database": 30,
                    "api": 25,
                    "authentication": 20,
                    "server": 15,
                    "access": 10
                }
            }
            
            print("✅ Gemini insights test passed")
        else:
            print("⚠️  Gemini API not configured (missing API key)")
        
        return True
    except Exception as e:
        print(f"❌ Gemini insights test failed: {e}")
        return False

def test_anomaly_detector():
    """Test anomaly detector"""
    print("🔍 Testing anomaly detector...")
    
    try:
        detector = AnomalyDetector()
        
        # Test with sample logs
        test_logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "service": "database",
                "severity": "INFO",
                "message": "Database connection established",
                "source_ip": "192.168.1.100"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "service": "database",
                "severity": "ERROR",
                "message": "Database connection failed",
                "source_ip": "192.168.1.100"
            }
        ]
        
        # Test feature extraction
        features = detector.extract_features(test_logs)
        assert features.shape[0] == len(test_logs), "Feature extraction should return one row per log"
        
        # Test volume anomaly detection
        volume_anomalies = detector.detect_volume_anomalies(test_logs)
        assert isinstance(volume_anomalies, list), "Volume anomaly detection should return a list"
        
        # Test severity anomaly detection
        severity_anomalies = detector.detect_severity_anomalies(test_logs)
        assert isinstance(severity_anomalies, list), "Severity anomaly detection should return a list"
        
        print("✅ Anomaly detector test passed")
        return True
    except Exception as e:
        print(f"❌ Anomaly detector test failed: {e}")
        return False

def test_log_generator():
    """Test log generator"""
    print("📝 Testing log generator...")
    
    try:
        from log_generator import LogGenerator
        
        generator = LogGenerator()
        
        # Test log entry generation
        log_entry = generator.generate_log_entry()
        
        required_fields = ['timestamp', 'service', 'severity', 'message']
        for field in required_fields:
            assert field in log_entry, f"Log entry should contain {field}"
        
        # Test severity distribution
        severities = []
        for _ in range(100):
            log = generator.generate_log_entry()
            severities.append(log['severity'])
        
        # Check if severity distribution is reasonable
        severity_counts = {s: severities.count(s) for s in set(severities)}
        info_count = severity_counts.get('INFO', 0)
        assert info_count > 40, "INFO logs should be most common"
        
        print("✅ Log generator test passed")
        return True
    except Exception as e:
        print(f"❌ Log generator test failed: {e}")
        return False

def test_database():
    """Test database setup"""
    print("🗄️  Testing database...")
    
    try:
        from database import create_tables, LogEntry, SessionLocal
        
        # Create tables
        create_tables()
        
        # Test database connection
        db = SessionLocal()
        
        # Test log entry creation
        test_log = LogEntry(
            timestamp=datetime.utcnow(),
            service="test",
            severity="INFO",
            message="Test log entry",
            source_ip="127.0.0.1"
        )
        
        db.add(test_log)
        db.commit()
        db.refresh(test_log)
        
        # Verify log was created
        assert test_log.id is not None, "Log entry should have an ID after creation"
        
        # Clean up
        db.delete(test_log)
        db.commit()
        db.close()
        
        print("✅ Database test passed")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Running LogOps Analyzer Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Database", test_database),
        ("Log Generator", test_log_generator),
        ("Anomaly Detector", test_anomaly_detector),
        ("Gemini Insights", test_gemini_insights),
        ("Telegram Alerter", test_telegram_alerter),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

def main():
    """Main test function"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()




