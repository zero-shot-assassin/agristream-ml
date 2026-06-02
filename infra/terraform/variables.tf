variable "aws_region" { default = "us-east-1" }
variable "s3_bucket_name" {}
variable "sqs_queue_name" { default = "agristream-jobs" }
variable "ecs_cluster_name" { default = "agristream-cluster" }
variable "worker_image_uri" {}  # ECR image URI
variable "common_tags" {
  default = {
    Project   = "agristream-ml"
    ManagedBy = "terraform"
  }
}