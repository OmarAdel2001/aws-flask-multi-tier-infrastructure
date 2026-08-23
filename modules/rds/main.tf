resource "aws_db_subnet_group" "db_subnet" {
  name        = "${var.environment}-db-subnet-group"
  subnet_ids  = var.private_db_subnet_ids
  description = "Subnet group for RDS database instances"

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_db_parameter_group" "pg" {
  name        = "${var.environment}-postgres-pg"
  family      = "postgres16"
  description = "Custom parameter group to enforce SSL/TLS on PostgreSQL"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  tags = {
    Name        = "${var.environment}-postgres-pg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "primary" {
  identifier                  = "${var.environment}-db-primary"
  allocated_storage           = 20
  max_allocated_storage       = 100
  storage_type                = "gp3"
  engine                      = "postgres"
  engine_version              = "16.3"
  instance_class              = var.db_instance_class
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  db_subnet_group_name        = aws_db_subnet_group.db_subnet.name
  vpc_security_group_ids      = [var.db_security_group_id]
  parameter_group_name        = aws_db_parameter_group.pg.name
  multi_az                    = true
  backup_retention_period     = 7
  backup_window               = "03:00-04:00"
  maintenance_window          = "Mon:04:00-Mon:05:00"
  skip_final_snapshot         = true
  publicly_accessible         = false
  deletion_protection         = false

  tags = {
    Name        = "${var.environment}-db-primary"
    Environment = var.environment
  }
}

resource "aws_db_instance" "replica" {
  identifier             = "${var.environment}-db-replica"
  replicate_source_db    = aws_db_instance.primary.identifier
  instance_class         = var.db_instance_class
  vpc_security_group_ids = [var.db_security_group_id]
  parameter_group_name   = aws_db_parameter_group.pg.name
  skip_final_snapshot    = true
  publicly_accessible    = false

  tags = {
    Name        = "${var.environment}-db-replica"
    Environment = var.environment
  }

  depends_on = [aws_db_instance.primary]
}
