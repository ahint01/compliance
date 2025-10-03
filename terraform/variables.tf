variable "project_name" {
  description = "compliance_checker"
  type        = string
  default     = "compliance-checker-demo"
}

variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-2"
}