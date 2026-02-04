"""
FastAPI Main Application for Product Discovery Service
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
import httpx
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional

from .models import DiscoveryRequest, DiscoveryResponse, UserTier
from .analyzer import ProductDiscoveryAnalyzer
from .config import DEFAULT_MODEL_FREE, PRO_MODELS
from .email_service import send_email_report

app = FastAPI(
    title="Product Discovery API",
    description="AI-powered Amazon product discovery and analysis service",
    version="1.0.0"
)


# Cache control middleware
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith(".html") or path == "/":
            response.headers["Cache-Control"] = "no-cache"
        elif path.endswith((".css", ".js")):
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")):
            response.headers["Cache-Control"] = "public, max-age=86400"
        return response

app.add_middleware(CacheControlMiddleware)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "https://amzaiagent.com,https://www.amzaiagent.com").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Serve static files (CSS, JS, Images)
# Mount specific directories to ensure assets load correctly from root paths
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/images", StaticFiles(directory="images"), name="images")

# Fallback: Mount root for other static files (like .html pages in root)
# Note: Specific mounts above take precedence.
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/{filename}.css")
async def read_css(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = f"{filename}.css"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{filename}.js")
async def read_js(filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = f"{filename}.js"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{filename}.html")
async def read_html(filename: str):
    # Security check: prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_path = f"{filename}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    # Check if it's a blog post (e.g. blog/xxx.html requested as xxx.html? No, usually it's /blog/xxx)
    # If filename matches a known page, return it.
    
    raise HTTPException(status_code=404, detail="Page not found")

# Handle blog post paths if they are like /blog/some-post.html
@app.get("/blog/{post_slug}.html")
async def read_blog_post(post_slug: str):
    # Strategy 1: If static HTML exists in data/blog/
    path1 = f"data/blog/{post_slug}.html"
    if os.path.exists(path1):
        return FileResponse(path1)
        
    # Strategy 2: If we use a template (blog-post.html) and client-side rendering
    # This is likely how it works if no static HTMLs exist.
    if os.path.exists("blog-post.html"):
        return FileResponse("blog-post.html")
        
    raise HTTPException(status_code=404, detail="Blog post not found")

@app.get("/styles.css")
async def read_css():
    return FileResponse('styles.css')

@app.get("/script_v2.js")
async def read_js():
    return FileResponse('script_v2.js')

@app.get("/sitemap.xml")
async def read_sitemap():
    return FileResponse('sitemap.xml')

@app.get("/robots.txt")
async def read_robots():
    return FileResponse('robots.txt')


# Global analyzer instance
analyzer = ProductDiscoveryAnalyzer()

# Store for completed reports (in production, use database)
reports_store = {}  # TODO: Replace with Supabase — lost on container restart


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Product Discovery API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/models")
async def get_available_models():
    """Get list of available models for Pro users"""
    return {
        "free_model": DEFAULT_MODEL_FREE,
        "pro_models": PRO_MODELS,
        "default_pro_model": PRO_MODELS[0]
    }


from fastapi import WebSocket
from .progress import progress_manager
import uuid

# ... (Existing code)

@app.websocket("/ws/progress/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await progress_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection open, wait for client messages if needed
            # For now, we only send server->client
            await websocket.receive_text()
    except Exception:
        progress_manager.disconnect(task_id, websocket)

async def run_analysis_task(request: DiscoveryRequest, task_id: str = None):
    """Background task to run analysis"""
    try:
        report = await analyzer.analyze(request, task_id)
        reports_store[report.report_id] = report
        
        # Determine if this is a Pro flow that requires payment
        is_pro_user = request.user_tier == UserTier.PRO
        
        # Send email with report (Full for Free, Preview+Link for Pro)
        await send_email_report(report, is_pro_flow=is_pro_user)
        
        print(f"Report {report.report_id} completed and stored")
    except Exception as e:
        print(f"Error in analysis task: {str(e)}")
        # If task_id exists, emit error
        if task_id:
            await progress_manager.emit(task_id, "Error", "Analysis Failed", 0, {"error": str(e)})
            
        # Send failure notification email
        from .email_service import send_failure_email
        await send_failure_email(request.user_email, request.keywords, str(e))

@app.post("/api/discovery/start-task", response_model=DiscoveryResponse)
async def start_analysis_task(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Start analysis with Real-time Progress Tracking
    Returns a task_id immediately. Client should then connect to /ws/progress/{task_id}
    """
    try:
        # Validate request
        if not request.category or not request.keywords:
            raise HTTPException(status_code=400, detail="Category and keywords are required")
        
        task_id = str(uuid.uuid4())
        
        # Start analysis in background with task_id
        background_tasks.add_task(run_analysis_task, request, task_id)
        
        return DiscoveryResponse(
            success=True,
            message="Analysis started. Connect to WebSocket for progress.",
            estimated_delivery_minutes=10,
            report_id=task_id  # Using report_id field to pass task_id for now
        )
        
    except Exception as e:
        print(f"Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from .payment_service import payment_service
from fastapi import Request

# Import persistent storage functions from supabase_client
import sys
sys.path.insert(0, '.')
from supabase_client import mark_email_paid, is_email_paid, mark_session_verified, is_session_verified

# In-memory fallback (used only when Supabase is unavailable)
_paid_reports_fallback = set()
_verified_sessions_fallback = set()

@app.get("/api/payments/verify-session")
async def verify_payment_session(session_id: str):
    """Verify a checkout session status using persistent storage."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # Check persistent storage first, fallback to memory
    if is_session_verified(session_id) or session_id in _verified_sessions_fallback:
        return {"status": "paid", "session_id": session_id}
    return {"status": "pending", "session_id": session_id}

@app.post("/api/payments/create-checkout")
async def create_checkout(report_id: str, email: str):
    """Create a Polar checkout for a specific report"""
    try:
        # Create checkout session
        checkout = await payment_service.create_checkout_session(
            user_email=email,
            product_name=f"Pro Report: {report_id}"
        )
        return {
            "checkout_url": checkout["url"],
            "checkout_id": checkout["checkout_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET", "")

@app.post("/api/webhooks/polar")
async def polar_webhook(request: Request):
    """Handle Polar payment webhooks"""
    payload = await request.body()
    signature = request.headers.get("webhook-signature") or request.headers.get("stripe-signature")

    # Verify webhook signature - REQUIRED in production
    if not WEBHOOK_SECRET:
        print("ERROR: POLAR_WEBHOOK_SECRET not set — rejecting webhook for security")
        raise HTTPException(status_code=503, detail="Webhook verification not configured")

    import hmac, hashlib
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    import json
    data = json.loads(payload)
    event_type = data.get("type")
    
    if event_type == "checkout.updated":
        checkout_data = data.get("data", {})
        status = checkout_data.get("status")

        if status == "succeeded":
            # Extract our custom data or find by email
            email = checkout_data.get("customer_email")
            checkout_id = checkout_data.get("id") or checkout_data.get("checkout_id")
            print(f"Payment succeeded for {email}, checkout_id: {checkout_id}")

            # Persist to database (with in-memory fallback)
            if email:
                if not mark_email_paid(email, checkout_id):
                    _paid_reports_fallback.add(email)  # Fallback to memory

            if checkout_id:
                if not mark_session_verified(checkout_id, email):
                    _verified_sessions_fallback.add(checkout_id)  # Fallback to memory

    return {"status": "ok"}

# Test endpoint - protected by secret token (disabled in production if not set)
TEST_ENDPOINT_SECRET = os.getenv("TEST_ENDPOINT_SECRET", "")

@app.get("/test-email")
async def test_email_endpoint(email: str, type: str = "success", token: str = ""):
    """Immediate test endpoint to verify email delivery - PROTECTED"""
    # Security: Require secret token to prevent abuse
    if not TEST_ENDPOINT_SECRET:
        raise HTTPException(status_code=404, detail="Not found")  # Hide endpoint in production
    if token != TEST_ENDPOINT_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        from .email_service import send_email_report
        from .models import AnalysisReport
        import datetime
        
        mock_report = AnalysisReport(
            report_id="test-immediate",
            user_email=email,
            keywords="Immediate Connection Test",
            category="Debugging",
            marketplace="US",
            generated_at=str(datetime.datetime.now()),
            model_used="system-test",
            sources_count=0,
            asins_analyzed=0,
            report_markdown="# Connection Successful\n\nThis email confirms that the Amz AI backend can successfully send emails via SMTP (SSL/465).",
            report_html="<div style='font-family:sans-serif; padding:20px; border:1px solid #ddd; border-radius:8px;'><h1>✅ Connection Successful</h1><p>This email confirms that the <strong>Amz AI backend</strong> can successfully send emails via SMTP (SSL/465).</p><p>If you are seeing this, the deployment is correct.</p></div>"
        )
        
        if type == "failure":
            from .email_service import send_failure_email
            await send_failure_email(email, "Test Failure Scenario", "This is a simulated error message to test the failure notification system.")
        else:
            await send_email_report(mock_report, is_pro_flow=False)
        return {"status": "success", "message": f"Test email sent to {email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# === Contact Form Endpoint ===
class ContactFormRequest(PydanticBaseModel):
    name: str
    email: str
    subject: str
    message: str

import re
from datetime import datetime as _dt
_contact_rate_limit: dict = {}  # IP -> (count, window_start)

@app.post("/api/contact")
async def handle_contact_form(req: ContactFormRequest, request: Request):
    """Handle contact form submission via SMTP email"""
    try:
        # Input validation
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', req.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        if len(req.name) > 100 or len(req.subject) > 200 or len(req.message) > 5000:
            raise HTTPException(status_code=400, detail="Input too long")

        # Simple rate limiting (5 per hour per IP)
        client_ip = request.client.host if request.client else "unknown"
        now = _dt.now()
        if client_ip in _contact_rate_limit:
            count, window_start = _contact_rate_limit[client_ip]
            if (now - window_start).seconds < 3600:
                if count >= 5:
                    raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
                _contact_rate_limit[client_ip] = (count + 1, window_start)
            else:
                _contact_rate_limit[client_ip] = (1, now)
        else:
            _contact_rate_limit[client_ip] = (1, now)

        from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        import smtplib
        from html import escape as html_escape
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not SMTP_USER or not SMTP_PASSWORD:
            raise HTTPException(status_code=503, detail="Email service not configured")

        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_USER  # Send to ourselves
        msg["Subject"] = f"[Contact Form] {html_escape(req.subject)}"
        msg["Reply-To"] = req.email

        html_body = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {html_escape(req.name)}</p>
            <p><strong>Email:</strong> {html_escape(req.email)}</p>
            <p><strong>Subject:</strong> {html_escape(req.subject)}</p>
            <hr>
            <p><strong>Message:</strong></p>
            <p>{html_escape(req.message)}</p>
        </div>
        """
        msg.attach(MIMEText(html_body, "html"))

        import asyncio
        from .email_service import _smtp_send
        await asyncio.to_thread(_smtp_send, SMTP_USER, msg)

        return {"status": "success", "message": "Your message has been sent. We'll get back to you soon."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message. Please try again later.")

# === Backend Proxy Endpoints ===
# These proxy n8n webhook calls so that webhook URLs are not exposed in frontend code.
N8N_CHECKOUT_URL = os.getenv("N8N_CHECKOUT_WEBHOOK_URL", "")
N8N_PRO_ANALYSIS_URL = os.getenv("N8N_PRO_ANALYSIS_WEBHOOK_URL", "")
N8N_SEND_REPORT_URL = os.getenv("N8N_SEND_REPORT_WEBHOOK_URL", "")

class CheckoutRequest(PydanticBaseModel):
    amount: str = "4.99"
    order_id: str
    success_url: str
    cancel_url: str

class SendReportRequest(PydanticBaseModel):
    order_id: str
    action: str = "send_full_report"
    resume_url: Optional[str] = None

@app.post("/api/proxy/create-checkout")
async def proxy_create_checkout(req: CheckoutRequest):
    """Proxy Stripe checkout creation to n8n (keeps webhook URL server-side)"""
    if not N8N_CHECKOUT_URL:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_CHECKOUT_URL, data={
                "amount": req.amount,
                "order_id": req.order_id,
                "success_url": req.success_url,
                "cancel_url": req.cancel_url,
            })
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Checkout proxy error: {e}")
        raise HTTPException(status_code=502, detail="Payment service unavailable")

@app.post("/api/proxy/pro-analysis")
async def proxy_pro_analysis(payload: dict):
    """Proxy Pro analysis submission to n8n"""
    if not N8N_PRO_ANALYSIS_URL:
        raise HTTPException(status_code=503, detail="Pro analysis service not configured")
    try:
        form_data = {}
        for key, value in payload.items():
            if isinstance(value, (list, dict)):
                import json
                form_data[key] = json.dumps(value)
            else:
                form_data[key] = str(value)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_PRO_ANALYSIS_URL, data=form_data)
            resp.raise_for_status()
            try:
                return resp.json()
            except Exception:
                return {"status": "ok"}
    except Exception as e:
        print(f"Pro analysis proxy error: {e}")
        raise HTTPException(status_code=502, detail="Pro analysis service unavailable")

