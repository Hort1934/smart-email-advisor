#!/bin/bash

# Generate secure secrets for .env.production
# Usage: ./generate-secrets.sh

echo "=========================================="
echo "Generating Secure Secrets"
echo "=========================================="
echo ""
echo "Copy these values to your .env.production file:"
echo ""
echo "# Database Password"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24)"
echo ""
echo "# Application Secret Key"
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo ""
echo "# Webhook Secret"
echo "WEBHOOK_SECRET=$(openssl rand -hex 32)"
echo ""
echo "=========================================="
echo "Done! Copy the values above to .env.production"
echo "=========================================="
