#!/bin/bash

# =============================================================================
# AWS EC2 Deployment Script for Smart Email Advisor
# =============================================================================
# This script sets up and deploys the application on an AWS EC2 instance
# Prerequisites: EC2 instance with Ubuntu 22.04 LTS, Elastic IP assigned

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/smart-email-advisor"
SERVICE_USER="smartemail"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Smart Email Advisor - AWS EC2 Deployment${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Update system
echo -e "${YELLOW}[1/8] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Step 2: Install Docker
echo -e "${YELLOW}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Set up Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
else
    echo -e "${GREEN}Docker is already installed${NC}"
fi

# Step 3: Install Docker Compose (standalone if not using plugin)
echo -e "${YELLOW}[3/8] Installing Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    # Install Docker Compose standalone
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose is already installed${NC}"
fi

# Step 4: Create application user
echo -e "${YELLOW}[4/8] Creating application user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$APP_DIR" -m "$SERVICE_USER"
    usermod -aG docker "$SERVICE_USER"
else
    echo -e "${GREEN}User $SERVICE_USER already exists${NC}"
fi

# Step 5: Create application directory
echo -e "${YELLOW}[5/8] Setting up application directory...${NC}"
mkdir -p "$APP_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

# Step 6: Configure firewall
echo -e "${YELLOW}[6/8] Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # HTTP
    ufw allow 443/tcp  # HTTPS
    echo -e "${GREEN}Firewall configured${NC}"
else
    echo -e "${YELLOW}UFW not found, skipping firewall configuration${NC}"
fi

# Step 7: Install additional tools
echo -e "${YELLOW}[7/8] Installing additional tools...${NC}"
apt-get install -y git curl wget htop

# Step 8: Display next steps
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "Next steps:"
echo -e "1. Copy your application files to: ${APP_DIR}"
echo -e "2. Create .env file in ${APP_DIR} (use .env.production.example as template)"
echo -e "3. Run deployment:"
echo -e "   ${YELLOW}cd ${APP_DIR}${NC}"
echo -e "   ${YELLOW}docker compose -f docker-compose.prod.yml up -d${NC}"
echo -e "\nTo check status:"
echo -e "   ${YELLOW}docker compose -f docker-compose.prod.yml ps${NC}"
echo -e "\nTo view logs:"
echo -e "   ${YELLOW}docker compose -f docker-compose.prod.yml logs -f${NC}"