@app.post("/api/proxy/send-full-report")
async def proxy_send_full_report(req: SendReportRequest):
    """Proxy full report trigger to n8n"""
    if not N8N_SEND_REPORT_URL:
        raise HTTPException(status_code=503, detail="Report service not configured")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_SEND_REPORT_URL, data={
                "order_id": req.order_id,
                "action": req.action,
            })
            resp.raise_for_status()
            return {"status": "ok"}
    except Exception as e:
        print(f"Send report proxy error: {e}")
        raise HTTPException(status_code=502, detail="Report service unavailable")

N8N_ALLOWED_HOSTS = os.getenv("N8N_ALLOWED_HOSTS", "").split(",")

@app.get("/api/proxy/resume-workflow")
async def proxy_resume_workflow(resume_url: str):
    """Proxy n8n resume URL call so the actual URL stays server-side"""
    if not resume_url:
        raise HTTPException(status_code=400, detail="resume_url is required")
    # SSRF protection: only allow requests to known n8n hosts
    from urllib.parse import urlparse
    parsed = urlparse(resume_url)
    if not parsed.hostname or not any(
        parsed.hostname == h.strip() or parsed.hostname.endswith("." + h.strip())
        for h in N8N_ALLOWED_HOSTS if h.strip()
    ):
        raise HTTPException(status_code=403, detail="URL not allowed")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(resume_url)
            return {"status": "ok", "code": resp.status_code}
    except Exception as e:
        print(f"Resume workflow proxy error: {e}")
        raise HTTPException(status_code=502, detail="Resume failed")

if __name__ == "__main__":
    print("Starting Product Discovery Service...")
    print("API will be available at: http://localhost:8000")
    print("WebSocket at: ws://localhost:8000/ws/progress/{task_id}")
    
    uvicorn.run(
        "discovery_service.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
