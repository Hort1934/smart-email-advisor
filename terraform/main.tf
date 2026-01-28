terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }

  # Optional: Backend configuration for state management
  # Uncomment and configure if using remote state
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "smart-email-advisor/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Smart Email Advisor"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# Data source for latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------------------------------------------------------------------------
# Networking (dedicated VPC)
# ---------------------------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ---------------------------------------------------------------------------
# Key Pair (created automatically)
# ---------------------------------------------------------------------------

resource "tls_private_key" "app_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "app_key_pair" {
  key_name   = var.create_key_pair ? "${var.project_name}-key" : var.key_pair_name
  public_key = tls_private_key.app_key.public_key_openssh

  tags = {
    Name = "${var.project_name}-key-pair"
  }
}

# Save private key locally
resource "local_file" "private_key" {
  count           = var.create_key_pair ? 1 : 0
  content         = tls_private_key.app_key.private_key_pem
  filename        = "${path.module}/${var.project_name}-key.pem"
  file_permission = "0600"
}

# ---------------------------------------------------------------------------
# SSM IAM Role and Instance Profile
# ---------------------------------------------------------------------------

resource "aws_iam_role" "ssm_role" {
  name = "${var.project_name}-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ssm-role"
  }
}

# Attach AWS managed policy for SSM
resource "aws_iam_role_policy_attachment" "ssm_managed_instance_core" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach CloudWatch agent policy (optional but useful)
resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Bedrock permissions (required for bedrock-runtime InvokeModel)
resource "aws_iam_role_policy_attachment" "bedrock_full_access" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# Create instance profile
resource "aws_iam_instance_profile" "ssm_instance_profile" {
  name = "${var.project_name}-ssm-profile"
  role = aws_iam_role.ssm_role.name

  tags = {
    Name = "${var.project_name}-ssm-profile"
  }
}

# Security Group for EC2 instance
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for Smart Email Advisor application"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    description = "SSH from specified IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  # HTTP access
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# Elastic IP
resource "aws_eip" "app_eip" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }

  depends_on = [aws_instance.app]
}

# EC2 Instance
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.create_key_pair ? aws_key_pair.app_key_pair.key_name : (var.key_pair_name != "" ? var.key_pair_name : null)
  iam_instance_profile   = aws_iam_instance_profile.ssm_instance_profile.name
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  subnet_id              = aws_subnet.public.id
  associate_public_ip_address = true

  root_block_device {
    volume_type = "gp3"
    volume_size = var.volume_size
    encrypted   = true
  }

  user_data = <<-EOF
              #!/bin/bash
              set -euxo pipefail

              # Update system
              apt-get update -y
              apt-get upgrade -y
              
              # Install basic tools needed for deployment/runtime
              apt-get install -y \
                ca-certificates \
                curl \
                wget \
                git \
                htop \
                jq \
                unzip \
                rsync \
                gnupg \
                lsb-release

              # Install Docker Engine + Docker Compose plugin (official repo)
              install -m 0755 -d /etc/apt/keyrings
              if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                chmod a+r /etc/apt/keyrings/docker.gpg
              fi

              echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
                > /etc/apt/sources.list.d/docker.list

              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              systemctl enable docker
              systemctl start docker

            # Add default Ubuntu user to docker group (so sudo is not required)
            usermod -aG docker ubuntu || true
            
            # Ensure docker group has correct permissions
            chmod 666 /var/run/docker.sock 2>/dev/null || true
            
            # Restart docker service to apply group changes
            systemctl restart docker || true
              
              # Ensure SSM Agent is installed and running (usually pre-installed on Ubuntu 22.04)
              # On Ubuntu 22.04 it is commonly installed via snap; try both service names.
              sudo systemctl enable amazon-ssm-agent || true
              sudo systemctl start amazon-ssm-agent || true
              sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service || true
              sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service || true
              
              # Log instance details
              docker --version > /tmp/docker-version.txt || true
              docker compose version > /tmp/docker-compose-version.txt || true
              echo "Instance ready for deployment" > /tmp/instance-ready.txt
              EOF

  tags = {
    Name = "${var.project_name}-instance"
  }
}

# Associate Elastic IP with instance
resource "aws_eip_association" "app_eip_assoc" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app_eip.id
}

