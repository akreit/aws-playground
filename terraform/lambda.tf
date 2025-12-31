# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for DynamoDB access
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "${var.project_name}-lambda-dynamodb-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.clickstream_events.arn,
          "${aws_dynamodb_table.clickstream_events.arn}/index/*"
        ]
      }
    ]
  })
}

# Package Lambda functions
data "archive_file" "post_event_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambdas"
  output_path = "${path.module}/lambda_packages/post_event.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]
}

data "archive_file" "get_events_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../src/lambdas"
  output_path = "${path.module}/lambda_packages/get_events.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]
}

# POST Event Lambda Function
resource "aws_lambda_function" "post_event" {
  filename         = data.archive_file.post_event_lambda.output_path
  function_name    = "${var.project_name}-post-event-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "post_event.handler.lambda_handler"
  source_code_hash = data.archive_file.post_event_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.clickstream_events.name
    }
  }
}

# GET Events Lambda Function
resource "aws_lambda_function" "get_events" {
  filename         = data.archive_file.get_events_lambda.output_path
  function_name    = "${var.project_name}-get-events-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "get_events.handler.lambda_handler"
  source_code_hash = data.archive_file.get_events_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.clickstream_events.name
    }
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "post_event_logs" {
  name              = "/aws/lambda/${aws_lambda_function.post_event.function_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "get_events_logs" {
  name              = "/aws/lambda/${aws_lambda_function.get_events.function_name}"
  retention_in_days = 7
}
