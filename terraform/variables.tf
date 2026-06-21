variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID (us-east-1 default)"
  type        = string
  default     = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS - us-east-1
}

variable "instance_type" {
  description = "EC2 instance type — t2.micro is free tier eligible"
  type        = string
  default     = "t2.micro"
}

variable "public_key_path" {
  description = "Path to your local SSH public key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "allowed_cidr" {
  description = "Your IP CIDR for SSH access (e.g. 1.2.3.4/32)"
  type        = string
  default     = "0.0.0.0/0" # restrict this to your IP in production
}
