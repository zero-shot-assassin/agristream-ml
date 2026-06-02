# infra/terraform/modules/sqs/main.tf

# Dead-Letter Queue — holds poison messages for inspection
resource "aws_sqs_queue" "dlq" {
  name = "${var.queue_name}-dlq"
  tags = var.tags
}

# Main queue with redrive policy
resource "aws_sqs_queue" "main" {
  name = var.queue_name
  tags = var.tags

  # Messages become visible again after 60s if not deleted
  visibility_timeout_seconds = 60

  # Long polling — worker waits up to 20s for messages
  receive_wait_time_seconds = 20

  # Redrive policy: after 3 failed receives, move to DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}