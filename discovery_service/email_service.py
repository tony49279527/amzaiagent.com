
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from .models import AnalysisReport

async def send_email_report(report: AnalysisReport, is_pro_flow: bool = False):
    """
    Send the analysis report via email.
    If is_pro_flow is True, sends a Preview + Payment Link instead of full report.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Error: SMTP credentials not set. Skipping email.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = report.user_email

        if is_pro_flow:
            # === PRO FLOW: Preview + Payment Link ===
            msg["Subject"] = f"Action Required: Complete Payment for {report.keywords} Analysis"
            
            # Extract preview (e.g., first 1500 chars or first section)
            preview_content = report.report_html[:2000] + "..." if report.report_html else report.report_markdown[:1000] + "..."
            
            # Payment Link (Production)
            payment_link = f"https://amzaiagent.com/report.html?id={report.report_id}&payment_pending=true"


            html_content = f"""
            <html>
                <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; background-color: #f3f4f6; margin: 0; padding: 0;">
                    <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                        <!-- Header -->
                        <div style="background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%); padding: 32px 24px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">Analysis Ready for Review</h1>
                            <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 16px;">Deposit Received • Final Step Required</p>
                        </div>

                        <!-- Content -->
                        <div style="padding: 32px 24px;">
                            <p style="margin-bottom: 24px; font-size: 16px;">
                                Hello, <br><br>
                                Your Pro AI Market Analysis for <strong>{report.keywords}</strong> is complete. 
                                As per your request, we have generated a deep-dive report including market gaps, sentiment analysis, and entry strategy.
                            </p>

                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                                <h3 style="margin-top: 0; color: #4b5563; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Report Preview</h3>
                                <div style="color: #64748b; font-size: 14px; max-height: 200px; overflow: hidden; position: relative;">
                                    {preview_content}
                                    <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 80px; background: linear-gradient(transparent, #f8fafc);"></div>
                                </div>
                            </div>

                            <p style="margin-bottom: 24px;">
                                Unlock the full 25+ page report, including the complete "Entry Strategy" and "Differentiation" chapters.
                            </p>

                            <!-- CTA Button -->
                            <div style="text-align: center; margin-bottom: 32px;">
                                <a href="{payment_link}" style="display: inline-block; background-color: #2563eb; color: #ffffff; font-weight: 600; padding: 14px 32px; text-decoration: none; border-radius: 50px; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: all 0.2s;">
                                    Pay $25.00 Balance & View Full Report
                                </a>
                            </div>
                            
                            <p style="font-size: 14px; color: #6b7280; text-align: center;">
                                Link expires in 24 hours. Secure payment via Stripe.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
        
        else:
            # === FREE FLOW: Full Report ===
            msg["Subject"] = f"Your AI Product Discovery Report: {report.keywords}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Product Discovery Analysis Complete</h2>
                        <p>Here is the analysis report for <strong>{report.keywords}</strong> in <strong>{report.category}</strong>.</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        {report.report_html if report.report_html else f"<pre>{report.report_markdown}</pre>"}
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #666;">Generated by Amz AI Agent</p>
                    </div>
                </body>
            </html>
            """
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        # Connect to server
        print(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}...")
        
        server = None
        port = int(SMTP_PORT)
        
        if port == 465:
            # SSL Connection (Implicit)
            print("Using SMTP_SSL (Implicit SSL)")
            server = smtplib.SMTP_SSL(SMTP_HOST, port)
            # server.starttls() is NOT needed for SMTP_SSL
        else:
            # TLS Connection (Explicit)
            print("Using SMTP (StartTLS)")
            server = smtplib.SMTP(SMTP_HOST, port)
            server.starttls()  # Secure the connection
            
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        # Send email
        server.sendmail(SMTP_USER, report.user_email, msg.as_string())
        server.quit()
        
        print(f"✅ Email sent successfully to {report.user_email}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        raise e  # Allow caller to handle error
