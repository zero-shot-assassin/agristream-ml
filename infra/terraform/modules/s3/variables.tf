variable "bucket_name" {
  description = "Globally unique S3 bucket name"
  type        = string
}

variable "tags" {
  description = "Resource tags for cost tracking"
  type        = map(string)
  default = {
    Project   = "agristream-ml"
    ManagedBy = "terraform"
  }
}