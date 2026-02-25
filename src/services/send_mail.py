"""Send Mail Service."""
import os
import smtplib
import src.config as config

def send_mail(subject: str, body: str, to: list[str]):
    """Send an email."""
    # Placeholder for email sending logic
    print(f"Sending email to {to} with subject '{subject}' and body '{body}'")

    