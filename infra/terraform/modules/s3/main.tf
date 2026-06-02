# infra/terraform/modules/s3/main.tf
resource "aws_s3_bucket" "images" {
  bucket = var.bucket_name
  tags   = var.tags
}

# Versioning — protects against accidental deletion/overwrites
resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rules — cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "archive-old-images"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"  # Infrequent Access — ~50% cheaper
    }

    transition {
      days          = 365
      storage_class = "GLACIER"        # Cold storage — ~90% cheaper
    }
  }
}

# Block public access — security baseline
resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}