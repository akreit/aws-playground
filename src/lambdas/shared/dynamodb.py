"""DynamoDB utilities for storing and retrieving clickstream events."""
import os
from datetime import UTC, datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Key

# Table name and TTL from environment variables
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "clickstream-events")
TTL_DAYS = int(os.environ.get("EVENT_TTL_DAYS", "30"))

# Initialize DynamoDB resource lazily
_dynamodb = None
_table = None


def _get_table():
    """Get DynamoDB table, initializing if necessary."""
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb")
        _table = _dynamodb.Table(TABLE_NAME)
    return _table


def store_event(event_data: dict) -> None:
    """
    Store a clickstream event in DynamoDB.

    Args:
        event_data: Dictionary containing event data
    """
    table = _get_table()

    # Add TTL (configurable via EVENT_TTL_DAYS environment variable, default: 30 days)
    ttl = int((datetime.now(UTC) + timedelta(days=TTL_DAYS)).timestamp())

    item = {
        "pk": f"EVENT#{event_data['event_id']}",
        "sk": event_data["timestamp"],
        "event_id": event_data["event_id"],
        "user_id": event_data["user_id"],
        "event_type": event_data["event_type"],
        "timestamp": event_data["timestamp"],
        "page_url": event_data.get("page_url"),
        "metadata": event_data.get("metadata", {}),
        "ttl": ttl,
        # GSI keys for querying by time
        "gsi1_pk": f"EVENTS#{event_data['timestamp'][:10]}",  # Date-based partition
        "gsi1_sk": event_data["timestamp"],
    }

    table.put_item(Item=item)


def get_events_by_period(period: str, date: str | None = None) -> list[dict]:
    """
    Retrieve events for a specific period.

    Args:
        period: Either 'hourly' or 'daily'
        date: Date string in YYYY-MM-DD format (default: today)

    Returns:
        List of event dictionaries
    """
    table = _get_table()

    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%d")

    # Query using GSI
    response = table.query(
        IndexName="TimestampIndex",
        KeyConditionExpression=Key("gsi1_pk").eq(f"EVENTS#{date}"),
        ScanIndexForward=True,
    )

    return response.get("Items", [])


def aggregate_events(events: list[dict], period: str) -> dict:
    """
    Aggregate events by period.

    Args:
        events: List of event dictionaries
        period: Either 'hourly' or 'daily'

    Returns:
        Dictionary with aggregated statistics
    """
    event_counts = {}
    unique_users = set()

    for event in events:
        # Count by event type
        event_type = event.get("event_type", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Track unique users
        if event.get("user_id"):
            unique_users.add(event["user_id"])

    if period == "hourly":
        # Group by hour
        hourly_stats = {}
        for event in events:
            timestamp = event.get("timestamp", "")
            if timestamp:
                hour_key = timestamp[:13]  # YYYY-MM-DDTHH
                if hour_key not in hourly_stats:
                    hourly_stats[hour_key] = {
                        "event_counts": {},
                        "unique_users": set(),
                    }
                event_type = event.get("event_type", "unknown")
                hourly_stats[hour_key]["event_counts"][event_type] = (
                    hourly_stats[hour_key]["event_counts"].get(event_type, 0) + 1
                )
                if event.get("user_id"):
                    hourly_stats[hour_key]["unique_users"].add(event["user_id"])

        # Convert sets to counts
        result = []
        for hour_key, stats in hourly_stats.items():
            result.append(
                {
                    "period": "hourly",
                    "start_time": hour_key + ":00:00",
                    "end_time": hour_key + ":59:59",
                    "event_counts": stats["event_counts"],
                    "unique_users": len(stats["unique_users"]),
                }
            )
        return {"aggregations": result}

    # Daily aggregation
    # Extract date from first event if available
    date_str = None
    if events and events[0].get("timestamp"):
        date_str = events[0]["timestamp"][:10]  # YYYY-MM-DD

    return {
        "period": "daily",
        "date": date_str,
        "event_counts": event_counts,
        "unique_users": len(unique_users),
        "total_events": len(events),
    }
