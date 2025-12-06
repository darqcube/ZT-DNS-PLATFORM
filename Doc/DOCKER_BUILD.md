# ZeroTrust DNS - Docker Build Guide

## Overview

This guide covers building and deploying the ZeroTrust DNS Platform with TLS Proxy using Docker. Choose between Go binaries (recommended) or Python binaries.

## Quick Start
```bash
# Build and run with Docker Compose (easiest)
docker-compose up -d

# Access web UI
open http://localhost:5001
```

## Dockerfile Options

### Option 1: Dockerfile.go (Recommended)

**Advantages:**
- ✅ Builds all 8 binaries (4 platforms × 2 types)
- ✅ Small binaries (~5-8 MB each)
- ✅ Fast startup
- ✅ Cross-platform compilation works perfectly
- ✅ No manual binary management needed

**What's Included:**
- `ZeroTrust-Client-x64.exe` (Windows x64)
- `ZeroTrust-Client-ARM64.exe` (Windows ARM64)
- `ZeroTrust-Client-x86_64` (Linux x64)
- `ZeroTrust-Client-arm64` (Linux ARM64)
- `ZeroTrust-Service-*` (Copies of client binaries)

**Build:**
```bash
docker build -f Dockerfile.go -t zerotrust-dns:latest .
```

### Option 2: Dockerfile.python (Alternative)

**Advantages:**
- ✅ No Go installation required
- ✅ Easier to debug and customize
- ✅ Python endpoint included

**Disadvantages:**
- ⚠️ Only creates Linux x64 binaries in Docker
- ⚠️ Windows and ARM64 binaries must be built manually
- ⚠️ Larger binaries (~15-30 MB vs ~5-8 MB)

**Build:**
```bash
docker build -f Dockerfile.python -t zerotrust-dns:python .
```

## Docker Compose Deployment

### Basic Setup

Create or use existing `docker-compose.yml`:
```yaml
version: '3.8'

services:
  zerotrust-dns:
    build:
      context: .
      dockerfile: Dockerfile.go  # or Dockerfile.python
    container_name: zerotrust-dns-server
    ports:
      - "5001:5001"  # Web UI
      - "853:853"    # DNS over TLS
      - "8443:8443"  # Service Proxy/Router
    volumes:
      - ./data/certs:/opt/zerotrust-dns/certs
      - ./data/data:/opt/zerotrust-dns/data
    restart: unless-stopped
```

### Commands
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose build
docker-compose up -d

# Restart
docker-compose restart
```

## Manual Docker Build & Run

### Build Image
```bash
# Build with Go binaries (recommended)
docker build -f Dockerfile.go -t zerotrust-dns:latest .

# Build with Python binaries
docker build -f Dockerfile.python -t zerotrust-dns:python .

# Check image size
docker images zerotrust-dns
```

### Run Container
```bash
# Basic run
docker run -d \
  -p 5001:5001 \
  -p 853:853 \
  -p 8443:8443 \
  --name zerotrust-dns \
  zerotrust-dns:latest

# With persistent volumes
docker run -d \
  -p 5001:5001 \
  -p 853:853 \
  -p 8443:8443 \
  -v $(pwd)/data/certs:/opt/zerotrust-dns/certs \
  -v $(pwd)/data/data:/opt/zerotrust-dns/data \
  --name zerotrust-dns \
  zerotrust-dns:latest

# With custom network
docker network create zerotrust-net

docker run -d \
  -p 5001:5001 \
  -p 853:853 \
  -p 8443:8443 \
  --network zerotrust-net \
  --name zerotrust-dns \
  zerotrust-dns:latest
```

### Manage Container
```bash
# View logs
docker logs -f zerotrust-dns

# Execute commands
docker exec -it zerotrust-dns bash

# Check processes
docker exec zerotrust-dns ps aux

# Stop container
docker stop zerotrust-dns

# Start container
docker start zerotrust-dns

# Restart container
docker restart zerotrust-dns

# Remove container
docker rm -f zerotrust-dns
```

## Extracting Binaries from Docker

If you want to use binaries outside of Docker:
```bash
# Create temporary container
docker create --name temp-extract zerotrust-dns:latest

# Extract binaries to local directory
mkdir -p ./extracted-binaries
docker cp temp-extract:/opt/zerotrust-dns/binaries/. ./extracted-binaries/

# Clean up
docker rm temp-extract

# List extracted binaries
ls -lh ./extracted-binaries/
```

Expected output:
```
-rwxr-xr-x ZeroTrust-Client-x64.exe       5.2M
-rwxr-xr-x ZeroTrust-Client-ARM64.exe     5.0M
-rwxr-xr-x ZeroTrust-Client-x86_64        5.3M
-rwxr-xr-x ZeroTrust-Client-arm64         5.1M
-rwxr-xr-x ZeroTrust-Service-x64.exe      5.2M
-rwxr-xr-x ZeroTrust-Service-ARM64.exe    5.0M
-rwxr-xr-x ZeroTrust-Service-x86_64       5.3M
-rwxr-xr-x ZeroTrust-Service-arm64        5.1M
```

## Verifying the Build

### Check Container Health
```bash
# Check if running
docker ps | grep zerotrust-dns

