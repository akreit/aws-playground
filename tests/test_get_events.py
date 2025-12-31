"""Tests for GET events Lambda handler."""
import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_get_events():
    """Mock DynamoDB get_events_by_period function."""
    with patch("get_events.handler.get_events_by_period") as mock:
        mock.return_value = [
            {
                "event_id": "event1",
                "user_id": "user1",
                "event_type": "click",
                "timestamp": "2024-01-01T10:00:00",
            },
            {
                "event_id": "event2",
                "user_id": "user2",
                "event_type": "view",
                "timestamp": "2024-01-01T10:30:00",
            },
            {
                "event_id": "event3",
                "user_id": "user1",
                "event_type": "click",
                "timestamp": "2024-01-01T11:00:00",
            },
        ]
        yield mock


@pytest.fixture
def mock_aggregate():
    """Mock aggregate_events function."""
    with patch("get_events.handler.aggregate_events") as mock:
        mock.return_value = {
            "period": "daily",
            "date": "2024-01-01",
            "event_counts": {"click": 2, "view": 1},
            "unique_users": 2,
            "total_events": 3,
        }
        yield mock


def test_lambda_handler_success_daily(mock_get_events, mock_aggregate):
    """Test successful retrieval with daily aggregation."""
    from get_events.handler import lambda_handler

    event = {"queryStringParameters": {"period": "daily", "date": "2024-01-01"}}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["period"] == "daily"
    assert body["total_events"] == 3
    mock_get_events.assert_called_once_with("daily", "2024-01-01")


def test_lambda_handler_success_hourly(mock_get_events, mock_aggregate):
    """Test successful retrieval with hourly aggregation."""
    from get_events.handler import lambda_handler

    mock_aggregate.return_value = {
        "aggregations": [
            {
                "period": "hourly",
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T10:59:59",
                "event_counts": {"click": 1, "view": 1},
                "unique_users": 2,
            }
        ]
    }

    event = {"queryStringParameters": {"period": "hourly"}}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "aggregations" in body


def test_lambda_handler_invalid_period(mock_get_events, mock_aggregate):
    """Test retrieval with invalid period."""
    from get_events.handler import lambda_handler

    event = {"queryStringParameters": {"period": "weekly"}}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    mock_get_events.assert_not_called()


def test_lambda_handler_invalid_date_format(mock_get_events, mock_aggregate):
    """Test retrieval with invalid date format."""
    from get_events.handler import lambda_handler

    event = {"queryStringParameters": {"date": "01-01-2024"}}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    mock_get_events.assert_not_called()


def test_lambda_handler_default_parameters(mock_get_events, mock_aggregate):
    """Test retrieval with default parameters."""
    from get_events.handler import lambda_handler

    event = {}
    context = MagicMock()

    response = lambda_handler(event, context)

    assert response["statusCode"] == 200
    mock_get_events.assert_called_once_with("daily", None)
