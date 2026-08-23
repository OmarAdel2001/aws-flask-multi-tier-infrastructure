variable "private_db_subnet_ids" {
  description = "List of private subnet IDs for the database tier"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security Group ID for the database instances"
  type        = string
}

variable "db_name" {
  description = "Name of the primary database"
  type        = string
  default     = "webappdb"
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
  default     = "dbadmin"
}

variable "db_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Instance class for the RDS database"
  type        = string
  default     = "db.t3.micro"
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
  default     = "production"
}
