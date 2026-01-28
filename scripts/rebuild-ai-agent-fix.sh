#!/bin/bash

# Rebuild AI Agent with database connection fix

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "Rebuilding AI Agent with Database Fix"
echo "=========================================="
echo ""

# Stop and remove old container
echo "1. Stopping AI Agent..."
sudo docker compose -f docker-compose.prod.yml stop ai-agent
sudo docker compose -f docker-compose.prod.yml rm -f ai-agent

echo ""
echo "2. Rebuilding AI Agent container..."
echo "   (This will take a few minutes)"
sudo docker compose -f docker-compose.prod.yml build --no-cache ai-agent

echo ""
echo "3. Starting AI Agent..."
sudo docker compose -f docker-compose.prod.yml up -d ai-agent

echo ""
echo "4. Waiting for AI Agent to start..."
sleep 20

echo ""
echo "5. Checking AI Agent status..."
sudo docker compose -f docker-compose.prod.yml ps ai-agent

echo ""
echo "6. Checking AI Agent logs for database connection..."
sudo docker compose -f docker-compose.prod.yml logs --tail=20 ai-agent | grep -i "database\|error" || echo "No database errors found"

echo ""
echo "7. Testing AI Agent health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8001/health 2>&1 || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo "✅ AI Agent health check passed: $HEALTH_RESPONSE"
else
    echo "⚠️  Health check response: $HEALTH_RESPONSE"
fi

echo ""
echo "=========================================="
echo "Rebuild Complete!"
echo "=========================================="
echo ""
echo "The database connection error should be fixed."
echo "Check logs: sudo docker compose -f docker-compose.prod.yml logs ai-agent"
echo ""
