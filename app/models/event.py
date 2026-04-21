"""
Event model — stores ingested AI workflow execution events.
Each event contains the service name, metric observed, value, and timestamp.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Event(Base):
    """SQLAlchemy model for the 'events' table."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(150), nullable=False, index=True, comment="Name of the AI service reporting the event")
    metric = Column(String(100), nullable=False, index=True, comment="Metric name (e.g. latency, error_rate)")
    value = Column(Float, nullable=False, comment="Observed metric value")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Timestamp of event ingestion")

    def __repr__(self):
        return f"<Event(id={self.id}, service='{self.service_name}', metric='{self.metric}', value={self.value})>"
