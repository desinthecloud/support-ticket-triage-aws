variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}


variable "project_name" {
  description = "Project identifier used in resource names"
  default     = "support-ticket-ml"
}


variable "bucket_suffix" {
  description = "Unique suffix to make the S3 bucket name globally unique"
  type        = string
}

variable "training_bucket_name" {
  description = "Name of the S3 bucket holding training data"
  type        = string
  default     = "support-ticket-ml-supporttickets0302"
}

