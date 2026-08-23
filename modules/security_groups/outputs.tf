output "alb_sg_id" {
  description = "The ID of the ALB Security Group"
  value       = aws_security_group.alb.id
}

output "app_sg_id" {
  description = "The ID of the App Security Group"
  value       = aws_security_group.app.id
}

output "db_sg_id" {
  description = "The ID of the Database Security Group"
  value       = aws_security_group.db.id
}
