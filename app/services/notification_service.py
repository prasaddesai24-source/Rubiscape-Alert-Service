"""
Notification Service — handles alert dispatch via console logging
and real SMTP email. Email sending runs in a background thread so
it doesn't block the API response. Includes retry logic and error handling.
"""

import logging
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.alert import Alert
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def send_console_notification(alert: Alert) -> None:
    """
    Log the alert to the console with structured formatting.

    Args:
        alert: The Alert object to notify about.
    """
    severity_icons = {
        "LOW": "ℹ️",
        "MEDIUM": "⚠️",
        "HIGH": "🔶",
        "CRITICAL": "🔴",
    }
    icon = severity_icons.get(alert.severity, "📢")

    logger.warning(
        f"\n{'=' * 60}\n"
        f"  {icon}  ALERT NOTIFICATION\n"
        f"{'=' * 60}\n"
        f"  Alert ID    : {alert.id}\n"
        f"  Service     : {alert.service_name}\n"
        f"  Severity    : {alert.severity}\n"
        f"  Message     : {alert.message}\n"
        f"  Timestamp   : {alert.created_at}\n"
        f"{'=' * 60}"
    )


def _build_email(alert: Alert) -> MIMEMultipart:
    """
    Build a formatted HTML email message for an alert.

    Args:
        alert: The Alert object to build the email for.

    Returns:
        MIMEMultipart email message ready to send.
    """
    severity_colors = {
        "LOW": "#22d3ee",
        "MEDIUM": "#eab308",
        "HIGH": "#f97316",
        "CRITICAL": "#ef4444",
    }
    color = severity_colors.get(alert.severity, "#6c63ff")

    subject = f"[{alert.severity}] Alert for {alert.service_name}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #1c1f2e; color: #e4e6f0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #161822; border-radius: 12px; border: 1px solid #2a2d3e; overflow: hidden;">
            <!-- Header -->
            <div style="background: {color}; padding: 16px 24px;">
                <h2 style="margin: 0; color: #fff; font-size: 18px;">
                    Rubiscape Alert Service
                </h2>
            </div>

            <!-- Body -->
            <div style="padding: 24px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #8b8fa3; width: 130px;">Alert ID</td>
                        <td style="padding: 8px 0; font-weight: bold;">#{alert.id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #8b8fa3;">Severity</td>
                        <td style="padding: 8px 0;">
                            <span style="background: {color}; color: #fff; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold;">
                                {alert.severity}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #8b8fa3;">Service</td>
                        <td style="padding: 8px 0; font-weight: bold;">{alert.service_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #8b8fa3;">Message</td>
                        <td style="padding: 8px 0;">{alert.message}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #8b8fa3;">Timestamp</td>
                        <td style="padding: 8px 0;">{alert.created_at}</td>
                    </tr>
                </table>
            </div>

            <!-- Footer -->
            <div style="padding: 16px 24px; border-top: 1px solid #2a2d3e; color: #5a5e72; font-size: 12px;">
                This is an automated alert from Rubiscape Alert Service.
                <br>View dashboard for details.
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.NOTIFICATION_EMAIL

    # Plain text fallback
    plain_text = (
        f"ALERT: [{alert.severity}] {alert.service_name}\n"
        f"Alert ID: #{alert.id}\n"
        f"Message: {alert.message}\n"
        f"Timestamp: {alert.created_at}\n"
    )
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    return msg


def _send_email_worker(alert_id, service_name, severity, message, created_at):
    """
    Background worker that sends the email.
    Runs in a separate thread so the API response is not blocked.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"[Email] Attempt {attempt}/{MAX_RETRIES} — "
                f"Sending alert #{alert_id} to {settings.NOTIFICATION_EMAIL}"
            )

            # Build email from stored alert data
            severity_colors = {
                "LOW": "#22d3ee", "MEDIUM": "#eab308",
                "HIGH": "#f97316", "CRITICAL": "#ef4444",
            }
            color = severity_colors.get(severity, "#6c63ff")
            subject = f"[{severity}] Alert for {service_name}"

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #1c1f2e; color: #e4e6f0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #161822; border-radius: 12px; border: 1px solid #2a2d3e; overflow: hidden;">
                    <div style="background: {color}; padding: 16px 24px;">
                        <h2 style="margin: 0; color: #fff; font-size: 18px;">Rubiscape Alert Service</h2>
                    </div>
                    <div style="padding: 24px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; color: #8b8fa3; width: 130px;">Alert ID</td><td style="padding: 8px 0; font-weight: bold;">#{alert_id}</td></tr>
                            <tr><td style="padding: 8px 0; color: #8b8fa3;">Severity</td><td style="padding: 8px 0;"><span style="background:{color};color:#fff;padding:4px 12px;border-radius:12px;font-size:13px;font-weight:bold;">{severity}</span></td></tr>
                            <tr><td style="padding: 8px 0; color: #8b8fa3;">Service</td><td style="padding: 8px 0; font-weight: bold;">{service_name}</td></tr>
                            <tr><td style="padding: 8px 0; color: #8b8fa3;">Message</td><td style="padding: 8px 0;">{message}</td></tr>
                            <tr><td style="padding: 8px 0; color: #8b8fa3;">Timestamp</td><td style="padding: 8px 0;">{created_at}</td></tr>
                        </table>
                    </div>
                    <div style="padding: 16px 24px; border-top: 1px solid #2a2d3e; color: #5a5e72; font-size: 12px;">
                        This is an automated alert from Rubiscape Alert Service.
                    </div>
                </div>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.NOTIFICATION_EMAIL
            msg.attach(MIMEText(f"ALERT: [{severity}] {service_name}\nMessage: {message}\nTimestamp: {created_at}", "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Connect to Gmail SMTP and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.SMTP_USER,
                    settings.NOTIFICATION_EMAIL,
                    msg.as_string(),
                )

            logger.info(
                f"[Email] ✅ Email sent successfully to {settings.NOTIFICATION_EMAIL} "
                f"for alert #{alert_id}"
            )
            return

        except Exception as e:
            logger.error(f"[Email] ❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"[Email] Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)

    logger.critical(
        f"[Email] All {MAX_RETRIES} attempts failed for alert #{alert_id}. "
        f"Check SMTP settings in .env file."
    )


def send_email_notification(alert: Alert) -> None:
    """
    Send a real email notification via Gmail SMTP in a background thread.
    This ensures the API responds immediately without waiting for email delivery.

    Args:
        alert: The Alert object to notify about.
    """
    thread = threading.Thread(
        target=_send_email_worker,
        args=(alert.id, alert.service_name, alert.severity, alert.message, alert.created_at),
        daemon=True,
    )
    thread.start()
    logger.info(f"[Email] Background email thread started for alert #{alert.id}")


def send_notification(alert: Alert) -> None:
    """
    Main notification dispatcher. Sends alerts via all configured channels.
    """
    try:
        # Always log to console
        send_console_notification(alert)

        # Send real email to admin (non-blocking, runs in background)
        send_email_notification(alert)

        # Send to Slack (no-op if not configured)
        from app.services.slack_notifier import send_slack_notification, send_webhook_notification
        send_slack_notification(alert, runbook=getattr(alert, "runbook", None))
        send_webhook_notification(alert)

        logger.info(f"Notification pipeline complete for alert #{alert.id}")

    except Exception as e:
        logger.error(
            f"Notification dispatch failed for alert #{alert.id}: {e}",
            exc_info=True,
        )

