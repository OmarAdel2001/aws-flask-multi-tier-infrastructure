output "primary_endpoint" {
  description = "The connection endpoint for the primary database (hostname:port)"
  value       = aws_db_instance.primary.endpoint
}

output "primary_address" {
  description = "The address of the primary database"
  value       = aws_db_instance.primary.address
}

output "replica_endpoint" {
  description = "The connection endpoint for the read replica database (hostname:port)"
  value       = aws_db_instance.replica.endpoint
}

output "replica_address" {
  description = "The address of the read replica database"
  value       = aws_db_instance.replica.address
}

output "db_name" {
  description = "The name of the database"
  value       = aws_db_instance.primary.db_name
}

output "db_username" {
  description = "The master username for the database"
  value       = aws_db_instance.primary.username
}
