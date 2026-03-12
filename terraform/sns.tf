# terraform/sns.tf

variable "alert_email" {
  description = "Email address to receive pipeline alerts"
  type        = string
}

resource "aws_sns_topic" "ml_pipeline_alerts" {
  name = "ml-pipeline-alerts"

  tags = {
    Project     = "support-ticket-triage"
    Environment = "dev"
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.ml_pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "sns_topic_arn" {
  value       = aws_sns_topic.ml_pipeline_alerts.arn
  description = "SNS topic ARN for pipeline alerts"
}


