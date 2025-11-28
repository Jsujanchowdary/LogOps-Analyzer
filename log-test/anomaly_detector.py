import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import asyncio
from config import Config

class AnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42
        )
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.is_fitted = False
        
        # Historical data for baseline
        self.historical_data = []
        self.baseline_stats = {}

    def extract_features(self, logs: List[Dict]) -> np.ndarray:
        """Extract numerical features from logs for anomaly detection"""
        features = []
        
        for log in logs:
            feature_vector = []
            
            # Time-based features
            timestamp = datetime.fromisoformat(log["timestamp"])
            feature_vector.extend([
                timestamp.hour,  # Hour of day
                timestamp.weekday(),  # Day of week
                timestamp.minute,  # Minute of hour
            ])
            
            # Severity encoding
            severity_map = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
            feature_vector.append(severity_map.get(log["severity"], 0))
            
            # Service encoding (simple hash)
            service_hash = hash(log["service"]) % 100
            feature_vector.append(service_hash)
            
            # Message length
            feature_vector.append(len(log["message"]))
            
            # IP address features (if available)
            if log.get("source_ip"):
                ip_parts = log["source_ip"].split(".")
                if len(ip_parts) == 4:
                    feature_vector.extend([int(part) for part in ip_parts])
                else:
                    feature_vector.extend([0, 0, 0, 0])
            else:
                feature_vector.extend([0, 0, 0, 0])
            
            # User ID features (if available)
            if log.get("user_id"):
                user_hash = hash(log["user_id"]) % 1000
                feature_vector.append(user_hash)
            else:
                feature_vector.append(0)
            
            features.append(feature_vector)
        
        return np.array(features)

    def detect_volume_anomalies(self, logs: List[Dict], window_minutes: int = 60) -> List[Dict]:
        """Detect anomalies in log volume patterns"""
        anomalies = []
        
        if len(logs) < 10:  # Need minimum data for analysis
            return anomalies
        
        # Group logs by time windows
        time_windows = {}
        for log in logs:
            timestamp = datetime.fromisoformat(log["timestamp"])
            window_key = timestamp.replace(minute=0, second=0, microsecond=0)
            if window_key not in time_windows:
                time_windows[window_key] = []
            time_windows[window_key].append(log)
        
        # Calculate volume statistics
        volumes = [len(window_logs) for window_logs in time_windows.values()]
        if len(volumes) < 3:
            return anomalies
        
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        # Detect volume spikes
        for window_time, window_logs in time_windows.items():
            volume = len(window_logs)
            z_score = (volume - mean_volume) / std_volume if std_volume > 0 else 0
            
            if z_score > 2.5:  # Volume spike threshold
                anomalies.append({
                    "type": "volume_spike",
                    "timestamp": window_time.isoformat(),
                    "severity": "WARNING",
                    "description": f"Log volume spike detected: {volume} logs (normal: {mean_volume:.1f} ± {std_volume:.1f})",
                    "confidence_score": min(z_score / 5.0, 1.0),
                    "affected_service": "multiple",
                    "metadata": {
                        "volume": volume,
                        "mean_volume": mean_volume,
                        "std_volume": std_volume,
                        "z_score": z_score
                    }
                })
        
        return anomalies

    def detect_severity_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect anomalies in severity patterns"""
        anomalies = []
        
        if len(logs) < 20:
            return anomalies
        
        # Count severities
        severity_counts = {}
        for log in logs:
            severity = log["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        total_logs = len(logs)
        
        # Check for unusual error rates
        error_rate = severity_counts.get("ERROR", 0) / total_logs
        critical_rate = severity_counts.get("CRITICAL", 0) / total_logs
        
        # Expected rates based on configuration
        expected_error_rate = Config.SEVERITY_WEIGHTS.get("ERROR", 0.12)
        expected_critical_rate = Config.SEVERITY_WEIGHTS.get("CRITICAL", 0.03)
        
        if error_rate > expected_error_rate * 2:  # Double the expected rate
            anomalies.append({
                "type": "high_error_rate",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "WARNING",
                "description": f"High error rate detected: {error_rate:.2%} (expected: {expected_error_rate:.2%})",
                "confidence_score": min(error_rate / expected_error_rate, 1.0),
                "affected_service": "multiple",
                "metadata": {
                    "error_rate": error_rate,
                    "expected_error_rate": expected_error_rate,
                    "error_count": severity_counts.get("ERROR", 0),
                    "total_logs": total_logs
                }
            })
        
        if critical_rate > expected_critical_rate * 3:  # Triple the expected rate
            anomalies.append({
                "type": "high_critical_rate",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "CRITICAL",
                "description": f"High critical rate detected: {critical_rate:.2%} (expected: {expected_critical_rate:.2%})",
                "confidence_score": min(critical_rate / expected_critical_rate, 1.0),
                "affected_service": "multiple",
                "metadata": {
                    "critical_rate": critical_rate,
                    "expected_critical_rate": expected_critical_rate,
                    "critical_count": severity_counts.get("CRITICAL", 0),
                    "total_logs": total_logs
                }
            })
        
        return anomalies

    def detect_service_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect anomalies in service-specific patterns"""
        anomalies = []
        
        if len(logs) < 20:
            return anomalies
        
        # Group logs by service
        service_logs = {}
        for log in logs:
            service = log["service"]
            if service not in service_logs:
                service_logs[service] = []
            service_logs[service].append(log)
        
        # Analyze each service
        for service, service_log_list in service_logs.items():
            if len(service_log_list) < 5:
                continue
            
            # Check for service-specific error patterns
            error_count = sum(1 for log in service_log_list if log["severity"] == "ERROR")
            critical_count = sum(1 for log in service_log_list if log["severity"] == "CRITICAL")
            
            total_service_logs = len(service_log_list)
            service_error_rate = error_count / total_service_logs
            service_critical_rate = critical_count / total_service_logs
            
            # Service-specific thresholds
            if service_error_rate > 0.3:  # 30% error rate for a service
                anomalies.append({
                    "type": "service_error_spike",
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "WARNING",
                    "description": f"High error rate in {service} service: {service_error_rate:.2%}",
                    "confidence_score": min(service_error_rate, 1.0),
                    "affected_service": service,
                    "metadata": {
                        "service": service,
                        "error_rate": service_error_rate,
                        "error_count": error_count,
                        "total_logs": total_service_logs
                    }
                })
            
            if service_critical_rate > 0.1:  # 10% critical rate for a service
                anomalies.append({
                    "type": "service_critical_spike",
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "CRITICAL",
                    "description": f"High critical rate in {service} service: {service_critical_rate:.2%}",
                    "confidence_score": min(service_critical_rate, 1.0),
                    "affected_service": service,
                    "metadata": {
                        "service": service,
                        "critical_rate": service_critical_rate,
                        "critical_count": critical_count,
                        "total_logs": total_service_logs
                    }
                })
        
        return anomalies

    def detect_pattern_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect anomalies using machine learning patterns"""
        anomalies = []
        
        if len(logs) < 50:  # Need more data for ML-based detection
            return anomalies
        
        try:
            # Extract features
            features = self.extract_features(logs)
            
            # Standardize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Fit isolation forest if not already fitted
            if not self.is_fitted:
                self.isolation_forest.fit(features_scaled)
                self.is_fitted = True
            
            # Predict anomalies
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            anomaly_predictions = self.isolation_forest.predict(features_scaled)
            
            # Identify anomalous logs
            for i, (log, score, prediction) in enumerate(zip(logs, anomaly_scores, anomaly_predictions)):
                if prediction == -1:  # Anomaly detected
                    confidence = abs(score) / 2.0  # Normalize confidence score
                    
                    anomalies.append({
                        "type": "pattern_anomaly",
                        "timestamp": log["timestamp"],
                        "severity": "WARNING",
                        "description": f"Unusual log pattern detected in {log['service']} service",
                        "confidence_score": min(confidence, 1.0),
                        "affected_service": log["service"],
                        "metadata": {
                            "service": log["service"],
                            "severity": log["severity"],
                            "anomaly_score": score,
                            "message_preview": log["message"][:100]
                        }
                    })
        
        except Exception as e:
            print(f"Error in pattern anomaly detection: {e}")
        
        return anomalies

    async def detect_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Main anomaly detection method that combines all detection techniques"""
        all_anomalies = []
        
        if not logs:
            return all_anomalies
        
        try:
            # Run different anomaly detection methods
            volume_anomalies = self.detect_volume_anomalies(logs)
            severity_anomalies = self.detect_severity_anomalies(logs)
            service_anomalies = self.detect_service_anomalies(logs)
            pattern_anomalies = self.detect_pattern_anomalies(logs)
            
            # Combine all anomalies
            all_anomalies.extend(volume_anomalies)
            all_anomalies.extend(severity_anomalies)
            all_anomalies.extend(service_anomalies)
            all_anomalies.extend(pattern_anomalies)
            
            # Filter by confidence threshold
            filtered_anomalies = [
                anomaly for anomaly in all_anomalies 
                if anomaly["confidence_score"] >= Config.ANOMALY_THRESHOLD
            ]
            
            return filtered_anomalies
            
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return []

    def update_baseline(self, logs: List[Dict]):
        """Update baseline statistics with new log data"""
        try:
            # Add to historical data
            self.historical_data.extend(logs)
            
            # Keep only recent data (last 1000 logs)
            if len(self.historical_data) > 1000:
                self.historical_data = self.historical_data[-1000:]
            
            # Update baseline statistics
            if len(self.historical_data) >= 100:
                # Calculate baseline severity distribution
                severity_counts = {}
                for log in self.historical_data:
                    severity = log["severity"]
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                total = len(self.historical_data)
                self.baseline_stats = {
                    severity: count / total 
                    for severity, count in severity_counts.items()
                }
                
        except Exception as e:
            print(f"Error updating baseline: {e}")




