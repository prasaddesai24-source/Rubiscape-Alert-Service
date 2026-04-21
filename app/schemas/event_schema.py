"""
Pydantic schemas for Event validation.
Provides request/response models for event ingestion.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    """Schema for ingesting a new workflow event."""
    service_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Name of the AI service reporting the event",
        examples=["Model Service"]
    )
    metric: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Metric name observed",
        examples=["latency"]
    )
    value: float = Field(
        ...,
        description="Observed metric value",
        examples=[150.0]
    )


class EventResponse(BaseModel):
    """Schema for event API responses."""
    id: int
    service_name: str
    metric: str
    value: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
