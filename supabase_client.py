import os
from supabase import create_client, Client

# Initialize Supabase Client
# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

supabase: Client = None

if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

def create_report(asin, marketplace):
    """
    Inserts a new report into InputRequests/AnalysisReports table.
    Returns the new report_id.
    """
    if not supabase:
        print(f"Supabase not initialized. Mocking create_report for {asin}")
        return "mock-report-id"

    data = {
        "asin": asin,
        "marketplace": marketplace,
        "status": "pending"
    }
    try:
        response = supabase.table("AnalysisReports").insert(data).execute()
        # response.data is a list of inserted records
        if response.data:
            return response.data[0]["id"]
    except Exception as e:
        print(f"Supabase insert failed: {e}")
    return None

def update_report_done(report_id, result_json):
    """
    Updates report status to 'done' and saves the result JSON.
    """
    if not supabase:
        print(f"Supabase not initialized. Mocking update_report_done for {report_id}")
        return

    data = {
        "status": "done",
        "result_json": result_json,
        "error_message": None
    }
    try:
        supabase.table("AnalysisReports").update(data).eq("id", report_id).execute()
    except Exception as e:
        print(f"Supabase update failed: {e}")

def update_report_failed(report_id, error_message):
    """
    Updates report status to 'failed' and saves the error message.
    """
    if not supabase:
        print(f"Supabase not initialized. Mocking update_report_failed for {report_id}")
        return

    data = {
        "status": "failed",
        "error_message": error_message
    }
    try:
        supabase.table("AnalysisReports").update(data).eq("id", report_id).execute()
    except Exception as e:
        print(f"Supabase update failed: {e}")

def get_global_config(key):
    """
    Fetches a configuration value by key from GlobalConfig.
    Returns the 'value' string directly, or None if not found.
    """
    if not supabase:
        return None

    try:
        response = supabase.table("GlobalConfig").select("value").eq("key", key).execute()
        if response.data:
            return response.data[0]["value"]
    except Exception as e:
        print(f"Supabase select failed: {e}")
    return None

def get_system_prompt(slug):
    """
    Fetches prompt configuration by slug from SystemPrompts.
    Returns a dict with system_prompt, user_prompt_template, model_params.
    """
    if not supabase:
        # Fallback for basic local testing if needed, or just return None
        return None

    try:
        response = supabase.table("SystemPrompts").select("*").eq("slug", slug).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Supabase select failed: {e}")
    return None

def get_report(report_id):
    """
    Fetches a specific report by ID from AnalysisReports.
    Returns the report dict or None.
    """
    if not supabase:
        print(f"Supabase not initialized. Mocking get_report for {report_id}")
        return None

    try:
        response = supabase.table("AnalysisReports").select("*").eq("id", report_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Supabase select failed: {e}")
    return None

def save_contact_inquiry(name, email, subject, message):
    """
    Inserts a new contact inquiry into ContactInquiries table.
    """
    if not supabase:
        print(f"Supabase not initialized. Mocking save_contact for {email}")
        return True

    data = {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message
    }
    try:
        supabase.table("ContactInquiries").insert(data).execute()
        return True
    except Exception as e:
        print(f"Supabase contact insert failed: {e}")
        return False
