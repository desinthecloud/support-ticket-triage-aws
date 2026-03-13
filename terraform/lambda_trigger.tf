data "archive_file" "github_dispatch" {
  type        = "zip"
  source_file = "${path.module}/../scripts/trigger/github_dispatch.py"
  output_path = "${path.module}/github_dispatch.zip"
}

resource "aws_iam_role" "lambda_trigger_role" {
  name = "support-ticket-lambda-trigger-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_trigger_policy" {
  name = "lambda-trigger-policy"
  role = aws_iam_role.lambda_trigger_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:us-east-1:140324736937:secret:github-actions-token-De4BRL"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "github_dispatch" {
  filename         = "${path.module}/github_dispatch.zip"
  function_name    = "support-ticket-github-dispatch"
  role             = aws_iam_role.lambda_trigger_role.arn
  handler          = "github_dispatch.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.github_dispatch.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      GITHUB_SECRET_NAME = "github-actions-token"
      GITHUB_REPO        = "desinthecloud/support-ticket-triage-aws"
      GITHUB_WORKFLOW    = "ml-pipeline.yml"
    }
  }
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.github_dispatch.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_new_data.arn
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule = aws_cloudwatch_event_rule.s3_new_data.name
  arn  = aws_lambda_function.github_dispatch.arn
}
