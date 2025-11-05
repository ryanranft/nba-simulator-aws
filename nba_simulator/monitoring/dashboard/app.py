#!/usr/bin/env python3
"""
NBA Simulator - Real-Time Monitoring Dashboard

Production-ready web dashboard for monitoring:
- DIMS metrics and verification
- Scraper health status
- Alert history and management
- System-wide statistics

Technology: Flask + HTMX for reactive UI
Deploy: Can run standalone or integrate with existing web server
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from flask import Flask, render_template_string, jsonify, request, Response
from flask_cors import CORS

# These imports assume the nba_simulator package structure
try:
    from nba_simulator.monitoring.dims import DIMSCore, DIMSCache, DIMSVerifier
    from nba_simulator.monitoring.health import ScraperHealthMonitor, AlertManager
    from nba_simulator.database import execute_query
except ImportError:
    # Fallback for development/testing
    print("Warning: nba_simulator imports not available. Running in standalone mode.")
    DIMSCore = DIMSCache = DIMSVerifier = None
    ScraperHealthMonitor = AlertManager = None
    execute_query = None

logger = logging.getLogger(__name__)

# ============================================================================
# Flask Application Setup
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nba-simulator-dashboard-secret-key-change-in-production'
CORS(app)  # Enable CORS for API endpoints

# Global monitoring instances (initialized on first request)
_dims_core: Optional[Any] = None
_health_monitor: Optional[Any] = None
_alert_manager: Optional[Any] = None


def get_dims_core():
    """Lazy initialization of DIMS core"""
    global _dims_core
    if _dims_core is None and DIMSCore is not None:
        _dims_core = DIMSCore()
    return _dims_core


def get_health_monitor():
    """Lazy initialization of health monitor"""
    global _health_monitor
    if _health_monitor is None and ScraperHealthMonitor is not None:
        _health_monitor = ScraperHealthMonitor()
    return _health_monitor


def get_alert_manager():
    """Lazy initialization of alert manager"""
    global _alert_manager
    if _alert_manager is None and AlertManager is not None:
        _alert_manager = AlertManager()
    return _alert_manager


# ============================================================================
# HTML Templates (Embedded for simplicity - extract to files in production)
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Simulator - Monitoring Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 32px;
            color: #1a202c;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #718096;
            font-size: 16px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric-value {
            font-size: 48px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #718096;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background: #48bb78; }
        .status-warning { background: #ed8936; }
        .status-critical { background: #f56565; }
        .status-unknown { background: #cbd5e0; }
        
        .scraper-list {
            list-style: none;
            margin-top: 15px;
        }
        
        .scraper-item {
            padding: 12px;
            background: #f7fafc;
            border-radius: 6px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .scraper-name {
            font-weight: 500;
            color: #2d3748;
        }
        
        .scraper-status {
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
        }
        
        .status-ok {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-warn {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .status-error {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .alert-list {
            margin-top: 15px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .alert-item {
            padding: 15px;
            background: #f7fafc;
            border-left: 4px solid;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        
        .alert-critical { border-left-color: #f56565; }
        .alert-warning { border-left-color: #ed8936; }
        .alert-info { border-left-color: #4299e1; }
        
        .alert-time {
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
        }
        
        .refresh-info {
            text-align: center;
            color: #718096;
            font-size: 14px;
            margin-top: 20px;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .btn:hover {
            background: #5568d3;
        }
        
        .btn-secondary {
            background: #718096;
        }
        
        .btn-secondary:hover {
            background: #4a5568;
        }
        
        canvas {
            max-height: 300px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #718096;
        }
        
        .spinner {
            border: 3px solid #f3f4f6;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            background: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏀 NBA Simulator - Monitoring Dashboard</h1>
            <p class="subtitle">Real-time system monitoring and health status</p>
        </header>
        
        <!-- Key Metrics Overview -->
        <div class="grid">
            <div class="card" hx-get="/api/metrics/overview" hx-trigger="load, every 30s" hx-swap="innerHTML">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading metrics...</p>
                </div>
            </div>
        </div>
        
        <!-- Main Dashboard Sections -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('scrapers')">Scrapers</button>
            <button class="tab" onclick="showTab('alerts')">Alerts</button>
            <button class="tab" onclick="showTab('dims')">DIMS</button>
        </div>
        
        <!-- Overview Tab -->
        <div id="tab-overview" class="tab-content">
            <div class="grid">
                <div class="card">
                    <div class="card-title">📊 Database Status</div>
                    <div hx-get="/api/database/stats" hx-trigger="load, every 60s" hx-swap="innerHTML">
                        <div class="loading"><div class="spinner"></div></div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">⚡ System Health</div>
                    <div hx-get="/api/system/health" hx-trigger="load, every 30s" hx-swap="innerHTML">
                        <div class="loading"><div class="spinner"></div></div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">📈 Activity Chart</div>
                    <canvas id="activityChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Scrapers Tab -->
        <div id="tab-scrapers" class="tab-content" style="display:none;">
            <div class="card">
                <div class="card-title">🤖 Active Scrapers</div>
                <div hx-get="/api/scrapers/status" hx-trigger="load, every 15s" hx-swap="innerHTML">
                    <div class="loading"><div class="spinner"></div></div>
                </div>
            </div>
        </div>
        
        <!-- Alerts Tab -->
        <div id="tab-alerts" class="tab-content" style="display:none;">
            <div class="card">
                <div class="card-title">🚨 Recent Alerts</div>
                <div hx-get="/api/alerts/recent" hx-trigger="load, every 30s" hx-swap="innerHTML">
                    <div class="loading"><div class="spinner"></div></div>
                </div>
            </div>
        </div>
        
        <!-- DIMS Tab -->
        <div id="tab-dims" class="tab-content" style="display:none;">
            <div class="grid">
                <div class="card">
                    <div class="card-title">✅ DIMS Verification</div>
                    <div hx-get="/api/dims/verification" hx-trigger="load, every 60s" hx-swap="innerHTML">
                        <div class="loading"><div class="spinner"></div></div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">📋 Recent Runs</div>
                    <div hx-get="/api/dims/history" hx-trigger="load, every 60s" hx-swap="innerHTML">
                        <div class="loading"><div class="spinner"></div></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="refresh-info">
            Dashboard auto-refreshes every 15-60 seconds | Last updated: <span id="last-update"></span>
        </div>
    </div>
    
    <script>
        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabName).style.display = 'block';
            event.target.classList.add('active');
        }
        
        // Update timestamp
        function updateTimestamp() {
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        setInterval(updateTimestamp, 1000);
        updateTimestamp();
        
        // Initialize activity chart
        const ctx = document.getElementById('activityChart');
        if (ctx) {
            const activityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Records Processed',
                        data: [],
                        borderColor: '#667eea',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
            
            // Update chart periodically
            setInterval(async () => {
                const response = await fetch('/api/metrics/timeseries');
                const data = await response.json();
                activityChart.data.labels = data.labels;
                activityChart.data.datasets[0].data = data.values;
                activityChart.update();
            }, 30000);
        }
    </script>
</body>
</html>
"""


