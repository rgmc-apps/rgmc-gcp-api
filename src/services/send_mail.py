"""Send Mail Service.

Every notification carries a fixed "ecosystem module" identity (BigQuery Bridge,
Generic/Internal, or API Watchdog — see _MODULES) that drives a distinct header
color/icon, independent of severity (error vs info/success), so an inbox full of these
can be told apart by WHICH SERVICE/PIPELINE sent them at a glance. rgmc-worker-pool's
own src/services/send_mail.py uses the same palette/icon for "bigquery_bridge" so a
BigQuery Bridge email looks the same regardless of which of the two services actually
sent it (worker-pool's is a manually-kept-in-sync port of this repo's own bridge).

Previously every email here used the same hardcoded green (#4CAF50) header regardless
of category — including ERROR emails, which is fixed below: category now drives a
severity badge (and the header accent), the module identity drives the header color.
"""
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage

import src.config as config
import src.mappings as mappings

logger = logging.getLogger("send_mail")

# module key -> (display label, header icon, header/accent color) — mirrors
# rgmc-worker-pool's own send_mail.py so "bigquery_bridge" renders identically in both
# services' emails.
_MODULES: dict[str, tuple[str, str, str]] = {
    "bigquery_bridge": ("BigQuery Bridge", "\U0001F309", "#4338ca"),  # bridge (indigo)
    "generic": ("Internal Notification", "✉️", "#374151"),  # envelope (slate)
    "api_watchdog": ("API Watchdog", "\U0001F6E1️", "#7f1d1d"),  # shield (maroon)
}
_DEFAULT_MODULE: tuple[str, str, str] = ("RGMC API", "⚙️", "#334155")  # gear (slate)

# severity -> (badge text, badge background, badge text color).
_SEVERITIES: dict[str, tuple[str, str, str]] = {
    "error": ("ERROR", "#fee2e2", "#991b1b"),
    "success": ("INFO", "#dcfce7", "#166534"),
}


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _card_html(
    module_key: str, severity: str, header_text: str, sub_label: str, body_html: str, timestamp: str,
) -> str:
    """Shared card shell for every email in this file — module_key picks the header
    color/icon, severity picks the status badge shown just under it."""
    module_label, module_icon, module_color = _MODULES.get(module_key, _DEFAULT_MODULE)
    badge_text, badge_bg, badge_fg = _SEVERITIES.get(severity, _SEVERITIES["success"])
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
        <table align="center" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:640px;background:#ffffff;margin-top:20px;border-radius:8px;overflow:hidden;
                      border-top:4px solid {module_color};">
            <tr>
                <td style="background-color:{module_color};padding:18px 20px;color:white;">
                    <span style="font-size:22px;vertical-align:middle;">{module_icon}</span>
                    <span style="font-size:17px;font-weight:bold;vertical-align:middle;margin-left:8px;">
                        {header_text}
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding:24px;color:#333333;font-size:14px;line-height:1.7;">
                    <span style="display:inline-block;background:{badge_bg};color:{badge_fg};
                                 font-size:11px;font-weight:bold;letter-spacing:.05em;text-transform:uppercase;
                                 padding:4px 10px;border-radius:999px;margin-bottom:10px;">
                        {badge_text}
                    </span>
                    {f'<div style="color:#777;font-size:12px;margin-bottom:14px;">{sub_label}</div>' if sub_label else ""}
                    <div style="color:#777;font-size:12px;margin-bottom:14px;">{timestamp}</div>
                    <pre style="background:#f8f8f8;padding:16px;border-radius:4px;overflow:auto;font-size:12px;
                                font-family:'Courier New',monospace;white-space:pre-wrap;word-break:break-all;
                                border-left:3px solid {module_color};">{body_html}</pre>
                </td>
            </tr>
            <tr>
                <td style="background-color:#eeeeee;padding:14px;text-align:center;font-size:11px;color:#777777;">
                    &copy; {datetime.now(timezone.utc).year} RGMC Group IT Department &mdash; automated message, do not reply.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def send_mail(body: str, category: str = "Info", method: str = "manual", module: str = "CustomerPOUL"):
    """Send a BigQuery Bridge run notification. `module` here is the bridge's own
    group_code ("customerpoul" / "customerra" / "onlinesalespo") — shown as a sub-label
    inside the card — not the ecosystem-module header identity, which is always
    "BigQuery Bridge" for this function (see _MODULES)."""
    smtp_server = config.mail_server
    smtp_port = config.mail_port
    sender_email = config.mail_sender
    sender_password = config.mail_password
    recepient_emails = config.mail_recipient.split(",")
    module_desc = mappings.module_mappings.get(module, module)
    if method.lower() == "scheduled":
        method = "Scheduled Run"
    elif method.lower() == "manual":
        method = "Manual Run"
    elif method.lower() == "triggered":
        method = "Triggered Run"

    severity = "error" if category.upper() == "ERROR" else "success"
    log_label = "Error Logs" if severity == "error" else "Run Logs"
    subject = f"SBIC Bigquery Bridge Notification ({module_desc}): {log_label} - {method}"

    body_html = body.replace("\n", "<br>")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html_content = _card_html(
        "bigquery_bridge", severity, "RGMC GCP API &mdash; BigQuery Bridge",
        f"Source: {module_desc} &middot; {method}", body_html, timestamp,
    )

    for recipient in recepient_emails:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient.strip()
        msg["Subject"] = subject
        msg.set_content(body)
        msg.add_alternative(html_content, subtype="html", charset="utf-8")
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(sender_email, sender_password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"send_mail: failed to send to {recipient.strip()}: {e}")


