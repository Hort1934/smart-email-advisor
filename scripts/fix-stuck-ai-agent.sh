#!/bin/bash

# Fix AI Agent container stuck in recreating state

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "Fixing Stuck AI Agent Container"
echo "=========================================="
echo ""

# 1. Stop the stuck container
echo "1. Stopping stuck AI Agent container..."
sudo docker compose -f docker-compose.prod.yml stop ai-agent 2>/dev/null || true
sudo docker compose -f docker-compose.prod.yml rm -f ai-agent 2>/dev/null || true

# Force remove if still running
echo "2. Force removing AI Agent container..."
sudo docker rm -f smart-email-advisor-ai-agent 2>/dev/null || true

echo ""
echo "3. Checking AI Agent logs (last 50 lines)..."
echo "----------------------------------------"
sudo docker compose -f docker-compose.prod.yml logs --tail=50 ai-agent 2>&1 | tail -50
echo ""

# 4. Check for common issues
echo "4. Checking for common issues..."
echo "----------------------------------------"

# Check if dependencies are running
echo "Checking dependencies..."
DB_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps db | grep -i "healthy\|running" || echo "NOT_RUNNING")
REDIS_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps redis | grep -i "healthy\|running" || echo "NOT_RUNNING")

if [ "$DB_STATUS" = "NOT_RUNNING" ]; then
    echo "⚠️  Database is not running - starting it..."
    sudo docker compose -f docker-compose.prod.yml up -d db
    sleep 10
fi

if [ "$REDIS_STATUS" = "NOT_RUNNING" ]; then
    echo "⚠️  Redis is not running - starting it..."
    sudo docker compose -f docker-compose.prod.yml up -d redis
    sleep 5
fi

echo ""

# 5. Check healthcheck command
echo "5. Testing healthcheck command..."
echo "----------------------------------------"
# The healthcheck uses wget, let's verify it works
HEALTHCHECK_TEST=$(sudo docker run --rm --network smart-email-advisor_smart-email-network nginx:alpine wget --quiet --tries=1 --spider http://ai-agent:8001/health 2>&1 || echo "FAILED")
if echo "$HEALTHCHECK_TEST" | grep -q "200 OK\|connected"; then
    echo "✅ Healthcheck endpoint is accessible"
else
    echo "⚠️  Healthcheck test failed (this is expected if container is not running)"
fi
echo ""

# 6. Try starting with relaxed healthcheck temporarily
echo "6. Starting AI Agent with relaxed healthcheck..."
echo "----------------------------------------"

# Create a temporary override file
cat > /tmp/docker-compose.ai-agent-override.yml << 'EOF'
services:
  ai-agent:
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8001/health"]
      interval: 60s
      timeout: 30s
      retries: 5
      start_period: 120s
EOF

# Start with override
sudo docker compose -f docker-compose.prod.yml -f /tmp/docker-compose.ai-agent-override.yml up -d ai-agent

echo ""
echo "Waiting 30 seconds for container to start..."
sleep 30

# 7. Check status
echo ""
echo "7. Checking AI Agent status..."
echo "----------------------------------------"
AI_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps ai-agent | grep -A 1 "ai-agent" || echo "NOT_FOUND")
echo "$AI_STATUS"
echo ""

# 8. Check logs again
echo "8. Recent AI Agent logs..."
echo "----------------------------------------"
sudo docker compose -f docker-compose.prod.yml logs --tail=30 ai-agent 2>&1 | tail -30
echo ""

# 9. If still failing, check for specific errors
echo "9. Checking for specific errors..."
echo "----------------------------------------"
ERRORS=$(sudo docker compose -f docker-compose.prod.yml logs ai-agent 2>&1 | grep -i "error\|exception\|traceback\|failed\|cannot" | tail -10 || echo "No errors found")
if [ "$ERRORS" != "No errors found" ]; then
    echo "⚠️  Found errors:"
    echo "$ERRORS"
else
    echo "✅ No obvious errors in logs"
fi
echo ""

# 10. Recommendations
echo "=========================================="
echo "Summary & Recommendations"
echo "=========================================="
echo ""

AI_CURRENT_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps ai-agent | grep -i "up\|exited\|restarting" || echo "UNKNOWN")

if echo "$AI_CURRENT_STATUS" | grep -q "Up.*healthy"; then
    echo "✅ AI Agent is now running and healthy!"
elif echo "$AI_CURRENT_STATUS" | grep -q "Up"; then
    echo "⚠️  AI Agent is running but not yet healthy"
    echo "   Wait a bit longer for healthcheck to pass"
    echo "   Check: sudo docker compose -f docker-compose.prod.yml ps ai-agent"
elif echo "$AI_CURRENT_STATUS" | grep -q "Exited\|Restarting"; then
    echo "❌ AI Agent is still having issues"
    echo ""
    echo "Try these steps:"
    echo "1. Check full logs: sudo docker compose -f docker-compose.prod.yml logs ai-agent"
    echo "2. Check environment variables: sudo docker compose -f docker-compose.prod.yml config | grep -A 20 ai-agent"
    echo "3. Try rebuilding: sudo docker compose -f docker-compose.prod.yml build --no-cache ai-agent"
    echo "4. Start without healthcheck: sudo docker compose -f docker-compose.prod.yml up -d --no-healthcheck ai-agent"
else
    echo "⚠️  Could not determine AI Agent status"
    echo "   Check manually: sudo docker compose -f docker-compose.prod.yml ps ai-agent"
fi

echo ""
echo "Clean up temporary override file:"
echo "  rm /tmp/docker-compose.ai-agent-override.yml"
echo ""
