#!/bin/bash

# =============================================================================
# One-Command AWS EC2 Deployment for Smart Email Advisor
# =============================================================================
# This script does everything: setup EC2, deploy application, verify deployment
# Usage: ./deploy.sh <ec2-user>@<ec2-ip-or-hostname> [--skip-setup]
#
# Options:
#   --skip-setup    Skip EC2 setup (Docker installation, etc.)
#                   Use this if EC2 is already configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
SKIP_SETUP=false
if [[ "$*" == *"--skip-setup"* ]]; then
    SKIP_SETUP=true
fi

if [ -z "$1" ] || [[ "$1" == --* ]]; then
    echo -e "${RED}Usage: $0 <ec2-user>@<ec2-ip-or-hostname> [--skip-setup]${NC}"
    echo -e "Example: $0 ubuntu@54.123.45.67"
    echo -e "Example: $0 ubuntu@54.123.45.67 --skip-setup  # Skip Docker installation"
    exit 1
fi

EC2_HOST="$1"
APP_DIR="/home/ubuntu/poc/smart-email-advisor"
REMOTE_USER=$(echo "$EC2_HOST" | cut -d'@' -f1)
EC2_IP=$(echo "$EC2_HOST" | cut -d'@' -f2)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}Smart Email Advisor - One-Command AWS EC2 Deployment${NC}  ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

# Check if .env.production exists
if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    echo -e "${YELLOW}⚠ .env.production not found. Creating from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.production.example" ]; then
        cp "$PROJECT_ROOT/.env.production.example" "$PROJECT_ROOT/.env.production"
        echo -e "${RED}✗ Please edit .env.production with your actual values!${NC}"
        echo -e "${YELLOW}  Key values to set:${NC}"
        echo -e "    - POSTGRES_PASSWORD"
        echo -e "    - SECRET_KEY (generate: openssl rand -hex 32)"
        echo -e "    - WEBHOOK_SECRET"
        echo -e "    - NEXT_PUBLIC_API_URL (http://$EC2_IP/api)"
        echo -e "    - OPENAI_API_KEY"
        echo -e "\n${YELLOW}Press Enter after editing .env.production to continue...${NC}"
        read -r
    else
        echo -e "${RED}✗ Error: .env.production.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env.production found${NC}"
fi

# Check SSH access
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$EC2_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to $EC2_HOST via SSH${NC}"
    echo -e "${YELLOW}Please ensure:${NC}"
    echo -e "  1. EC2 instance is running"
    echo -e "  2. Security group allows SSH (port 22) from your IP"
    echo -e "  3. SSH key is correct and has proper permissions"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"

# Step 2: Setup EC2 instance (if not skipped)
if [ "$SKIP_SETUP" = false ]; then
    echo -e "\n${YELLOW}[2/5] Setting up EC2 instance (installing Docker, etc.)...${NC}"
    
    # Copy setup script to EC2
    echo -e "${YELLOW}Copying setup script...${NC}"
    scp "$PROJECT_ROOT/scripts/aws-ec2-deploy.sh" "$EC2_HOST:/tmp/setup.sh" 2>/dev/null || {
        # If scp fails, try inline script
        echo -e "${YELLOW}Running inline setup...${NC}"
        ssh "$EC2_HOST" "sudo bash -s" << 'SETUP_SCRIPT'
            # Update system
            apt-get update -qq
            apt-get upgrade -y -qq
            
            # Install Docker if not present
            if ! command -v docker &> /dev/null; then
                apt-get install -y -qq ca-certificates curl gnupg lsb-release
                install -m 0755 -d /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                chmod a+r /etc/apt/keyrings/docker.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
                apt-get update -qq
                apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                systemctl start docker
                systemctl enable docker
            fi
            
            # Add user to docker group
            usermod -aG docker $USER || true
            
            # Configure firewall
            if command -v ufw &> /dev/null; then
                ufw --force enable || true
                ufw allow 22/tcp || true
                ufw allow 80/tcp || true
                ufw allow 443/tcp || true
            fi
            
            # Install tools
            apt-get install -y -qq git curl wget htop || true
            
            echo "Setup complete"
SETUP_SCRIPT
    }
    
    echo -e "${GREEN}✓ EC2 setup completed${NC}"