# Check health status
docker inspect zerotrust-dns | jq '.[0].State.Health'

# Test web UI
curl -f http://localhost:5001 || echo "Web UI not accessible"

# Test DNS port
nc -zv localhost 853

# Test proxy port
nc -zv localhost 8443
```

### Check Binaries Inside Container
```bash
# List binaries
docker exec zerotrust-dns ls -lh /opt/zerotrust-dns/binaries/

# Count binaries (should be 8)
docker exec zerotrust-dns bash -c "ls /opt/zerotrust-dns/binaries/ | wc -l"

# Check binary sizes
docker exec zerotrust-dns du -sh /opt/zerotrust-dns/binaries/*
```

### Verify Services
```bash
# Check if all services are running
docker exec zerotrust-dns netstat -tlnp

# Should show:
# Port 5001 (Flask)
# Port 853 (DNS over TLS)
# Port 8443 (TLS Proxy)
```

## Multi-Platform Builds

### Building for Different Architectures

Docker Buildx allows building for multiple platforms:
```bash
# Setup buildx
docker buildx create --name zerotrust-builder --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.go \
  -t zerotrust-dns:latest \
  --push \
  .

# Build for specific platform
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile.go \
  -t zerotrust-dns:arm64 \
  --load \
  .
```

## Volume Management

### Persistent Data

The container uses these directories:
```
/opt/zerotrust-dns/certs/   - CA and server certificates
/opt/zerotrust-dns/data/    - Endpoints, zones, routes
/opt/zerotrust-dns/binaries/ - Compiled endpoint binaries
```

### Backup Volumes
```bash
# Backup certs
docker cp zerotrust-dns:/opt/zerotrust-dns/certs ./backup/certs-$(date +%Y%m%d)

# Backup data
docker cp zerotrust-dns:/opt/zerotrust-dns/data ./backup/data-$(date +%Y%m%d)

# Create tarball
tar -czf zerotrust-backup-$(date +%Y%m%d).tar.gz ./backup/
```

### Restore Volumes
```bash
# Stop container
docker stop zerotrust-dns

# Restore certs
docker cp ./backup/certs-20241205/ zerotrust-dns:/opt/zerotrust-dns/certs

# Restore data
docker cp ./backup/data-20241205/ zerotrust-dns:/opt/zerotrust-dns/data

# Start container
docker start zerotrust-dns
```

## Custom Binary Injection

### Method 1: Volume Mount
```bash
# Build binaries locally
./build-all-binaries.sh

# Mount custom binaries
docker run -d \
  -p 5001:5001 -p 853:853 -p 8443:8443 \
  -v $(pwd)/binaries:/opt/zerotrust-dns/binaries \
  --name zerotrust-dns \
  zerotrust-dns:latest
```

### Method 2: Copy into Running Container
```bash
# Copy binaries to running container
docker cp ./binaries/. zerotrust-dns:/opt/zerotrust-dns/binaries/

# Verify
docker exec zerotrust-dns ls -lh /opt/zerotrust-dns/binaries/

# Restart container
docker restart zerotrust-dns
```

### Method 3: Build Custom Image

Create `Dockerfile.custom`:
```dockerfile
FROM zerotrust-dns:latest

# Copy your pre-built binaries
COPY ./my-binaries/ /opt/zerotrust-dns/binaries/

# Make executable
RUN chmod +x /opt/zerotrust-dns/binaries/ZeroTrust-*
```

Build:
```bash
docker build -f Dockerfile.custom -t zerotrust-dns:custom .
docker run -d -p 5001:5001 -p 853:853 -p 8443:8443 zerotrust-dns:custom
```

## Environment Variables

### Available Variables
```yaml
environment:
  - PYTHONUNBUFFERED=1        # Python logging
  - TZ=UTC                    # Timezone
  - FLASK_ENV=production      # Flask mode
  - LOG_LEVEL=INFO            # Logging level
```

### Custom Configuration
```bash
docker run -d \
  -p 5001:5001 -p 853:853 -p 8443:8443 \
  -e PYTHONUNBUFFERED=1 \
  -e TZ=America/New_York \
  -e LOG_LEVEL=DEBUG \
  --name zerotrust-dns \
  zerotrust-dns:latest
```

## Docker Networking

### Bridge Network (Default)
```bash
# Create network
docker network create zerotrust-net

# Run container on network
docker run -d \
  --network zerotrust-net \
  -p 5001:5001 -p 853:853 -p 8443:8443 \
  --name zerotrust-dns \
  zerotrust-dns:latest
```

### Host Network
```bash
# Use host network (direct port binding)
docker run -d \
  --network host \
  --name zerotrust-dns \
  zerotrust-dns:latest

# Access on host IP directly
# http://YOUR_SERVER_IP:5001
```

### Connect to Other Services
```bash
# Connect to database container
docker network connect zerotrust-net postgres-db

# DNS server can now reach postgres-db by name
```

## Production Configuration

### Resource Limits
```yaml
services:
  zerotrust-dns:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Logging Configuration
```yaml
services:
  zerotrust-dns:
    # ... existing config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Auto-Restart Policy
```yaml
services:
  zerotrust-dns:
    # ... existing config ...
    restart: unless-stopped  # or "always" or "on-failure"
```

### Health Checks
```yaml
services:
  zerotrust-dns:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "python3", "-c", "import socket; s=socket.socket(); s.connect(('127.0.0.1', 5001)); s.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/docker-build.yml`:
```yaml
name: Build Docker Image

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build Docker image
        run: |
          docker build -f Dockerfile.go -t zerotrust-dns:${{ github.sha }} .
      
      - name: Test image
        run: |
          docker run -d -p 5001:5001 -p 853:853 -p 8443:8443 --name test zerotrust-dns:${{ github.sha }}
          sleep 10
          curl -f http://localhost:5001 || exit 1
          docker logs test
          docker stop test
      
      - name: Login to Docker Hub
        if: github.ref == 'refs/heads/main'
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Push to Docker Hub
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag zerotrust-dns:${{ github.sha }} yourusername/zerotrust-dns:latest
          docker push yourusername/zerotrust-dns:latest
```

### GitLab CI

Create `.gitlab-ci.yml`:
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -f Dockerfile.go -t zerotrust-dns:$CI_COMMIT_SHA .
    - docker save zerotrust-dns:$CI_COMMIT_SHA > image.tar
  artifacts:
    paths:
      - image.tar

test:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker load < image.tar
    - docker run -d -p 5001:5001 --name test zerotrust-dns:$CI_COMMIT_SHA
    - sleep 10
    - curl -f http://localhost:5001 || exit 1

deploy:
  stage: deploy
  only:
    - main
  script:
    - docker load < image.tar
    - docker tag zerotrust-dns:$CI_COMMIT_SHA registry.example.com/zerotrust-dns:latest
    - docker push registry.example.com/zerotrust-dns:latest
```

## Troubleshooting

### Build Fails
```bash
# Clean Docker cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -f Dockerfile.go -t zerotrust-dns:latest .

# Check Docker logs
docker logs $(docker ps -aq --filter ancestor=zerotrust-dns:latest)
```

### Container Won't Start
```bash
# Check logs
docker logs zerotrust-dns

# Check if ports are in use
netstat -tlnp | grep -E "5001|853|8443"

# Inspect container
docker inspect zerotrust-dns

# Try running interactively
docker run -it --rm -p 5001:5001 -p 853:853 -p 8443:8443 zerotrust-dns:latest
```

### Binaries Not Found
```bash
# Check if binaries exist in image
docker run --rm zerotrust-dns:latest ls -la /opt/zerotrust-dns/binaries/

# Rebuild image
docker-compose build --no-cache

# Check build logs
docker-compose build 2>&1 | tee build.log
```

### Connection Issues
```bash
# Check if container is running
docker ps | grep zerotrust-dns

# Check network
docker network inspect bridge

# Test from inside container
docker exec zerotrust-dns curl -v http://localhost:5001

# Test from host
curl -v http://localhost:5001
```

### Performance Issues
```bash
# Check resource usage
docker stats zerotrust-dns

# Check container logs for errors
docker logs zerotrust-dns | grep -i error

# Increase resources
docker update --cpus="2" --memory="1g" zerotrust-dns
```

## Best Practices

### 1. Use Multi-Stage Builds
- Smaller final images
- Faster deployment
- Better security (no build tools in production)

### 2. Pin Versions
```dockerfile
FROM python:3.11-slim  # ✓ Good - specific version
# NOT: FROM python:latest
```

### 3. Use .dockerignore
Create `.dockerignore`:
```
.git
.gitignore
*.md
docs/
binaries/
data/
certs/
__pycache__/
*.pyc
```

### 4. Health Checks
Always include health checks for production:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5001"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 5. Logging
Use structured logging:
```python
import logging
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)
```

### 6. Security
```dockerfile
# Don't run as root
RUN useradd -m -u 1000 zerotrust
USER zerotrust

# Scan for vulnerabilities
docker scan zerotrust-dns:latest
```

## Summary

**Recommended Workflow:**

1. **For Production:** Use `Dockerfile.go` - builds everything automatically
2. **For Development:** Use `build-all-binaries.sh` - fast local builds
3. **For CI/CD:** Use GitHub Actions - automated multi-platform builds

**Quick Commands:**
```bash
# Build with Go binaries (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

**Ports:**
- 5001: Web UI
- 853: DNS over TLS
- 8443: TLS Proxy/Router

**Volumes:**
- `./data/certs` - Certificates
- `./data/data` - Endpoints, zones, routes

**Access:**
- Web UI: http://localhost:5001
- Create clients and services via UI
- Download binaries for distribution

---

**Ready to deploy with Docker!** 🐳

All binaries are automatically included in the Docker image and ready for distribution via the web UI!