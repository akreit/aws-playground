"""Data models for clickstream events."""
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ClickstreamEvent(BaseModel):
    """Model for a clickstream event."""

    event_id: str = Field(..., description="Unique identifier for the event")
    user_id: str = Field(..., description="User identifier")
    event_type: str = Field(..., description="Type of event (e.g., click, view, purchase)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )
    page_url: str | None = Field(None, description="Page URL where event occurred")
    metadata: dict | None = Field(default_factory=dict, description="Additional event metadata")


class AggregatedEvents(BaseModel):
    """Model for aggregated event statistics."""

    period: str = Field(..., description="Aggregation period (hourly or daily)")
    start_time: datetime = Field(..., description="Start of the aggregation period")
    end_time: datetime = Field(..., description="End of the aggregation period")
    event_counts: dict[str, int] = Field(
        default_factory=dict, description="Count of events by type"
    )
    unique_users: int = Field(0, description="Number of unique users in period")
