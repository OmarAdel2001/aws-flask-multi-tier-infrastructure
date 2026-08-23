output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "The public DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "db_primary_endpoint" {
  description = "The endpoint address of the primary database"
  value       = module.rds.primary_address
}

output "db_replica_endpoint" {
  description = "The endpoint address of the read replica database"
  value       = module.rds.replica_address
}

output "db_name" {
  description = "The name of the database"
  value       = module.rds.db_name
}

output "db_username" {
  description = "The database master username"
  value       = module.rds.db_username
}
