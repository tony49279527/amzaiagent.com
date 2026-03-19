import os
import json
import threading
from typing import Set, Dict, Any, Optional

# Fallback memory stores (useful for local dev or when Supabase is down)
_paid_emails: Set[str] = set()
_verified_sessions: Set[str] = set()
_paid_orders: Set[str] = set()
_paid_order_to_email: Dict[str, str] = {}
_lock = threading.Lock()

_supabase = None

def _get_supabase_client():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        _supabase = create_client(url, key)
        return _supabase
    except Exception as e:
        print(f"Supabase init failed in payment_store: {e}")
        return None

def _get_state(key: str) -> Optional[dict]:
    """Retrieve raw json state for a key."""
    client = _get_supabase_client()
    if client:
        try:
            resp = client.table("PaymentState").select("value").eq("key", key).execute()
            if resp.data:
                return resp.data[0]["value"]
        except Exception as e:
            print(f"PaymentState GET {key} failed: {e}")
    return None

def _set_state(key: str, value: dict) -> bool:
    """Upsert pure json state into Supabase."""
    client = _get_supabase_client()
    if client:
        try:
            data = {"key": key, "value": value}
            client.table("PaymentState").upsert(data, on_conflict="key").execute()
            return True
        except Exception as e:
            print(f"PaymentState SET {key} failed: {e}")
    return False

# ==================================
# Public API
# ==================================

def add_paid_email(email: str):
    email = email.lower().strip()
    with _lock:
        _paid_emails.add(email)
    _set_state(f"paid_email:{email}", {"paid": True})

def is_email_paid(email: str) -> bool:
    email = email.lower().strip()
    if email in _paid_emails:
        return True
    
    val = _get_state(f"paid_email:{email}")
    if val and val.get("paid"):
        with _lock:
            _paid_emails.add(email)
        return True
    return False

def add_verified_session(session_id: str):
    with _lock:
        _verified_sessions.add(session_id)
    _set_state(f"session:{session_id}", {"verified": True})

def is_session_verified(session_id: str) -> bool:
    if session_id in _verified_sessions:
        return True
    
    val = _get_state(f"session:{session_id}")
    if val and val.get("verified"):
        with _lock:
            _verified_sessions.add(session_id)
        return True
    return False

def add_paid_order(order_id: str, email: str = None):
    with _lock:
        _paid_orders.add(order_id)
        if email:
            email = email.lower().strip()
            _paid_order_to_email[order_id] = email
    
    _set_state(f"order:{order_id}", {"paid": True, "email": email})

def is_order_paid(order_id: str) -> bool:
    if order_id in _paid_orders:
        return True
        
    val = _get_state(f"order:{order_id}")
    if val and val.get("paid"):
        with _lock:
            _paid_orders.add(order_id)
            if val.get("email"):
                _paid_order_to_email[order_id] = val.get("email")
        return True
    return False

def get_order_email(order_id: str) -> Optional[str]:
    with _lock:
        if order_id in _paid_order_to_email:
            return _paid_order_to_email[order_id]
            
    val = _get_state(f"order:{order_id}")
    if val and val.get("email"):
        return val.get("email")
    return None