#!/bin/bash

# =============================================================================
# Deploy Application Files to EC2 via SSM
# =============================================================================
# This script only deploys application files (doesn't provision infrastructure)
# Usage: ./deploy-app-only.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
APP_DIR="/home/ubuntu/poc/smart-email-advisor"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}Deploy Application Files to EC2${NC}                              ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

# Get instance ID
if [ ! -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
    echo -e "${RED}✗ Terraform state not found. Please run terraform apply first.${NC}"
    exit 1
fi

INSTANCE_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw instance_id 2>/dev/null || echo "")

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}✗ Could not determine instance ID${NC}"
    exit 1
fi

echo -e "${GREEN}Instance ID: ${INSTANCE_ID}${NC}\n"

# Check .env.production exists
if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    echo -e "${YELLOW}⚠ .env.production not found. Creating from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.production.example" ]; then
        cp "$PROJECT_ROOT/.env.production.example" "$PROJECT_ROOT/.env.production"
        echo -e "${YELLOW}⚠ Please edit .env.production with your values!${NC}"
    fi
fi

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

# Create tar archive
TAR_FILE="$TEMP_DIR/app.tar.gz"
cd "$TEMP_DIR"
tar -czf "$TAR_FILE" . > /dev/null 2>&1

# Base64 encode
echo -e "${YELLOW}Uploading application files via SSM...${NC}"
TAR_B64=$(base64 -w 0 "$TAR_FILE" 2>/dev/null || base64 "$TAR_FILE" | tr -d '\n')

# Upload and extract via SSM
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[
        'mkdir -p $APP_DIR',
        'cd $APP_DIR',
        'echo \"${TAR_B64}\" | base64 -d | tar -xzf -',
        'chown -R ubuntu:ubuntu $APP_DIR',
        'ls -la $APP_DIR | head -20'
    ]" \
    --output text \
    --query "Command.CommandId" > /tmp/ssm-upload-command-id.txt

COMMAND_ID=$(cat /tmp/ssm-upload-command-id.txt)
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

echo -e "\n${GREEN}✓ Application files deployed to $APP_DIR${NC}"
echo -e "\n${YELLOW}Next step: Start the application${NC}"
echo -e "  ${BLUE}cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml up -d --build${NC}\n"
