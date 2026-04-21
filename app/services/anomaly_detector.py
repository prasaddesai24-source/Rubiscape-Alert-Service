"""
AI Anomaly Detector — uses IsolationForest to detect unusual metric values.
Runs automatically during event ingestion alongside the rule engine.
"""

import logging
import numpy as np
from sqlalchemy.orm import Session
from app.models.event import Event

logger = logging.getLogger(__name__)

# Minimum data points required before running anomaly detection
MIN_DATA_POINTS = 10


def detect_anomaly(db: Session, metric: str, new_value: float) -> bool:
    """
    Detect whether a new metric value is an anomaly using IsolationForest.

    Args:
        db: Active database session.
        metric: The metric name to analyze.
        new_value: The newly observed metric value.

    Returns:
        True if anomaly detected, False otherwise.
    """
    try:
        from sklearn.ensemble import IsolationForest

        # Fetch last 50 historical values for this metric
        historical = (
            db.query(Event.value)
            .filter(Event.metric == metric)
            .order_by(Event.created_at.desc())
            .limit(50)
            .all()
        )
        values = [row[0] for row in historical]

        if len(values) < MIN_DATA_POINTS:
            logger.info(
                f"[Anomaly] Not enough data for metric '{metric}' "
                f"({len(values)}/{MIN_DATA_POINTS} points). Skipping."
            )
            return False

        # Prepare training data
        X_train = np.array(values).reshape(-1, 1)
        X_new = np.array([[new_value]])

        # Fit IsolationForest
        model = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            random_state=42,
        )
        model.fit(X_train)

        # Predict: -1 = anomaly, 1 = normal
        prediction = model.predict(X_new)[0]
        is_anomaly = prediction == -1

        if is_anomaly:
            logger.warning(
                f"[Anomaly] 🚨 ANOMALY detected: metric='{metric}', "
                f"value={new_value} (trained on {len(values)} points)"
            )
        else:
            logger.debug(f"[Anomaly] Normal value: metric='{metric}', value={new_value}")

        return is_anomaly

    except Exception as e:
        logger.error(f"[Anomaly] Detection failed for metric '{metric}': {e}")
        return False
