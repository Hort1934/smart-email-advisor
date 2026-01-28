#!/bin/bash

# Force rebuild frontend with explicit API URL
# This script ensures the build arg is passed correctly

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

ELASTIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "=========================================="
echo "Force Rebuild Frontend Container"
echo "=========================================="
echo ""

# Get API URL from .env.production or use Elastic IP
if [ -f .env.production ]; then
    API_URL=$(grep "^NEXT_PUBLIC_API_URL=" .env.production | cut -d= -f2 | tr -d '"' | tr -d "'")
    if [ -z "$API_URL" ] || echo "$API_URL" | grep -q "/api"; then
        echo "⚠️  Fixing API URL in .env.production..."
        API_URL="http://${ELASTIC_IP}"
        sed -i.bak "s|^NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=${API_URL}|g" .env.production
    fi
else
    API_URL="http://${ELASTIC_IP}"
    echo "⚠️  .env.production not found, using Elastic IP: $API_URL"
fi

echo "Using API URL: $API_URL"
echo ""

# Stop and remove old frontend container
echo "Stopping old frontend container..."
sudo docker compose -f docker-compose.prod.yml stop frontend 2>/dev/null || true
sudo docker compose -f docker-compose.prod.yml rm -f frontend 2>/dev/null || true

# Remove old frontend image to force rebuild
echo "Removing old frontend image..."
sudo docker rmi smart-email-advisor-frontend 2>/dev/null || true

# Build with explicit build arg
echo "Building frontend with API URL: $API_URL"
echo "This will take a few minutes..."
echo ""

# Use docker build directly to ensure build arg is passed
cd frontend
sudo docker build \
    --no-cache \
    --pull \
    --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
    -t smart-email-advisor-frontend \
    -f Dockerfile \
    .
cd ..

echo ""
echo "Starting frontend container..."
sudo docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "Waiting for frontend to start..."
sleep 15

echo ""
echo "Restarting nginx..."
sudo docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo "Checking container status..."
sudo docker compose -f docker-compose.prod.yml ps frontend

echo ""
echo "Verifying build..."
# Check if the built files contain the API URL
echo "Checking built static files..."
BUILT_HTML=$(sudo docker exec smart-email-advisor-frontend cat /usr/share/nginx/html/index.html 2>/dev/null | head -20 || echo "")
if echo "$BUILT_HTML" | grep -q "$ELASTIC_IP"; then
    echo "✅ Built files contain Elastic IP"
else
    echo "⚠️  Could not verify built files"
fi

echo ""
echo "Checking environment variable..."
FRONTEND_ENV=$(sudo docker exec smart-email-advisor-frontend env | grep NEXT_PUBLIC_API_URL 2>&1 || echo "NOT_FOUND")
echo "Frontend NEXT_PUBLIC_API_URL: $FRONTEND_ENV"

# Note: For Next.js static export, the env var is baked into the build
# The runtime env var won't matter, but we check it anyway
if echo "$FRONTEND_ENV" | grep -q "/api"; then
    echo "⚠️  Runtime env var still has '/api', but build-time value should be correct"
    echo "   (Next.js static exports use build-time values, not runtime env vars)"
else
    echo "✅ Runtime env var looks correct"
fi

echo ""
echo "=========================================="
echo "Rebuild Complete!"
echo "=========================================="
echo ""
echo "Frontend built with API URL: $API_URL"
echo ""
echo "Test URLs:"
echo "  - Frontend: http://${ELASTIC_IP}"
echo "  - Health: http://${ELASTIC_IP}/health"
echo "  - Stats: http://${ELASTIC_IP}/api/stats/stats"
echo ""
echo "⚠️  IMPORTANT: Next.js static exports bake NEXT_PUBLIC_API_URL into the build."
echo "   If the frontend still shows the wrong URL, clear your browser cache"
echo "   and check the browser's Network tab to see what URL is being called."
