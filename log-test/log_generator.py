import random
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import requests
from config import Config

class LogGenerator:
    def __init__(self):
        self.running = False
        self.api_url = f"http://{Config.API_HOST}:{Config.API_PORT}/api/logs"
        
        # Realistic log templates for different services and severities
        self.log_templates = {
            "database": {
                "INFO": [
                    "Database connection established successfully",
                    "Query executed in {duration}ms",
                    "Connection pool size: {pool_size}",
                    "Database backup completed successfully",
                    "Index optimization completed for table {table}",
                    "Database statistics updated",
                    "Connection from {source_ip} established"
                ],
                "WARNING": [
                    "Slow query detected: {query} took {duration}ms",
                    "Database connection pool at {percentage}% capacity",
                    "Index fragmentation detected on table {table}",
                    "Database backup taking longer than expected",
                    "Connection timeout for user {user_id}",
                    "Database disk usage at {percentage}%"
                ],
                "ERROR": [
                    "Database connection failed: {error}",
                    "Query execution failed: {error}",
                    "Database backup failed: {error}",
                    "Connection pool exhausted",
                    "Database disk space critical",
                    "Transaction rollback due to deadlock"
                ],
                "CRITICAL": [
                    "Database server unreachable",
                    "Database corruption detected",
                    "Critical data loss detected",
                    "Database cluster split-brain detected"
                ]
            },
            "authentication": {
                "INFO": [
                    "User {user_id} logged in successfully",
                    "Authentication token refreshed for user {user_id}",
                    "Password reset request for user {user_id}",
                    "Two-factor authentication enabled for user {user_id}",
                    "Session created for user {user_id}",
                    "User {user_id} logged out"
                ],
                "WARNING": [
                    "Multiple failed login attempts for user {user_id}",
                    "Suspicious login pattern detected for user {user_id}",
                    "Authentication token expired for user {user_id}",
                    "Password reset rate limit exceeded",
                    "Unusual login location for user {user_id}"
                ],
                "ERROR": [
                    "Authentication failed for user {user_id}: {error}",
                    "Token validation failed: {error}",
                    "Password reset failed: {error}",
                    "Session creation failed: {error}",
                    "User account locked: {user_id}"
                ],
                "CRITICAL": [
                    "Authentication service unavailable",
                    "Security breach detected",
                    "Mass account compromise detected",
                    "Authentication database compromised"
                ]
            },
            "access": {
                "INFO": [
                    "API request from {source_ip} to {endpoint}",
                    "File uploaded successfully: {filename}",
                    "Resource accessed: {resource}",
                    "API rate limit: {current}/{limit} requests",
                    "Cache hit for key: {cache_key}",
                    "Request processed in {duration}ms"
                ],
                "WARNING": [
                    "High API usage detected from {source_ip}",
                    "Large file upload detected: {filename} ({size}MB)",
                    "Unusual access pattern detected",
                    "API rate limit approaching for {source_ip}",
                    "Cache miss for frequently accessed key"
                ],
                "ERROR": [
                    "API request failed: {error}",
                    "File upload failed: {error}",
                    "Access denied for resource: {resource}",
                    "API rate limit exceeded for {source_ip}",
                    "Cache service unavailable"
                ],
                "CRITICAL": [
                    "API service unavailable",
                    "File storage service down",
                    "Access control system failure",
                    "Mass unauthorized access detected"
                ]
            },
            "server": {
                "INFO": [
                    "Server started successfully on port {port}",
                    "Health check passed",
                    "Server metrics: CPU {cpu}%, Memory {memory}%",
                    "Server configuration reloaded",
                    "Server maintenance completed",
                    "Load balancer health check passed"
                ],
                "WARNING": [
                    "High CPU usage detected: {cpu}%",
                    "High memory usage detected: {memory}%",
                    "Disk space low: {percentage}% remaining",
                    "Server response time increased: {duration}ms",
                    "Load balancer backend unhealthy"
                ],
                "ERROR": [
                    "Server error: {error}",
                    "Service unavailable: {service}",
                    "Server restart required",
                    "Configuration error: {error}",
                    "Load balancer backend failed"
                ],
                "CRITICAL": [
                    "Server crashed",
                    "Critical service failure",
                    "Server disk full",
                    "Load balancer failure"
                ]
            }
        }
        
        # Additional services
        for service in ["api", "cache", "queue", "storage", "monitoring"]:
            self.log_templates[service] = {
                "INFO": [f"{service.title()} service running normally", f"{service.title()} operation completed"],
                "WARNING": [f"{service.title()} service experiencing delays", f"{service.title()} resource usage high"],
                "ERROR": [f"{service.title()} service error: {{error}}", f"{service.title()} operation failed"],
                "CRITICAL": [f"{service.title()} service down", f"{service.title()} critical failure"]
            }

    def generate_log_entry(self) -> Dict:
        """Generate a single realistic log entry"""
        # Select service and severity based on weights
        service = random.choice(Config.SERVICES)
        severity = self._select_severity()
        
        # Get template and fill it with realistic data
        template = random.choice(self.log_templates[service][severity])
        message = self._fill_template(template, service, severity)
        
        # Generate metadata
        metadata = self._generate_metadata(service, severity)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": service,
            "severity": severity,
            "message": message,
            "source_ip": self._generate_ip(),
            "user_id": self._generate_user_id() if random.random() < 0.7 else None,
            "request_id": self._generate_request_id(),
            "metadata": metadata
        }

    def _select_severity(self) -> str:
        """Select severity based on configured weights"""
        rand = random.random()
        cumulative = 0
        for severity, weight in Config.SEVERITY_WEIGHTS.items():
            cumulative += weight
            if rand <= cumulative:
                return severity
        return "INFO"

    def _fill_template(self, template: str, service: str, severity: str) -> str:
        """Fill template with realistic values"""
        replacements = {
            "duration": random.randint(10, 5000),
            "pool_size": random.randint(10, 100),
            "table": f"table_{random.randint(1, 20)}",
            "percentage": random.randint(60, 95),
            "query": f"SELECT * FROM users WHERE id = {random.randint(1, 10000)}",
            "user_id": f"user_{random.randint(1000, 9999)}",
            "error": random.choice([
                "Connection timeout", "Invalid credentials", "Resource not found",
                "Permission denied", "Internal server error", "Network unreachable"
            ]),
            "source_ip": self._generate_ip(),
            "endpoint": random.choice(["/api/users", "/api/orders", "/api/products", "/api/auth"]),
            "filename": f"file_{random.randint(1, 1000)}.txt",
            "resource": f"/resource/{random.randint(1, 100)}",
            "current": random.randint(1, 100),
            "limit": 100,
            "cache_key": f"cache_{random.randint(1, 1000)}",
            "port": random.choice([3000, 8000, 8080, 9000]),
            "cpu": random.randint(20, 80),
            "memory": random.randint(30, 85),
            "size": random.randint(1, 100)
        }
        
        try:
            return template.format(**replacements)
        except KeyError:
            return template

    def _generate_metadata(self, service: str, severity: str) -> Dict:
        """Generate realistic metadata for the log entry"""
        metadata = {
            "service_version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "environment": random.choice(["production", "staging", "development"]),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
            "instance_id": f"i-{random.randint(10000000, 99999999)}"
        }
        
        if severity in ["ERROR", "CRITICAL"]:
            metadata["error_code"] = f"ERR_{random.randint(1000, 9999)}"
            metadata["stack_trace"] = "Stack trace available in error logs"
        
        return metadata

    def _generate_ip(self) -> str:
        """Generate realistic IP address"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def _generate_user_id(self) -> str:
        """Generate realistic user ID"""
        return f"user_{random.randint(1000, 9999)}"

    def _generate_request_id(self) -> str:
        """Generate realistic request ID"""
        return f"req_{random.randint(100000, 999999)}"

    def send_logs_to_api(self, logs: List[Dict]) -> bool:
        """Send generated logs to the API"""
        try:
            response = requests.post(
                self.api_url,
                json={"logs": logs},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send logs to API: {e}")
            return False

    def generate_logs_batch(self) -> List[Dict]:
        """Generate a batch of logs"""
        batch_size = random.randint(1, Config.MAX_LOGS_PER_BATCH)
        return [self.generate_log_entry() for _ in range(batch_size)]

    def start_generation(self):
        """Start continuous log generation"""
        self.running = True
        print("Starting log generation...")
        
        while self.running:
            try:
                # Generate batch of logs
                logs = self.generate_logs_batch()
                
                # Send to API
                success = self.send_logs_to_api(logs)
                if success:
                    print(f"Generated and sent {len(logs)} logs")
                else:
                    print(f"Failed to send {len(logs)} logs")
                
                # Wait before next batch
                time.sleep(Config.LOG_GENERATION_INTERVAL)
                
            except KeyboardInterrupt:
                print("Log generation stopped by user")
                break
            except Exception as e:
                print(f"Error in log generation: {e}")
                time.sleep(5)  # Wait before retrying

    def stop_generation(self):
        """Stop log generation"""
        self.running = False
        print("Stopping log generation...")

def main():
    """Main function to run log generator"""
    generator = LogGenerator()
    
    try:
        generator.start_generation()
    except KeyboardInterrupt:
        generator.stop_generation()

if __name__ == "__main__":
    main()




