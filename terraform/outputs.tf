output "bucket_name" {
  value = aws_s3_bucket.ml_bucket.bucket
}


output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker_role.arn
}

