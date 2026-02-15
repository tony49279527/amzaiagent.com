"""
Report storage for Discovery Service.
Uses Supabase when configured, falls back to in-memory store.
"""
import os
from typing import Optional
from .models import AnalysisReport

# In-memory fallback (lost on restart)
_reports_memory: dict = {}

def _get_supabase():
    """Lazy init Supabase client."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase init failed: {e}")
        return None

_supabase = None

def _supabase_client():
    global _supabase
    if _supabase is None:
        _supabase = _get_supabase()
    return _supabase

def save_report(report: AnalysisReport) -> bool:
    """Save report to Supabase or memory."""
    client = _supabase_client()
    if client:
        try:
            data = {
                "id": report.report_id,
                "user_email": report.user_email,
                "category": report.category,
                "keywords": report.keywords,
                "marketplace": report.marketplace,
                "report_markdown": report.report_markdown,
                "report_html": report.report_html,
                "generated_at": report.generated_at,
                "model_used": report.model_used,
                "sources_count": report.sources_count,
                "asins_analyzed": report.asins_analyzed,
            }
            client.table("DiscoveryReports").upsert(data, on_conflict="id").execute()
            return True
        except Exception as e:
            print(f"Supabase save_report failed: {e}")
    _reports_memory[report.report_id] = report
    return True

def get_report(report_id: str) -> Optional[AnalysisReport]:
    """Load report from Supabase or memory."""
    client = _supabase_client()
    if client:
        try:
            resp = client.table("DiscoveryReports").select("*").eq("id", report_id).execute()
            if resp.data and len(resp.data) > 0:
                row = resp.data[0]
                return AnalysisReport(
                    report_id=row["id"],
                    user_email=row["user_email"],
                    category=row["category"],
                    keywords=row["keywords"],
                    marketplace=row["marketplace"],
                    report_markdown=row.get("report_markdown", ""),
                    report_html=row.get("report_html", ""),
                    generated_at=row.get("generated_at", ""),
                    model_used=row.get("model_used", ""),
                    sources_count=row.get("sources_count", 0),
                    asins_analyzed=row.get("asins_analyzed", 0),
                )
        except Exception as e:
            print(f"Supabase get_report failed: {e}")
    return _reports_memory.get(report_id)


# === Payment Status Persistence ===

def mark_email_paid(email: str, checkout_id: str = None) -> bool:
    """Persist payment status to Supabase. Returns True if saved."""
    client = _supabase_client()
    if client:
        try:
            client.table("PaidReports").upsert(
                {"email": email, "checkout_id": checkout_id},
                on_conflict="email"
            ).execute()
            return True
        except Exception as e:
            print(f"Supabase mark_email_paid failed: {e}")
    return False


def is_email_paid(email: str) -> bool:
    """Check if email has paid via Supabase."""
    client = _supabase_client()
    if client:
        try:
            resp = client.table("PaidReports").select("email").eq("email", email).execute()
            return len(resp.data) > 0
        except Exception as e:
            print(f"Supabase is_email_paid failed: {e}")
    return False


def mark_session_verified(session_id: str, email: str = None) -> bool:
    """Persist verified session to Supabase."""
    client = _supabase_client()
    if client:
        try:
            client.table("VerifiedSessions").upsert(
                {"session_id": session_id, "email": email},
                on_conflict="session_id"
            ).execute()
            return True
        except Exception as e:
            print(f"Supabase mark_session_verified failed: {e}")
    return False


def is_session_verified(session_id: str) -> bool:
    """Check if session is verified via Supabase."""
    client = _supabase_client()
    if client:
        try:
            resp = client.table("VerifiedSessions").select("session_id").eq("session_id", session_id).execute()
            return len(resp.data) > 0
        except Exception as e:
            print(f"Supabase is_session_verified failed: {e}")
    return False


def mark_order_paid(order_id: str, email: str = None) -> bool:
    """Persist paid order to Supabase."""
    client = _supabase_client()
    if client:
        try:
            client.table("PaidOrders").upsert(
                {"order_id": order_id, "email": email},
                on_conflict="order_id"
            ).execute()
            return True
        except Exception as e:
            print(f"Supabase mark_order_paid failed: {e}")
    return False


def is_order_paid(order_id: str) -> bool:
    """Check if order is paid via Supabase."""
    client = _supabase_client()
    if client:
        try:
            resp = client.table("PaidOrders").select("order_id").eq("order_id", order_id).execute()
            return len(resp.data) > 0
        except Exception as e:
            print(f"Supabase is_order_paid failed: {e}")
    return False


def get_order_email(order_id: str) -> Optional[str]:
    """Get email associated with a paid order from Supabase."""
    client = _supabase_client()
    if client:
        try:
            resp = client.table("PaidOrders").select("email").eq("order_id", order_id).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data[0].get("email")
        except Exception as e:
            print(f"Supabase get_order_email failed: {e}")
    return None
