module "vpc" {
  source = "./modules/vpc"

  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  environment        = var.environment
}

module "security_groups" {
  source = "./modules/security_groups"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}

module "rds" {
  source = "./modules/rds"

  private_db_subnet_ids = module.vpc.private_db_subnet_ids
  db_security_group_id  = module.security_groups.db_sg_id
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  db_instance_class     = var.db_instance_class
  environment           = var.environment
}

module "alb" {
  source = "./modules/alb"

  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_sg_id
  environment           = var.environment
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket" "app_bucket" {
  bucket        = "cloudscale-app-deploy-${random_string.bucket_suffix.result}"
  force_destroy = true

  tags = {
    Name        = "${var.environment}-app-deploy-bucket"
    Environment = var.environment
  }
}

resource "aws_s3_object" "app_py" {
  bucket = aws_s3_bucket.app_bucket.id
  key    = "app.py"
  source = "${path.module}/app/app.py"
  etag   = filemd5("${path.module}/app/app.py")
}

resource "aws_s3_object" "requirements_txt" {
  bucket = aws_s3_bucket.app_bucket.id
  key    = "requirements.txt"
  source = "${path.module}/app/requirements.txt"
  etag   = filemd5("${path.module}/app/requirements.txt")
}

resource "aws_s3_object" "index_html" {
  bucket = aws_s3_bucket.app_bucket.id
  key    = "index.html"
  source = "${path.module}/app/templates/index.html"
  etag   = filemd5("${path.module}/app/templates/index.html")
}

module "asg" {
  source = "./modules/asg"

  private_app_subnet_ids = module.vpc.private_app_subnet_ids
  app_security_group_id  = module.security_groups.app_sg_id
  target_group_arn       = module.alb.target_group_arn
  db_primary_endpoint    = module.rds.primary_address
  db_replica_endpoint    = module.rds.replica_address
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  app_bucket_name        = aws_s3_bucket.app_bucket.id
  app_bucket_arn         = aws_s3_bucket.app_bucket.arn
  instance_type          = var.app_instance_type
  environment            = var.environment

  depends_on = [
    aws_s3_object.app_py,
    aws_s3_object.requirements_txt,
    aws_s3_object.index_html
  ]
}
