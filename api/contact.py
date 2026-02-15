import os
import json
import smtplib
from email.mime.text import MIMEText
from supabase_client import save_contact_inquiry

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
TARGET_EMAIL = os.getenv("CONTACT_TARGET_EMAIL", SMTP_USER)

def process_contact_request(data):
    """
    Handles the contact form request from the frontend.
    1. Extracts Name, Email, Subject, Message.
    2. Saves to Supabase.
    3. Sends an email notification to the owner.
    """
    name = data.get('name', 'N/A')
    email = data.get('email', 'N/A')
    subject = data.get('subject', 'No Subject')
    message = data.get('message', 'No Message')

    print(f"Contact Inquiry from {name} ({email}): {subject}")

    # 1. Save to Supabase
    db_success = save_contact_inquiry(name, email, subject, message)
    
    # 2. Send Email Notification
    email_success = send_notification_email(name, email, subject, message)

    if db_success or email_success:
        return {
            "message": "Your message has been received! We'll get back to you soon.",
            "status": "success"
        }, 200
    else:
        return {
            "message": "There was an error processing your request. Please email us directly.",
            "status": "error"
        }, 500

def send_notification_email(name, email, subject, message):
    """
    Sends a notification email about the new contact inquiry.
    """
    try:
        if not SMTP_USER or not SMTP_PASSWORD or not TARGET_EMAIL:
            print("SMTP not configured for contact notifications")
            return False

        body = f"""
        New Contact Inquiry from Amz AI Agent:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        
        ---
        Check Supabase for full history.
        """
        
        msg = MIMEText(body)
        msg["Subject"] = f"New Contact: {subject}"
        msg["From"] = SMTP_USER
        msg["To"] = TARGET_EMAIL
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, TARGET_EMAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send notification email: {e}")
        return False
