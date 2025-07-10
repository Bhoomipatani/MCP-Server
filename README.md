# K8ProcessMonitor MCP Server

This project provides a set of tools for managing remote SSH and Kubernetes sessions via a FastMCP server. It allows you to connect to remote machines over SSH, fetch Kubernetes kubeconfig files, interact with Kubernetes clusters, and manage sessions programmatically.

## Features

- Establish SSH connections to remote hosts
- Run commands on remote machines via SSH
- Fetch and use remote Kubernetes kubeconfig files
- List pods in a Kubernetes namespace
- Cleanly disconnect and clean up sessions

## Quick Start

### Using Docker (Recommended)

1. **Run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Or use the Makefile:**
```bash
make run
```

3. **Test the server:**
```bash
curl http://localhost:8001/health
```

### Manual Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
python -m src.main
```

## Documentation

- [Docker Deployment Guide](DOCKER.md) - Complete guide for containerized deployment
- [API Documentation](docs/API.md) - API reference (if available)

## Container Images

The server is available as a Docker container with the following features:
- Multi-stage build for optimized image size
- Non-root user for security
- Health check endpoint
- Configurable via environment variables
- Volume mounts for configuration and logs

## Development

### Local Development with Docker

```bash
# Start in development mode with hot reload
make run-dev

# View logs
make logs

# Open shell in container
make shell

# Stop services
make stop
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker
5. Submit a pull request

## License

[Add your license here]


