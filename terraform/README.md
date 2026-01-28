# Terraform Infrastructure for Smart Email Advisor

This directory contains Terraform configuration to provision AWS infrastructure for the Smart Email Advisor application.

## What Gets Created

- **VPC** - Dedicated VPC with public subnet, Internet Gateway, and route table
- **EC2 Instance** - Ubuntu 22.04 LTS server with SSM Session Manager enabled
- **Elastic IP** - Static public IP address
- **Security Group** - Firewall rules (SSH, HTTP, HTTPS)
- **Key Pair** - Automatically created (or use existing)
- **IAM Role** - SSM role for Session Manager access
- **Instance Profile** - Attached to EC2 for SSM access

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** installed (>= 1.0)
   ```bash
   # Install Terraform
   # macOS: brew install terraform
   # Linux: https://www.terraform.io/downloads
   ```
3. **AWS CLI** configured
   ```bash
   aws configure
   ```
4. **AWS Key Pair** created in AWS Console
   - Go to EC2 → Key Pairs → Create key pair
   - Download the private key (.pem file)
   - Note the key pair name

## Quick Start

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Required settings:**
- `create_key_pair` - Set to `true` to auto-create key pair (recommended)
- `ssh_allowed_cidrs` - Your IP address (for security)

**Optional settings:**
- `key_pair_name` - Only needed if `create_key_pair = false` (use existing key)

**Get your IP:**
```bash
curl -s https://checkip.amazonaws.com
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

### 5. View Outputs

```bash
terraform output
```

### 6. Access via SSM Session Manager

After deployment, you can access the instance via SSM (no SSH key needed):

```bash
# Using AWS CLI
aws ssm start-session --target i-xxxxxxxxxxxxx

# Or use the output command
terraform output -raw ssm_session_command
```

**Benefits of SSM:**
- ✅ No SSH keys needed
- ✅ No security group rules for SSH required
- ✅ Encrypted connection
- ✅ Session logging
- ✅ Works through AWS Console too

## Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `project_name` | Project name for resources | `smart-email-advisor` |
| `environment` | Environment name | `prod` |
| `instance_type` | EC2 instance type | `t3.medium` |
| `volume_size` | Root volume size (GB) | `40` |
| `create_key_pair` | Auto-create key pair | `true` |
| `key_pair_name` | Existing key pair name (if create_key_pair=false) | `""` |
| `instance_user` | SSH user | `ubuntu` |
| `ssh_allowed_cidrs` | Allowed SSH IPs | `["0.0.0.0/0"]` |
| `vpc_cidr` | VPC CIDR block | `10.20.0.0/16` |
| `public_subnet_cidr` | Public subnet CIDR | `10.20.1.0/24` |
| `availability_zone` | Availability zone (empty = auto) | `""` |

## Instance Types

Recommended instance types:

- **Development**: `t3.small` (2 vCPU, 2 GB RAM)
- **Production**: `t3.medium` (2 vCPU, 4 GB RAM) - Minimum
- **Production**: `t3.large` (2 vCPU, 8 GB RAM) - Recommended
- **High Load**: `t3.xlarge` (4 vCPU, 16 GB RAM)

## Security Best Practices

1. **Restrict SSH Access**
   ```hcl
   ssh_allowed_cidrs = ["YOUR_IP/32"]
   ```
   Get your IP: `curl -s https://checkip.amazonaws.com`

2. **Use Encrypted Volumes**
   - Volumes are encrypted by default

3. **Regular Updates**
   - Instance runs `apt-get update` on first boot

## Outputs

After applying, Terraform outputs:

- `instance_id` - EC2 Instance ID
- `elastic_ip` - Elastic IP address
- `application_url` - Application URL
- `ssh_command` - SSH connection command
- `ssm_session_command` - SSM Session Manager command (no SSH needed!)
- `ssm_session_manager_url` - AWS Console URL for SSM
- `key_pair_name` - Name of key pair (created or existing)
- `private_key_path` - Path to private key (if created)

## Managing Infrastructure

### View Current State

```bash
terraform show
```

### View Outputs

```bash
terraform output
```

### Update Infrastructure

```bash
# Modify terraform.tfvars or variables
terraform plan
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

**Warning**: This will delete all resources including the EC2 instance and data!

## Integration with Deployment

The infrastructure is automatically integrated with the deployment script:

```bash
# From project root
./deploy-all.sh
```

This will:
1. Provision infrastructure (if needed)
2. Deploy application

## Troubleshooting

### Terraform Not Found

```bash
# Install Terraform
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### AWS Credentials Not Configured

```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

### Key Pair Management

**Option 1: Auto-create (Recommended)**
- Set `create_key_pair = true` in `terraform.tfvars`
- Key pair will be created automatically
- Private key saved to `terraform/${project_name}-key.pem`
- Set permissions: `chmod 600 terraform/${project_name}-key.pem`

**Option 2: Use Existing Key**
- Set `create_key_pair = false`
- Set `key_pair_name` to your existing key pair name

### Access Methods

**SSM Session Manager (Recommended - No SSH needed)**
```bash
aws ssm start-session --target i-xxxxxxxxxxxxx
```

**SSH (if key pair created)**
```bash
ssh -i terraform/smart-email-advisor-key.pem ubuntu@ELASTIC_IP
```

### Permission Denied on SSH Key

```bash
chmod 600 terraform/smart-email-advisor-key.pem
```

## Cost Estimation

Approximate monthly costs (us-east-1):

- **t3.medium**: ~$30/month
- **t3.large**: ~$60/month
- **Elastic IP**: Free (when attached to instance)
- **Data Transfer**: ~$0.09/GB (first 100 GB free)

**Total**: ~$30-60/month for basic setup

## Advanced Configuration

### Custom VPC

To use a custom VPC instead of default:

1. Create VPC in AWS Console
2. Add data source in `main.tf`:
   ```hcl
   data "aws_vpc" "custom" {
     id = "vpc-xxxxx"
   }
   ```
3. Update `vpc_id` references

### Remote State (Optional)

To use S3 backend for state:

1. Create S3 bucket
2. Uncomment backend block in `main.tf`
3. Update bucket name and region

### Additional Security Groups

Add more security groups as needed in `main.tf`:

```hcl
resource "aws_security_group_rule" "custom" {
  type              = "ingress"
  from_port         = 8080
  to_port           = 8080
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}
```

## Support

For issues:
1. Check Terraform version: `terraform version`
2. Check AWS credentials: `aws sts get-caller-identity`
3. Review Terraform plan: `terraform plan`
4. Check AWS Console for resource status
