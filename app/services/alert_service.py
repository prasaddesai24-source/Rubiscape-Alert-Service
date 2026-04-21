"""
Alert Service — creates alerts, generates AI runbooks, and broadcasts via WebSocket.
Extended with anomaly alert creation and AI runbook generation.
"""

import logging
import asyncio
import threading
from typing import List
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.rule import Rule
from app.services.notification_service import send_notification

logger = logging.getLogger(__name__)


def generate_alert_message(metric: str, service_name: str, rule: Rule) -> str:
    """Generate a human-readable alert message."""
    return (
        f"{metric.replace('_', ' ').title()} threshold exceeded for {service_name} "
        f"(rule: {metric} {rule.operator} {rule.threshold})"
    )


def _generate_and_save_runbook(alert_id: int, service_name: str, metric: str, value: float, severity: str):
    """Background thread: generate AI runbook and save to alert record."""
    try:
        from app.services.ai_runbook_service import generate_runbook
        from app.database import SessionLocal

        runbook = generate_runbook(service_name, metric, value, severity)
        if runbook:
            db = SessionLocal()
            try:
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                if alert:
                    alert.runbook = runbook
                    db.commit()
                    logger.info(f"[Runbook] Saved to alert #{alert_id}")
            finally:
                db.close()
    except Exception as e:
        logger.error(f"[Runbook] Background save failed for alert #{alert_id}: {e}")


def _broadcast_alert(alert: Alert):
    """Broadcast new alert to all connected WebSocket clients."""
    try:
        from app.core.connection_manager import manager
        import asyncio

        alert_data = {
            "id": alert.id,
            "service_name": alert.service_name,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": str(alert.created_at),
        }

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.broadcast(alert_data))
        except RuntimeError:
            pass
    except Exception as e:
        logger.debug(f"[WS] Broadcast skipped: {e}")


def create_alerts(
    db: Session,
    service_name: str,
    metric: str,
    value: float,
    triggered_rules: List[Rule],
) -> List[Alert]:
    """Create alert records for each triggered rule and dispatch notifications."""
    created_alerts: List[Alert] = []

    for rule in triggered_rules:
        message = generate_alert_message(metric, service_name, rule)

        alert = Alert(
            service_name=service_name,
            message=message,
            severity=rule.severity,
            status="OPEN",
        )

        try:
            db.add(alert)
            db.commit()
            db.refresh(alert)
            created_alerts.append(alert)

            logger.info(f"Alert #{alert.id} created — [{alert.severity}] {alert.message}")

            # Dispatch notifications
            send_notification(alert)

            # Broadcast to WebSocket clients
            _broadcast_alert(alert)

            # Generate AI runbook for HIGH/CRITICAL alerts in background
            if rule.severity in ("HIGH", "CRITICAL"):
                thread = threading.Thread(
                    target=_generate_and_save_runbook,
                    args=(alert.id, service_name, metric, value, rule.severity),
                    daemon=True,
                )
                thread.start()

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert for rule {rule.id}: {e}")

    logger.info(f"Alert generation complete: {len(created_alerts)} alerts for '{service_name}'")
    return created_alerts


def create_anomaly_alert(db: Session, service_name: str, metric: str, value: float) -> Alert:
    """Create an anomaly alert when the AI detector flags an outlier."""
    message = (
        f"🤖 Anomaly detected: {metric.replace('_', ' ').title()} value {value} "
        f"for {service_name} is statistically unusual"
    )

    alert = Alert(
        service_name=service_name,
        message=message,
        severity="HIGH",
        status="OPEN",
    )

    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.warning(f"[Anomaly] Alert #{alert.id} created for '{service_name}' — {metric}={value}")

        send_notification(alert)
        _broadcast_alert(alert)

        # Generate runbook for anomaly alert too
        thread = threading.Thread(
            target=_generate_and_save_runbook,
            args=(alert.id, service_name, metric, value, "HIGH"),
            daemon=True,
        )
        thread.start()

        return alert

    except Exception as e:
        db.rollback()
        logger.error(f"[Anomaly] Failed to create anomaly alert: {e}")
        return None
