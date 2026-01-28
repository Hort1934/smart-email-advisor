#!/bin/bash

# Fix NEXT_PUBLIC_API_URL to use base URL without /api
# This script updates .env.production and rebuilds frontend

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

# Get Elastic IP
ELASTIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "=========================================="
echo "Fixing NEXT_PUBLIC_API_URL"
echo "=========================================="
echo ""

# Update .env.production - remove /api from NEXT_PUBLIC_API_URL
if [ -f .env.production ]; then
    echo "Current NEXT_PUBLIC_API_URL:"
    grep NEXT_PUBLIC_API_URL .env.production || echo "Not found"
    echo ""
    
    # Update to base URL (without /api)
    # Remove trailing /api if present
    sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${ELASTIC_IP}|g" .env.production
    
    echo "Updated NEXT_PUBLIC_API_URL to: http://${ELASTIC_IP}"
    echo ""
    echo "New value:"
    grep NEXT_PUBLIC_API_URL .env.production
    echo ""
    
    # Rebuild and restart frontend
    echo "Rebuilding frontend with new API URL..."
    echo "This may take a few minutes..."
    sudo docker compose -f docker-compose.prod.yml build --no-cache frontend
    
    echo ""
    echo "Restarting frontend..."
    sudo docker compose -f docker-compose.prod.yml up -d frontend
    
    echo ""
    echo "Waiting for frontend to start..."
    sleep 15
    
    echo ""
    echo "Restarting nginx..."
    sudo docker compose -f docker-compose.prod.yml restart nginx
    
    echo ""
    echo "Checking container status..."
    sudo docker compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "=========================================="
    echo "Fix Complete!"
    echo "=========================================="
    echo ""
    echo "Frontend should now use: http://${ELASTIC_IP}"
    echo ""
    echo "API endpoints:"
    echo "  - http://${ELASTIC_IP}/health"
    echo "  - http://${ELASTIC_IP}/api/emails/folders"
    echo "  - http://${ELASTIC_IP}/api/stats/stats"
    echo ""
    echo "Test from EC2:"
    echo "  curl http://localhost/health"
    echo "  curl http://localhost/api/stats/stats"
else
    echo "Error: .env.production not found!"
    exit 1
fi
