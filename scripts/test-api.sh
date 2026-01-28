#!/bin/bash

# Test API endpoints from EC2
# Run this to verify backend API is accessible

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

ELASTIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo "=========================================="
echo "Testing API Endpoints"
echo "=========================================="
echo ""

echo "1. Testing Backend Health Endpoint..."
echo "   URL: http://localhost/api/health"
curl -s http://localhost/api/health | jq '.' 2>/dev/null || curl -s http://localhost/api/health
echo ""
echo ""

echo "2. Testing Backend Health (direct)..."
echo "   URL: http://localhost/health"
curl -s http://localhost/health | jq '.' 2>/dev/null || curl -s http://localhost/health
echo ""
echo ""

echo "3. Testing Stats Endpoint..."
echo "   URL: http://localhost/api/stats/stats"
STATS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost/api/stats/stats)
HTTP_CODE=$(echo "$STATS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$STATS_RESPONSE" | grep -v "HTTP_CODE")
echo "   HTTP Code: $HTTP_CODE"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo ""

echo "4. Testing Email Folders Endpoint..."
echo "   URL: http://localhost/api/emails/folders"
FOLDERS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost/api/emails/folders)
HTTP_CODE=$(echo "$FOLDERS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$FOLDERS_RESPONSE" | grep -v "HTTP_CODE")
echo "   HTTP Code: $HTTP_CODE"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo ""

echo "5. Testing from Frontend Container..."
docker exec smart-email-advisor-frontend wget -q -O- http://backend:8000/health 2>/dev/null || sudo docker exec smart-email-advisor-frontend wget -q -O- http://backend:8000/health 2>/dev/null || echo "Cannot test from frontend container"
echo ""
echo ""

echo "6. Checking NEXT_PUBLIC_API_URL in frontend..."
docker exec smart-email-advisor-frontend env | grep NEXT_PUBLIC_API_URL 2>/dev/null || sudo docker exec smart-email-advisor-frontend env | grep NEXT_PUBLIC_API_URL || echo "Environment variable not found"
echo ""
echo ""

echo "7. Testing Backend Container Directly..."
docker exec smart-email-advisor-backend curl -s http://localhost:8000/health 2>/dev/null || sudo docker exec smart-email-advisor-backend curl -s http://localhost:8000/health 2>/dev/null || echo "Cannot test backend directly"
echo ""
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Expected Elastic IP: $ELASTIC_IP"
echo "Frontend should use: http://$ELASTIC_IP/api"
