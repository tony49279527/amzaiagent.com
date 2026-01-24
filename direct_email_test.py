import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env manually to be sure
load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
# ...
try:
    print(f"1. Connecting to {SMTP_HOST}:{SMTP_PORT} (SSL)...")
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    server.set_debuglevel(1)
    
    # SSL is implicit, no starttls needed
    
    print("3. Logging in...")
    # Try logging in
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ Login Successful!")
    
    print("4. Sending Test Email...")
    msg = MIMEText("This is a direct SMTP test from the Amz AI debugging script.")
    msg["Subject"] = "Amz AI SMTP Debug Test"
    msg["From"] = SMTP_USER
    msg["To"] = TARGET_EMAIL
    
    server.sendmail(SMTP_USER, TARGET_EMAIL, msg.as_string())
    print(f"✅ Email sent to {TARGET_EMAIL}")
    
    server.quit()
    
except Exception as e:
    print(f"❌ SMTP Error: {e}")
