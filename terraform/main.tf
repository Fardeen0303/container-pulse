terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.aws_region
}

# ── Security Group ──────────────────────────────────────────────────────────
resource "aws_security_group" "container_pulse" {
  name        = "container-pulse-sg"
  description = "Allow SSH, HTTP, and app ports"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  ingress {
    description = "Dashboard"
    from_port   = 8888
    to_port     = 8888
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Grafana"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Flask App"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "container-pulse-sg"
    Project = "container-pulse"
  }
}

# ── Key Pair ────────────────────────────────────────────────────────────────
resource "aws_key_pair" "container_pulse" {
  key_name   = "container-pulse-key"
  public_key = file(var.public_key_path)
}

# ── EC2 Instance ────────────────────────────────────────────────────────────
resource "aws_instance" "container_pulse" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.container_pulse.key_name
  vpc_security_group_ids = [aws_security_group.container_pulse.id]

  user_data = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size = 20
    volume_type = "gp2"
  }

  tags = {
    Name    = "container-pulse-server"
    Project = "container-pulse"
  }
}
