# AWS Clickstream API

A serverless clickstream event processing system built with AWS Lambda, API Gateway, and DynamoDB.

## Overview

This project implements a scalable, serverless API for collecting and analyzing clickstream events. It features:

- **POST /events**: Receives clickstream events in real-time
- **GET /events**: Returns aggregated event statistics (hourly & daily)
- **DynamoDB**: Cost-effective persistence with automatic TTL
- **Infrastructure as Code**: Terraform for complete AWS infrastructure
- **CI/CD**: GitHub Actions for automated testing and deployment

## Architecture

```
Client → API Gateway → Lambda Functions → DynamoDB
                           ↓
                    CloudWatch Logs
```

### Components

- **API Gateway (HTTP API)**: RESTful endpoints with CORS support
- **Lambda Functions**: Python 3.11 serverless compute
  - `post-event`: Stores incoming clickstream events
  - `get-events`: Aggregates and returns event statistics
- **DynamoDB**: NoSQL database with GSI for time-based queries
- **CloudWatch**: Logging and monitoring
- **Terraform**: Infrastructure provisioning

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- [Terraform](https://www.terraform.io/downloads.html) >= 1.5
- AWS Account with appropriate permissions
- AWS CLI configured

## Local Development

### Setup

1. Install dependencies with uv:
```bash
uv sync --all-extras
```

2. Run tests:
```bash
uv run pytest tests/ -v
```

3. Lint code:
```bash
uv run ruff check src/
```

### Project Structure

```
.
├── src/lambdas/
│   ├── post_event/       # POST event handler
│   ├── get_events/       # GET events handler
│   └── shared/           # Shared utilities and models
├── terraform/            # Infrastructure as Code
│   ├── main.tf          # Provider configuration
│   ├── lambda.tf        # Lambda functions
│   ├── api_gateway.tf   # API Gateway setup
│   ├── dynamodb.tf      # DynamoDB table
│   └── variables.tf     # Input variables
├── tests/               # Unit tests
├── .github/workflows/   # CI/CD pipelines
└── pyproject.toml       # Python project configuration
```

## Deployment

### Using GitHub Actions (Recommended)

1. Set up GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

2. Push to main branch or manually trigger the deploy workflow

### Manual Deployment

1. Initialize Terraform:
```bash
cd terraform
terraform init
```

2. Plan infrastructure changes:
```bash
terraform plan -var="environment=dev"
```

3. Apply infrastructure:
```bash
terraform apply -var="environment=dev"
```

4. Get the API Gateway URL:
```bash
terraform output api_gateway_url
```

## API Usage

### POST /events

Submit a clickstream event:

```bash
curl -X POST https://your-api-url.amazonaws.com/dev/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "event_type": "click",
    "page_url": "https://example.com/page",
    "metadata": {
      "button": "submit",
      "section": "header"
    }
  }'
```

**Request Body:**
- `user_id` (required): User identifier
- `event_type` (required): Event type (e.g., click, view, purchase)
- `event_id` (optional): Custom event ID (auto-generated if not provided)
- `timestamp` (optional): ISO 8601 timestamp (defaults to current time)
- `page_url` (optional): URL where event occurred
- `metadata` (optional): Additional event data

**Response:**
```json
{
  "message": "Event received successfully",
  "event_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /events

Retrieve aggregated event statistics:

```bash
# Daily aggregation (default)
curl "https://your-api-url.amazonaws.com/dev/events?period=daily&date=2024-01-01"

# Hourly aggregation
curl "https://your-api-url.amazonaws.com/dev/events?period=hourly&date=2024-01-01"
```

**Query Parameters:**
- `period` (optional): `daily` or `hourly` (default: `daily`)
- `date` (optional): Date in YYYY-MM-DD format (default: today)

**Response (daily):**
```json
{
  "period": "daily",
  "date": "2024-01-01",
  "event_counts": {
    "click": 150,
    "view": 300,
    "purchase": 25
  },
  "unique_users": 75,
  "total_events": 475
}
```

**Response (hourly):**
```json
{
  "aggregations": [
    {
      "period": "hourly",
      "start_time": "2024-01-01T10:00:00",
      "end_time": "2024-01-01T10:59:59",
      "event_counts": {
        "click": 15,
        "view": 30
      },
      "unique_users": 12
    }
  ]
}
```

## Data Retention

Events are automatically deleted after 30 days via DynamoDB TTL to manage costs.

## Cost Optimization

This architecture is designed for low cost:

- **DynamoDB**: Pay-per-request billing (no provisioned capacity)
- **Lambda**: Pay only for execution time
- **API Gateway**: HTTP API (cheaper than REST API)
- **CloudWatch**: 7-day log retention
- **TTL**: Automatic data cleanup after 30 days

## Monitoring

CloudWatch Logs are available for:
- Lambda function executions
- API Gateway access logs
- Error tracking and debugging

Access logs via AWS Console or AWS CLI:
```bash
aws logs tail /aws/lambda/clickstream-api-post-event-dev --follow
```

## CI/CD Workflows

### Test Workflow
- Runs on every push and pull request
- Executes linting and unit tests
- Reports test coverage

### Deploy Workflow
- Runs on push to main branch
- Can be manually triggered for different environments
- Deploys infrastructure via Terraform
- Outputs API Gateway URL

## License

MIT License - see LICENSE file for details
