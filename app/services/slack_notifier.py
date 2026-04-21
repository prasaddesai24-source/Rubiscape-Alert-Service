"""
Slack & Webhook Notifiers — send alert notifications to Slack channels
and generic HTTP webhook endpoints using httpx (async-compatible).
"""

import logging
import threading
from app.core.config import settings

logger = logging.getLogger(__name__)

SEVERITY_COLORS = {
    "LOW": "#22d3ee",
    "MEDIUM": "#eab308",
    "HIGH": "#f97316",
    "CRITICAL": "#ef4444",
}


def _slack_worker(alert_id, service_name, severity, message, created_at, runbook=None):
    """Background worker: sends Slack message via incoming webhook."""
    try:
        import httpx

        color = SEVERITY_COLORS.get(severity, "#aaaaaa")
        severity_icons = {"LOW": "ℹ️", "MEDIUM": "⚠️", "HIGH": "🔶", "CRITICAL": "🔴"}
        icon = severity_icons.get(severity, "📢")

        fields = [
            {"title": "Alert ID", "value": f"#{alert_id}", "short": True},
            {"title": "Severity", "value": severity, "short": True},
            {"title": "Service", "value": service_name, "short": True},
            {"title": "Timestamp", "value": str(created_at), "short": True},
        ]

        if runbook:
            # Add first 2 runbook steps to Slack message
            steps = runbook.split("\n")[:2]
            fields.append({"title": "🤖 AI Fix (first steps)", "value": "\n".join(steps), "short": False})

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{icon} [{severity}] Alert — {service_name}",
                    "text": message,
                    "fields": fields,
                    "footer": "Rubiscape Alert Service",
                }
            ]
        }

        response = httpx.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"[Slack] ✅ Alert #{alert_id} sent to Slack")
        else:
            logger.warning(f"[Slack] ⚠️ Slack returned status {response.status_code}")

    except Exception as e:
        logger.error(f"[Slack] ❌ Failed to send Slack notification: {e}")


def send_slack_notification(alert, runbook=None):
    """Send alert to Slack in a background thread (non-blocking)."""
    if not settings.SLACK_WEBHOOK_URL:
        logger.debug("[Slack] SLACK_WEBHOOK_URL not configured — skipping.")
        return

    thread = threading.Thread(
        target=_slack_worker,
        args=(alert.id, alert.service_name, alert.severity, alert.message, alert.created_at, runbook),
        daemon=True,
    )
    thread.start()


def _webhook_worker(alert_id, service_name, severity, message, created_at):
    """Background worker: sends generic HTTP webhook POST."""
    try:
        import httpx

        payload = {
            "alert_id": alert_id,
            "service_name": service_name,
            "severity": severity,
            "message": message,
            "timestamp": str(created_at),
            "source": "rubiscape-alert-service",
        }

        response = httpx.post(settings.GENERIC_WEBHOOK_URL, json=payload, timeout=10)
        logger.info(f"[Webhook] ✅ Alert #{alert_id} sent (status={response.status_code})")

    except Exception as e:
        logger.error(f"[Webhook] ❌ Failed to send webhook: {e}")


def send_webhook_notification(alert):
    """Send alert to generic webhook in a background thread (non-blocking)."""
    if not settings.GENERIC_WEBHOOK_URL:
        logger.debug("[Webhook] GENERIC_WEBHOOK_URL not configured — skipping.")
        return

    thread = threading.Thread(
        target=_webhook_worker,
        args=(alert.id, alert.service_name, alert.severity, alert.message, alert.created_at),
        daemon=True,
    )
    thread.start()
