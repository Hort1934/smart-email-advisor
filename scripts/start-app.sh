#!/bin/bash

# =============================================================================
# Start Application on EC2 Instance
# =============================================================================
# Run this script directly on the EC2 instance to start all containers
# Usage: ./start-app.sh

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"

echo "=========================================="
echo "Starting Smart Email Advisor Application"
echo "=========================================="
echo ""

# Check if directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory not found at $APP_DIR"
    echo "Please deploy application files first."
    exit 1
fi

cd "$APP_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using defaults."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "Stopping existing containers (if any)..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || sudo docker compose -f docker-compose.prod.yml down || true

echo ""
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache 2>/dev/null || sudo docker compose -f docker-compose.prod.yml build --no-cache

echo ""
echo "Starting all containers..."
docker compose -f docker-compose.prod.yml up -d 2>/dev/null || sudo docker compose -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for services to start (15 seconds)..."
sleep 15

echo ""
echo "Container status:"
docker compose -f docker-compose.prod.yml ps 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "Application started!"
echo "=========================================="
echo ""
echo "To view logs:"
echo "  cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To check status:"
echo "  cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml ps"
echo ""
echo "To stop:"
echo "  cd $APP_DIR && sudo docker compose -f docker-compose.prod.yml down"
echo ""
