"""
Pydantic schemas for Rule validation.
Provides request/response models with strict input validation.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class RuleCreate(BaseModel):
    """Schema for creating a new rule."""
    metric: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Metric name to monitor (e.g. latency, error_rate, memory_usage)",
        examples=["latency"]
    )
    operator: Literal[">", "<", ">=", "<=", "=="] = Field(
        ...,
        description="Comparison operator for rule evaluation",
        examples=[">"]
    )
    threshold: float = Field(
        ...,
        description="Threshold value that triggers the alert",
        examples=[100.0]
    )
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Severity level of the alert when rule is triggered",
        examples=["HIGH"]
    )


class RuleUpdate(BaseModel):
    """Schema for updating an existing rule. All fields are optional."""
    metric: Optional[str] = Field(None, min_length=1, max_length=100)
    operator: Optional[Literal[">", "<", ">=", "<=", "=="]] = None
    threshold: Optional[float] = None
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None


class RuleResponse(BaseModel):
    """Schema for rule API responses."""
    id: int
    metric: str
    operator: str
    threshold: float
    severity: str

    class Config:
        from_attributes = True
