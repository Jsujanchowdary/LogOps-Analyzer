import google.generativeai as genai
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from config import Config

class GeminiInsights:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        else:
            self.model = None
            print("Gemini API key not configured")

    def _format_logs_for_analysis(self, logs: List[Dict], max_logs: int = 100) -> str:
        """Format logs for LLM analysis"""
        if not logs:
            return "No logs available for analysis."
        
        # Limit number of logs to avoid token limits
        logs_to_analyze = logs[:max_logs]
        
        formatted_logs = "Recent Log Entries:\n"
        formatted_logs += "=" * 50 + "\n"
        
        for i, log in enumerate(logs_to_analyze, 1):
            formatted_logs += f"{i}. [{log.get('timestamp', 'N/A')}] "
            formatted_logs += f"{log.get('severity', 'UNKNOWN')} - "
            formatted_logs += f"{log.get('service', 'unknown')}: "
            formatted_logs += f"{log.get('message', 'No message')}\n"
            
            if log.get('source_ip'):
                formatted_logs += f"   Source IP: {log['source_ip']}\n"
            if log.get('user_id'):
                formatted_logs += f"   User ID: {log['user_id']}\n"
            if log.get('metadata'):
                formatted_logs += f"   Metadata: {json.dumps(log['metadata'], indent=2)}\n"
            formatted_logs += "\n"
        
        return formatted_logs

    def _format_statistics_for_analysis(self, stats: Dict) -> str:
        """Format statistics for LLM analysis"""
        if not stats:
            return "No statistics available."
        
        formatted_stats = "Log Statistics:\n"
        formatted_stats += "=" * 30 + "\n"
        
        # Time range
        if 'time_range' in stats:
            time_range = stats['time_range']
            formatted_stats += f"Time Range: {time_range.get('start', 'N/A')} to {time_range.get('end', 'N/A')}\n"
            formatted_stats += f"Duration: {time_range.get('hours', 'N/A')} hours\n\n"
        
        # Total logs
        formatted_stats += f"Total Logs: {stats.get('total_logs', 0):,}\n\n"
        
        # Severity distribution
        severity_dist = stats.get('severity_distribution', {})
        if severity_dist:
            formatted_stats += "Severity Distribution:\n"
            for severity, count in severity_dist.items():
                percentage = (count / stats.get('total_logs', 1)) * 100
                formatted_stats += f"  {severity}: {count:,} ({percentage:.1f}%)\n"
            formatted_stats += "\n"
        
        # Service distribution
        service_dist = stats.get('service_distribution', {})
        if service_dist:
            formatted_stats += "Service Distribution:\n"
            sorted_services = sorted(service_dist.items(), key=lambda x: x[1], reverse=True)
            for service, count in sorted_services:
                percentage = (count / stats.get('total_logs', 1)) * 100
                formatted_stats += f"  {service}: {count:,} ({percentage:.1f}%)\n"
            formatted_stats += "\n"
        
        # Hourly distribution (top 5)
        hourly_dist = stats.get('hourly_distribution', {})
        if hourly_dist:
            formatted_stats += "Peak Hours (Top 5):\n"
            sorted_hours = sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:5]
            for hour, count in sorted_hours:
                formatted_stats += f"  {hour}: {count:,} logs\n"
            formatted_stats += "\n"
        
        return formatted_stats

    async def analyze_log_patterns(self, logs: List[Dict], stats: Dict) -> Dict:
        """Analyze log patterns and provide insights"""
        if not self.model:
            return {"error": "Gemini API not configured"}
        
        try:
            # Format data for analysis
            logs_text = self._format_logs_for_analysis(logs)
            stats_text = self._format_statistics_for_analysis(stats)
            
            # Create prompt for pattern analysis
            prompt = f"""
            As a DevOps engineer and log analysis expert, analyze the following log data and provide insights:

            {stats_text}

            {logs_text}

            Please provide a comprehensive analysis including:

            1. **Overall Health Assessment**: Rate the system health (1-10) and explain why
            2. **Key Patterns**: Identify any notable patterns in the logs
            3. **Potential Issues**: Highlight any concerning trends or anomalies
            4. **Service Performance**: Analyze individual service performance
            5. **Recommendations**: Provide actionable recommendations for improvement
            6. **Risk Assessment**: Identify potential risks and their severity

            Format your response as a structured analysis with clear sections and actionable insights.
            Keep the analysis concise but comprehensive, focusing on the most important findings.
            """
            
            # Generate response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            return {
                "analysis": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "logs_analyzed": len(logs),
                "analysis_type": "pattern_analysis"
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    async def generate_anomaly_insights(self, anomalies: List[Dict], logs: List[Dict]) -> Dict:
        """Generate insights for detected anomalies"""
        if not self.model:
            return {"error": "Gemini API not configured"}
        
        try:
            # Format anomalies for analysis
            anomalies_text = "Detected Anomalies:\n"
            anomalies_text += "=" * 30 + "\n"
            
            for i, anomaly in enumerate(anomalies, 1):
                anomalies_text += f"{i}. Type: {anomaly.get('type', 'Unknown')}\n"
                anomalies_text += f"   Severity: {anomaly.get('severity', 'Unknown')}\n"
                anomalies_text += f"   Service: {anomaly.get('affected_service', 'Unknown')}\n"
                anomalies_text += f"   Confidence: {anomaly.get('confidence_score', 0):.2f}\n"
                anomalies_text += f"   Description: {anomaly.get('description', 'No description')}\n"
                anomalies_text += f"   Timestamp: {anomaly.get('timestamp', 'Unknown')}\n\n"
            
            # Get recent logs for context
            recent_logs = logs[-20:] if logs else []
            logs_text = self._format_logs_for_analysis(recent_logs, 20)
            
            # Create prompt for anomaly analysis
            prompt = f"""
            As a senior DevOps engineer, analyze these detected anomalies and provide actionable insights:

            {anomalies_text}

            Recent Context Logs:
            {logs_text}

            Please provide:

            1. **Anomaly Assessment**: Evaluate the severity and impact of each anomaly
            2. **Root Cause Analysis**: Suggest potential root causes for the anomalies
            3. **Immediate Actions**: Recommend immediate steps to address the issues
            4. **Prevention Strategies**: Suggest ways to prevent similar anomalies
            5. **Monitoring Improvements**: Recommend monitoring enhancements
            6. **Priority Ranking**: Rank the anomalies by urgency and impact

            Focus on practical, actionable advice that a DevOps team can implement immediately.
            """
            
            # Generate response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            return {
                "insights": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "anomalies_analyzed": len(anomalies),
                "analysis_type": "anomaly_insights"
            }
            
        except Exception as e:
            return {"error": f"Anomaly analysis failed: {str(e)}"}

    async def generate_daily_summary(self, stats: Dict, anomalies: List[Dict] = None) -> Dict:
        """Generate a daily summary report"""
        if not self.model:
            return {"error": "Gemini API not configured"}
        
        try:
            # Format statistics
            stats_text = self._format_statistics_for_analysis(stats)
            
            # Format anomalies if provided
            anomalies_text = ""
            if anomalies:
                anomalies_text = f"\nAnomalies Detected: {len(anomalies)}\n"
                for anomaly in anomalies[:5]:  # Top 5 anomalies
                    anomalies_text += f"- {anomaly.get('type', 'Unknown')}: {anomaly.get('description', 'No description')}\n"
            
            # Create prompt for daily summary
            prompt = f"""
            As a DevOps team lead, create a comprehensive daily summary report based on this log data:

            {stats_text}
            {anomalies_text}

            Please provide:

            1. **Executive Summary**: High-level overview of system health and key metrics
            2. **Performance Highlights**: Notable performance achievements or issues
            3. **Incident Summary**: Any incidents, anomalies, or issues that occurred
            4. **Trends Analysis**: Key trends compared to previous periods
            5. **Action Items**: Specific tasks for the team to address
            6. **Recommendations**: Strategic recommendations for system improvement
            7. **Health Score**: Overall system health score (1-10) with justification

            Format this as a professional daily report suitable for both technical and management audiences.
            """
            
            # Generate response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            return {
                "summary": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "report_type": "daily_summary",
                "total_logs": stats.get('total_logs', 0),
                "anomalies_count": len(anomalies) if anomalies else 0
            }
            
        except Exception as e:
            return {"error": f"Daily summary generation failed: {str(e)}"}

    async def suggest_optimizations(self, logs: List[Dict], stats: Dict) -> Dict:
        """Suggest system optimizations based on log analysis"""
        if not self.model:
            return {"error": "Gemini API not configured"}
        
        try:
            # Analyze error patterns
            error_logs = [log for log in logs if log.get('severity') in ['ERROR', 'CRITICAL']]
            warning_logs = [log for log in logs if log.get('severity') == 'WARNING']
            
            # Format error analysis
            error_analysis = f"Error Analysis:\n"
            error_analysis += f"Total Errors: {len(error_logs)}\n"
            error_analysis += f"Total Warnings: {len(warning_logs)}\n"
            
            if error_logs:
                error_analysis += "\nRecent Errors:\n"
                for error in error_logs[-10:]:  # Last 10 errors
                    error_analysis += f"- {error.get('service', 'Unknown')}: {error.get('message', 'No message')}\n"
            
            # Format statistics
            stats_text = self._format_statistics_for_analysis(stats)
            
            # Create prompt for optimization suggestions
            prompt = f"""
            As a senior system architect and performance engineer, analyze this log data and provide optimization recommendations:

            {stats_text}

            {error_analysis}

            Please provide:

            1. **Performance Bottlenecks**: Identify performance bottlenecks and their impact
            2. **Resource Optimization**: Suggest resource allocation improvements
            3. **Error Reduction**: Recommend strategies to reduce error rates
            4. **Monitoring Enhancements**: Suggest monitoring and alerting improvements
            5. **Infrastructure Changes**: Recommend infrastructure or configuration changes
            6. **Code Quality**: Suggest code quality improvements based on error patterns
            7. **Capacity Planning**: Provide capacity planning recommendations
            8. **Cost Optimization**: Suggest ways to optimize costs while maintaining performance

            Focus on practical, implementable recommendations with clear business impact.
            """
            
            # Generate response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            return {
                "recommendations": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_type": "optimization_suggestions",
                "errors_analyzed": len(error_logs),
                "warnings_analyzed": len(warning_logs)
            }
            
        except Exception as e:
            return {"error": f"Optimization analysis failed: {str(e)}"}

    async def explain_anomaly(self, anomaly: Dict, context_logs: List[Dict] = None) -> Dict:
        """Provide detailed explanation of a specific anomaly"""
        if not self.model:
            return {"error": "Gemini API not configured"}
        
        try:
            # Format anomaly details
            anomaly_text = f"""
            Anomaly Details:
            Type: {anomaly.get('type', 'Unknown')}
            Severity: {anomaly.get('severity', 'Unknown')}
            Service: {anomaly.get('affected_service', 'Unknown')}
            Confidence: {anomaly.get('confidence_score', 0):.2f}
            Description: {anomaly.get('description', 'No description')}
            Timestamp: {anomaly.get('timestamp', 'Unknown')}
            """
            
            if anomaly.get('metadata'):
                anomaly_text += f"\nMetadata: {json.dumps(anomaly['metadata'], indent=2)}"
            
            # Add context logs if provided
            context_text = ""
            if context_logs:
                context_text = "\n\nContext Logs (around the time of anomaly):\n"
                context_text += self._format_logs_for_analysis(context_logs, 20)
            
            # Create prompt for anomaly explanation
            prompt = f"""
            As a senior incident response engineer, provide a detailed analysis of this anomaly:

            {anomaly_text}
            {context_text}

            Please provide:

            1. **Anomaly Explanation**: What this anomaly means and why it occurred
            2. **Impact Assessment**: Potential impact on system and users
            3. **Root Cause Analysis**: Most likely root causes
            4. **Immediate Response**: Steps to take immediately
            5. **Investigation Steps**: How to investigate further
            6. **Prevention Measures**: How to prevent similar anomalies
            7. **Monitoring Improvements**: How to better detect such anomalies

            Provide a thorough, technical analysis suitable for incident response teams.
            """
            
            # Generate response
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            return {
                "explanation": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "anomaly_type": anomaly.get('type', 'Unknown'),
                "analysis_type": "anomaly_explanation"
            }
            
        except Exception as e:
            return {"error": f"Anomaly explanation failed: {str(e)}"}

