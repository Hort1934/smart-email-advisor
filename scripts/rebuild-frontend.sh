#!/bin/bash

# Rebuild frontend with correct API URL from .env.production

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

ELASTIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "=========================================="
echo "Rebuilding Frontend Container"
echo "=========================================="
echo ""

# Verify .env.production has correct value
if [ -f .env.production ]; then
    API_URL=$(grep NEXT_PUBLIC_API_URL .env.production | cut -d= -f2)
    echo "Current NEXT_PUBLIC_API_URL in .env.production: $API_URL"
    
    if echo "$API_URL" | grep -q "/api"; then
        echo "⚠️  WARNING: NEXT_PUBLIC_API_URL still contains '/api'"
        echo "   Updating to base URL..."
        sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://${ELASTIC_IP}|g" .env.production
        API_URL="http://${ELASTIC_IP}"
        echo "   Updated to: $API_URL"
    fi
    echo ""
else
    echo "❌ Error: .env.production not found!"
    exit 1
fi

# Load environment variables from .env.production
set -a
source .env.production
set +a

# Ensure NEXT_PUBLIC_API_URL is set correctly
export NEXT_PUBLIC_API_URL="$API_URL"

echo "Rebuilding frontend container..."
echo "Using NEXT_PUBLIC_API_URL: $NEXT_PUBLIC_API_URL"
echo "This will take a few minutes..."
echo ""

# Rebuild frontend with no cache to ensure fresh build
# Pass the variable explicitly to ensure it's used
sudo -E docker compose -f docker-compose.prod.yml build --no-cache --build-arg NEXT_PUBLIC_API_URL="$API_URL" frontend

echo ""
echo "Stopping old frontend container..."
sudo docker compose -f docker-compose.prod.yml stop frontend

echo ""
echo "Starting new frontend container..."
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
echo "Verifying frontend API URL..."
FRONTEND_ENV=$(sudo docker exec smart-email-advisor-frontend env | grep NEXT_PUBLIC_API_URL 2>&1 || echo "NOT_FOUND")
if [ "$FRONTEND_ENV" != "NOT_FOUND" ]; then
    echo "Frontend NEXT_PUBLIC_API_URL: $FRONTEND_ENV"
    if echo "$FRONTEND_ENV" | grep -q "/api"; then
        echo "⚠️  WARNING: Frontend still has '/api' in URL"
        echo "   The build may have cached the old value"
        echo "   Try: sudo docker compose -f docker-compose.prod.yml build --no-cache --pull frontend"
    else
        echo "✅ Frontend API URL looks correct"
    fi
else
    echo "⚠️  NEXT_PUBLIC_API_URL not found in frontend container"
fi

echo ""
echo "=========================================="
echo "Rebuild Complete!"
echo "=========================================="
echo ""
echo "Frontend should now use: $API_URL"
echo ""
echo "Test URLs:"
echo "  - Frontend: http://${ELASTIC_IP}"
echo "  - Health: http://${ELASTIC_IP}/health"
echo "  - Stats: http://${ELASTIC_IP}/api/stats/stats"
echo ""
echo "Refresh your browser to see the updated status!"
