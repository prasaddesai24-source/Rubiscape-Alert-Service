"""
Event routes — ingest AI workflow events, trigger rule engine, anomaly detection,
and generate alerts automatically.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event
from app.schemas.event_schema import EventCreate, EventResponse
from app.services.rule_engine import evaluate_rules
from app.services.alert_service import create_alerts, create_anomaly_alert
from app.services.anomaly_detector import detect_anomaly

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def ingest_event(request: Request, event_data: EventCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Ingest an AI workflow event.

    Flow:
    1. Store the event in the database
    2. Evaluate all matching simple rules
    3. Generate alerts for triggered rules
    4. Run AI anomaly detection (generates auto-alert if anomaly found)
    5. Return event + alert summary
    """
    # Step 1: Store the event
    event = Event(
        service_name=event_data.service_name,
        metric=event_data.metric,
        value=event_data.value,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"Event #{event.id} ingested: {event}")

    # Step 2: Evaluate rules
    triggered_rules = evaluate_rules(db, event_data.metric, event_data.value)

    # Step 3: Generate rule-based alerts
    alerts = []
    if triggered_rules:
        alerts = create_alerts(
            db=db,
            service_name=event_data.service_name,
            metric=event_data.metric,
            value=event_data.value,
            triggered_rules=triggered_rules,
        )

    # Step 4: AI Anomaly Detection
    anomaly_alert = None
    is_anomaly = detect_anomaly(db, event_data.metric, event_data.value)
    if is_anomaly:
        anomaly_alert = create_anomaly_alert(
            db=db,
            service_name=event_data.service_name,
            metric=event_data.metric,
            value=event_data.value,
        )
        if anomaly_alert:
            alerts.append(anomaly_alert)

    # Step 5: Return summary
    return {
        "event": {
            "id": event.id,
            "service_name": event.service_name,
            "metric": event.metric,
            "value": event.value,
            "created_at": str(event.created_at) if event.created_at else None,
        },
        "rules_evaluated": len(triggered_rules),
        "anomaly_detected": is_anomaly,
        "alerts_generated": len(alerts),
        "alerts": [
            {"id": a.id, "severity": a.severity, "message": a.message}
            for a in alerts
        ],
    }


@router.get("/", response_model=List[EventResponse])
def get_all_events(db: Session = Depends(get_db)):
    """Retrieve all ingested events."""
    return db.query(Event).order_by(Event.created_at.desc()).all()
