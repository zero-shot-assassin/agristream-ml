variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    Project   = "agristream-ml"
    ManagedBy = "terraform"
  }
}