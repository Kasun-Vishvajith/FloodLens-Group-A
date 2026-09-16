terraform {
  required_version = ">= 1.6"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = var.region }
variable "region" { default = "ap-south-1" }
variable "bucket_name" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "backend_security_group_id" { type = string }
variable "db_password" {
  type = string
  sensitive = true
}
resource "aws_s3_bucket" "raw" { bucket = var.bucket_name }
resource "aws_s3_bucket_public_access_block" "raw" {
  bucket = aws_s3_bucket.raw.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}
resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_db_subnet_group" "db" {
  name = "floodlens-db"
  subnet_ids = var.private_subnet_ids
}
resource "aws_security_group" "db" {
  name = "floodlens-postgres"
  vpc_id = var.vpc_id
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    security_groups = [var.backend_security_group_id]
  }
}
resource "aws_db_instance" "db" {
  identifier = "floodlens-group-a"
  engine = "postgres"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  storage_encrypted = true
  db_name = "floodlens"
  username = "floodlens"
  password = var.db_password
  db_subnet_group_name = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible = false
  backup_retention_period = 1
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "floodlens-final"
}
output "bucket" { value = aws_s3_bucket.raw.id }
output "database_host" { value = aws_db_instance.db.address }
