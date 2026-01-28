#!/bin/bash

# Fix OPENAI_API_KEY configuration

set -e

APP_DIR="/home/ubuntu/poc/smart-email-advisor"
cd "$APP_DIR" 2>/dev/null || { echo "Error: Cannot find $APP_DIR"; exit 1; }

echo "=========================================="
echo "Fixing OPENAI_API_KEY Configuration"
echo "=========================================="
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production not found!"
    exit 1
fi

# Check if OPENAI_API_KEY is already set
if grep -q "^OPENAI_API_KEY=" .env.production; then
    CURRENT_KEY=$(grep "^OPENAI_API_KEY=" .env.production | cut -d= -f2)
    if [ -n "$CURRENT_KEY" ] && [ "$CURRENT_KEY" != "your-openai-api-key-here" ] && [ "$CURRENT_KEY" != "" ]; then
        echo "✅ OPENAI_API_KEY is already set in .env.production"
        echo "   (value is hidden for security)"
        echo ""
        echo "Restarting backend to apply changes..."
        sudo docker compose -f docker-compose.prod.yml restart backend
        echo ""
        echo "Waiting for backend to start..."
        sleep 10
        
        echo ""
        echo "Verifying OPENAI_API_KEY in backend container..."
        BACKEND_KEY=$(sudo docker exec smart-email-advisor-backend env | grep OPENAI_API_KEY || echo "NOT_SET")
        if [ "$BACKEND_KEY" != "NOT_SET" ]; then
            echo "✅ OPENAI_API_KEY is now set in backend container"
        else
            echo "⚠️  OPENAI_API_KEY still not set in backend container"
            echo "   Check .env.production and ensure it's loaded correctly"
        fi
        exit 0
    else
        echo "⚠️  OPENAI_API_KEY is set but appears to be a placeholder"
        echo "   Current value: $CURRENT_KEY"
    fi
else
    echo "⚠️  OPENAI_API_KEY is not set in .env.production"
fi

echo ""
echo "To set OPENAI_API_KEY:"
echo ""
echo "1. Get your OpenAI API key from: https://platform.openai.com/api-keys"
echo ""
echo "2. Add it to .env.production:"
echo "   echo 'OPENAI_API_KEY=sk-your-key-here' >> .env.production"
echo ""
echo "3. Or edit .env.production and add:"
echo "   OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "4. Then restart the backend:"
echo "   sudo docker compose -f docker-compose.prod.yml restart backend"
echo ""
echo "Note: OPENAI_API_KEY is used as a fallback when AI Agent is unavailable."
echo "      Since AI Agent is working, this may not be strictly necessary,"
echo "      but it's recommended for reliability."
echo ""

# Check if user wants to set it now
read -p "Do you want to set OPENAI_API_KEY now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your OpenAI API key: " OPENAI_KEY
    if [ -n "$OPENAI_KEY" ]; then
        # Remove old OPENAI_API_KEY if exists
        sed -i.bak '/^OPENAI_API_KEY=/d' .env.production
        
        # Add new OPENAI_API_KEY
        echo "OPENAI_API_KEY=$OPENAI_KEY" >> .env.production
        
        echo ""
        echo "✅ OPENAI_API_KEY added to .env.production"
        echo ""
        echo "Restarting backend..."
        sudo docker compose -f docker-compose.prod.yml restart backend
        
        echo ""
        echo "Waiting for backend to start..."
        sleep 10
        
        echo ""
        echo "Verifying..."
        BACKEND_KEY=$(sudo docker exec smart-email-advisor-backend env | grep OPENAI_API_KEY || echo "NOT_SET")
        if [ "$BACKEND_KEY" != "NOT_SET" ]; then
            echo "✅ OPENAI_API_KEY is now set in backend container"
        else
            echo "⚠️  OPENAI_API_KEY still not set in backend container"
            echo "   You may need to rebuild the container:"
            echo "   sudo docker compose -f docker-compose.prod.yml build backend"
            echo "   sudo docker compose -f docker-compose.prod.yml up -d backend"
        fi
    else
        echo "❌ No key provided"
    fi
fi
