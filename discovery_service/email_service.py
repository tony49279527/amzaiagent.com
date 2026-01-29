
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from .models import AnalysisReport
import sys
import io
from contextlib import redirect_stderr, redirect_stdout


def _smtp_send(to_email: str, msg: MIMEMultipart):
    """Synchronous SMTP send — meant to be called via asyncio.to_thread"""
    port = int(SMTP_PORT)
    if port == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, port)
    else:
        server = smtplib.SMTP(SMTP_HOST, port)
        server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(SMTP_USER, to_email, msg.as_string())
    server.quit()

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
            
            # Extract meaningful preview from report markdown
            # Try to find Executive Summary or first substantive section
            import re
            preview_content = ""
            
            if report.report_markdown:
                # Try to extract a specific section
                patterns = [
                    r'## Executive Summary\s*\n([\s\S]*?)(?=\n## |\Z)',
                    r'## Summary\s*\n([\s\S]*?)(?=\n## |\Z)',
                    r'## Market Entry Strategy\s*\n([\s\S]*?)(?=\n## |\Z)',
                    r'## Overview\s*\n([\s\S]*?)(?=\n## |\Z)',
                    r'## Market Analysis\s*\n([\s\S]*?)(?=\n## |\Z)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, report.report_markdown)
                    if match:
                        preview_content = match.group(1).strip()[:1500]
                        break
                
                # Fallback: take content after first heading
                if not preview_content:
                    lines = report.report_markdown.split('\n')
                    in_content = False
                    content_lines = []
                    for line in lines:
                        if line.startswith('#') and not in_content:
                            in_content = True
                            continue
                        if in_content:
                            if line.startswith('## ') and len(content_lines) > 5:
                                break
                            content_lines.append(line)
                    preview_content = '\n'.join(content_lines)[:1200]
            
            # Convert markdown to simple HTML for email
            # Basic conversion for bullet points and paragraphs
            preview_html = preview_content.replace('\n\n', '</p><p>').replace('\n- ', '</p><li>').replace('\n', '<br>')
            if '<li>' in preview_html:
                preview_html = '<p>' + preview_html + '</li></ul>'
                preview_html = preview_html.replace('</p><li>', '<ul><li>')
            else:
                preview_html = '<p>' + preview_html + '</p>'
            
            # Payment Link - now points to discovery_report.html
            payment_link = f"https://amzaiagent.com/discovery_report.html?id={report.report_id}&payment_pending=true"


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
                                    {preview_html}
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

        # Send email in a thread to avoid blocking the async event loop
        print(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}...")
        await asyncio.to_thread(_smtp_send, report.user_email, msg)
        
        print(f"✅ Email sent successfully to {report.user_email}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        raise e  # Allow caller to handle error

async def send_failure_email(user_email: str, keywords: str, error_details: str):
    """
    Send a failure notification email to the user.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Error: SMTP credentials not set. Skipping failure email.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = user_email
        msg["Subject"] = f"Update on your analysis for: {keywords}"

        html_content = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; background-color: #f3f4f6; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); padding: 32px 24px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">Analysis Delayed</h1>
                        <p style="color: #fee2e2; margin: 8px 0 0 0; font-size: 16px;">Action Required</p>
                    </div>

                    <!-- Content -->
                    <div style="padding: 32px 24px;">
                        <p style="margin-bottom: 24px; font-size: 16px;">
                            Hello, <br><br>
                            We encountered a temporary issue while generating your market analysis for <strong>{keywords}</strong>.
                        </p>

                        <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                            <h3 style="margin-top: 0; color: #991b1b; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">System Message</h3>
                            <p style="color: #7f1d1d; font-size: 14px; margin: 0;">
                                {error_details}
                            </p>
                            <p style="color: #7f1d1d; font-size: 14px; margin-top: 10px;">
                                This is often caused by high traffic on our AI models or temporary data source unavailability.
                            </p>
                        </div>

                        <p style="margin-bottom: 24px;">
                            Please try submitting your request again in 10-15 minutes. No credits have been deducted from your account.
                        </p>

                        <!-- CTA Button -->
                        <div style="text-align: center; margin-bottom: 32px;">
                            <a href="https://amzaiagent.com/discovery.html" style="display: inline-block; background-color: #4b5563; color: #ffffff; font-weight: 600; padding: 14px 32px; text-decoration: none; border-radius: 50px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: all 0.2s;">
                                Try Again
                            </a>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        # Send email in a thread to avoid blocking the async event loop
        await asyncio.to_thread(_smtp_send, user_email, msg)
        
        print(f"✅ Failure notification sent successfully to {user_email}")
        
    except Exception as e:
        print(f"❌ Failed to send failure email: {str(e)}")


