#!/bin/bash

# Fix database container issues
# Run this on EC2 if database won't start

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR"

echo "=== Stopping all containers ==="
docker compose -f docker-compose.prod.yml down

echo ""
echo "=== Removing database volume (WARNING: This deletes all data!) ==="
read -p "This will delete all database data. Continue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker volume rm smart-email-advisor_postgres_data 2>/dev/null || true
    echo "Database volume removed"
else
    echo "Skipping volume removal"
fi

echo ""
echo "=== Checking .env file ==="
if [ -f ".env" ]; then
    if grep -q "POSTGRES_PASSWORD=" .env; then
        echo "✓ POSTGRES_PASSWORD found in .env"
        grep "POSTGRES_PASSWORD=" .env | head -1
    else
        echo "⚠ POSTGRES_PASSWORD not found in .env"
        echo "Adding default password..."
        echo "POSTGRES_PASSWORD=postgres123" >> .env
    fi
else
    echo "⚠ .env file not found, creating with defaults..."
    cat > .env << EOF
POSTGRES_DB=smart_email_advisor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
EOF
fi

echo ""
echo "=== Starting database container ==="
docker compose -f docker-compose.prod.yml up -d db

echo ""
echo "=== Waiting for database to be healthy (60 seconds) ==="
for i in {1..12}; do
    STATUS=$(docker compose -f docker-compose.prod.yml ps db --format json | jq -r '.[0].Health // "unknown"' 2>/dev/null || echo "checking")
    if [ "$STATUS" = "healthy" ]; then
        echo "✓ Database is healthy!"
        break
    fi
    echo "Waiting... ($i/12)"
    sleep 5
done

echo ""
echo "=== Database status ==="
docker compose -f docker-compose.prod.yml ps db

echo ""
echo "=== Database logs ==="
docker compose -f docker-compose.prod.yml logs --tail=20 db

echo ""
echo "=== Starting all containers ==="
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "=== Final status ==="
docker compose -f docker-compose.prod.yml ps
