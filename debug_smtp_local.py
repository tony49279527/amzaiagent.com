
import smtplib
import ssl
import traceback

SMTP_PORT = 465
SMTP_SERVER = "smtp.gmail.com"
SMTP_USER = "leetony4927@gmail.com"
# Password with spaces stripped manually
SMTP_PASSWORD = "pvcgrjjvmghikreq"

def test_smtp_connection():
    print(f"Testing connection to {SMTP_SERVER}:{SMTP_PORT}...")
    print(f"User: {SMTP_USER}")
    
    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            print("Connected to server.")
            print("Attempting login...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ LOGIN SUCCESSFUL! Credentials are valid.")
            
            # Send a test email to self
            subject = "Local SMTP Debug Test"
            body = "If you receive this, the credentials are completely valid."
            message = f"Subject: {subject}\n\n{body}"
            
            server.sendmail(SMTP_USER, "aurotony4927@gmail.com", message)
            print("✅ EMAIL SENT SUCCESSFULY from local script.")
            return True
            
    except Exception as e:
        print("\n❌ CONNECTION FAILED")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_smtp_connection()
