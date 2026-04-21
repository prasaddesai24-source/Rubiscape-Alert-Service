"""
Rule routes — CRUD endpoints for managing alert rules.
Extended with: POST /rules/from-text (natural language rule creation via Gemini AI)
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rule import Rule
from app.schemas.rule_schema import RuleCreate, RuleUpdate, RuleResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rules", tags=["Rules"])

class NLRuleRequest(BaseModel):
    prompt: str


@router.post("/from-text", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule_from_text(body: NLRuleRequest, db: Session = Depends(get_db)):
    """
    Create a monitoring rule from a plain English description using Google Gemini AI.

    Example prompt: "Alert me if latency exceeds 300ms with HIGH severity"
    """
    try:
        from app.services.nl_rule_parser import parse_rule_from_text
        rule_data = parse_rule_from_text(body.prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    rule = Rule(
        metric=rule_data["metric"],
        operator=rule_data["operator"],
        threshold=rule_data["threshold"],
        severity=rule_data["severity"],
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info(f"[NL Rule] Rule #{rule.id} created from text: '{body.prompt}'")
    return rule


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(rule_data: RuleCreate, db: Session = Depends(get_db)):
    """Create a new alert rule."""
    rule = Rule(
        metric=rule_data.metric,
        operator=rule_data.operator,
        threshold=rule_data.threshold,
        severity=rule_data.severity,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info(f"Rule #{rule.id} created: {rule}")
    return rule


@router.get("/", response_model=List[RuleResponse])
def get_all_rules(db: Session = Depends(get_db)):
    """Retrieve all alert rules."""
    return db.query(Rule).all()


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """Retrieve a single rule by ID."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Rule with id {rule_id} not found")
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, rule_data: RuleUpdate, db: Session = Depends(get_db)):
    """Update an existing rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Rule with id {rule_id} not found")

    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    logger.info(f"Rule #{rule.id} updated: {rule}")
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a rule by ID."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Rule with id {rule_id} not found")
    db.delete(rule)
    db.commit()
    logger.info(f"Rule #{rule_id} deleted")
    return None
