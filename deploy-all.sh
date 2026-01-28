#!/bin/bash

# =============================================================================
# Complete AWS Deployment: Infrastructure + Application
# =============================================================================
# This script provisions AWS infrastructure and deploys the application
# Usage: ./deploy-all.sh [--skip-infra] [--skip-app]
#
# Options:
#   --skip-infra    Skip infrastructure provisioning (use existing)
#   --skip-app      Skip application deployment (only provision infrastructure)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
SKIP_INFRA=false
SKIP_APP=false

for arg in "$@"; do
    case $arg in
        --skip-infra)
            SKIP_INFRA=true
            shift
            ;;
        --skip-app)
            SKIP_APP=true
            shift
            ;;
        *)
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Best-effort: read project_name from terraform.tfvars (used for key filename defaults)
PROJECT_NAME="$(grep -E '^project_name' "$TERRAFORM_DIR/terraform.tfvars" 2>/dev/null | cut -d'\"' -f2 || true)"
if [ -z "$PROJECT_NAME" ]; then
  PROJECT_NAME="smart-email-advisor"
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}Smart Email Advisor - Complete AWS Deployment${NC}                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${CYAN}Infrastructure + Application${NC}                                      ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

# Check prerequisites
echo -e "${YELLOW}[Pre-flight Checks]${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}✗ Terraform not found. Please install Terraform first.${NC}"
    echo -e "${YELLOW}  Install: https://www.terraform.io/downloads${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Terraform found${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found. Please install AWS CLI first.${NC}"
    echo -e "${YELLOW}  Install: https://aws.amazon.com/cli/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured.${NC}"
    echo -e "${YELLOW}  Run: aws configure${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Check Terraform variables file
if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    echo -e "${YELLOW}⚠ terraform.tfvars not found. Creating from example...${NC}"
    if [ -f "$TERRAFORM_DIR/terraform.tfvars.example" ]; then
        cp "$TERRAFORM_DIR/terraform.tfvars.example" "$TERRAFORM_DIR/terraform.tfvars"
        echo -e "${RED}✗ Please edit terraform/terraform.tfvars with your values!${NC}"
        echo -e "${YELLOW}  Required:${NC}"
        echo -e "    - ssh_allowed_cidrs (your IP address for security)"
        echo -e "    - create_key_pair (true recommended; creates key automatically)"
        echo -e "    - key_pair_name (only if create_key_pair=false)"
        echo -e "\n${YELLOW}Press Enter after editing terraform.tfvars to continue...${NC}"
        read -r
    else
        echo -e "${RED}✗ Error: terraform.tfvars.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Terraform variables file found${NC}"
fi

# Check .env.production
if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    echo -e "${YELLOW}⚠ .env.production not found. Creating from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.production.example" ]; then
        cp "$PROJECT_ROOT/.env.production.example" "$PROJECT_ROOT/.env.production"
        echo -e "${YELLOW}⚠ Please edit .env.production with your values.${NC}"
        echo -e "${YELLOW}  We'll update NEXT_PUBLIC_API_URL after infrastructure is created.${NC}"
    fi
fi

