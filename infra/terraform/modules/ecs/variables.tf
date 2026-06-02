variable "cluster_name" { type = string }
variable "task_family" { type = string }
variable "container_image" { type = string }
variable "s3_bucket_arn" { type = string }
variable "s3_bucket_name" { type = string }
variable "sqs_queue_arn" { type = string }
variable "sqs_queue_url" { type = string }
variable "aws_region" { type = string default = "us-east-1" }
variable "tags" { type = map(string) default = {} }