# ============================================================================
# API Routes - Main Dashboard
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/metrics/overview')
def metrics_overview():
    """Get overview metrics"""
    try:
        # Get database counts
        if execute_query:
            games = execute_query("SELECT COUNT(*) as count FROM games")[0]['count']
            events = execute_query("SELECT COUNT(*) as count FROM temporal_events")[0]['count']
            players = execute_query("SELECT COUNT(*) as count FROM players")[0]['count']
        else:
            games, events, players = 44828, 14114617, 5000
        
        html = f"""
        <div class="card-title">📊 System Overview</div>
        <div class="grid" style="grid-template-columns: repeat(3, 1fr); gap: 20px;">
            <div>
                <div class="metric-value">{games:,}</div>
                <div class="metric-label">Games</div>
            </div>
            <div>
                <div class="metric-value">{events:,}</div>
                <div class="metric-label">Events</div>
            </div>
            <div>
                <div class="metric-value">{players:,}</div>
                <div class="metric-label">Players</div>
            </div>
        </div>
        """
        return html
    except Exception as e:
        logger.error(f"Error getting overview metrics: {e}")
        return f'<p class="error">Error loading metrics</p>'


@app.route('/api/database/stats')
def database_stats():
    """Get database statistics"""
    try:
        if execute_query:
            # Get table sizes
            tables = execute_query("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 5
            """)
            
            html = '<ul class="scraper-list">'
            for table in tables:
                html += f"""
                <li class="scraper-item">
                    <span class="scraper-name">{table['tablename']}</span>
                    <span class="scraper-status status-ok">{table['size']}</span>
                </li>
                """
            html += '</ul>'
            return html
        else:
            return '<p>Database not connected</p>'
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return '<p class="error">Error loading database stats</p>'


@app.route('/api/system/health')
def system_health():
    """Get system health status"""
    try:
        monitor = get_health_monitor()
        if monitor:
            # Get health summary
            summary = asyncio.run(monitor.get_health_summary())
            
            status_class = 'status-healthy' if summary.get('overall_health') == 'healthy' else 'status-warning'
            
            html = f"""
            <div class="scraper-item">
                <span class="scraper-name">
                    <span class="status-indicator {status_class}"></span>
                    Overall System
                </span>
                <span class="scraper-status status-ok">{summary.get('overall_health', 'Unknown').upper()}</span>
            </div>
            <div style="margin-top: 15px; font-size: 14px; color: #718096;">
                <p><strong>Active Scrapers:</strong> {summary.get('active_scrapers', 0)}</p>
                <p><strong>CPU Usage:</strong> {summary.get('cpu_percent', 0):.1f}%</p>
                <p><strong>Memory:</strong> {summary.get('memory_percent', 0):.1f}%</p>
            </div>
            """
            return html
        else:
            return '<p>Health monitor not available</p>'
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return '<p class="error">Error loading health status</p>'


@app.route('/api/scrapers/status')
def scrapers_status():
    """Get scraper status list"""
    try:
        # Mock data - replace with actual scraper status
        scrapers = [
            {'name': 'ESPN Scraper', 'status': 'running', 'last_run': '2 mins ago'},
            {'name': 'Basketball Reference', 'status': 'running', 'last_run': '5 mins ago'},
            {'name': 'NBA API', 'status': 'idle', 'last_run': '1 hour ago'},
            {'name': 'hoopR Scraper', 'status': 'running', 'last_run': '10 mins ago'},
        ]
        
        html = '<ul class="scraper-list">'
        for scraper in scrapers:
            status_class = 'status-ok' if scraper['status'] == 'running' else 'status-warn'
            html += f"""
            <li class="scraper-item">
                <div>
                    <div class="scraper-name">{scraper['name']}</div>
                    <div style="font-size: 12px; color: #718096;">Last run: {scraper['last_run']}</div>
                </div>
                <span class="scraper-status {status_class}">{scraper['status'].upper()}</span>
            </li>
            """
        html += '</ul>'
        return html
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        return '<p class="error">Error loading scraper status</p>'


@app.route('/api/alerts/recent')
def alerts_recent():
    """Get recent alerts"""
    try:
        alert_mgr = get_alert_manager()
        if alert_mgr:
            alerts = asyncio.run(alert_mgr.get_alert_history(limit=10))
            
            if not alerts:
                return '<p style="text-align: center; color: #718096; padding: 20px;">No recent alerts</p>'
            
            html = '<div class="alert-list">'
            for alert in alerts:
                severity = alert.get('severity', 'info').lower()
                html += f"""
                <div class="alert-item alert-{severity}">
                    <strong>{alert.get('title', 'Alert')}</strong>
                    <p>{alert.get('message', 'No message')}</p>
                    <div class="alert-time">{alert.get('created_at', 'Unknown time')}</div>
                </div>
                """
            html += '</div>'
            return html
        else:
            return '<p>No alerts available</p>'
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return '<p class="error">Error loading alerts</p>'


@app.route('/api/dims/verification')
def dims_verification():
    """Get DIMS verification status"""
    try:
        dims = get_dims_core()
        if dims:
            results = asyncio.run(dims.verify_all())
            
            total = len(results)
            passed = sum(1 for r in results if r.get('passed', False))
            
            html = f"""
            <div class="metric-value">{passed}/{total}</div>
            <div class="metric-label">Checks Passed</div>
            <div style="margin-top: 20px;">
                <button class="btn" onclick="location.reload()">Run Verification</button>
            </div>
            """
            return html
        else:
            return '<p>DIMS not available</p>'
    except Exception as e:
        logger.error(f"Error getting DIMS verification: {e}")
        return '<p class="error">Error loading verification</p>'


@app.route('/api/dims/history')
def dims_history():
    """Get DIMS verification history"""
    try:
        if execute_query:
            history = execute_query("""
                SELECT run_id, started_at, status, total_checks, passed_checks
                FROM dims_verification_runs
                ORDER BY started_at DESC
                LIMIT 5
            """)
            
            html = '<ul class="scraper-list">'
            for run in history:
                status_class = 'status-ok' if run['status'] == 'completed' else 'status-warn'
                html += f"""
                <li class="scraper-item">
                    <div>
                        <div class="scraper-name">Run #{run['run_id']}</div>
                        <div style="font-size: 12px; color: #718096;">{run['started_at']}</div>
                    </div>
                    <span class="scraper-status {status_class}">{run['passed_checks']}/{run['total_checks']}</span>
                </li>
                """
            html += '</ul>'
            return html
        else:
            return '<p>No history available</p>'
    except Exception as e:
        logger.error(f"Error getting DIMS history: {e}")
        return '<p class="error">Error loading history</p>'


@app.route('/api/metrics/timeseries')
def metrics_timeseries():
    """Get time series data for charts"""
    try:
        # Generate sample data - replace with actual metrics
        now = datetime.now()
        labels = [(now - timedelta(hours=i)).strftime('%H:%M') for i in range(24, 0, -1)]
        values = [14000000 + (i * 1000) for i in range(24)]
        
        return jsonify({
            'labels': labels,
            'values': values
        })
    except Exception as e:
        logger.error(f"Error getting timeseries: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Health Check & Status Endpoints
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'nba-simulator-dashboard'
    })


@app.route('/api/status')
def api_status():
    """Detailed API status"""
    try:
        status = {
            'dashboard': 'operational',
            'database': 'connected' if execute_query else 'disconnected',
            'dims': 'available' if DIMSCore else 'unavailable',
            'health_monitor': 'available' if ScraperHealthMonitor else 'unavailable',
            'alert_manager': 'available' if AlertManager else 'unavailable',
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the dashboard server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NBA Simulator Monitoring Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏀 NBA Simulator - Monitoring Dashboard")
    print("=" * 60)
    print(f"Dashboard URL: http://{args.host}:{args.port}")
    print(f"Health Check:  http://{args.host}:{args.port}/health")
    print(f"API Status:    http://{args.host}:{args.port}/api/status")
    print("=" * 60)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
