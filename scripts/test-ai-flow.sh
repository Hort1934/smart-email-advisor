#!/bin/bash

# Test the full AI analysis flow

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "Testing AI Analysis Flow"
echo "=========================================="
echo ""

# 1. Test AI Agent directly
echo "1. Testing AI Agent analyze endpoint directly..."
TEST_EMAIL='{"subject":"Test Email","content":"This is a test email for analysis","sender":"test@example.com","recipient":"user@example.com"}'
AI_RESPONSE=$(sudo docker exec smart-email-advisor-backend curl -s -X POST http://ai-agent:8001/analyze -H "Content-Type: application/json" -d "$TEST_EMAIL" 2>&1)
if echo "$AI_RESPONSE" | grep -q "priority"; then
    echo "✅ AI Agent analyze works"
    echo "   Response: $(echo "$AI_RESPONSE" | head -3)"
else
    echo "❌ AI Agent analyze failed: $AI_RESPONSE"
fi
echo ""

# 2. Check backend logs for AI Agent calls
echo "2. Checking recent backend logs for AI Agent calls..."
sudo docker compose -f docker-compose.prod.yml logs --tail=20 backend | grep -i "ai agent\|analyze" || echo "No recent AI logs"
echo ""

# 3. Test analyze-from-spam endpoint
echo "3. Testing analyze-from-spam endpoint..."
ANALYZE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "http://localhost/api/emails/analyze-from-spam?limit=1" 2>&1)
HTTP_CODE=$(echo "$ANALYZE_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$ANALYZE_RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ analyze-from-spam endpoint works (HTTP $HTTP_CODE)"
    echo "   Response: $(echo "$BODY" | head -5)"
else
    echo "❌ analyze-from-spam endpoint failed (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
    echo ""
    echo "   Checking backend logs for errors..."
    sudo docker compose -f docker-compose.prod.yml logs --tail=30 backend | grep -i "error\|exception" | tail -5
fi
echo ""

# 4. Check if OPENAI_API_KEY is needed
echo "4. Checking if OPENAI_API_KEY is set..."
OPENAI_KEY=$(sudo docker exec smart-email-advisor-backend env | grep OPENAI_API_KEY || echo "NOT_SET")
if [ "$OPENAI_KEY" = "NOT_SET" ]; then
    echo "⚠️  OPENAI_API_KEY is not set"
    echo "   This is required as a fallback when AI Agent fails"
    echo "   Set it in .env.production and restart backend"
else
    echo "✅ OPENAI_API_KEY is set (hidden)"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "If analyze-from-spam is failing:"
echo "  1. Check backend logs: sudo docker compose -f docker-compose.prod.yml logs backend | grep -i 'ai\|error'"
echo "  2. Set OPENAI_API_KEY in .env.production as fallback"
echo "  3. Restart backend: sudo docker compose -f docker-compose.prod.yml restart backend"
echo ""
