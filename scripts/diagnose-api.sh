#!/bin/bash

# Comprehensive API and Database Diagnostic Script
# Run this on EC2 to diagnose API connection issues

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

ELASTIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "=========================================="
echo "API & Database Diagnostic"
echo "=========================================="
echo ""

# 1. Check container status
echo "1. Container Status:"
echo "----------------------------------------"
sudo docker compose -f docker-compose.prod.yml ps
echo ""

# 2. Check backend health
echo "2. Backend Health Check:"
echo "----------------------------------------"
echo "Testing: http://localhost/health"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost/health 2>&1 || echo "FAILED")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "N/A")
BODY=$(echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE" | head -1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Backend is healthy: $BODY"
else
    echo "❌ Backend health check failed"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $BODY"
fi
echo ""

# 3. Check backend container directly
echo "3. Backend Container Direct Check:"
echo "----------------------------------------"
BACKEND_DIRECT=$(sudo docker exec smart-email-advisor-backend curl -s http://localhost:8000/health 2>&1 || echo "FAILED")
if echo "$BACKEND_DIRECT" | grep -q "ok"; then
    echo "✅ Backend container is responding: $BACKEND_DIRECT"
else
    echo "❌ Backend container not responding"
    echo "   Response: $BACKEND_DIRECT"
fi
echo ""

# 4. Check database connectivity via API
echo "4. Database Connectivity (via API):"
echo "----------------------------------------"
DB_API_CHECK=$(curl -s http://localhost/api/stats/stats 2>&1 || echo "FAILED")
if echo "$DB_API_CHECK" | grep -q "totalEmails"; then
    echo "✅ Database accessible via API"
    echo "   Response includes stats data"
else
    echo "❌ Database not accessible via API"
    echo "   Response: $DB_API_CHECK"
fi
echo ""

# 5. Check database container
echo "5. Database Container Status:"
echo "----------------------------------------"
DB_STATUS=$(sudo docker exec smart-email-advisor-db pg_isready -U postgres 2>&1 || echo "FAILED")
if echo "$DB_STATUS" | grep -q "accepting connections"; then
    echo "✅ Database is ready: $DB_STATUS"
else
    echo "❌ Database not ready"
    echo "   Status: $DB_STATUS"
fi
echo ""

# 6. Test API endpoints
echo "6. API Endpoints Test:"
echo "----------------------------------------"

# Test /api/stats/stats
echo "Testing: http://localhost/api/stats/stats"
STATS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost/api/stats/stats 2>&1 || echo "FAILED")
STATS_CODE=$(echo "$STATS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "N/A")
STATS_BODY=$(echo "$STATS_RESPONSE" | grep -v "HTTP_CODE" | head -1)
if [ "$STATS_CODE" = "200" ]; then
    echo "✅ /api/stats/stats: OK"
    echo "$STATS_BODY" | head -3
else
    echo "❌ /api/stats/stats failed (HTTP $STATS_CODE)"
    echo "   Response: $STATS_BODY"
fi
echo ""

# Test /api/emails/folders
echo "Testing: http://localhost/api/emails/folders"
FOLDERS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost/api/emails/folders 2>&1 || echo "FAILED")
FOLDERS_CODE=$(echo "$FOLDERS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "N/A")
FOLDERS_BODY=$(echo "$FOLDERS_RESPONSE" | grep -v "HTTP_CODE" | head -1)
if [ "$FOLDERS_CODE" = "200" ] || [ "$FOLDERS_CODE" = "401" ]; then
    echo "✅ /api/emails/folders: OK (HTTP $FOLDERS_CODE)"
else
    echo "❌ /api/emails/folders failed (HTTP $FOLDERS_CODE)"
    echo "   Response: $FOLDERS_BODY"
fi
echo ""

# 7. Check frontend API URL configuration
echo "7. Frontend API URL Configuration:"
echo "----------------------------------------"
FRONTEND_ENV=$(sudo docker exec smart-email-advisor-frontend env | grep NEXT_PUBLIC_API_URL 2>&1 || echo "NOT_FOUND")
if [ "$FRONTEND_ENV" != "NOT_FOUND" ]; then
    echo "Frontend NEXT_PUBLIC_API_URL: $FRONTEND_ENV"
    if echo "$FRONTEND_ENV" | grep -q "/api"; then
        echo "⚠️  WARNING: NEXT_PUBLIC_API_URL contains '/api' - should be base URL only"
    else
        echo "✅ NEXT_PUBLIC_API_URL looks correct"
    fi
else
    echo "❌ NEXT_PUBLIC_API_URL not found in frontend container"
fi
echo ""

# 8. Check .env.production
echo "8. .env.production Configuration:"
echo "----------------------------------------"
if [ -f .env.production ]; then
    API_URL=$(grep NEXT_PUBLIC_API_URL .env.production || echo "NOT_FOUND")
    echo "$API_URL"
    if echo "$API_URL" | grep -q "/api"; then
        echo "⚠️  WARNING: NEXT_PUBLIC_API_URL contains '/api' - should be base URL only"
        echo "   Run: ./scripts/fix-api-url.sh"
    fi
else
    echo "❌ .env.production not found"
fi
echo ""

# 9. Check backend logs for errors
echo "9. Recent Backend Errors:"
echo "----------------------------------------"
BACKEND_ERRORS=$(sudo docker compose -f docker-compose.prod.yml logs --tail=20 backend 2>&1 | grep -i "error\|exception\|failed" | tail -5 || echo "No recent errors")
if [ "$BACKEND_ERRORS" != "No recent errors" ]; then
    echo "⚠️  Recent backend errors:"
    echo "$BACKEND_ERRORS"
else
    echo "✅ No recent backend errors"
fi
echo ""

# 10. Check database logs
echo "10. Database Logs (last 5 lines):"
echo "----------------------------------------"
sudo docker compose -f docker-compose.prod.yml logs --tail=5 db 2>&1 | tail -5
echo ""

# 11. Network connectivity test
echo "11. Container Network Connectivity:"
echo "----------------------------------------"
echo "Testing frontend -> backend connectivity..."
FRONTEND_TO_BACKEND=$(sudo docker exec smart-email-advisor-frontend wget -q -O- --timeout=5 http://backend:8000/health 2>&1 || echo "FAILED")
if echo "$FRONTEND_TO_BACKEND" | grep -q "ok"; then
    echo "✅ Frontend can reach backend"
else
    echo "❌ Frontend cannot reach backend"
    echo "   Response: $FRONTEND_TO_BACKEND"
fi
echo ""

# 12. Summary and recommendations
echo "=========================================="
echo "Summary & Recommendations"
echo "=========================================="
echo ""

# Check if fix is needed
NEEDS_FIX=false
if ! echo "$FRONTEND_ENV" | grep -q "http://${ELASTIC_IP}"; then
    NEEDS_FIX=true
fi
if echo "$FRONTEND_ENV" | grep -q "/api"; then
    NEEDS_FIX=true
fi

if [ "$NEEDS_FIX" = true ]; then
    echo "🔧 ACTION REQUIRED:"
    echo "   Run: ./scripts/fix-api-url.sh"
    echo "   Or manually update .env.production and rebuild frontend"
    echo ""
fi

echo "Test URLs:"
echo "  - Health: http://${ELASTIC_IP}/health"
echo "  - Stats: http://${ELASTIC_IP}/api/stats/stats"
echo "  - Frontend: http://${ELASTIC_IP}"
echo ""
