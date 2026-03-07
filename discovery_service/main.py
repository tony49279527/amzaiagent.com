"""
FastAPI Main Application for Product Discovery Service
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
import httpx
import json
import threading
import hashlib
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional, Any

from .models import DiscoveryRequest, DiscoveryResponse, UserTier
from .analyzer import ProductDiscoveryAnalyzer
from .config import DEFAULT_MODEL_FREE, PRO_MODELS
from .email_service import send_email_report

app = FastAPI(
    title="Product Discovery API",
    description="AI-powered Amazon product discovery and analysis service",
    version="1.0.0"
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return 404.html with proper 404 status for page-not-found errors (fixes Soft 404)"""
    if exc.status_code == 404 and os.path.exists("404.html"):
        with open("404.html", "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(content=html, status_code=404)
    # Re-raise for other HTTP exceptions (FastAPI will handle normally)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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

@app.get("/health")
async def health_check():
    """Health check endpoint (avoids conflicting with /)"""
    return {"service": "Product Discovery API", "status": "running", "version": "1.0.0"}

@app.get("/index.html")
async def redirect_index():
    """Redirect /index.html to / for canonical URL"""
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)

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
        # CRITICAL: Force no-cache for HTML files to ensure latest version
        from starlette.responses import FileResponse
        response = FileResponse(file_path)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    # Check if it's a blog post (e.g. blog/xxx.html requested as xxx.html? No, usually it's /blog/xxx)
    # If filename matches a known page, return it.
    
    raise HTTPException(status_code=404, detail="Page not found")

def _get_blog_slug_to_id() -> dict:
    """Map URL slug -> canonical post id from posts_en.json (for redirect)"""
    mapping = {}
    path = "data/blog/posts_en.json"
    if not os.path.exists(path):
        return mapping
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
        for p in posts:
            pid = p.get("id") or p.get("slug", "")
            if pid:
                mapping[pid] = pid
                mapping[pid.replace(".html", "")] = pid
    except Exception:
        pass
    return mapping


# Handle blog post paths if they are like /blog/some-post.html
@app.get("/blog/{post_slug}.html")
async def read_blog_post(post_slug: str):
    # Strategy 1: If static HTML exists in data/blog/
    path1 = f"data/blog/{post_slug}.html"
    if os.path.exists(path1):
        return FileResponse(path1)

    slug_to_id = _get_blog_slug_to_id()
    canonical_id = slug_to_id.get(post_slug)
    if not canonical_id:
        raise HTTPException(status_code=404, detail="Blog post not found")

    # Valid slug - redirect to canonical blog-post.html?id=xxx for proper indexing
    if os.path.exists("blog-post.html"):
        from starlette.responses import RedirectResponse
        return RedirectResponse(url=f"/blog-post.html?id={canonical_id}", status_code=301)

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

# Store for completed reports (fallback when Supabase not configured)
reports_store = {}

# Payment state persistence (fallback). In production, use a real external DB.
PAYMENT_STATE_FILE = os.getenv(
    "PAYMENT_STATE_FILE",
    os.path.join(os.path.dirname(__file__), ".payment_state.json")
)
_payment_state_lock = threading.Lock()
paid_reports = set()  # tracks paid emails
verified_sessions = set()  # tracks verified checkout session IDs
paid_orders = set()  # tracks paid order IDs
paid_order_to_email = {}  # order_id -> customer_email


def _persist_payment_state():
    state = {
        "paid_reports": sorted(paid_reports),
        "verified_sessions": sorted(verified_sessions),
        "paid_orders": sorted(paid_orders),
        "paid_order_to_email": paid_order_to_email,
    }
    tmp_path = PAYMENT_STATE_FILE + ".tmp"
    with _payment_state_lock:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp_path, PAYMENT_STATE_FILE)


