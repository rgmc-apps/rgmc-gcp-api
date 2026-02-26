"""Send Mail Service."""
import os
import smtplib
import ssl

from oauthlib.uri_validate import port
import src.config as config
from email.message import EmailMessage

def send_mail(body: str, category: str = "Info", method: str = "manual"):
    """Send an email."""
    # Placeholder for email sending logic
    smtp_server = config.mail_server
    smtp_port = config.mail_port
    sender_email = config.mail_sender
    sender_password = config.mail_password
    recepient_emails = config.mail_recipient.split(",")  # Assuming multiple recipients are comma-separated
    body = body.replace("\n", "<br>")  # Convert newlines to HTML line breaks
    if method.lower() == "scheduled":
        method = "Scheduled Run"
    elif method.lower() == "manual":
        method = "Manual Run"

    if category.upper() == "ERROR":
        subject = f'SBIC Bigquery Bridge Notification: Error Logs - {method}'
    elif category.upper() == "INFO":
        subject = f'SBIC Bigquery Bridge Notification: Run Logs - {method}'
    
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
                    <td style="background-color:#4CAF50;padding:20px;text-align:center;color:white;font-size:24px;font-weight:bold;">
                        {email_header}
                    </td>
                </tr>

                <!-- Content -->
                <tr>
                    <td style="padding:30px;color:#333333;font-size:16px;line-height:1.6;">
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


    