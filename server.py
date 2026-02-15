import http.server
import socketserver
import json
import sys
import os

# Load .env manually since python-dotenv might not be available
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Import our backend logic
from api.analysis import process_analysis_request
from api.contact import process_contact_request
from supabase_client import get_report

PORT = int(os.environ.get('PORT', 8000))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 1. Routing: /api/report?report_id=...
        if self.path.startswith('/api/report'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            report_id = query.get('report_id', [None])[0]
            
            if not report_id:
                self.send_error(400, "Missing report_id")
                return

            report = get_report(report_id)
            if report:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                # Allow CORS for local dev
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Convert datetime objects to string if needed (Supabase usually returns strings)
                self.wfile.write(json.dumps(report, default=str).encode('utf-8'))
            else:
                self.send_error(404, "Report not found")
        else:
            # Fallback to serving static files
            super().do_GET()

    def do_POST(self):
        # 1. Routing: Only handle /api/analysis
        if self.path == '/api/analysis':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Call our Serverless Function logic
                response_data, status_code = process_analysis_request(data)
                
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid JSON"}')
        elif self.path == '/api/contact':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                response_data, status_code = process_contact_request(data)
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Contact Error: {str(e)}")
        elif self.path == '/api/proxy/analysis-request':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Forward to n8n (Server-side only)
                N8N_WEBHOOK_URL = os.environ.get("N8N_ANALYSIS_WEBHOOK_URL", "")
                
                import urllib.request
                req = urllib.request.Request(
                    N8N_WEBHOOK_URL, 
                    data=post_data, 
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req) as response:
                    response_body = response.read()
                    self.send_response(response.getcode())
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(response_body)
                    
            except Exception as e:
                self.send_error(500, f"Proxy Error: {str(e)}")

        else:
            self.send_error(404, "Not Found")

print(f"Server started at http://localhost:{PORT}")
print(f"Backend API available at http://localhost:{PORT}/api/analysis")

# Allow address reuse to prevent "Address already in use" errors during quick restarts
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    httpd.serve_forever()
