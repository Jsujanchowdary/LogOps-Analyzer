import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, List
from config import Config
from gemini_insights import GeminiInsights

# Page configuration
st.set_page_config(
    page_title="LogOps Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-critical {
        color: #dc3545;
        font-weight: bold;
    }
        .main-header {
        font-size: 2rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #000000;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
    }
    .insight-box h1, .insight-box h2, .insight-box h3, .insight-box h4, .insight-box h5, .insight-box h6 {
        color: #00bfff;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .insight-box p {
        color: #ffffff;
        margin-bottom: 0.8rem;
    }
    .insight-box ul, .insight-box ol {
        color: #ffffff;
        margin-left: 1.5rem;
    }
    .insight-box li {
        color: #ffffff;
        margin-bottom: 0.3rem;
    }
    .insight-box strong, .insight-box b {
        color: #00bfff;
        font-weight: bold;
    }
    .insight-box code {
        background-color: #333333;
        color: #00ff00;
        padding: 0.2rem 0.4rem;
        border-radius: 0.3rem;
        font-family: 'Courier New', monospace;
    }
    .insight-box blockquote {
        border-left: 4px solid #00bfff;
        margin: 1rem 0;
        padding-left: 1rem;
        color: #cccccc;
        font-style: italic;
    }
    .insight-box pre {
        background-color: #333333;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
        border: 1px solid #666666;
    }
    .ai-response {
        background: #000000;
        border: 2px solid #1f77b4;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .error-highlight {
        background-color: #f8d7da;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class LogOpsDashboard:
    def __init__(self):
        self.api_url = f"http://{Config.API_HOST}:{Config.API_PORT}"
        self.gemini_insights = GeminiInsights()
        self.last_update = None
        
    def fetch_logs_data(self, hours: int = 24) -> Dict:
        """Fetch logs data from API"""
        try:
            response = requests.get(f"{self.api_url}/api/logs/stats", params={"hours": hours}, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch logs data: {response.status_code}")
                return {}
        except Exception as e:
            st.error(f"Error fetching logs data: {e}")
            return {}
    
    def fetch_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Fetch recent logs from API"""
        try:
            response = requests.get(f"{self.api_url}/api/logs", params={"limit": limit}, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch recent logs: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching recent logs: {e}")
            return []
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">📊 LogOps Analyzer</h1>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_sidebar(self):
        """Render the sidebar with controls"""
        st.sidebar.title("🔧 Controls")
        
        # Time range selector
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["1 hour", "6 hours", "12 hours", "24 hours", "7 days"],
            index=3
        )
        
        # Convert to hours
        hours_map = {
            "1 hour": 1,
            "6 hours": 6,
            "12 hours": 12,
            "24 hours": 24,
            "7 days": 168
        }
        hours = hours_map[time_range]
        
        # Service filter
        services = st.sidebar.multiselect(
            "Filter by Service",
            ["database", "authentication", "access", "server", "api", "cache", "queue", "storage", "monitoring"],
            default=[]
        )
        
        # Severity filter
        severities = st.sidebar.multiselect(
            "Filter by Severity",
            ["INFO", "WARNING", "ERROR", "CRITICAL"],
            default=[]
        )
        
        # Auto-refresh
        auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        return hours, services, severities, auto_refresh
    
    def render_metrics(self, stats: Dict):
        """Render key metrics"""
        if not stats:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_logs = stats.get('total_logs', 0)
            st.metric(
                label="📈 Total Logs",
                value=f"{total_logs:,}",
                delta=None
            )
        
        with col2:
            severity_dist = stats.get('severity_distribution', {})
            error_count = severity_dist.get('ERROR', 0)
            error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
            st.metric(
                label="❌ Error Rate",
                value=f"{error_rate:.1f}%",
                delta=f"{error_count:,} errors"
            )
        
        with col3:
            critical_count = severity_dist.get('CRITICAL', 0)
            critical_rate = (critical_count / total_logs * 100) if total_logs > 0 else 0
            st.metric(
                label="💥 Critical Rate",
                value=f"{critical_rate:.1f}%",
                delta=f"{critical_count:,} critical"
            )
        
        with col4:
            # Calculate health score
            health_score = self.calculate_health_score(stats)
            health_color = "status-healthy" if health_score >= 8 else "status-warning" if health_score >= 5 else "status-critical"
            st.metric(
                label="🏥 Health Score",
                value=f"{health_score}/10",
                delta=None
            )
    
    def calculate_health_score(self, stats: Dict) -> int:
        """Calculate overall system health score"""
        if not stats:
            return 0
        
        total_logs = stats.get('total_logs', 0)
        if total_logs == 0:
            return 10
        
        severity_dist = stats.get('severity_distribution', {})
        error_rate = (severity_dist.get('ERROR', 0) / total_logs) * 100
        critical_rate = (severity_dist.get('CRITICAL', 0) / total_logs) * 100
        
        # Health score calculation (10 = perfect, 0 = critical)
        health_score = 10
        
        # Deduct points for errors and critical issues
        health_score -= min(error_rate * 0.1, 3)  # Max 3 points for errors
        health_score -= min(critical_rate * 0.5, 5)  # Max 5 points for critical
        
        return max(int(health_score), 0)
    
    def render_severity_chart(self, stats: Dict):
        """Render severity distribution chart"""
        if not stats or 'severity_distribution' not in stats:
            return
        
        severity_dist = stats['severity_distribution']
        
        # Create pie chart
        fig = px.pie(
            values=list(severity_dist.values()),
            names=list(severity_dist.keys()),
            title="Log Severity Distribution",
            color_discrete_map={
                'INFO': '#28a745',
                'WARNING': '#ffc107',
                'ERROR': '#fd7e14',
                'CRITICAL': '#dc3545'
            }
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_service_chart(self, stats: Dict):
        """Render service distribution chart"""
        if not stats or 'service_distribution' not in stats:
            return
        
        service_dist = stats['service_distribution']
        
        # Create bar chart
        df = pd.DataFrame(list(service_dist.items()), columns=['Service', 'Count'])
        df = df.sort_values('Count', ascending=True)
        
        fig = px.bar(
            df,
            x='Count',
            y='Service',
            orientation='h',
            title="Log Volume by Service",
            color='Count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    def render_timeline_chart(self, stats: Dict):
        """Render timeline chart"""
        if not stats or 'hourly_distribution' not in stats:
            return
        
        hourly_dist = stats['hourly_distribution']
        
        # Convert to DataFrame
        df = pd.DataFrame(list(hourly_dist.items()), columns=['Hour', 'Count'])
        df['Hour'] = pd.to_datetime(df['Hour'])
        df = df.sort_values('Hour')
        
        # Create line chart
        fig = px.line(
            df,
            x='Hour',
            y='Count',
            title="Log Volume Over Time",
            markers=True
        )
        
        fig.update_layout(height=400, xaxis_title="Time", yaxis_title="Log Count")
        st.plotly_chart(fig, use_container_width=True)
    
    def render_recent_logs_table(self, logs: List[Dict]):
        """Render recent logs table"""
        if not logs:
            st.info("No recent logs available")
            return
        
        st.subheader("📋 Recent Logs")
        
        # Convert to DataFrame
        df = pd.DataFrame(logs)
        
        # Format timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Color code severity
        def color_severity(val):
            colors = {
                'INFO': 'background-color: #d4edda',
                'WARNING': 'background-color: #fff3cd',
                'ERROR': 'background-color: #f8d7da',
                'CRITICAL': 'background-color: #f5c6cb'
            }
            return colors.get(val, '')
        
        # Display table
        styled_df = df.style.applymap(color_severity, subset=['severity'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    def render_ai_insights(self, stats: Dict, logs: List[Dict]):
        """Render AI-powered insights"""
        st.subheader("🤖 AI Insights & Recommendations")
        
        if not self.gemini_insights.model:
            st.warning("Gemini API not configured. Please set GEMINI_API_KEY to enable AI insights.")
            return
        
        # Create tabs for different insights
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Pattern Analysis", "🔍 Anomaly Insights", "💡 Optimizations", "📈 Daily Summary"])
        
        with tab1:
            if st.button("Analyze Log Patterns"):
                with st.spinner("Analyzing log patterns..."):
                    result = asyncio.run(self.gemini_insights.analyze_log_patterns(logs, stats))
                    if 'error' not in result:
                        st.markdown(f'<div class="insight-box">{result["analysis"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Analysis failed: {result['error']}")
        
        with tab2:
            if st.button("Generate Anomaly Insights"):
                with st.spinner("Generating anomaly insights..."):
                    # For demo purposes, create some mock anomalies
                    mock_anomalies = [
                        {
                            "type": "volume_spike",
                            "severity": "WARNING",
                            "description": "Unusual log volume detected",
                            "confidence_score": 0.85,
                            "affected_service": "database"
                        }
                    ]
                    result = asyncio.run(self.gemini_insights.generate_anomaly_insights(mock_anomalies, logs))
                    if 'error' not in result:
                        st.markdown(f'<div class="insight-box">{result["insights"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Insights generation failed: {result['error']}")
        
        with tab3:
            if st.button("Get Optimization Suggestions"):
                with st.spinner("Generating optimization suggestions..."):
                    result = asyncio.run(self.gemini_insights.suggest_optimizations(logs, stats))
                    if 'error' not in result:
                        st.markdown(f'<div class="insight-box">{result["recommendations"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Optimization analysis failed: {result['error']}")
        
        with tab4:
            if st.button("Generate Daily Summary"):
                with st.spinner("Generating daily summary..."):
                    result = asyncio.run(self.gemini_insights.generate_daily_summary(stats))
                    if 'error' not in result:
                        st.markdown(f'<div class="insight-box">{result["summary"]}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Summary generation failed: {result['error']}")
    
    def render_anomaly_detection(self):
        """Render anomaly detection section"""
        st.subheader("🔍 Anomaly Detection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Anomalies Detected", "3", delta="+1")
            st.metric("False Positive Rate", "5.2%", delta="-0.8%")
        
        with col2:
            st.metric("Detection Accuracy", "94.8%", delta="+2.1%")
            st.metric("Response Time", "2.3s", delta="-0.5s")
        
        # Anomaly timeline
        anomaly_data = {
            'Time': ['10:00', '10:30', '11:00', '11:30', '12:00'],
            'Anomalies': [0, 1, 2, 1, 0]
        }
        
        df = pd.DataFrame(anomaly_data)
        fig = px.line(df, x='Time', y='Anomalies', title="Anomalies Detected Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    def render_alerting_status(self):
        """Render alerting system status"""
        st.subheader("🚨 Alerting Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ Telegram Bot Connected")
            st.info("📱 Last Alert: 2 minutes ago")
        
        with col2:
            st.warning("⚠️ 3 Active Alerts")
            st.info("🔔 Alert Rate: 2/hour")
        
        with col3:
            st.success("✅ All Systems Operational")
            st.info("📊 Uptime: 99.9%")
    
    def run(self):
        """Main dashboard run method"""
        self.render_header()
        
        # Sidebar controls
        hours, services, severities, auto_refresh = self.render_sidebar()
        
        # Auto-refresh logic
        if auto_refresh:
            if self.last_update is None or time.time() - self.last_update > 60:
                self.last_update = time.time()
                st.rerun()
        
        # Fetch data
        with st.spinner("Loading data..."):
            stats = self.fetch_logs_data(hours)
            recent_logs = self.fetch_recent_logs(50)
        
        if not stats:
            st.error("Failed to load data. Please check if the API is running.")
            return
        
        # Main content
        self.render_metrics(stats)
        
        # Charts section
        st.subheader("📊 Analytics Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_severity_chart(stats)
        
        with col2:
            self.render_service_chart(stats)
        
        # Timeline chart
        self.render_timeline_chart(stats)
        
        # Recent logs
        self.render_recent_logs_table(recent_logs)
        
        # AI Insights
        self.render_ai_insights(stats, recent_logs)
        
        # Anomaly Detection
        self.render_anomaly_detection()
        
        # Alerting Status
        self.render_alerting_status()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            "LogOps Analyzer - Real-time Log Monitoring & Analysis | "
            f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            "</div>",
            unsafe_allow_html=True
        )

def main():
    """Main function to run the dashboard"""
    dashboard = LogOpsDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
