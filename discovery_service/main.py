"""
FastAPI Main Application for Product Discovery Service
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Global analyzer instance
analyzer = ProductDiscoveryAnalyzer()

# Store for completed reports (in production, use database)
reports_store = {}


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

@app.get("/test-email")
async def test_email_endpoint(email: str):
    """Immediate test endpoint to verify email delivery"""
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

@app.post("/api/contact")
async def handle_contact_form(req: ContactFormRequest):
    """Handle contact form submission via SMTP email"""
    try:
        from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not SMTP_USER or not SMTP_PASSWORD:
            raise HTTPException(status_code=503, detail="Email service not configured")

        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_USER  # Send to ourselves
        msg["Subject"] = f"[Contact Form] {req.subject}"
        msg["Reply-To"] = req.email

        html_body = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {req.name}</p>
            <p><strong>Email:</strong> {req.email}</p>
            <p><strong>Subject:</strong> {req.subject}</p>
            <hr>
            <p><strong>Message:</strong></p>
            <p>{req.message}</p>
        </div>
        """
        msg.attach(MIMEText(html_body, "html"))

        if int(SMTP_PORT) == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, int(SMTP_PORT))
        else:
            server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT))
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, SMTP_USER, msg.as_string())
        server.quit()

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

@app.get("/api/proxy/resume-workflow")
async def proxy_resume_workflow(resume_url: str):
    """Proxy n8n resume URL call so the actual URL stays server-side"""
    if not resume_url:
        raise HTTPException(status_code=400, detail="resume_url is required")
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