def send_generic_mail(subject: str, body: str, recipients: list[str] | None = None, module: str = "generic") -> bool:
    """Send a plain, custom-subject email. Used by other internal services (e.g. the
    Attribute Checker) via the POST /notifications/send-mail route, so they don't need
    their own SMTP credentials — this service already owns them.

    Returns True if the message was sent to at least one recipient.
    """
    smtp_server = config.mail_server
    smtp_port = config.mail_port
    sender_email = config.mail_sender
    sender_password = config.mail_password
    recipient_list = recipients or [r.strip() for r in config.mail_recipient.split(",") if r.strip()]

    body_html = _escape(body).replace("\n", "<br>")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html_content = _card_html(module, "success", subject, "", body_html, timestamp)

    sent_any = False
    for recipient in recipient_list:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        msg.add_alternative(html_content, subtype="html", charset="utf-8")
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(sender_email, sender_password)
                server.send_message(msg)
            sent_any = True
        except Exception as e:
            logger.error(f"send_generic_mail: failed to send to {recipient}: {e}")
    return sent_any


def notify_error(method: str, url: str, status_code: int, body: str, client_ip: str = "") -> None:
    """Send a developer alert email for 500/502 API responses.

    Silently skips if DEVELOPER_EMAIL or SMTP credentials are not configured.
    Intended to be called from a daemon thread so it never blocks the HTTP response.
    """
    if not config.developer_email or not config.smtp_user or not config.smtp_password:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"[RGMC API {status_code}] {method} {url}"

    details = (
        f'<table width="100%" cellpadding="6" cellspacing="0">'
        f'<tr><td style="color:#777;width:120px;">Method</td><td><strong>{_escape(method)}</strong></td></tr>'
        f'<tr><td style="color:#777;">URL</td><td style="word-break:break-all;"><strong>{_escape(url)}</strong></td></tr>'
        f'<tr><td style="color:#777;">Status</td><td><strong style="color:#991b1b;">{status_code}</strong></td></tr>'
        f'<tr><td style="color:#777;">Client IP</td><td>{_escape(client_ip) or "&mdash;"}</td></tr>'
        f"</table>"
        f'<hr style="margin:16px 0;border:none;border-top:1px solid #eeeeee;">'
        f"{_escape(body).replace(chr(10), '<br>')}"
    )
    html_content = _card_html(
        "api_watchdog", "error", "RGMC API &mdash; API Watchdog", "", details, timestamp,
    )

    msg = EmailMessage()
    msg["From"] = config.smtp_user
    msg["To"] = config.developer_email
    msg["Subject"] = subject
    msg.set_content(f"[{timestamp}] {method} {url} -> {status_code}\n\nClient IP: {client_ip or '-'}\n\n{body}")
    msg.add_alternative(html_content, subtype="html", charset="utf-8")

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls(context=ctx)
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        logger.error(f"notify_error: failed to send alert email: {exc}")