else
    echo -e "\n${YELLOW}[2/5] Skipping EC2 setup (--skip-setup flag used)${NC}"
fi

# Step 3: Prepare and copy application files
echo -e "\n${YELLOW}[3/5] Preparing application files...${NC}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${YELLOW}Copying files (excluding unnecessary files)...${NC}"

# Use rsync if available, otherwise use tar
if command -v rsync &> /dev/null; then
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
        --exclude '*.swp' \
        --exclude '*.swo' \
        "$PROJECT_ROOT/" "$TEMP_DIR/" > /dev/null 2>&1
else
    # Fallback to tar
    tar --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='.env.docker' \
        --exclude='*.log' \
        --exclude='.next' \
        --exclude='out' \
        --exclude='.DS_Store' \
        -czf "$TEMP_DIR/app.tar.gz" -C "$PROJECT_ROOT" . 2>/dev/null
fi

# Copy production env file
cp "$PROJECT_ROOT/.env.production" "$TEMP_DIR/.env"

echo -e "${GREEN}✓ Files prepared${NC}"

# Step 4: Deploy to EC2
echo -e "\n${YELLOW}[4/5] Deploying application to EC2...${NC}"

# Create app directory on EC2
ssh "$EC2_HOST" "mkdir -p $APP_DIR && chown $REMOTE_USER:$REMOTE_USER $APP_DIR" 2>/dev/null

# Copy files
echo -e "${YELLOW}Copying files to EC2...${NC}"
if command -v rsync &> /dev/null; then
    rsync -av --progress \
        "$TEMP_DIR/" "$EC2_HOST:$APP_DIR/" > /dev/null 2>&1
else
    # Fallback: use scp
    scp -r "$TEMP_DIR"/* "$EC2_HOST:$APP_DIR/" > /dev/null 2>&1
fi

echo -e "${GREEN}✓ Files copied${NC}"

# Build and start containers
echo -e "${YELLOW}Building and starting containers (this may take several minutes)...${NC}"
ssh "$EC2_HOST" << 'DEPLOY_SCRIPT'
    cd /home/ubuntu/poc/smart-email-advisor
    
    # Stop existing containers if running
    sudo docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build images
    echo "Building Docker images..."
    sudo docker compose -f docker-compose.prod.yml build --no-cache 2>&1 | grep -E "(Step|Building|Successfully)" || true
    
    # Start containers
    echo "Starting containers..."
    sudo docker compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    sleep 15
    
    # Show status
    echo ""
    echo "Container status:"
    sudo docker compose -f docker-compose.prod.yml ps
DEPLOY_SCRIPT

echo -e "${GREEN}✓ Application deployed${NC}"

# Step 5: Verify deployment
echo -e "\n${YELLOW}[5/5] Verifying deployment...${NC}"

# Check if containers are running
CONTAINERS_RUNNING=$(ssh "$EC2_HOST" "cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml ps --format json" 2>/dev/null | grep -c '"State":"running"' || echo "0")

if [ "$CONTAINERS_RUNNING" -ge "5" ]; then
    echo -e "${GREEN}✓ Containers are running ($CONTAINERS_RUNNING containers)${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Only $CONTAINERS_RUNNING containers running (expected 6+)${NC}"
fi

# Test health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
sleep 5
if curl -s -f -m 10 "http://$EC2_IP/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Backend health check failed (may need a few more seconds)${NC}"
fi

# Test frontend
if curl -s -f -m 10 "http://$EC2_IP" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Frontend check failed (may need a few more seconds)${NC}"
fi

# Final summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ Deployment Completed Successfully!${NC}                    ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Application URL:${NC}"
echo -e "  ${YELLOW}http://$EC2_IP${NC}\n"

echo -e "${GREEN}Useful commands:${NC}"
echo -e "  ${YELLOW}View logs:${NC}     ssh $EC2_HOST 'cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml logs -f'"
echo -e "  ${YELLOW}Check status:${NC}  ssh $EC2_HOST 'cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml ps'"
echo -e "  ${YELLOW}Restart:${NC}       ssh $EC2_HOST 'cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml restart'"
echo -e "  ${YELLOW}Stop:${NC}          ssh $EC2_HOST 'cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml down'\n"

echo -e "${BLUE}Note:${NC} If services are still starting, wait 30-60 seconds and check again.\n"
