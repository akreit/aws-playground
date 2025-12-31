output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.clickstream_events.name
}

output "post_event_function_name" {
  description = "Name of the POST event Lambda function"
  value       = aws_lambda_function.post_event.function_name
}

output "get_events_function_name" {
  description = "Name of the GET events Lambda function"
  value       = aws_lambda_function.get_events.function_name
}
