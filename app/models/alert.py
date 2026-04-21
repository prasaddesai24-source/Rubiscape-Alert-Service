"""
Alert model — stores generated alerts when rule conditions are met.
Extended with lifecycle management (status, ack, resolve) and AI runbook field.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    """SQLAlchemy model for the 'alerts' table."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(150), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Lifecycle Management ──────────────────────────────────
    status = Column(String(20), nullable=False, default="OPEN", index=True,
                    comment="OPEN, ACKNOWLEDGED, RESOLVED, SUPPRESSED")
    acknowledged_by = Column(String(150), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # ── AI Runbook ────────────────────────────────────────────
    runbook = Column(Text, nullable=True, comment="AI-generated remediation steps")

    def __repr__(self):
        return f"<Alert(id={self.id}, service='{self.service_name}', severity='{self.severity}', status='{self.status}')>"
