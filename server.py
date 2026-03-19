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
    def do_HEAD(self):
        # Fallback to standard HEAD handling for static files
        super().do_HEAD()

    def do_GET(self):
        # 0. SEO 301 Redirects for old blog URLs
        if self.path.startswith('/blog-post.html'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            old_id = query.get('id', [None])[0]
            
            if old_id:
                # Manual mappings for mismatched slugs
                mappings = {
                    'amazon-gmv-growth-2025-record-milestone': 'amazon-gmv-growth-2025-milestone',
                    'amazon-bsa-compliance-update-2024-seller-tools-ai': 'amazon-seller-tool-compliance-2024-bsa-rules',
                    'amazon-seller-ad-fees-outage-2026-fba-impact': 'amazon-fba-ad-fee-crisis-2026-outage-charges',
                    'amazon-fba-ad-fee-outage-2026-seller-impact': 'amazon-fba-ad-fee-crisis-2026-outage-charges',
                }
                new_slug = mappings.get(old_id, old_id)
                new_path = f"/blog/{new_slug}.html"
                
                # Check file existence to avoid 404s after redirect
                file_sys_path = os.path.join(os.path.dirname(__file__), 'blog', f"{new_slug}.html")
                if os.path.exists(file_sys_path):
                    redirect_url = new_path
                else:
                    redirect_url = "/blog.html"
            else:
                redirect_url = "/blog.html"
                
            self.send_response(301)
            self.send_header('Location', redirect_url)
            self.end_headers()
            return

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
        elif self.path in ['/api/proxy/analysis-request', '/api/proxy/free-analysis']:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Forward to n8n (server-side only)
                N8N_WEBHOOK_URL = os.environ.get("N8N_FREE_ANALYSIS_URL", "")
                if not N8N_WEBHOOK_URL:
                    self.send_error(503, "Free analysis service not configured")
                    return
                
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
