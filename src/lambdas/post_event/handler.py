"""Lambda handler for receiving clickstream events via POST."""
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from shared.dynamodb import store_event

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle POST requests to store clickstream events.

    Args:
        event: API Gateway event object
        context: Lambda context object

    Returns:
        API Gateway response object
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["user_id", "event_type"]
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "error": "Missing required fields",
                        "missing_fields": missing_fields,
                    }
                ),
            }

        # Create event data
        event_data = {
            "event_id": body.get("event_id", str(uuid4())),
            "user_id": body["user_id"],
            "event_type": body["event_type"],
            "timestamp": datetime.now(UTC).isoformat(),  # Use server timestamp
            "page_url": body.get("page_url"),
            "metadata": body.get("metadata", {}),
        }

        # Store event in DynamoDB
        store_event(event_data)

        logger.info("Successfully stored event: %s", event_data["event_id"])

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": "Event received successfully",
                    "event_id": event_data["event_id"],
                }
            ),
        }

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }

    except Exception as e:
        logger.error("Error processing event: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }
