"""Tests for POST event Lambda handler."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB store_event function."""
    with patch("post_event.handler.store_event") as mock:
        yield mock


def test_lambda_handler_success(mock_dynamodb):
    """Test successful event posting."""
    # Import here to ensure mock is in place
    from post_event.handler import lambda_handler

    event = {
        "body": json.dumps(
            {
                "user_id": "user123",
                "event_type": "click",
                "page_url": "https://example.com/page",
                "metadata": {"button": "submit"},
            }
        )
    }
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["message"] == "Event received successfully"
    assert "event_id" in body
    mock_dynamodb.assert_called_once()


def test_lambda_handler_missing_required_fields(mock_dynamodb):
    """Test event posting with missing required fields."""
    from post_event.handler import lambda_handler

    event = {"body": json.dumps({"user_id": "user123"})}  # Missing event_type
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert "event_type" in body["missing_fields"]
    mock_dynamodb.assert_not_called()


def test_lambda_handler_invalid_json(mock_dynamodb):
    """Test event posting with invalid JSON."""
    from post_event.handler import lambda_handler

    event = {"body": "not valid json"}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    mock_dynamodb.assert_not_called()


def test_lambda_handler_with_custom_event_id(mock_dynamodb):
    """Test event posting with custom event ID."""
    from post_event.handler import lambda_handler

    custom_event_id = "custom-event-123"
    event = {
        "body": json.dumps(
            {
                "event_id": custom_event_id,
                "user_id": "user123",
                "event_type": "view",
            }
        )
    }
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["event_id"] == custom_event_id