# Step 1: Provision Infrastructure
if [ "$SKIP_INFRA" = false ]; then
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}[1/2] Provisioning AWS Infrastructure${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}\n"
    
    cd "$TERRAFORM_DIR"
    
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init
    
    echo -e "${YELLOW}Planning infrastructure changes...${NC}"
    terraform plan -out=tfplan
    
    echo -e "${YELLOW}Applying infrastructure...${NC}"
    terraform apply tfplan
    
    # Get outputs
    INSTANCE_IP=$(terraform output -raw elastic_ip)
    INSTANCE_USER=$(grep -E "^instance_user" terraform.tfvars 2>/dev/null | cut -d'"' -f2 || echo "ubuntu")
    
    # Check if key pair was created or using existing
    CREATE_KEY_PAIR=$(grep -E "^create_key_pair" terraform.tfvars 2>/dev/null | grep -oE "(true|false)" | head -1 || echo "true")
    
    if [ "$CREATE_KEY_PAIR" = "true" ]; then
        SSH_KEY_PATH=$(terraform output -raw private_key_path 2>/dev/null || echo "./${PROJECT_NAME}-key.pem")
        # Expand tilde if present
        if [[ "$SSH_KEY_PATH" == ~* ]]; then
            SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"
        fi
        # Make absolute path
        if [[ "$SSH_KEY_PATH" != /* ]]; then
            SSH_KEY_PATH="$TERRAFORM_DIR/$SSH_KEY_PATH"
        fi
    else
        SSH_KEY_PATH=$(grep -E "^ssh_key_path" terraform.tfvars 2>/dev/null | cut -d'"' -f2 || echo "~/.ssh/id_rsa")
        if [[ "$SSH_KEY_PATH" == ~* ]]; then
            SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"
        fi
    fi
    
    echo -e "\n${GREEN}✓ Infrastructure provisioned successfully!${NC}"
    echo -e "${GREEN}  Instance IP: ${INSTANCE_IP}${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Update .env.production with Elastic IP
    if [ -f "$PROJECT_ROOT/.env.production" ]; then
        echo -e "${YELLOW}Updating .env.production with Elastic IP...${NC}"
        sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${INSTANCE_IP}|g" "$PROJECT_ROOT/.env.production"
        sed -i.bak "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=http://${INSTANCE_IP}/api|g" "$PROJECT_ROOT/.env.production" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.env.production.bak"
        echo -e "${GREEN}✓ Environment file updated${NC}"
    fi
    
    # Wait for instance to be ready
    echo -e "${YELLOW}Waiting for instance to be ready (30 seconds)...${NC}"
    sleep 30
    
else
    echo -e "\n${YELLOW}[1/2] Skipping infrastructure provisioning${NC}"
    
    # Try to get IP from existing Terraform state
    if [ -f "$TERRAFORM_DIR/terraform.tfstate" ] || [ -f "$TERRAFORM_DIR/.terraform/terraform.tfstate" ]; then
        INSTANCE_IP=$(cd "$TERRAFORM_DIR" && terraform output -raw elastic_ip 2>/dev/null || echo "")
        INSTANCE_USER=$(cd "$TERRAFORM_DIR" && grep -E "^instance_user" terraform.tfvars 2>/dev/null | cut -d'"' -f2 || echo "ubuntu")
        
        CREATE_KEY_PAIR=$(cd "$TERRAFORM_DIR" && grep -E "^create_key_pair" terraform.tfvars 2>/dev/null | grep -oE "(true|false)" | head -1 || echo "true")
        
        if [ "$CREATE_KEY_PAIR" = "true" ]; then
            SSH_KEY_PATH=$(cd "$TERRAFORM_DIR" && terraform output -raw private_key_path 2>/dev/null || echo "./${PROJECT_NAME}-key.pem")
            if [[ "$SSH_KEY_PATH" != /* ]]; then
                SSH_KEY_PATH="$TERRAFORM_DIR/$SSH_KEY_PATH"
            fi
        else
            SSH_KEY_PATH=$(cd "$TERRAFORM_DIR" && grep -E "^ssh_key_path" terraform.tfvars 2>/dev/null | cut -d'"' -f2 || echo "~/.ssh/id_rsa")
            if [[ "$SSH_KEY_PATH" == ~* ]]; then
                SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"
            fi
        fi
        
        if [ -z "$INSTANCE_IP" ]; then
            echo -e "${RED}✗ Could not determine instance IP. Please run without --skip-infra${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Using existing infrastructure: ${INSTANCE_IP}${NC}"
    else
        echo -e "${RED}✗ No Terraform state found. Cannot skip infrastructure.${NC}"
        exit 1
    fi
fi

# Step 2: Deploy Application
if [ "$SKIP_APP" = false ]; then
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}[2/2] Deploying Application${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}\n"
    
    # Get instance ID
    INSTANCE_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw instance_id 2>/dev/null || echo "")
    
    if [ -z "$INSTANCE_ID" ]; then
        echo -e "${RED}✗ Could not determine instance ID${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Deploying to instance: ${INSTANCE_ID}${NC}\n"
    
    # Prepare deployment package
    echo -e "${YELLOW}Preparing deployment package...${NC}"
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    # Copy files (excluding unnecessary ones)
    rsync -av --progress \
        --exclude '.git' \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.env' \
        --exclude '.env.docker' \
        --exclude '*.log' \
        --exclude '.next' \
        --exclude 'out' \
        --exclude '.DS_Store' \
        --exclude 'terraform' \
        "$PROJECT_ROOT/" "$TEMP_DIR/" > /dev/null 2>&1 || true
    
    # Copy production env file
    cp "$PROJECT_ROOT/.env.production" "$TEMP_DIR/.env" 2>/dev/null || true
    
    # Create tar archive for transfer
    TAR_FILE="$TEMP_DIR/app.tar.gz"
    cd "$TEMP_DIR"
    tar -czf "$TAR_FILE" . > /dev/null 2>&1
    
    # Base64 encode the tar file
    echo -e "${YELLOW}Uploading application files via SSM...${NC}"
    TAR_B64=$(base64 -w 0 "$TAR_FILE" 2>/dev/null || base64 "$TAR_FILE" | tr -d '\n')
    
    # Upload and extract via SSM
    aws ssm send-command \
        --instance-ids "$INSTANCE_ID" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[
            'mkdir -p /home/ubuntu/poc/smart-email-advisor',
            'cd /home/ubuntu/poc/smart-email-advisor',
            'echo \"${TAR_B64}\" | base64 -d | tar -xzf -',
            'chown -R ubuntu:ubuntu /home/ubuntu/poc/smart-email-advisor'
        ]" \
        --output text \
        --query "Command.CommandId" > /tmp/ssm-command-id.txt
    
    COMMAND_ID=$(cat /tmp/ssm-command-id.txt)
    echo -e "${YELLOW}Waiting for file upload to complete...${NC}"
    
    # Wait for command to complete
    for i in {1..30}; do
        STATUS=$(aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --query "Status" \
            --output text 2>/dev/null || echo "InProgress")
        
        if [ "$STATUS" = "Success" ]; then
            echo -e "${GREEN}✓ Files uploaded successfully${NC}"
            break
        elif [ "$STATUS" = "Failed" ]; then
            echo -e "${RED}✗ File upload failed${NC}"
            aws ssm get-command-invocation \
                --command-id "$COMMAND_ID" \
                --instance-id "$INSTANCE_ID" \
                --query "StandardErrorContent" \
                --output text
            exit 1
        fi
        sleep 2
    done
    
    # Build and start containers via SSM
    echo -e "${YELLOW}Building and starting containers (this may take several minutes)...${NC}"
    aws ssm send-command \
        --instance-ids "$INSTANCE_ID" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[
            'cd /home/ubuntu/poc/smart-email-advisor',
            'sudo docker compose -f docker-compose.prod.yml down || true',
            'sudo docker compose -f docker-compose.prod.yml build --no-cache',
            'sudo docker compose -f docker-compose.prod.yml up -d',
            'sleep 15',
            'sudo docker compose -f docker-compose.prod.yml ps'
        ]" \
        --output text \
        --query "Command.CommandId" > /tmp/ssm-deploy-command-id.txt
    
    DEPLOY_COMMAND_ID=$(cat /tmp/ssm-deploy-command-id.txt)
    
    # Wait for deployment to complete
    echo -e "${YELLOW}Waiting for containers to start...${NC}"
    for i in {1..120}; do
        STATUS=$(aws ssm get-command-invocation \
            --command-id "$DEPLOY_COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --query "Status" \
            --output text 2>/dev/null || echo "InProgress")
        
        if [ "$STATUS" = "Success" ]; then
            echo -e "${GREEN}✓ Application deployed successfully${NC}"
            # Show output
            aws ssm get-command-invocation \
                --command-id "$DEPLOY_COMMAND_ID" \
                --instance-id "$INSTANCE_ID" \
                --query "StandardOutputContent" \
                --output text | tail -20
            break
        elif [ "$STATUS" = "Failed" ]; then
            echo -e "${RED}✗ Deployment failed${NC}"
            aws ssm get-command-invocation \
                --command-id "$DEPLOY_COMMAND_ID" \
                --instance-id "$INSTANCE_ID" \
                --query "StandardErrorContent" \
                --output text
            exit 1
        fi
        sleep 5
    done
    
    if [ "$STATUS" != "Success" ]; then
        echo -e "${YELLOW}⚠ Deployment still in progress. Check status manually.${NC}"
    fi
    
else
    echo -e "\n${YELLOW}[2/2] Skipping application deployment${NC}"
fi

# Final Summary
echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ Deployment Complete!${NC}                                        ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

if [ "$SKIP_INFRA" = false ]; then
    INSTANCE_IP=$(cd "$TERRAFORM_DIR" && terraform output -raw elastic_ip)
fi

echo -e "${GREEN}Application URL:${NC}"
echo -e "  ${YELLOW}http://${INSTANCE_IP}${NC}\n"

echo -e "${GREEN}Infrastructure Management:${NC}"
echo -e "  ${YELLOW}View outputs:${NC}     cd terraform && terraform output"
echo -e "  ${YELLOW}Destroy infra:${NC}    cd terraform && terraform destroy"
echo -e "  ${YELLOW}Show state:${NC}       cd terraform && terraform show\n"

echo -e "${GREEN}Application Management:${NC}"
INSTANCE_ID_OUTPUT=$(cd terraform && terraform output -raw instance_id 2>/dev/null || echo "INSTANCE_ID")
echo -e "  ${YELLOW}SSM Session:${NC}       aws ssm start-session --target ${INSTANCE_ID_OUTPUT}"
echo -e "  ${YELLOW}View logs:${NC}        aws ssm start-session --target ${INSTANCE_ID_OUTPUT} --document-name AWS-StartInteractiveCommand --parameters command=\"cd /home/ubuntu/poc/smart-email-advisor && docker compose -f docker-compose.prod.yml logs -f\""
echo -e "  ${YELLOW}Check status:${NC}     aws ssm start-session --target ${INSTANCE_ID_OUTPUT} --document-name AWS-StartInteractiveCommand --parameters command=\"cd /home/ubuntu/poc/smart-email-advisor && docker compose -f docker-compose.prod.yml ps\"\n"

echo -e "${BLUE}Note:${NC} It may take 1-2 minutes for all services to be fully ready.\n"
