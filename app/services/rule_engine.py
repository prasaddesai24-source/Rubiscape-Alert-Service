"""
Rule Engine — core evaluation logic for matching events against rules.
This module is intentionally separated from route logic for reusability.
"""

import logging
import operator as op
from typing import List
from sqlalchemy.orm import Session
from app.models.rule import Rule

logger = logging.getLogger(__name__)

# ── Operator mapping ──────────────────────────────────────────
OPERATOR_MAP = {
    ">":  op.gt,
    "<":  op.lt,
    ">=": op.ge,
    "<=": op.le,
    "==": op.eq,
}


def evaluate_rules(db: Session, metric: str, value: float) -> List[Rule]:
    """
    Evaluate all rules matching the given metric against the provided value.

    Args:
        db: Active database session.
        metric: The metric name from the ingested event.
        value: The observed metric value.

    Returns:
        List of Rule objects whose conditions are satisfied.
    """
    # Fetch all rules that monitor this metric
    matching_rules = db.query(Rule).filter(Rule.metric == metric).all()

    if not matching_rules:
        logger.info(f"No rules found for metric '{metric}'")
        return []

    triggered_rules: List[Rule] = []

    for rule in matching_rules:
        comparator = OPERATOR_MAP.get(rule.operator)

        if comparator is None:
            logger.warning(
                f"Rule {rule.id} has invalid operator '{rule.operator}' — skipping"
            )
            continue

        # Evaluate: does the event value satisfy the rule condition?
        if comparator(value, rule.threshold):
            logger.info(
                f"Rule {rule.id} TRIGGERED: {value} {rule.operator} {rule.threshold} "
                f"[severity={rule.severity}]"
            )
            triggered_rules.append(rule)
        else:
            logger.debug(
                f"Rule {rule.id} not triggered: {value} {rule.operator} {rule.threshold}"
            )

    logger.info(
        f"Evaluation complete for metric '{metric}': "
        f"{len(triggered_rules)}/{len(matching_rules)} rules triggered"
    )
    return triggered_rules
