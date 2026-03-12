resource "aws_cloudwatch_event_rule" "s3_new_data" {
  name        = "s3-new-training-data"
  description = "Fires when new data is uploaded to training bucket"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.training_bucket_name]
      }
      object = {
        key = [{ suffix = ".csv" }]
      }
    }
  })
}
