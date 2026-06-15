"""Send Mail Service."""
import logging
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage

from oauthlib.uri_validate import port
import src.config as config
import src.mappings as mappings

logger = logging.getLogger("send_mail")

def send_mail(body: str, category: str = "Info", method: str = "manual", module: str = "CustomerPOUL"):
    """Send an email."""
    # Placeholder for email sending logic
    smtp_server = config.mail_server
    smtp_port = config.mail_port
    sender_email = config.mail_sender
    sender_password = config.mail_password
    recepient_emails = config.mail_recipient.split(",")  # Assuming multiple recipients are comma-separated
    body = body.replace("\n", "<br>")  # Convert newlines to HTML line breaks
    module_desc = mappings.module_mappings.get(module, module)
    if method.lower() == "scheduled":
        method = "Scheduled Run"
    elif method.lower() == "manual":
        method = "Manual Run"
    elif method.lower() == "triggered":
        method = "Triggered Run"

    if category.upper() == "ERROR":
        subject = f'SBIC Bigquery Bridge Notification ({module_desc}): Error Logs - {method}'
    elif category.upper() == "INFO":
        subject = f'SBIC Bigquery Bridge Notification ({module_desc}): Run Logs - {method}'

    email_header = subject
    
    for recipient in recepient_emails:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient.strip()  # Use each recipient email
        msg["Subject"] = subject

        # Plain text fallback
        msg.set_content(body)

        # Basic HTML email layout
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;margin-top:20px;border-radius:8px;overflow:hidden;">
                
                <!-- Header -->
                <tr>
                    <td style="background-color:#4CAF50;padding:20px;text-align:center;color:white;font-size:20px;font-weight:bold;">
                        {email_header}
                    </td>
                </tr>

                <!-- Content -->
                <tr>
                    <td style="padding:30px;color:#333333;font-size:16px;line-height:1.6;font-family:'Courier New', monospace;">
                        {body}
                    </td>
                </tr>

                <!-- Footer -->
                <tr>
                    <td style="background-color:#eeeeee;padding:15px;text-align:center;font-size:12px;color:#777777;">
                        © 2026 RGMC Group IT Department<br>
                        This is an automated message. Please do not reply.
                    </td>
                </tr>

            </table>
        </body>
        </html>
        """

        msg.add_alternative(html_content, subtype="html")

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")


def notify_error(method: str, url: str, status_code: int, body: str, client_ip: str = "") -> None:
    """Send a developer alert email for 500/502 API responses.

    Silently skips if DEVELOPER_EMAIL or SMTP credentials are not configured.
    Intended to be called from a daemon thread so it never blocks the HTTP response.
    """
    if not config.developer_email or not config.smtp_user or not config.smtp_password:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"[RGMC API {status_code}] {method} {url}"

    body_html = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
        <table align="center" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:640px;background:#ffffff;margin-top:20px;border-radius:8px;overflow:hidden;">
            <tr>
                <td style="background-color:#c0392b;padding:20px;text-align:center;color:white;font-size:18px;font-weight:bold;">
                    RGMC API — Error {status_code}
                </td>
            </tr>
            <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.7;">
                    <table width="100%" cellpadding="6" cellspacing="0">
                        <tr><td style="color:#777;width:120px;">Timestamp</td><td><strong>{timestamp}</strong></td></tr>
                        <tr><td style="color:#777;">Method</td><td><strong>{method}</strong></td></tr>
                        <tr><td style="color:#777;">URL</td><td style="word-break:break-all;"><strong>{url}</strong></td></tr>
                        <tr><td style="color:#777;">Status</td><td><strong style="color:#c0392b;">{status_code}</strong></td></tr>
                        <tr><td style="color:#777;">Client IP</td><td>{client_ip or "—"}</td></tr>
                    </table>
                    <hr style="margin:20px 0;border:none;border-top:1px solid #eeeeee;">
                    <p style="margin:0 0 8px;color:#777;font-size:12px;text-transform:uppercase;letter-spacing:.05em;">Response Body</p>
                    <pre style="background:#f8f8f8;padding:16px;border-radius:4px;overflow:auto;font-size:12px;
                                font-family:'Courier New',monospace;white-space:pre-wrap;word-break:break-all;">{body_html}</pre>
                </td>
            </tr>
            <tr>
                <td style="background-color:#eeeeee;padding:14px;text-align:center;font-size:11px;color:#777777;">
                    &copy; {datetime.now(timezone.utc).year} RGMC Group IT Department &mdash; automated alert, do not reply.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg = EmailMessage()
    msg["From"] = config.smtp_user
    msg["To"] = config.developer_email
    msg["Subject"] = subject
    msg.set_content(f"[{timestamp}] {method} {url} → {status_code}\n\nClient IP: {client_ip or '—'}\n\n{body}")
    msg.add_alternative(html_content, subtype="html")

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls(context=ctx)
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        logger.error(f"notify_error: failed to send alert email: {exc}")
