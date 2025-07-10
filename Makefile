# Makefile for K8ProcessMonitor MCP Server

.PHONY: build run stop clean logs shell help

# Default target
help:
	@echo "Available targets:"
	@echo "  build     - Build the Docker image"
	@echo "  run       - Run the container with docker-compose"
	@echo "  run-dev   - Run in development mode"
	@echo "  stop      - Stop the container"
	@echo "  clean     - Clean up containers and images"
	@echo "  logs      - View container logs"
	@echo "  shell     - Open shell in running container"
	@echo "  test      - Test the health endpoint"
	@echo "  help      - Show this help message"

# Build the Docker image
build:
	@echo "Building MCP Server Docker image..."
	docker build -t mcp-server:latest .
	docker tag mcp-server:latest mcp-server:dev

# Run with docker-compose
run:
	@echo "Starting MCP Server with docker-compose..."
	docker-compose up -d --build

# Run in development mode
run-dev:
	@echo "Starting MCP Server in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Stop the container
stop:
	@echo "Stopping MCP Server..."
	docker-compose down

# Clean up containers and images
clean:
	@echo "Cleaning up..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# View container logs
logs:
	docker-compose logs -f mcp-server

# Open shell in running container
shell:
	docker exec -it k8-process-monitor bash

# Test the health endpoint
test:
	@echo "Testing health endpoint..."
	curl -f http://localhost:8001/health || echo "Health check failed"

# Install dependencies locally (for development)
install:
	pip install -r requirements.txt

# Format code
format:
	black src/
	isort src/

# Check code quality
lint:
	flake8 src/
	black --check src/
	isort --check-only src/