# Example usage and testing
async def main():
    """Test the Gemini insights functionality"""
    insights = GeminiInsights()
    
    if not insights.model:
        print("Gemini API not configured. Please set GEMINI_API_KEY in your environment.")
        return
    
    # Test data
    test_logs = [
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "service": "database",
            "severity": "ERROR",
            "message": "Database connection failed: timeout",
            "source_ip": "192.168.1.100"
        },
        {
            "timestamp": "2024-01-15T10:31:00Z",
            "service": "api",
            "severity": "WARNING",
            "message": "High response time detected: 5000ms",
            "source_ip": "192.168.1.101"
        }
    ]
    
    test_stats = {
        "total_logs": 1000,
        "severity_distribution": {
            "INFO": 600,
            "WARNING": 250,
            "ERROR": 120,
            "CRITICAL": 30
        },
        "service_distribution": {
            "database": 300,
            "api": 250,
            "authentication": 200,
            "server": 150,
            "access": 100
        }
    }
    
    # Test pattern analysis
    print("Testing pattern analysis...")
    result = await insights.analyze_log_patterns(test_logs, test_stats)
    print("Pattern Analysis Result:")
    print(result.get('analysis', 'No analysis available'))
    
    # Test daily summary
    print("\nTesting daily summary...")
    summary = await insights.generate_daily_summary(test_stats)
    print("Daily Summary:")
    print(summary.get('summary', 'No summary available'))

if __name__ == "__main__":
    asyncio.run(main())




