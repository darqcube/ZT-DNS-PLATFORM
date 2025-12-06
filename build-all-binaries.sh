#!/bin/bash
set -e

# ZeroTrust DNS - Build All Platform Binaries
# Compiles endpoint.go for Windows and Linux (x64 and ARM64)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/binaries}"

echo "========================================"
echo "ZeroTrust DNS - Binary Builder"
echo "========================================"
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check Go installation
if ! command -v go &> /dev/null; then
    echo "❌ ERROR: Go is not installed!"
    echo ""
    echo "Install Go from: https://go.dev/dl/"
    echo ""
    echo "Quick install (Linux):"
    echo "  wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz"
    echo "  sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz"
    echo "  export PATH=\$PATH:/usr/local/go/bin"
    exit 1
fi

GO_VERSION=$(go version)
echo "✓ Found: $GO_VERSION"
echo ""

# Check if endpoint.go exists
if [ ! -f "$SCRIPT_DIR/endpoint.go" ]; then
    echo "❌ ERROR: endpoint.go not found"
    echo "Expected location: $SCRIPT_DIR/endpoint.go"
    exit 1
fi

echo "✓ Found: endpoint.go"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Change to script directory for Go build
cd "$SCRIPT_DIR"

# Initialize Go module if needed
if [ ! -f "go.mod" ]; then
    echo "Initializing Go module..."
    go mod init zerotrust-endpoint
    go get github.com/golang-jwt/jwt/v5
    go mod tidy
    echo ""
fi

# Ensure dependencies are downloaded
echo "Downloading Go dependencies..."
go mod download
go mod verify
echo ""

echo "Building binaries for all platforms..."
echo "--------------------------------------"
echo ""

# Build matrix
declare -A PLATFORMS=(
    ["windows/amd64"]="ZeroTrust-Client-x64.exe"
    ["windows/arm64"]="ZeroTrust-Client-ARM64.exe"
    ["linux/amd64"]="ZeroTrust-Client-x86_64"
    ["linux/arm64"]="ZeroTrust-Client-arm64"
)

# Build each platform
for platform in "${!PLATFORMS[@]}"; do
    IFS='/' read -r GOOS GOARCH <<< "$platform"
    CLIENT_OUTPUT="${PLATFORMS[$platform]}"
    SERVICE_OUTPUT="${CLIENT_OUTPUT/Client/Service}"
    
    echo -n "Building $CLIENT_OUTPUT ... "
    
    # Determine build flags
    if [[ "$GOOS" == "windows" ]]; then
        LDFLAGS="-s -w -H=windowsgui"
    else
        LDFLAGS="-s -w"
    fi
    
    # Build client binary
    GOOS=$GOOS GOARCH=$GOARCH CGO_ENABLED=0 go build \
        -ldflags="$LDFLAGS" \
        -trimpath \
        -o "$OUTPUT_DIR/$CLIENT_OUTPUT" \
        endpoint.go
    
    if [ $? -eq 0 ]; then
        SIZE=$(du -h "$OUTPUT_DIR/$CLIENT_OUTPUT" | cut -f1)
        echo "✓ ($SIZE)"
        
        # Create service binary (copy of client)
        echo -n "Creating $SERVICE_OUTPUT ... "
        cp "$OUTPUT_DIR/$CLIENT_OUTPUT" "$OUTPUT_DIR/$SERVICE_OUTPUT"
        echo "✓"
    else
        echo "❌ FAILED"
        exit 1
    fi
    
    echo ""
done

# Make Linux binaries executable
chmod +x "$OUTPUT_DIR"/ZeroTrust-*-x86_64 2>/dev/null || true
chmod +x "$OUTPUT_DIR"/ZeroTrust-*-arm64 2>/dev/null || true

echo "========================================"
echo "Build Summary"
echo "========================================"
echo ""
ls -lh "$OUTPUT_DIR"/ZeroTrust-* | awk '{printf "%-40s %8s\n", $9, $5}'
echo ""
echo "✓ All binaries built successfully!"
echo ""
echo "Next steps:"
echo "  1. Copy binaries to server: cp $OUTPUT_DIR/* /opt/zerotrust-dns/binaries/"
echo "  2. Or use with Docker: docker-compose up -d"
echo "  3. Start server: python3 server.py"
echo ""