#!/bin/bash

# Build the Docker Image (This might take a while first time due to Rust compilation)
echo "Building Docker Image (casper-client included)..."
docker build -t casper-oracle .

# Stop existing container if any
docker stop oracle || true
docker rm oracle || true

# Run the Container
# We mount the logs directory so the host can see logs (and health checker can see them)
echo "Starting Oracle Agent..."
docker run -d \
  --name oracle \
  --restart unless-stopped \
  -v $(pwd)/../risk-dashboard/public:/app/../risk-dashboard/public \
  casper-oracle

echo "Agent deployed! Logs available at ../risk-dashboard/public/agent_logs.txt"
