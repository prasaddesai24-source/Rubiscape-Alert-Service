"""
Alert routes — list, filter, lifecycle management, and metrics endpoints.
Extended with: status filter, acknowledge, resolve, suppress, notes, and runbook in response.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.alert import Alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


class NoteRequest(BaseModel):
    note: str
    operator: str = "system"


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = "admin"


# ── List Alerts ───────────────────────────────────────────────
@router.get("/", response_model=List[Dict[str, Any]])
def get_all_alerts(
    severity: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, ACKNOWLEDGED, RESOLVED, SUPPRESSED"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve alerts with optional filtering by severity, service, and lifecycle status."""
    query = db.query(Alert).order_by(Alert.created_at.desc())

    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if service:
        query = query.filter(Alert.service_name == service)
    if status:
        query = query.filter(Alert.status == status.upper())

    alerts = query.limit(limit).all()

    return [
        {
            "id": a.id,
            "service_name": a.service_name,
            "message": a.message,
            "severity": a.severity,
            "status": a.status,
            "acknowledged_by": a.acknowledged_by,
            "acknowledged_at": str(a.acknowledged_at) if a.acknowledged_at else None,
            "resolved_at": str(a.resolved_at) if a.resolved_at else None,
            "notes": a.notes,
            "runbook": a.runbook,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in alerts
    ]


# ── Acknowledge ───────────────────────────────────────────────
@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    body: AcknowledgeRequest,
    db: Session = Depends(get_db),
):
    """Mark an alert as ACKNOWLEDGED."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = body.acknowledged_by
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Alert #{alert_id} acknowledged by {body.acknowledged_by}")
    return {"message": f"Alert #{alert_id} acknowledged.", "status": alert.status}


# ── Resolve ───────────────────────────────────────────────────
@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as RESOLVED."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Alert #{alert_id} resolved.")
    return {"message": f"Alert #{alert_id} resolved.", "status": alert.status}


# ── Suppress ──────────────────────────────────────────────────
@router.patch("/{alert_id}/suppress")
def suppress_alert(alert_id: int, db: Session = Depends(get_db)):
    """Suppress an alert (mark as SUPPRESSED to reduce noise)."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    alert.status = "SUPPRESSED"
    db.commit()
    return {"message": f"Alert #{alert_id} suppressed.", "status": alert.status}


# ── Notes ─────────────────────────────────────────────────────
@router.post("/{alert_id}/notes")
def add_note(alert_id: int, body: NoteRequest, db: Session = Depends(get_db)):
    """Add an operator note to an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    new_note = f"[{timestamp}] {body.operator}: {body.note}"
    alert.notes = f"{alert.notes}\n{new_note}" if alert.notes else new_note
    db.commit()
    return {"message": "Note added.", "notes": alert.notes}


# ── Metrics Report ────────────────────────────────────────────
@router.get("/metrics/report")
def get_metrics_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Metrics report: totals, by severity, by service, 24h trend."""
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0

    severity_counts = (
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity).all()
    )
    by_severity = {s: c for s, c in severity_counts}

    service_counts = (
        db.query(Alert.service_name, func.count(Alert.id))
        .group_by(Alert.service_name).all()
    )
    by_service = {s: c for s, c in service_counts}

    status_counts = (
        db.query(Alert.status, func.count(Alert.id))
        .group_by(Alert.status).all()
    )
    by_status = {s: c for s, c in status_counts}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_count = (
        db.query(func.count(Alert.id))
        .filter(Alert.created_at >= cutoff)
        .scalar() or 0
    )

    trend = "stable"
    if total_alerts > 0:
        ratio = recent_count / total_alerts
        if ratio > 0.5:
            trend = "increasing"
        elif ratio < 0.1:
            trend = "decreasing"

    return {
        "total_alerts": total_alerts,
        "by_severity": by_severity,
        "by_service": by_service,
        "by_status": by_status,
        "recent_24h": recent_count,
        "trend": trend,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
