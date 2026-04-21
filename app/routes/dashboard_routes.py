"""
Dashboard routes — renders the Jinja2 HTML dashboard for alert monitoring.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.alert import Alert

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboard"])

# Jinja2 template directory
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard")
def dashboard(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
):
    """Render the alert monitoring dashboard."""

    # Fetch alerts with optional severity filter
    query = db.query(Alert).order_by(Alert.created_at.desc())
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    alerts = query.all()

    # Total alert count
    total_count = db.query(func.count(Alert.id)).scalar() or 0

    # Severity distribution
    severity_dist = dict(
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "alerts": alerts,
            "total_count": total_count,
            "severity_dist": severity_dist,
            "current_filter": severity,
            "severity_levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        },
    )
