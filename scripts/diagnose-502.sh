#!/bin/bash

# Diagnose 502 Bad Gateway issues
# Run this on EC2 to check what's wrong

echo "=========================================="
echo "502 Bad Gateway Diagnostic"
echo "=========================================="
echo ""

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "1. Checking container status..."
# Try without sudo first, fallback to sudo if needed
docker compose -f docker-compose.prod.yml ps 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps

echo ""
echo "2. Checking if frontend container is running..."
FRONTEND_STATUS=$(docker compose -f docker-compose.prod.yml ps frontend --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps frontend --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")
echo "Frontend status: $FRONTEND_STATUS"

if [ "$FRONTEND_STATUS" != "running" ]; then
    echo "⚠ Frontend container is not running!"
    echo "Frontend logs:"
    docker compose -f docker-compose.prod.yml logs --tail=30 frontend 2>/dev/null || sudo docker compose -f docker-compose.prod.yml logs --tail=30 frontend
fi

echo ""
echo "3. Checking if backend container is running..."
BACKEND_STATUS=$(docker compose -f docker-compose.prod.yml ps backend --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps backend --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")
echo "Backend status: $BACKEND_STATUS"

if [ "$BACKEND_STATUS" != "running" ]; then
    echo "⚠ Backend container is not running!"
    echo "Backend logs:"
    docker compose -f docker-compose.prod.yml logs --tail=30 backend 2>/dev/null || sudo docker compose -f docker-compose.prod.yml logs --tail=30 backend
fi

echo ""
echo "4. Testing frontend connectivity from nginx container..."
docker compose -f docker-compose.prod.yml exec -T nginx wget -q -O- http://frontend:80 2>&1 | head -5 || sudo docker compose -f docker-compose.prod.yml exec -T nginx wget -q -O- http://frontend:80 2>&1 | head -5 || echo "Cannot connect to frontend:80"

echo ""
echo "5. Testing backend connectivity from nginx container..."
docker compose -f docker-compose.prod.yml exec -T nginx wget -q -O- http://backend:8000/health 2>&1 | head -5 || sudo docker compose -f docker-compose.prod.yml exec -T nginx wget -q -O- http://backend:8000/health 2>&1 | head -5 || echo "Cannot connect to backend:8000"

echo ""
echo "6. Checking nginx logs..."
echo "Nginx error log (last 20 lines):"
docker compose -f docker-compose.prod.yml logs --tail=20 nginx 2>/dev/null | grep -i error || sudo docker compose -f docker-compose.prod.yml logs --tail=20 nginx 2>/dev/null | grep -i error || echo "No errors found"

echo ""
echo "7. Checking network connectivity..."
docker network inspect smart-email-advisor_smart-email-network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' 2>/dev/null || sudo docker network inspect smart-email-advisor_smart-email-network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' 2>/dev/null || echo "Cannot inspect network"

echo ""
echo "8. Checking if frontend is listening on port 80..."
docker compose -f docker-compose.prod.yml exec -T frontend netstat -tuln 2>/dev/null | grep :80 || docker compose -f docker-compose.prod.yml exec -T frontend ss -tuln 2>/dev/null | grep :80 || sudo docker compose -f docker-compose.prod.yml exec -T frontend netstat -tuln 2>/dev/null | grep :80 || echo "Cannot check port 80"

echo ""
echo "=========================================="
echo "Diagnostic complete!"
echo "=========================================="