def _load_payment_state():
    if not os.path.exists(PAYMENT_STATE_FILE):
        return
    try:
        with open(PAYMENT_STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        paid_reports.update(state.get("paid_reports", []))
        verified_sessions.update(state.get("verified_sessions", []))
        paid_orders.update(state.get("paid_orders", []))
        paid_order_to_email.update(state.get("paid_order_to_email", {}))
    except Exception as e:
        print(f"Payment state load failed: {e}")


_load_payment_state()

# Lightweight analytics log for conversion funnel visibility.
ANALYTICS_LOG_FILE = os.getenv(
    "ANALYTICS_LOG_FILE",
    os.path.join(os.path.dirname(__file__), "analytics_events.jsonl")
)
_analytics_lock = threading.Lock()


def _hash_email(email: str) -> Optional[str]:
    normalized = (email or "").strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _sanitize_event_value(value: Any) -> Any:
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        return value[:240]
    if isinstance(value, list):
        return [_sanitize_event_value(v) for v in value[:12]]
    if isinstance(value, dict):
        cleaned = {}
        for key, val in list(value.items())[:24]:
            k = str(key)[:64]
            if "email" in k.lower():
                cleaned[f"{k}_hash"] = _hash_email(str(val))
                continue
            if "session" in k.lower():
                session_raw = str(val)
                cleaned[k] = session_raw[:6] + "***" if session_raw else ""
                continue
            cleaned[k] = _sanitize_event_value(val)
        return cleaned
    return str(value)[:240]


def _log_event(event_name: str, payload: Optional[dict] = None, req: Optional[Request] = None):
    if not event_name:
        return
    event = {
        "ts": _dt.utcnow().isoformat() + "Z",
        "event": event_name[:80],
        "payload": _sanitize_event_value(payload or {}),
    }
    if req is not None:
        event["path"] = req.url.path[:120]
        event["method"] = req.method
        event["ip"] = req.client.host if req.client else "unknown"
        event["ua"] = (req.headers.get("user-agent") or "")[:180]
    try:
        line = json.dumps(event, ensure_ascii=True)
        with _analytics_lock:
            with open(ANALYTICS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception as e:
        print(f"Analytics log write failed: {e}")


@app.get("/models")
async def get_available_models():
    """Get list of available models for Pro users"""
    return {
        "free_model": DEFAULT_MODEL_FREE,
        "pro_models": PRO_MODELS,
        "default_pro_model": PRO_MODELS[0]
    }


class TrackEventRequest(PydanticBaseModel):
    event: str
    payload: Optional[dict] = None


@app.post("/api/track")
async def track_event(req: TrackEventRequest, request: Request):
    """Client-side analytics events for page views and key clicks."""
    event_name = (req.event or "").strip()
    if not event_name or len(event_name) > 80:
        raise HTTPException(status_code=400, detail="invalid event")
    _log_event(f"web.{event_name}", req.payload, request)
    return {"status": "ok"}


@app.get("/api/discovery-report/{report_id}")
async def get_discovery_report(report_id: str, request: Request):
    """Fetch a completed discovery report by ID (for discovery_report.html)"""
    report = reports_store.get(report_id)
    if not report:
        try:
            from .report_store import get_report
            report = get_report(report_id)
        except Exception:
            pass
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not yet ready")
    # Report access rule:
    # - Free reports (DEFAULT_MODEL_FREE) can be read in full.
    # - Pro reports require final payment (paid_orders contains report_id).
    is_pro_report = report.model_used != DEFAULT_MODEL_FREE
    full_report_unlocked = (not is_pro_report) or (report_id in paid_orders)
    _log_event(
        "discovery.report_view",
        {"report_id": report_id, "is_pro_report": is_pro_report, "unlocked": full_report_unlocked},
        request
    )

    # Extract executive summary from first ## section if no dedicated field
    executive_summary = None
    if report.report_markdown:
        import re
        match = re.search(r'^##\s+(?:Executive Summary|Summary|Overview)\s*\n([\s\S]*?)(?=\n##\s|\Z)', report.report_markdown, re.IGNORECASE)
        if match:
            executive_summary = match.group(1).strip()
        elif report.report_markdown:
            sections = report.report_markdown.split('\n## ')
            if len(sections) > 1:
                executive_summary = sections[1].strip()[:2000]
    return {
        "report_id": report.report_id,
        "keywords": report.keywords,
        "category": report.category,
        "user_email": report.user_email,
        "marketplace": report.marketplace,
        "executive_summary": executive_summary,
        "report_markdown": report.report_markdown if full_report_unlocked else None,
        "report_html": report.report_html if full_report_unlocked else None,
        "full_report_unlocked": full_report_unlocked,
        "generated_at": report.generated_at,
        "model_used": report.model_used,
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
        # Persist to Supabase when configured
        try:
            from .report_store import save_report
            save_report(report)
        except Exception as e:
            print(f"Report persistence failed: {e}")

        # Determine if this is a Pro flow that requires payment
        is_pro_user = request.user_tier == UserTier.PRO
        
        # Send email with report (Full for Free, Preview+Link for Pro)
        await send_email_report(report, is_pro_flow=is_pro_user)
        _log_event(
            "discovery.completed",
            {
                "task_id": task_id,
                "report_id": report.report_id,
                "tier": request.user_tier.value,
                "user_email": request.user_email
            }
        )
        
        print(f"Report {report.report_id} completed and stored")
    except Exception as e:
        print(f"Error in analysis task: {str(e)}")
        # If task_id exists, emit error
        if task_id:
            await progress_manager.emit(task_id, "Error", "Analysis Failed", 0, {"error": str(e)})
            
        # Send failure notification email
        from .email_service import send_failure_email
        await send_failure_email(request.user_email, request.keywords, str(e))
        _log_event(
            "discovery.failed",
            {"task_id": task_id, "tier": request.user_tier.value, "user_email": request.user_email, "error": str(e)}
        )

@app.post("/api/discovery/start-task", response_model=DiscoveryResponse)
async def start_analysis_task(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Start analysis with Real-time Progress Tracking
    Returns a task_id immediately. Client should then connect to /ws/progress/{task_id}
    """
    try:
        _log_event(
            "discovery.start_requested",
            {
                "tier": request.user_tier.value,
                "marketplace": request.marketplace.value,
                "has_reference_asins": bool(request.reference_asins),
            },
            http_request
        )
        # Validate request
        if not request.category or not request.keywords:
            raise HTTPException(status_code=400, detail="Category and keywords are required")

        # Pro tier: verify payment before starting (Polar webhook populates paid_reports)
        if request.user_tier == UserTier.PRO:
            if request.user_email not in paid_reports:
                _log_event(
                    "discovery.pro_blocked_unpaid",
                    {"email_hash": _hash_email(request.user_email)},
                    http_request
                )
                raise HTTPException(
                    status_code=402,
                    detail="Payment required. Please complete your Pro payment before starting analysis. If you just paid, wait a moment and try again."
                )

        task_id = str(uuid.uuid4())
        _log_event(
            "discovery.started",
            {"task_id": task_id, "tier": request.user_tier.value},
            http_request
        )
        
        # Start analysis in background with task_id
        background_tasks.add_task(run_analysis_task, request, task_id)
        
        return DiscoveryResponse(
            success=True,
            message="Analysis started. Connect to WebSocket for progress.",
            estimated_delivery_minutes=10,
            report_id=task_id  # Using report_id field to pass task_id for now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting analysis: {str(e)}")
        _log_event("discovery.start_failed", {"error": str(e)}, http_request)
        raise HTTPException(status_code=500, detail=str(e))

from .payment_service import payment_service

@app.get("/api/payments/verify-session")
async def verify_payment_session(session_id: str, request: Request):
    """Verify checkout session. Uses verified_sessions (from n8n) or direct Stripe API as fallback."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    if session_id in verified_sessions:
        _log_event("payment.session_verify", {"status": "paid", "source": "memory", "session_id": session_id}, request)
        return {"status": "paid", "session_id": session_id}

    # Fallback: direct Stripe API verification (handles race when n8n webhook is slow)
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key and session_id.startswith("cs_"):
        try:
            import stripe
            stripe.api_key = stripe_key
            sess = stripe.checkout.Session.retrieve(session_id)
            if getattr(sess, "payment_status", None) == "paid" and getattr(sess, "status", None) == "complete":
                verified_sessions.add(session_id)
                _persist_payment_state()
                _log_event("payment.session_verify", {"status": "paid", "source": "stripe_api", "session_id": session_id}, request)
                return {"status": "paid", "session_id": session_id}
        except Exception as e:
            print(f"Stripe verify fallback error: {e}")

    _log_event("payment.session_verify", {"status": "pending", "session_id": session_id}, request)
    return {"status": "pending", "session_id": session_id}


class ConfirmSessionRequest(PydanticBaseModel):
    session_id: str
    customer_email: Optional[str] = None  # When provided, also add to paid_reports for Pro verification
    order_id: Optional[str] = None


class ConfirmBalancePaidRequest(PydanticBaseModel):
    session_id: str
    report_id: str


@app.post("/api/payments/confirm-balance-paid")
async def confirm_balance_paid(req: ConfirmBalancePaidRequest, request: Request):
    """
    After user pays $25 balance on discovery_report page: verify session, add report to paid_orders,
    and send full report email. Idempotent: if report_id already in paid_orders, only returns success.
    """
    if not req.session_id or not req.report_id:
        raise HTTPException(status_code=400, detail="session_id and report_id required")
    # 1) Verify session is paid (memory or Stripe API)
    if req.session_id not in verified_sessions:
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key and req.session_id.startswith("cs_"):
            try:
                import stripe
                stripe.api_key = stripe_key
                sess = stripe.checkout.Session.retrieve(req.session_id)
                if getattr(sess, "payment_status", None) == "paid" and getattr(sess, "status", None) == "complete":
                    verified_sessions.add(req.session_id)
                    _persist_payment_state()
            except Exception as e:
                print(f"Stripe verify error in confirm-balance-paid: {e}")
                raise HTTPException(status_code=402, detail="Payment not verified")
        else:
            raise HTTPException(status_code=402, detail="Payment not verified")
    # 2) Mark report as paid
    already_paid = req.report_id in paid_orders
    paid_orders.add(req.report_id)
    _persist_payment_state()
    _log_event(
        "payment.balance_paid_confirmed",
        {"report_id": req.report_id, "session_id": req.session_id, "already_paid": already_paid},
        request
    )
    # 3) Send full report email once
    if not already_paid:
        report = reports_store.get(req.report_id)
        if not report:
            try:
                from .report_store import get_report
                report = get_report(req.report_id)
            except Exception as e:
                print(f"confirm_balance_paid: get_report failed: {e}")
        if report:
            len_md = len(report.report_markdown or "")
            len_html = len(report.report_html or "")
            print(f"confirm_balance_paid: report_id={req.report_id} report_markdown={len_md} chars report_html={len_html} chars")
            if len_md < 500 and len_html < 500:
                print(f"Warning: report content very short. Full report email may be incomplete.")
            try:
                await send_email_report(report, is_pro_flow=False)
                _log_event("report.full_email_sent", {"report_id": req.report_id}, request)
            except Exception as e:
                print(f"Failed to send full report email: {e}")
                _log_event("report.full_email_failed", {"report_id": req.report_id, "error": str(e)}, request)
    return {"status": "ok", "report_id": req.report_id}


@app.post("/api/payments/confirm-session")
async def confirm_payment_session(req: ConfirmSessionRequest, request: Request):
    """
    Called by n8n when Stripe payment succeeds. Adds session to verified_sessions.
    If customer_email provided, also adds to paid_reports for Discovery Pro verification.
    """
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    verified_sessions.add(req.session_id)
    if req.customer_email:
        paid_reports.add(req.customer_email)
    if req.order_id:
        paid_orders.add(req.order_id)
        if req.customer_email:
            paid_order_to_email[req.order_id] = req.customer_email
    _persist_payment_state()
    _log_event(
        "payment.session_confirmed",
        {"session_id": req.session_id, "order_id": req.order_id, "customer_email": req.customer_email},
        request
    )
    return {"status": "ok", "session_id": req.session_id}

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

    # Verify webhook signature
    if WEBHOOK_SECRET:
        import hmac, hashlib
        expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
    else:
        print("WARNING: POLAR_WEBHOOK_SECRET not set — webhook signature verification disabled")

    import json
    data = json.loads(payload)
    event_type = data.get("type")
    _log_event("payment.webhook_received", {"event_type": event_type}, request)
    
    if event_type == "checkout.updated":
        checkout_data = data.get("data", {})
        status = checkout_data.get("status")
        
        if status == "succeeded":
            # Extract our custom data or find by email
            email = checkout_data.get("customer_email")
            print(f"Payment succeeded for {email}")
            # In a real app, mark the report as paid in DB
            # For now, we'll use the email to match or a metadata field if supported
            paid_reports.add(email)
            metadata = checkout_data.get("metadata") or {}
            order_id = metadata.get("order_id") or metadata.get("orderId")
            if order_id:
                paid_orders.add(order_id)
                if email:
                    paid_order_to_email[order_id] = email
            # Also track checkout session ID if available
            checkout_id = checkout_data.get("id") or checkout_data.get("checkout_id")
            if checkout_id:
                verified_sessions.add(checkout_id)
            _persist_payment_state()
            _log_event(
                "payment.webhook_succeeded",
                {"customer_email": email, "order_id": order_id, "checkout_id": checkout_id},
                request
            )

    return {"status": "ok"}

@app.get("/test-email")
async def test_email_endpoint(email: str, type: str = "success"):
    """Immediate test endpoint to verify email delivery"""
    try:
        if os.getenv("ENABLE_TEST_EMAIL_ENDPOINT", "").lower() != "true":
            raise HTTPException(status_code=404, detail="Not found")
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
    except HTTPException:
        raise
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
        _log_event("contact.submit_attempt", {"email": req.email, "subject_len": len(req.subject)}, request)
        # Input validation
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', req.email):
            _log_event("contact.submit_rejected", {"reason": "invalid_email", "email": req.email}, request)
            raise HTTPException(status_code=400, detail="Invalid email address")
        if len(req.name) > 100 or len(req.subject) > 200 or len(req.message) > 5000:
            _log_event("contact.submit_rejected", {"reason": "input_too_long", "email": req.email}, request)
            raise HTTPException(status_code=400, detail="Input too long")

        # Simple rate limiting (5 per hour per IP)
        client_ip = request.client.host if request.client else "unknown"
        now = _dt.now()
        if client_ip in _contact_rate_limit:
            count, window_start = _contact_rate_limit[client_ip]
            if (now - window_start).seconds < 3600:
                if count >= 5:
                    _log_event("contact.submit_rejected", {"reason": "rate_limited", "email": req.email}, request)
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
            _log_event("contact.submit_failed", {"reason": "smtp_not_configured"}, request)
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
        _log_event("contact.submit_success", {"email": req.email}, request)
        return {"status": "success", "message": "Your message has been sent. We'll get back to you soon."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Contact form error: {e}")
        _log_event("contact.submit_failed", {"reason": "internal_error", "error": str(e)}, request)
        raise HTTPException(status_code=500, detail="Failed to send message. Please try again later.")

# === Backend Proxy Endpoints ===
# These proxy n8n webhook calls so that webhook URLs are not exposed in frontend code.
N8N_CHECKOUT_URL = os.getenv("N8N_CHECKOUT_WEBHOOK_URL", "")
N8N_FREE_ANALYSIS_URL = os.getenv("N8N_FREE_ANALYSIS_URL", "")
# Support both legacy and current env var names to prevent deploy mismatches.
N8N_PRO_ANALYSIS_URL = os.getenv("N8N_PRO_ANALYSIS_WEBHOOK_URL", "") or os.getenv("N8N_PRO_ANALYSIS_URL", "")
N8N_SEND_REPORT_URL = os.getenv("N8N_SEND_REPORT_WEBHOOK_URL", "") or os.getenv("N8N_SEND_REPORT_URL", "")

# CRITICAL: Validate webhook URLs on startup
print("=" * 60)
print("[STARTUP] Webhook Configuration Check")
print("=" * 60)
print(f"[CONFIG] N8N_FREE_ANALYSIS_URL configured: {'YES' if N8N_FREE_ANALYSIS_URL else 'NO'}")
print(f"[CONFIG] N8N_PRO_ANALYSIS_URL configured: {'YES' if N8N_PRO_ANALYSIS_URL else 'NO'}")

if N8N_FREE_ANALYSIS_URL:
    free_suffix = N8N_FREE_ANALYSIS_URL[-20:]
    print(f"[CONFIG] Free webhook ends with: ...{free_suffix}")
    # Expected: ...c6b3034f-250a-433f-9017-c14c3f8c7f9f
    if "c6b3034f-250a-433f-9017-c14c3f8c7f9f" in N8N_FREE_ANALYSIS_URL:
        print("[CONFIG] ✓ Free webhook URL matches expected pattern")
    else:
        print("[WARNING] Free webhook URL does not match expected pattern!")

if N8N_PRO_ANALYSIS_URL:
    pro_suffix = N8N_PRO_ANALYSIS_URL[-20:]
    print(f"[CONFIG] Pro webhook ends with: ...{pro_suffix}")
    # Expected: ...3f76a439-5a54-4d08-97cd-6e98d7b6e034
    if "3f76a439-5a54-4d08-97cd-6e98d7b6e034" in N8N_PRO_ANALYSIS_URL:
        print("[CONFIG] ✓ Pro webhook URL matches expected pattern")
    else:
        print("[WARNING] Pro webhook URL does not match expected pattern!")

# CRITICAL CHECK: Ensure webhooks are different
if N8N_FREE_ANALYSIS_URL and N8N_PRO_ANALYSIS_URL:
    if N8N_FREE_ANALYSIS_URL == N8N_PRO_ANALYSIS_URL:
        print("[CRITICAL ERROR] Free and Pro webhooks are IDENTICAL!")
        print("[CRITICAL ERROR] This will cause routing errors!")
    else:
        print("[CONFIG] ✓ Free and Pro webhooks are different (correct)")
print("=" * 60)

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
async def proxy_create_checkout(req: CheckoutRequest, request: Request):
    """Proxy Stripe checkout creation to n8n (keeps webhook URL server-side)"""
    if not N8N_CHECKOUT_URL:
        _log_event("checkout.create_failed", {"reason": "not_configured", "amount": req.amount}, request)
        raise HTTPException(status_code=503, detail="Payment service not configured")
    try:
        _log_event("checkout.create_requested", {"amount": req.amount, "order_id": req.order_id}, request)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_CHECKOUT_URL, data={
                "amount": req.amount,
                "order_id": req.order_id,
                "success_url": req.success_url,
                "cancel_url": req.cancel_url,
            })
            resp.raise_for_status()
            _log_event("checkout.create_success", {"amount": req.amount, "order_id": req.order_id}, request)
            return resp.json()
    except Exception as e:
        print(f"Checkout proxy error: {e}")
        _log_event("checkout.create_failed", {"reason": "upstream_error", "error": str(e), "order_id": req.order_id}, request)
        raise HTTPException(status_code=502, detail="Payment service unavailable")

@app.post("/api/proxy/pro-analysis")
async def proxy_pro_analysis(payload: dict, request: Request):
    """Proxy Pro analysis submission to n8n - CRITICAL: Must use Pro webhook URL"""
    if not N8N_PRO_ANALYSIS_URL:
        print("[ERROR] N8N_PRO_ANALYSIS_URL is not configured!")
        _log_event("analysis.pro_failed", {"reason": "not_configured"}, request)
        raise HTTPException(status_code=503, detail="Pro analysis service not configured")
    
    # CRITICAL VALIDATION: Ensure we're using the PRO webhook, not FREE
    if N8N_PRO_ANALYSIS_URL == N8N_FREE_ANALYSIS_URL:
        print(f"[CRITICAL ERROR] Pro and Free webhooks are the same! URL: {N8N_PRO_ANALYSIS_URL}")
        raise HTTPException(status_code=500, detail="Configuration error: Pro and Free webhooks cannot be the same")
    
    try:
        # Server-side paywall: ignore client-side unlock state and require payment proof.
        user_email = str(payload.get("user_email", "")).strip()
        order_id = str(payload.get("order_id", "")).strip()
        print(f"[PRO ANALYSIS] Request received - Email: {user_email}, Order: {order_id}")
        print(f"[PRO ANALYSIS] Webhook URL (last 20 chars): ...{N8N_PRO_ANALYSIS_URL[-20:]}")
        _log_event(
            "analysis.pro_requested",
            {
                "user_email": user_email,
                "order_id": order_id,
                "main_asins_count": len(payload.get("main_asins", []) or []),
                "competitor_asins_count": len(payload.get("competitor_asins", []) or []),
                "webhook_url_suffix": N8N_PRO_ANALYSIS_URL[-20:] if N8N_PRO_ANALYSIS_URL else "NOT_SET",
            },
            request
        )
        email_paid = bool(user_email and user_email in paid_reports)
        order_paid = bool(order_id and order_id in paid_orders)
        if not email_paid and not order_paid:
            _log_event("analysis.pro_rejected", {"reason": "payment_required", "user_email": user_email, "order_id": order_id}, request)
            raise HTTPException(
                status_code=402,
                detail="Payment required. Please complete payment before submitting Pro analysis."
            )
        if order_paid and user_email:
            mapped_email = paid_order_to_email.get(order_id)
            if mapped_email and mapped_email != user_email:
                _log_event("analysis.pro_rejected", {"reason": "order_email_mismatch", "order_id": order_id, "user_email": user_email}, request)
                raise HTTPException(
                    status_code=403,
                    detail="Order does not match this email."
                )

        form_data = {}
        for key, value in payload.items():
            if isinstance(value, (list, dict)):
                import json
                form_data[key] = json.dumps(value)
            else:
                form_data[key] = str(value)
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Debug: Log the actual webhook URL being used
            print(f"[DEBUG] Pro analysis webhook URL: {N8N_PRO_ANALYSIS_URL}")
            _log_event("analysis.pro_webhook_called", {"webhook_url": N8N_PRO_ANALYSIS_URL, "order_id": order_id}, request)
            resp = await client.post(N8N_PRO_ANALYSIS_URL, data=form_data)
            resp.raise_for_status()
            _log_event("analysis.pro_success", {"order_id": order_id, "user_email": user_email}, request)
            try:
                return resp.json()
            except Exception:
                return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Pro analysis proxy error: {e}")
        _log_event("analysis.pro_failed", {"reason": "upstream_error", "error": str(e), "order_id": order_id}, request)
        raise HTTPException(status_code=502, detail="Pro analysis service unavailable")

@app.post("/api/proxy/free-analysis")
async def proxy_free_analysis(payload: dict, request: Request):
    """Proxy Free analysis submission to n8n - CRITICAL: Must use Free webhook URL"""
    if not N8N_FREE_ANALYSIS_URL:
        print("[ERROR] N8N_FREE_ANALYSIS_URL is not configured!")
        _log_event("analysis.free_failed", {"reason": "not_configured"}, request)
        raise HTTPException(status_code=503, detail="Free analysis service not configured")
    
    # CRITICAL VALIDATION: Ensure we're using the FREE webhook, not PRO
    if N8N_FREE_ANALYSIS_URL == N8N_PRO_ANALYSIS_URL:
        print(f"[CRITICAL ERROR] Free and Pro webhooks are the same! URL: {N8N_FREE_ANALYSIS_URL}")
        raise HTTPException(status_code=500, detail="Configuration error: Free and Pro webhooks cannot be the same")
    
    try:
        user_email = str(payload.get("user_email", "")).strip()
        order_id = str(payload.get("order_id", "")).strip()
        print(f"[FREE ANALYSIS] Request received - Email: {user_email}, Order: {order_id}")
        print(f"[FREE ANALYSIS] Webhook URL (last 20 chars): ...{N8N_FREE_ANALYSIS_URL[-20:]}")
        _log_event(
            "analysis.free_requested",
            {
                "user_email": user_email,
                "order_id": order_id,
                "main_asins_count": len(payload.get("main_asins", []) or []),
                "competitor_asins_count": len(payload.get("competitor_asins", []) or []),
                "webhook_url_suffix": N8N_FREE_ANALYSIS_URL[-20:] if N8N_FREE_ANALYSIS_URL else "NOT_SET",
            },
            request
        )
        form_data = {}
        for key, value in payload.items():
            if isinstance(value, (list, dict)):
                import json
                form_data[key] = json.dumps(value)
            else:
                form_data[key] = str(value)
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Debug: Log the actual webhook URL being used
            print(f"[DEBUG] Free analysis webhook URL: {N8N_FREE_ANALYSIS_URL}")
            _log_event("analysis.free_webhook_called", {"webhook_url": N8N_FREE_ANALYSIS_URL, "user_email": user_email}, request)
            resp = await client.post(N8N_FREE_ANALYSIS_URL, data=form_data)
            resp.raise_for_status()
            _log_event("analysis.free_success", {"user_email": user_email}, request)
            try:
                return resp.json()
            except Exception:
                return {"status": "ok"}
    except Exception as e:
        print(f"Free analysis proxy error: {e}")
        _log_event("analysis.free_failed", {"reason": "upstream_error", "error": str(e)}, request)
        raise HTTPException(status_code=502, detail="Free analysis service unavailable")

@app.post("/api/proxy/send-full-report")
async def proxy_send_full_report(req: SendReportRequest, request: Request):
    """Proxy full report trigger to n8n"""
    if not N8N_SEND_REPORT_URL:
        _log_event("report.send_full_failed", {"reason": "not_configured", "order_id": req.order_id}, request)
        raise HTTPException(status_code=503, detail="Report service not configured")
    try:
        _log_event("report.send_full_requested", {"order_id": req.order_id, "action": req.action}, request)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_SEND_REPORT_URL, data={
                "order_id": req.order_id,
                "action": req.action,
            })
            resp.raise_for_status()
            _log_event("report.send_full_success", {"order_id": req.order_id}, request)
            return {"status": "ok"}
    except Exception as e:
        print(f"Send report proxy error: {e}")
        _log_event("report.send_full_failed", {"reason": "upstream_error", "order_id": req.order_id, "error": str(e)}, request)
        raise HTTPException(status_code=502, detail="Report service unavailable")

N8N_ALLOWED_HOSTS = os.getenv("N8N_ALLOWED_HOSTS", "").split(",")

@app.get("/api/proxy/resume-workflow")
async def proxy_resume_workflow(resume_url: str, request: Request):
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
        _log_event("workflow.resume_rejected", {"reason": "host_not_allowed", "host": parsed.hostname}, request)
        raise HTTPException(status_code=403, detail="URL not allowed")
    try:
        _log_event("workflow.resume_requested", {"host": parsed.hostname, "path": parsed.path}, request)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(resume_url)
            _log_event("workflow.resume_success", {"code": resp.status_code, "host": parsed.hostname}, request)
            return {"status": "ok", "code": resp.status_code}
    except Exception as e:
        print(f"Resume workflow proxy error: {e}")
        _log_event("workflow.resume_failed", {"host": parsed.hostname, "error": str(e)}, request)
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
