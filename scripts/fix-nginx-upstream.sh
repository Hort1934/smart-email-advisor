#!/bin/bash

# Fix nginx upstream connection issues
# Run this on EC2

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR"

echo "=========================================="
echo "Fixing Nginx Upstream Connection"
echo "=========================================="
echo ""

echo "1. Checking frontend container IP..."
FRONTEND_IP=$(docker inspect smart-email-advisor-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || sudo docker inspect smart-email-advisor-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Frontend IP: $FRONTEND_IP"

echo ""
echo "2. Testing frontend connectivity from nginx..."
docker exec smart-email-advisor-nginx wget -q -O- http://frontend:80 2>&1 | head -5 || sudo docker exec smart-email-advisor-nginx wget -q -O- http://frontend:80 2>&1 | head -5 || echo "Cannot connect"

echo ""
echo "3. Testing direct IP connection..."
docker exec smart-email-advisor-nginx wget -q -O- http://${FRONTEND_IP}:80 2>&1 | head -5 || sudo docker exec smart-email-advisor-nginx wget -q -O- http://${FRONTEND_IP}:80 2>&1 | head -5 || echo "Cannot connect to IP"

echo ""
echo "4. Restarting nginx container..."
docker compose -f docker-compose.prod.yml restart nginx 2>/dev/null || sudo docker compose -f docker-compose.prod.yml restart nginx

echo ""
echo "5. Waiting for nginx to restart..."
sleep 5

echo ""
echo "6. Testing again..."
docker exec smart-email-advisor-nginx wget -q -O- http://frontend:80 2>&1 | head -5 || sudo docker exec smart-email-advisor-nginx wget -q -O- http://frontend:80 2>&1 | head -5 || echo "Still cannot connect"

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
