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
