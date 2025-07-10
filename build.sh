#!/bin/bash
set -e

# Build the Docker image
echo "Building MCP Server Docker image..."
docker build -t mcp-server:latest .

# Tag for different environments
docker tag mcp-server:latest mcp-server:dev
docker tag mcp-server:latest mcp-server:prod

echo "Build completed successfully!"
echo "Available images:"
docker images | grep mcp-server
