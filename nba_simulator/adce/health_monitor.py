"""
Health Monitor - HTTP Server for ADCE Status

Provides HTTP endpoints for monitoring autonomous loop health.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from ..utils import setup_logging

logger = setup_logging(__name__)


class HealthMonitorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health monitoring"""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(format % args)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get health status from server's loop_state
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "loop_state": getattr(self.server, 'loop_state', {})
            }
            
            self.wfile.write(json.dumps(health_data, default=str).encode())
            
        elif self.path == "/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status_data = {
                "service": "adce-autonomous-loop",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
            }
            
            self.wfile.write(json.dumps(status_data).encode())
        else:
            self.send_response(404)
            self.end_headers()


class HealthMonitor:
    """
    HTTP health monitoring server for ADCE
    
    Provides endpoints:
    - /health - Detailed health status
    - /status - Simple status check
    """
    
    def __init__(self, port=8080, loop_state=None):
        """
        Initialize health monitor
        
        Args:
            port: HTTP port to listen on
            loop_state: Reference to autonomous loop state dict
        """
        self.port = port
        self.loop_state = loop_state or {}
        self.server = None
        
    def start(self):
        """Start HTTP server"""
        try:
            self.server = HTTPServer(('localhost', self.port), HealthMonitorHandler)
            
            # Attach loop state to server so handler can access it
            self.server.loop_state = self.loop_state
            
            logger.info(f"Health monitor listening on port {self.port}")
            self.server.serve_forever()
            
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
