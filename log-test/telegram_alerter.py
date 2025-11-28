import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional
from config import Config

class TelegramAlerter:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None
        
        # Rate limiting
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes cooldown between similar alerts

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("Telegram bot token or chat ID not configured")
            return False
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("ok", False)
                else:
                    print(f"Telegram API error: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def _format_alert_message(self, alert_type: str, details: Dict) -> str:
        """Format alert message for Telegram"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Emoji mapping for different alert types
        emoji_map = {
            "error_spike": "🚨",
            "critical_spike": "🔴",
            "volume_spike": "📈",
            "service_down": "⚠️",
            "anomaly": "🔍",
            "high_error_rate": "❌",
            "high_critical_rate": "💥"
        }
        
        emoji = emoji_map.get(alert_type, "⚠️")
        
        # Base message
        message = f"{emoji} *LogOps Alert*\n"
        message += f"🕐 Time: `{timestamp}`\n"
        message += f"📊 Type: `{alert_type.replace('_', ' ').title()}`\n"
        
        # Add specific details based on alert type
        if alert_type == "error_spike":
            message += f"❌ Error Count: `{details.get('error_count', 'N/A')}`\n"
            message += f"📈 Threshold: `{details.get('threshold', 'N/A')}`\n"
            
        elif alert_type == "critical_spike":
            message += f"💥 Critical Count: `{details.get('critical_count', 'N/A')}`\n"
            message += f"📈 Threshold: `{details.get('threshold', 'N/A')}`\n"
            
        elif alert_type == "volume_spike":
            message += f"📊 Volume: `{details.get('volume', 'N/A')}` logs\n"
            message += f"📈 Normal: `{details.get('normal_volume', 'N/A')}` ± `{details.get('std_volume', 'N/A')}`\n"
            message += f"📊 Z-Score: `{details.get('z_score', 'N/A')}`\n"
            
        elif alert_type == "service_down":
            message += f"🔧 Service: `{details.get('service', 'N/A')}`\n"
            message += f"⏱️ Downtime: `{details.get('downtime', 'N/A')}`\n"
            
        elif alert_type == "anomaly":
            message += f"🔍 Confidence: `{details.get('confidence', 'N/A')}`\n"
            message += f"🔧 Service: `{details.get('service', 'N/A')}`\n"
            message += f"📝 Description: `{details.get('description', 'N/A')}`\n"
            
        elif alert_type in ["high_error_rate", "high_critical_rate"]:
            message += f"📊 Rate: `{details.get('rate', 'N/A')}`\n"
            message += f"📈 Expected: `{details.get('expected_rate', 'N/A')}`\n"
            message += f"🔧 Service: `{details.get('service', 'N/A')}`\n"
        
        # Add common details
        if details.get('affected_services'):
            services = ', '.join(details['affected_services'])
            message += f"🔧 Affected Services: `{services}`\n"
        
        if details.get('recommendation'):
            message += f"\n💡 *Recommendation:*\n`{details['recommendation']}`\n"
        
        # Add footer
        message += f"\n🔗 *LogOps Analyzer* - Real-time monitoring"
        
        return message

    def _should_send_alert(self, alert_type: str, details: Dict) -> bool:
        """Check if alert should be sent based on cooldown and rate limiting"""
        alert_key = f"{alert_type}_{details.get('service', 'global')}"
        current_time = datetime.utcnow().timestamp()
        
        if alert_key in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[alert_key]
            if time_since_last < self.alert_cooldown:
                return False
        
        self.last_alert_time[alert_key] = current_time
        return True

    async def send_alert(self, message: str, alert_type: str = "general", details: Dict = None) -> bool:
        """Send an alert to Telegram"""
        if details is None:
            details = {}
        
        # Check rate limiting
        if not self._should_send_alert(alert_type, details):
            print(f"Alert {alert_type} suppressed due to rate limiting")
            return False
        
        # Format message
        if alert_type != "general":
            formatted_message = self._format_alert_message(alert_type, details)
        else:
            formatted_message = f"⚠️ *LogOps Alert*\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n{message}"
        
        # Send message
        success = await self._send_message(formatted_message)
        
        if success:
            print(f"Alert sent successfully: {alert_type}")
        else:
            print(f"Failed to send alert: {alert_type}")
        
        return success

    async def send_error_spike_alert(self, error_count: int, threshold: int, services: List[str] = None) -> bool:
        """Send alert for error spike"""
        details = {
            "error_count": error_count,
            "threshold": threshold,
            "affected_services": services or ["multiple"]
        }
        return await self.send_alert("", "error_spike", details)

    async def send_critical_spike_alert(self, critical_count: int, threshold: int, services: List[str] = None) -> bool:
        """Send alert for critical spike"""
        details = {
            "critical_count": critical_count,
            "threshold": threshold,
            "affected_services": services or ["multiple"]
        }
        return await self.send_alert("", "critical_spike", details)

    async def send_volume_spike_alert(self, volume: int, normal_volume: float, std_volume: float, z_score: float) -> bool:
        """Send alert for volume spike"""
        details = {
            "volume": volume,
            "normal_volume": f"{normal_volume:.1f}",
            "std_volume": f"{std_volume:.1f}",
            "z_score": f"{z_score:.2f}"
        }
        return await self.send_alert("", "volume_spike", details)

    async def send_service_down_alert(self, service: str, downtime_minutes: int) -> bool:
        """Send alert for service down"""
        details = {
            "service": service,
            "downtime": f"{downtime_minutes} minutes"
        }
        return await self.send_alert("", "service_down", details)

    async def send_anomaly_alert(self, anomaly_type: str, confidence: float, service: str, description: str) -> bool:
        """Send alert for detected anomaly"""
        details = {
            "confidence": f"{confidence:.2f}",
            "service": service,
            "description": description
        }
        return await self.send_alert("", "anomaly", details)

    async def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily summary report"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        
        message = f"📊 *Daily Log Summary - {timestamp}*\n\n"
        
        # Total logs
        total_logs = stats.get("total_logs", 0)
        message += f"📈 Total Logs: `{total_logs:,}`\n"
        
        # Severity breakdown
        severity_dist = stats.get("severity_distribution", {})
        if severity_dist:
            message += "\n📊 *Severity Distribution:*\n"
            for severity, count in severity_dist.items():
                percentage = (count / total_logs * 100) if total_logs > 0 else 0
                emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "💥"}.get(severity, "📝")
                message += f"{emoji} {severity}: `{count:,}` ({percentage:.1f}%)\n"
        
        # Service breakdown
        service_dist = stats.get("service_distribution", {})
        if service_dist:
            message += "\n🔧 *Top Services:*\n"
            sorted_services = sorted(service_dist.items(), key=lambda x: x[1], reverse=True)[:5]
            for service, count in sorted_services:
                percentage = (count / total_logs * 100) if total_logs > 0 else 0
                message += f"🔧 {service}: `{count:,}` ({percentage:.1f}%)\n"
        
        # Anomalies detected
        anomalies = stats.get("anomalies_detected", 0)
        if anomalies > 0:
            message += f"\n🔍 Anomalies Detected: `{anomalies}`\n"
        
        # Health status
        error_rate = (severity_dist.get("ERROR", 0) / total_logs * 100) if total_logs > 0 else 0
        critical_rate = (severity_dist.get("CRITICAL", 0) / total_logs * 100) if total_logs > 0 else 0
        
        if critical_rate > 1:
            message += "\n🔴 *Status: Critical Issues Detected*\n"
        elif error_rate > 5:
            message += "\n⚠️ *Status: High Error Rate*\n"
        else:
            message += "\n✅ *Status: Healthy*\n"
        
        message += "\n🔗 *LogOps Analyzer* - Daily Report"
        
        return await self._send_message(message)

    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.bot_token or not self.chat_id:
            print("Telegram configuration missing")
            return False
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/getMe"
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        bot_info = result.get("result", {})
                        print(f"Telegram bot connected: @{bot_info.get('username', 'unknown')}")
                        return True
                    else:
                        print("Telegram bot connection failed")
                        return False
                else:
                    print(f"Telegram API error: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"Error testing Telegram connection: {e}")
            return False

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Example usage and testing
async def main():
    """Test the Telegram alerter"""
    alerter = TelegramAlerter()
    
    # Test connection
    if await alerter.test_connection():
        print("Telegram connection successful")
        
        # Test different alert types
        await alerter.send_alert("Test alert from LogOps Analyzer", "general")
        await alerter.send_error_spike_alert(15, 10, ["database", "api"])
        await alerter.send_volume_spike_alert(1000, 500, 100, 5.0)
        
        # Test daily summary
        test_stats = {
            "total_logs": 10000,
            "severity_distribution": {
                "INFO": 6000,
                "WARNING": 2500,
                "ERROR": 1200,
                "CRITICAL": 300
            },
            "service_distribution": {
                "database": 3000,
                "api": 2500,
                "authentication": 2000,
                "server": 1500,
                "access": 1000
            },
            "anomalies_detected": 5
        }
        await alerter.send_daily_summary(test_stats)
    
    await alerter.close()

if __name__ == "__main__":
    asyncio.run(main())




