# ZeroTrust DNS Server with Go Endpoint Binaries
# This builds all platform binaries during Docker image creation

FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.23
RUN wget -q https://go.dev/dl/go1.23.4.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz && \
    rm go1.23.4.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV CGO_ENABLED=0

# Set up build directory
WORKDIR /build

# Copy Go source and dependencies
COPY endpoint.go .
COPY go.mod .
COPY go.sum .

# Download Go dependencies
RUN go mod download && go mod verify

# Build Windows x64 binaries
RUN GOOS=windows GOARCH=amd64 go build \
    -ldflags="-s -w -H=windowsgui" \
    -trimpath \
    -o ZeroTrust-Client-x64.exe \
    endpoint.go

RUN cp ZeroTrust-Client-x64.exe ZeroTrust-Service-x64.exe

# Build Windows ARM64 binaries
RUN GOOS=windows GOARCH=arm64 go build \
    -ldflags="-s -w -H=windowsgui" \
    -trimpath \
    -o ZeroTrust-Client-ARM64.exe \
    endpoint.go

RUN cp ZeroTrust-Client-ARM64.exe ZeroTrust-Service-ARM64.exe

# Build Linux x86_64 binaries
RUN GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w" \
    -trimpath \
    -o ZeroTrust-Client-x86_64 \
    endpoint.go

RUN cp ZeroTrust-Client-x86_64 ZeroTrust-Service-x86_64

# Build Linux ARM64 binaries
RUN GOOS=linux GOARCH=arm64 go build \
    -ldflags="-s -w" \
    -trimpath \
    -o ZeroTrust-Client-arm64 \
    endpoint.go

RUN cp ZeroTrust-Client-arm64 ZeroTrust-Service-arm64

# Verify builds
RUN ls -lh /build/ZeroTrust-* && \
    echo "✓ All binaries built successfully"

# ============================================
# Final runtime image
# ============================================
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask==3.0.0 \
    jwcrypto==1.5.6 \
    dnslib==0.9.24 \
    httpx==0.25.2 \
    cryptography==41.0.7

# Create application structure
RUN mkdir -p /opt/zerotrust-dns/certs \
    /opt/zerotrust-dns/data \
    /opt/zerotrust-dns/binaries \
    /app/templates \
    /app/static

WORKDIR /app

# Copy binaries from builder stage
COPY --from=builder /build/ZeroTrust-* /opt/zerotrust-dns/binaries/

# Copy application files
COPY server.py .
COPY templates/ templates/
COPY static/ static/

# Expose ports
# 5001 - Web interface
# 853  - DNS over TLS (mTLS)
# 8443 - Service Proxy/Router (mTLS)
EXPOSE 5001 853 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1', 5001)); s.close()" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run server
CMD ["python3", "server.py"]