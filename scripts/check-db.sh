#!/bin/bash

# Quick database diagnostic script
# Run this on EC2 to check database status

echo "=== Database Container Status ==="
docker compose -f /home/ubuntu/poc/smart-email-advisor/docker-compose.prod.yml ps db

echo ""
echo "=== Database Logs (last 50 lines) ==="
docker compose -f /home/ubuntu/poc/smart-email-advisor/docker-compose.prod.yml logs --tail=50 db

echo ""
echo "=== Environment Variables ==="
docker compose -f /home/ubuntu/poc/smart-email-advisor/docker-compose.prod.yml config | grep -A 5 "POSTGRES"

echo ""
echo "=== Health Check ==="
sudo docker inspect smart-email-advisor-db --format='{{json .State.Health}}' | jq '.' 2>/dev/null || sudo docker inspect smart-email-advisor-db --format='{{.State.Status}}'
