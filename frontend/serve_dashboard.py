#!/usr/bin/env python3
"""
Simple HTTP server to serve the electricity theft detection dashboard.
This script serves the simple-dashboard.html file with proper CORS headers.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers for API access."""
    
    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests, serve index.html for root path."""
        if self.path == '/':
            self.path = '/simple-dashboard.html'
        return super().do_GET()

def main():
    """Start the HTTP server."""
    # Change to the frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Server configuration
    PORT = 3000
    HOST = 'localhost'
    
    # Check if the dashboard file exists
    dashboard_file = frontend_dir / 'simple-dashboard.html'
    if not dashboard_file.exists():
        print(f"❌ Error: Dashboard file not found at {dashboard_file}")
        sys.exit(1)
    
    print(f"🚀 Starting Electricity Theft Detection Dashboard...")
    print(f"📁 Serving from: {frontend_dir}")
    print(f"🌐 Dashboard URL: http://{HOST}:{PORT}")
    print(f"⚡ Make sure the API server is running on http://localhost:8000")
    print(f"🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        with socketserver.TCPServer((HOST, PORT), CORSRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use.")
            print(f"Try using a different port or kill the process using port {PORT}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()