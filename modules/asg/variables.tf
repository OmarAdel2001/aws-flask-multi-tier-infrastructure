variable "private_app_subnet_ids" {
  description = "List of private subnet IDs for the application tier"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security Group ID for the application instances"
  type        = string
}

variable "target_group_arn" {
  description = "The ARN of the ALB Target Group"
  type        = string
}

variable "db_primary_endpoint" {
  description = "Connection endpoint of the primary database"
  type        = string
}

variable "db_replica_endpoint" {
  description = "Connection endpoint of the read replica database"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database master username"
  type        = string
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "app_bucket_name" {
  description = "Name of the S3 bucket holding application deployment code"
  type        = string
}

variable "app_bucket_arn" {
  description = "ARN of the S3 bucket holding application deployment code"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
  default     = "production"
}
