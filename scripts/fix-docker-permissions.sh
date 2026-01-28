#!/bin/bash

# Fix Docker permissions for ubuntu user
# Run this on EC2 if you get "permission denied" errors

echo "=========================================="
echo "Fixing Docker Permissions"
echo "=========================================="
echo ""

# Add ubuntu user to docker group
echo "Adding ubuntu user to docker group..."
sudo usermod -aG docker ubuntu

# Set docker socket permissions (temporary fix)
echo "Setting docker socket permissions..."
sudo chmod 666 /var/run/docker.sock

# Restart docker service
echo "Restarting docker service..."
sudo systemctl restart docker

echo ""
echo "=========================================="
echo "Docker permissions fixed!"
echo "=========================================="
echo ""
echo "Note: You may need to log out and log back in for group changes to take effect."
echo "Or run: newgrp docker"
echo ""
echo "Test with: docker ps"
