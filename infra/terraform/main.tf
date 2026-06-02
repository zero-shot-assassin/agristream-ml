terraform {
  required_providers { aws = { source = "hashicorp/aws" version = "~> 5.0" } }
}

provider "aws" { region = var.aws_region }

module "s3" {
  source      = "./modules/s3"
  bucket_name = var.s3_bucket_name
  tags        = var.common_tags
}

module "sqs" {
  source     = "./modules/sqs"
  queue_name = var.sqs_queue_name
  tags       = var.common_tags
}

module "ecs" {
  source          = "./modules/ecs"
  cluster_name    = var.ecs_cluster_name
  task_family     = "agristream-worker"
  container_image = var.worker_image_uri
  s3_bucket_arn   = module.s3.bucket_arn
  s3_bucket_name  = module.s3.bucket_name
  sqs_queue_arn   = module.sqs.queue_arn
  sqs_queue_url   = module.sqs.queue_url
  aws_region      = var.aws_region
  tags            = var.common_tags
}