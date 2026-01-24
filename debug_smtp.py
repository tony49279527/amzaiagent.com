import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load config directly or from env
# Load config directly or from env
sys.path.append(os.getcwd()) # Ensure current directory is in path for module imports

# Hardcoded for debugging isolation
SMTP_HOST = "142.251.10.108"
SMTP_PORT = 465
SMTP_USER = "leetony4927@gmail.com"
SMTP_PASSWORD = "deaz lqro wons vcee"

print(f"DEBUG: SMTP Settings: Host={SMTP_HOST}, Port={SMTP_PORT}, User={SMTP_USER}")

def send_debug_email(to_email):
    print(f" Attempting to send email to {to_email}...")
    
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Debug Email Test - Amz AI Agent"
    
    html_content = """
    <html>
        <body>
            <h1>This is a debug email.</h1>
            <p>If you received this, the SMTP configuration is working.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    import ssl
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        if int(SMTP_PORT) == 465 or int(SMTP_PORT) == 587: # Try logic adaptable to both, using 465 first
             # Reverting to 465 for SSL test with unverified context
            print(f" Using SMTP_SSL (Implicit SSL) on port {SMTP_PORT} with UNVERIFIED context")
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.set_debuglevel(1)
                print(" Logging in...")
                server.login(SMTP_USER, SMTP_PASSWORD)
                print(" Sending email...")
                server.sendmail(SMTP_USER, to_email, msg.as_string())
                print(" Email sent successfully!")


    except Exception as e:
        print(f" ERROR: Failed to send email: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_email = sys.argv[1]
    else:
        target_email = "aurotony4927@gmail.com"
        
    send_debug_email(target_email)
