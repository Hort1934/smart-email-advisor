#!/bin/bash

# =============================================================================
# Deploy Application to AWS EC2 Instance
# =============================================================================
# This script copies the application to EC2 and starts the containers
# Usage: ./deploy-to-ec2.sh <ec2-user>@<ec2-ip-or-hostname>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <ec2-user>@<ec2-ip-or-hostname>${NC}"
    echo -e "Example: $0 ubuntu@ec2-54-123-45-67.compute-1.amazonaws.com"
    exit 1
fi

EC2_HOST="$1"
APP_DIR="/home/ubuntu/poc/smart-email-advisor"
REMOTE_USER=$(echo "$EC2_HOST" | cut -d'@' -f1)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Smart Email Advisor to EC2${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env.production exists
if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    echo -e "${YELLOW}Warning: .env.production not found. Creating from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.production.example" ]; then
        cp "$PROJECT_ROOT/.env.production.example" "$PROJECT_ROOT/.env.production"
        echo -e "${YELLOW}Please edit .env.production with your actual values before continuing.${NC}"
        read -p "Press Enter to continue after editing .env.production..."
    else
        echo -e "${RED}Error: .env.production.example not found${NC}"
        exit 1
    fi
fi

# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Preparing deployment package...${NC}"

# Copy necessary files
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
    "$PROJECT_ROOT/" "$TEMP_DIR/"

# Copy production env file
cp "$PROJECT_ROOT/.env.production" "$TEMP_DIR/.env"

echo -e "${YELLOW}Copying files to EC2 instance...${NC}"
ssh "$EC2_HOST" "mkdir -p $APP_DIR && chown $REMOTE_USER:$REMOTE_USER $APP_DIR"

rsync -av --progress \
    "$TEMP_DIR/" "$EC2_HOST:$APP_DIR/"

# Cleanup temp directory
rm -rf "$TEMP_DIR"

echo -e "${YELLOW}Starting application on EC2...${NC}"
ssh "$EC2_HOST" << 'ENDSSH'
    cd /home/ubuntu/poc/smart-email-advisor
    docker compose -f docker-compose.prod.yml down || true
    docker compose -f docker-compose.prod.yml build --no-cache
    docker compose -f docker-compose.prod.yml up -d
    echo "Waiting for services to start..."
    sleep 10
    docker compose -f docker-compose.prod.yml ps
ENDSSH

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "Application should be available at:"
echo -e "  ${YELLOW}http://$(echo $EC2_HOST | cut -d'@' -f2)${NC}\n"
echo -e "To check logs:"
echo -e "  ${YELLOW}ssh $EC2_HOST 'cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml logs -f'${NC}\n"
