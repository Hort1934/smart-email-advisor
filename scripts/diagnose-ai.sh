#!/bin/bash

# Diagnostic script for AI Analysis issues

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "AI Analysis Diagnostic"
echo "=========================================="
echo ""

# 1. Check AI Agent container status
echo "1. AI Agent Container Status:"
echo "----------------------------------------"
AI_AGENT_STATUS=$(sudo docker compose -f docker-compose.prod.yml ps ai-agent 2>&1 | grep -A 1 "ai-agent" || echo "NOT_FOUND")
echo "$AI_AGENT_STATUS"
echo ""

# 2. Check AI Agent health
echo "2. AI Agent Health Check:"
echo "----------------------------------------"
AI_AGENT_HEALTH=$(curl -s http://localhost:8001/health 2>&1 || echo "FAILED")
if echo "$AI_AGENT_HEALTH" | grep -q "ok\|healthy"; then
    echo "✅ AI Agent is healthy: $AI_AGENT_HEALTH"
else
    echo "❌ AI Agent health check failed"
    echo "   Response: $AI_AGENT_HEALTH"
fi
echo ""

# 3. Test AI Agent from backend container
echo "3. Backend -> AI Agent Connectivity:"
echo "----------------------------------------"
BACKEND_TO_AI=$(sudo docker exec smart-email-advisor-backend curl -s http://ai-agent:8001/health 2>&1 || echo "FAILED")
if echo "$BACKEND_TO_AI" | grep -q "ok\|healthy"; then
    echo "✅ Backend can reach AI Agent: $BACKEND_TO_AI"
else
    echo "❌ Backend cannot reach AI Agent"
    echo "   Response: $BACKEND_TO_AI"
fi
echo ""

# 4. Check AI Agent logs for errors
echo "4. Recent AI Agent Errors:"
echo "----------------------------------------"
AI_AGENT_ERRORS=$(sudo docker compose -f docker-compose.prod.yml logs --tail=30 ai-agent 2>&1 | grep -i "error\|exception\|failed\|traceback" | tail -10 || echo "No recent errors")
if [ "$AI_AGENT_ERRORS" != "No recent errors" ]; then
    echo "⚠️  Recent AI Agent errors:"
    echo "$AI_AGENT_ERRORS"
else
    echo "✅ No recent AI Agent errors"
fi
echo ""

# 5. Check environment variables
echo "5. AI Service Configuration:"
echo "----------------------------------------"
echo "Backend AI_AGENT_URL:"
BACKEND_AI_URL=$(sudo docker exec smart-email-advisor-backend env | grep AI_AGENT_URL 2>&1 || echo "NOT_SET")
echo "  $BACKEND_AI_URL"

echo ""
echo "Backend OPENAI_API_KEY:"
BACKEND_OPENAI=$(sudo docker exec smart-email-advisor-backend env | grep OPENAI_API_KEY 2>&1 | sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=***HIDDEN***/' || echo "NOT_SET")
echo "  $BACKEND_OPENAI"
echo ""

# 6. Test AI Agent analyze endpoint
echo "6. Testing AI Agent Analyze Endpoint:"
echo "----------------------------------------"
TEST_EMAIL='{"subject":"Test Email","content":"This is a test email","sender":"test@example.com","recipient":"user@example.com"}'
AI_ANALYZE_RESPONSE=$(sudo docker exec smart-email-advisor-backend curl -s -X POST http://ai-agent:8001/analyze -H "Content-Type: application/json" -d "$TEST_EMAIL" 2>&1 || echo "FAILED")
if echo "$AI_ANALYZE_RESPONSE" | grep -q "priority\|category"; then
    echo "✅ AI Agent analyze endpoint is working"
    echo "   Response preview: $(echo "$AI_ANALYZE_RESPONSE" | head -3)"
else
    echo "❌ AI Agent analyze endpoint failed"
    echo "   Response: $AI_ANALYZE_RESPONSE"
fi
echo ""

# 7. Test backend analyze-from-spam endpoint
echo "7. Testing Backend Analyze-from-Spam Endpoint:"
echo "----------------------------------------"
ANALYZE_RESPONSE=$(curl -s -X POST http://localhost/api/emails/analyze-from-spam?limit=1 2>&1 || echo "FAILED")
ANALYZE_CODE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost/api/emails/analyze-from-spam?limit=1 2>&1 | grep "HTTP_CODE" | cut -d: -f2 || echo "N/A")
if [ "$ANALYZE_CODE" = "200" ]; then
    echo "✅ Analyze-from-spam endpoint is working (HTTP $ANALYZE_CODE)"
    echo "   Response preview: $(echo "$ANALYZE_RESPONSE" | head -5)"
else
    echo "❌ Analyze-from-spam endpoint failed (HTTP $ANALYZE_CODE)"
    echo "   Response: $ANALYZE_RESPONSE"
fi
echo ""

# 8. Check backend logs for AI-related errors
echo "8. Recent Backend AI Errors:"
echo "----------------------------------------"
BACKEND_AI_ERRORS=$(sudo docker compose -f docker-compose.prod.yml logs --tail=50 backend 2>&1 | grep -i "ai\|agent\|openai\|analysis" | grep -i "error\|exception\|failed" | tail -10 || echo "No recent AI errors")
if [ "$BACKEND_AI_ERRORS" != "No recent AI errors" ]; then
    echo "⚠️  Recent backend AI errors:"
    echo "$BACKEND_AI_ERRORS"
else
    echo "✅ No recent backend AI errors"
fi
echo ""

# 9. Check network connectivity
echo "9. Container Network Connectivity:"
echo "----------------------------------------"
echo "Backend -> AI Agent network test:"
BACKEND_NETWORK=$(sudo docker exec smart-email-advisor-backend ping -c 2 ai-agent 2>&1 | grep -i "packet loss\|unreachable" || echo "Network test failed")
if echo "$BACKEND_NETWORK" | grep -q "0% packet loss"; then
    echo "✅ Network connectivity OK"
else
    echo "⚠️  Network connectivity issue: $BACKEND_NETWORK"
fi
echo ""

# 10. Summary and recommendations
echo "=========================================="
echo "Summary & Recommendations"
echo "=========================================="
echo ""

# Check if AI Agent is healthy
if echo "$AI_AGENT_STATUS" | grep -q "unhealthy"; then
    echo "🔧 ACTION REQUIRED:"
    echo "   AI Agent container is unhealthy"
    echo "   Check logs: sudo docker compose -f docker-compose.prod.yml logs ai-agent"
    echo "   Restart: sudo docker compose -f docker-compose.prod.yml restart ai-agent"
    echo ""
fi

# Check if OpenAI API key is set
if echo "$BACKEND_OPENAI" | grep -q "NOT_SET"; then
    echo "⚠️  WARNING:"
    echo "   OPENAI_API_KEY is not set in backend container"
    echo "   AI analysis will fail if AI Agent is unavailable"
    echo "   Set OPENAI_API_KEY in .env.production"
    echo ""
fi

# Check if AI Agent URL is correct
if echo "$BACKEND_AI_URL" | grep -q "NOT_SET"; then
    echo "⚠️  WARNING:"
    echo "   AI_AGENT_URL is not set in backend container"
    echo "   Backend will try to use default: http://ai-agent:8001"
    echo ""
fi

echo "Test the analyze endpoint:"
echo "  curl -X POST http://localhost/api/emails/analyze-from-spam?limit=1"
echo ""
