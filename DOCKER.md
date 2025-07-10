# K8ProcessMonitor MCP Server - Containerized Deployment

This document provides instructions for containerizing and deploying the K8ProcessMonitor MCP Server.

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the container:**
```bash
docker-compose up --build
```

2. **Run in detached mode:**
```bash
docker-compose up -d --build
```

3. **View logs:**
```bash
docker-compose logs -f mcp-server
```

4. **Stop the service:**
```bash
docker-compose down
```

### Using Docker directly

1. **Build the image:**
```bash
./build.sh
# or manually:
docker build -t mcp-server:latest .
```

2. **Run the container:**
```bash
docker run -d \
  --name k8-process-monitor \
  -p 8001:8001 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  mcp-server:latest
```

## Configuration

### Environment Variables

The following environment variables can be used to configure the server:

- `SERVER_HOST`: Server bind address (default: "0.0.0.0")
- `SERVER_PORT`: Server port (default: 8001)
- `LOG_LEVEL`: Logging level (default: "info")

### Configuration Files

1. **Copy the example config:**
```bash
cp config/config.yaml.example config/config.yaml
```

2. **Edit the configuration file as needed:**
```yaml
server:
  host: "0.0.0.0"
  port: 8001
  log_level: "INFO"

ssh:
  timeout: 30
  max_connections: 10

kubernetes:
  default_namespace: "default"
  timeout: 30
```

### Volume Mounts

The Docker setup includes the following volume mounts:

- `./config:/app/config:ro` - Configuration files (read-only)
- `./logs:/app/logs` - Log files
- Optionally mount SSH keys and kubeconfig files as needed

## Security Considerations

1. **SSH Keys**: Mount SSH private keys securely:
```bash
docker run -d \
  --name k8-process-monitor \
  -p 8001:8001 \
  -v ~/.ssh:/home/mcpuser/.ssh:ro \
  -v $(pwd)/config:/app/config:ro \
  mcp-server:latest
```

2. **Kubeconfig Files**: Mount kubeconfig files:
```bash
docker run -d \
  --name k8-process-monitor \
  -p 8001:8001 \
  -v ~/.kube:/home/mcpuser/.kube:ro \
  -v $(pwd)/config:/app/config:ro \
  mcp-server:latest
```

3. **Network Security**: The container runs on port 8001. Consider using a reverse proxy or VPN for production deployments.

## Health Check

The server includes a health check endpoint:
```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "service": "K8ProcessMonitor MCP Server"
}
```

## Development

### Local Development with Docker

1. **Build development image:**
```bash
docker build -t mcp-server:dev .
```

2. **Run with code mounting for development:**
```bash
docker run -d \
  --name mcp-dev \
  -p 8001:8001 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/config:/app/config:ro \
  mcp-server:dev
```

### Debugging

1. **View container logs:**
```bash
docker logs -f k8-process-monitor
```

2. **Execute commands in container:**
```bash
docker exec -it k8-process-monitor bash
```

3. **Check container status:**
```bash
docker ps
docker inspect k8-process-monitor
```

## Production Deployment

### Docker Compose Production Setup

1. **Create a production docker-compose.yml:**
```yaml
version: '3.8'

services:
  mcp-server:
    image: mcp-server:prod
    container_name: k8-process-monitor-prod
    ports:
      - "8001:8001"
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8001
      - LOG_LEVEL=info
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - /etc/ssl/certs:/etc/ssl/certs:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Kubernetes Deployment

For Kubernetes deployment, create the following manifests:

1. **Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: mcp-server:latest
        ports:
        - containerPort: 8001
        env:
        - name: SERVER_HOST
          value: "0.0.0.0"
        - name: SERVER_PORT
          value: "8001"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          limits:
            cpu: 1000m
            memory: 512Mi
          requests:
            cpu: 500m
            memory: 256Mi
```

2. **Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
spec:
  selector:
    app: mcp-server
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: LoadBalancer
```

## Monitoring

### Prometheus Metrics

To add Prometheus metrics, extend the Dockerfile to include:
```dockerfile
RUN pip install prometheus-client
```

### Logging

Logs are written to `/app/logs/` inside the container and can be accessed via:
- Volume mount: `./logs:/app/logs`
- Docker logs: `docker logs k8-process-monitor`

## Troubleshooting

1. **Container won't start:**
   - Check Docker logs: `docker logs k8-process-monitor`
   - Verify port availability: `lsof -i :8001`
   - Check resource limits

2. **SSH connections fail:**
   - Verify SSH keys are mounted correctly
   - Check network connectivity from container
   - Validate SSH key permissions

3. **Kubernetes operations fail:**
   - Verify kubeconfig is mounted and valid
   - Check cluster connectivity
   - Validate RBAC permissions

## Support

For issues and questions, please check the logs and ensure all dependencies are properly configured.
