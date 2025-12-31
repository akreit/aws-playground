"""Lambda handler for retrieving aggregated clickstream events via GET."""
import json
import logging
from datetime import datetime
from typing import Any

from shared.dynamodb import aggregate_events, get_events_by_period

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle GET requests to retrieve aggregated clickstream events.

    Query Parameters:
        - period: 'hourly' or 'daily' (default: 'daily')
        - date: Date in YYYY-MM-DD format (default: today)

    Args:
        event: API Gateway event object
        context: Lambda context object

    Returns:
        API Gateway response object
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        period = query_params.get("period", "daily")
        date = query_params.get("date")

        # Validate period
        if period not in ["hourly", "daily"]:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "error": "Invalid period. Must be 'hourly' or 'daily'",
                    }
                ),
            }

        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(
                        {
                            "error": "Invalid date format. Use YYYY-MM-DD",
                        }
                    ),
                }

        # Retrieve events
        events = get_events_by_period(period, date)

        # Aggregate events
        aggregated_data = aggregate_events(events, period)

        logger.info(
            "Successfully retrieved and aggregated %d events for period: %s",
            len(events),
            period,
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(aggregated_data, default=str),
        }

    except Exception as e:
        logger.error("Error retrieving events: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }
