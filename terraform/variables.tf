variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "smart-email-advisor"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition = can(regex("^t[23]\\.[a-z]+$", var.instance_type))
    error_message = "Instance type must be a valid T2 or T3 instance type."
  }
}

variable "volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 40
}

variable "create_key_pair" {
  description = "Whether to create a new key pair. If true, key_pair_name will be auto-generated"
  type        = bool
  default     = true
}

variable "key_pair_name" {
  description = "Name of existing AWS Key Pair for SSH access (required if create_key_pair is false)"
  type        = string
  default     = ""
  
  validation {
    condition     = var.create_key_pair || length(var.key_pair_name) > 0
    error_message = "key_pair_name must be provided when create_key_pair is false."
  }
}

variable "ssh_key_path" {
  description = "Local path to SSH private key file"
  type        = string
  default     = "~/.ssh/id_rsa"
}

variable "instance_user" {
  description = "SSH user for EC2 instance"
  type        = string
  default     = "ubuntu"
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH to instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Change this to your IP for security
  
  validation {
    condition     = length(var.ssh_allowed_cidrs) > 0
    error_message = "At least one SSH allowed CIDR must be specified."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.20.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for the public subnet (leave empty to auto-pick the first available AZ)"
  type        = string
  default     = ""
}
