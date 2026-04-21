"""
Rule model — stores alert rules that define conditions for triggering alerts.
Each rule specifies a metric, comparison operator, threshold, and severity level.
"""

from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Rule(Base):
    """SQLAlchemy model for the 'rules' table."""

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric = Column(String(100), nullable=False, index=True, comment="Metric name to monitor (e.g. latency, error_rate)")
    operator = Column(String(5), nullable=False, comment="Comparison operator: >, <, >=, <=, ==")
    threshold = Column(Float, nullable=False, comment="Threshold value for rule evaluation")
    severity = Column(String(20), nullable=False, comment="Alert severity: LOW, MEDIUM, HIGH, CRITICAL")

    def __repr__(self):
        return f"<Rule(id={self.id}, metric='{self.metric}', operator='{self.operator}', threshold={self.threshold}, severity='{self.severity}')>"
