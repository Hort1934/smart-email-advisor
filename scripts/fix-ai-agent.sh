#!/bin/bash

# Fix AI Agent issues

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "Fixing AI Agent Issues"
echo "=========================================="
echo ""

# 1. Check AI Agent container status
echo "1. Checking AI Agent status..."
AI_AGENT_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps ai-agent | grep -i "unhealthy\|exited\|restarting" || echo "OK")
if [ "$AI_AGENT_STATUS" != "OK" ]; then
    echo "⚠️  AI Agent is not healthy: $AI_AGENT_STATUS"
    echo ""
    
    # Check logs
    echo "2. Checking AI Agent logs..."
    sudo docker compose -f docker-compose.prod.yml logs --tail=30 ai-agent
    echo ""
    
    # Restart AI Agent
    echo "3. Restarting AI Agent..."
    sudo docker compose -f docker-compose.prod.yml restart ai-agent
    sleep 10
    
    # Check status again
    echo "4. Checking status after restart..."
    sudo docker compose -f docker-compose.prod.yml ps ai-agent
    echo ""
else
    echo "✅ AI Agent container appears healthy"
    echo ""
fi

# 5. Test AI Agent health endpoint
echo "5. Testing AI Agent health endpoint..."
AI_HEALTH=$(curl -s http://localhost:8001/health 2>&1 || echo "FAILED")
if echo "$AI_HEALTH" | grep -q "ok\|healthy"; then
    echo "✅ AI Agent health endpoint is working: $AI_HEALTH"
else
    echo "⚠️  AI Agent health endpoint test failed: $AI_HEALTH"
    echo "   This might be normal if the endpoint doesn't exist"
fi
echo ""

# 6. Test from backend container
echo "6. Testing backend -> AI Agent connectivity..."
BACKEND_TEST=$(sudo docker exec smart-email-advisor-backend curl -s http://ai-agent:8001/health 2>&1 || echo "FAILED")
if echo "$BACKEND_TEST" | grep -q "ok\|healthy"; then
    echo "✅ Backend can reach AI Agent: $BACKEND_TEST"
else
    echo "⚠️  Backend cannot reach AI Agent: $BACKEND_TEST"
    echo "   Checking if AI Agent is running on port 8001..."
    AI_PORT=$(sudo docker exec smart-email-advisor-ai-agent netstat -tlnp 2>/dev/null | grep 8001 || echo "NOT_FOUND")
    if [ "$AI_PORT" != "NOT_FOUND" ]; then
        echo "   ✅ AI Agent is listening on port 8001"
    else
        echo "   ❌ AI Agent is not listening on port 8001"
    fi
fi
echo ""

# 7. Check environment variables
echo "7. Checking AI configuration..."
echo "Backend AI_AGENT_URL:"
sudo docker exec smart-email-advisor-backend env | grep AI_AGENT_URL || echo "  NOT SET (will use default: http://ai-agent:8001)"
echo ""

echo "Backend OPENAI_API_KEY:"
OPENAI_SET=$(sudo docker exec smart-email-advisor-backend env | grep OPENAI_API_KEY || echo "NOT_SET")
if [ "$OPENAI_SET" != "NOT_SET" ]; then
    echo "  ✅ OPENAI_API_KEY is set (hidden)"
else
    echo "  ⚠️  OPENAI_API_KEY is NOT set"
    echo "     AI analysis will fail if AI Agent is unavailable"
    echo "     Set OPENAI_API_KEY in .env.production and restart backend"
fi
echo ""

# 8. Test analyze endpoint
echo "8. Testing analyze endpoint..."
TEST_EMAIL='{"subject":"Test","content":"Test content","sender":"test@example.com","recipient":"user@example.com"}'
ANALYZE_TEST=$(sudo docker exec smart-email-advisor-backend curl -s -X POST http://ai-agent:8001/analyze -H "Content-Type: application/json" -d "$TEST_EMAIL" 2>&1 | head -5 || echo "FAILED")
if echo "$ANALYZE_TEST" | grep -q "priority\|category\|error"; then
    if echo "$ANALYZE_TEST" | grep -q "error"; then
        echo "⚠️  Analyze endpoint returned error: $ANALYZE_TEST"
    else
        echo "✅ Analyze endpoint is working"
        echo "   Response preview: $ANALYZE_TEST"
    fi
else
    echo "❌ Analyze endpoint test failed: $ANALYZE_TEST"
fi
echo ""

# 9. Recommendations
echo "=========================================="
echo "Summary & Next Steps"
echo "=========================================="
echo ""

if echo "$AI_AGENT_STATUS" | grep -q "unhealthy\|exited"; then
    echo "🔧 If AI Agent is still unhealthy:"
    echo "   1. Check logs: sudo docker compose -f docker-compose.prod.yml logs ai-agent"
    echo "   2. Check if required environment variables are set in .env.production"
    echo "   3. Try rebuilding: sudo docker compose -f docker-compose.prod.yml build --no-cache ai-agent"
    echo "   4. Restart: sudo docker compose -f docker-compose.prod.yml restart ai-agent"
    echo ""
fi

if echo "$OPENAI_SET" | grep -q "NOT_SET"; then
    echo "⚠️  IMPORTANT: Set OPENAI_API_KEY in .env.production"
    echo "   This is required as a fallback if AI Agent fails"
    echo ""
fi

echo "Test the full flow:"
echo "  curl -X POST http://localhost/api/emails/analyze-from-spam?limit=1"
echo ""
