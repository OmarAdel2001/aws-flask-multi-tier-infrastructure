variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "The deployment environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "The availability zones for the subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_name" {
  description = "The database name"
  type        = string
  default     = "webappdb"
}

variable "db_username" {
  description = "The master username for the database"
  type        = string
  default     = "dbadmin"
}

variable "db_password" {
  description = "The master password for the database"
  type        = string
  sensitive   = true
  default     = "CloudScaleAdmin2026"
}

variable "db_instance_class" {
  description = "The instance class for the database nodes"
  type        = string
  default     = "db.t3.micro"
}

variable "app_instance_type" {
  description = "The instance type for the application servers"
  type        = string
  default     = "t3.micro"
}
