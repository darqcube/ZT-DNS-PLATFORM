# ZeroTrust DNS - Binary Compilation Guide

## Overview

The ZeroTrust DNS platform requires pre-compiled endpoint binaries for distribution to clients and services. The server **does not compile binaries on-the-fly** - they must be built beforehand and placed in `/opt/zerotrust-dns/binaries/`.

## Required Binaries

### Client Binaries
- `ZeroTrust-Client-x64.exe` (Windows x64)
- `ZeroTrust-Client-ARM64.exe` (Windows ARM64)
- `ZeroTrust-Client-x86_64` (Linux x64)
- `ZeroTrust-Client-arm64` (Linux ARM64)

### Service Binaries
- `ZeroTrust-Service-x64.exe` (Windows x64)
- `ZeroTrust-Service-ARM64.exe` (Windows ARM64)
- `ZeroTrust-Service-x86_64` (Linux x64)
- `ZeroTrust-Service-arm64` (Linux ARM64)

**Note:** Service binaries are copies of client binaries since they use the same code. The `type` field in the JWT configuration determines behavior.

## Quick Start - Go Version (Recommended)

### 1. Install Go

**Linux:**
```bash
# Download Go
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz

# Extract
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz

# Add to PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Verify
go version
```

**macOS:**
```bash
# Using Homebrew
brew install go

# Or download from https://go.dev/dl/

# Verify
go version
```

**Windows:**
```powershell
# Download installer from https://go.dev/dl/
# Run installer
# Verify in new PowerShell window
go version
```

### 2. Build All Binaries

**Linux/macOS:**
```bash
# Make script executable
chmod +x build-all-binaries.sh

# Build for all platforms
./build-all-binaries.sh

# Or specify custom output directory
./build-all-binaries.sh /path/to/output
```

**Windows:**
```cmd
# Run batch file
build-all-binaries.bat

# Or double-click the file
```

### 3. Verify Build
```bash
# Check binaries directory
ls -lh binaries/

# Expected output:
# ZeroTrust-Client-x64.exe       (5.2M)
# ZeroTrust-Client-ARM64.exe     (5.0M)
# ZeroTrust-Client-x86_64        (5.3M)
# ZeroTrust-Client-arm64         (5.1M)
# ZeroTrust-Service-x64.exe      (5.2M)
# ZeroTrust-Service-ARM64.exe    (5.0M)
# ZeroTrust-Service-x86_64       (5.3M)
# ZeroTrust-Service-arm64        (5.1M)

# Count files (should be 8)
ls binaries/ | wc -l
```

### 4. Copy to Server
```bash
# Copy to server binaries directory
sudo cp binaries/* /opt/zerotrust-dns/binaries/

# Verify on server
ls -lh /opt/zerotrust-dns/binaries/
```

## Detailed Build Instructions

### Go Build Process

The build process uses Go's cross-compilation feature to build for all platforms from a single machine.

**Build Command Structure:**
```bash
GOOS=<os> GOARCH=<arch> go build \
  -ldflags="<flags>" \
  -trimpath \
  -o <output> \
  endpoint.go
```

**Build Flags Explained:**

| Flag | Purpose |
|------|---------|
| `GOOS` | Target operating system (windows, linux, darwin) |
| `GOARCH` | Target architecture (amd64, arm64) |
| `CGO_ENABLED=0` | Disable C dependencies (static linking) |
| `-ldflags="-s -w"` | Strip debug info (reduces size ~30%) |
| `-ldflags="-H=windowsgui"` | Hide console window on Windows |
| `-trimpath` | Remove absolute paths from binary |
| `-o` | Output file name |

### Manual Platform-Specific Builds

#### Windows x64
```bash
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build \
  -ldflags="-s -w -H=windowsgui" \
  -trimpath \
  -o ZeroTrust-Client-x64.exe \
  endpoint.go

cp ZeroTrust-Client-x64.exe ZeroTrust-Service-x64.exe
```

#### Windows ARM64
```bash
GOOS=windows GOARCH=arm64 CGO_ENABLED=0 go build \
  -ldflags="-s -w -H=windowsgui" \
  -trimpath \
  -o ZeroTrust-Client-ARM64.exe \
  endpoint.go

cp ZeroTrust-Client-ARM64.exe ZeroTrust-Service-ARM64.exe
```

#### Linux x64
```bash
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build \
  -ldflags="-s -w" \
  -trimpath \
  -o ZeroTrust-Client-x86_64 \
  endpoint.go

cp ZeroTrust-Client-x86_64 ZeroTrust-Service-x86_64
chmod +x ZeroTrust-Client-x86_64 ZeroTrust-Service-x86_64
```

#### Linux ARM64
```bash
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build \
  -ldflags="-s -w" \
  -trimpath \
  -o ZeroTrust-Client-arm64 \
  endpoint.go

cp ZeroTrust-Client-arm64 ZeroTrust-Service-arm64
chmod +x ZeroTrust-Client-arm64 ZeroTrust-Service-arm64
```

## Python Version (Alternative)

### Why Python?

**Advantages:**
- ✅ No Go installation required
- ✅ Easier to debug and customize
- ✅ Familiar to Python developers

**Disadvantages:**
- ❌ Larger file size (~15-30MB vs ~5-8MB for Go)
- ❌ Cannot cross-compile (must build on target platform)
- ❌ Slower startup time
- ❌ Requires Python runtime or PyInstaller

### Building Python Binaries

#### Prerequisites
```bash
# Install PyInstaller
pip3 install pyinstaller

# Install dependencies
pip3 install -r requirements.txt
```

#### Linux x64 Build
```bash
# Must run on Linux x64 machine
pyinstaller --onefile \
  --name ZeroTrust-Client-x86_64 \
  --strip \
  --clean \
  endpoint.py

cp dist/ZeroTrust-Client-x86_64 binaries/
cp binaries/ZeroTrust-Client-x86_64 binaries/ZeroTrust-Service-x86_64
chmod +x binaries/ZeroTrust-*-x86_64
```

#### Linux ARM64 Build
```bash
# Must run on Linux ARM64 machine (Raspberry Pi, AWS Graviton, etc.)
pyinstaller --onefile \
  --name ZeroTrust-Client-arm64 \
  --strip \
  --clean \
  endpoint.py

cp dist/ZeroTrust-Client-arm64 binaries/
cp binaries/ZeroTrust-Client-arm64 binaries/ZeroTrust-Service-arm64
chmod +x binaries/ZeroTrust-*-arm64
```

#### Windows x64 Build
```powershell
# Must run on Windows x64 machine
pyinstaller --onefile `
  --name ZeroTrust-Client-x64.exe `
  --noconsole `
  --clean `
  endpoint.py

Copy-Item dist\ZeroTrust-Client-x64.exe binaries\
Copy-Item binaries\ZeroTrust-Client-x64.exe binaries\ZeroTrust-Service-x64.exe
```

#### Windows ARM64 Build
```powershell
# Must run on Windows ARM64 machine
pyinstaller --onefile `
  --name ZeroTrust-Client-ARM64.exe `
  --noconsole `
  --clean `
  endpoint.py

Copy-Item dist\ZeroTrust-Client-ARM64.exe binaries\
Copy-Item binaries\ZeroTrust-Client-ARM64.exe binaries\ZeroTrust-Service-ARM64.exe
```

### Python Build Script

Save as `build-python-binaries.sh`:
```bash
#!/bin/bash
# Build Python endpoint for current platform

set -e

echo "Building Python endpoint for current platform..."

# Detect platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64)
        ARCH_SUFFIX="x86_64"
        ;;
    aarch64|arm64)
        ARCH_SUFFIX="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    linux*)
        EXT=""
        OUTPUT="ZeroTrust-Client-${ARCH_SUFFIX}"
        ;;
    darwin*)
        EXT=""
        OUTPUT="ZeroTrust-Client-${ARCH_SUFFIX}"
        echo "Building on macOS (will create macOS binary)"
        ;;
    mingw*|msys*|cygwin*)
        EXT=".exe"
        ARCH_NAME="x64"
        if [ "$ARCH_SUFFIX" = "arm64" ]; then
            ARCH_NAME="ARM64"
        fi
        OUTPUT="ZeroTrust-Client-${ARCH_NAME}.exe"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

echo "Building: $OUTPUT"

pyinstaller --onefile \
    --name "$OUTPUT" \
    --strip \
    --clean \
    endpoint.py

mkdir -p binaries
cp "dist/$OUTPUT" "binaries/"

# Create service binary
SERVICE_OUTPUT="${OUTPUT/Client/Service}"
cp "binaries/$OUTPUT" "binaries/$SERVICE_OUTPUT"

echo "✓ Built: $OUTPUT"
echo "✓ Created: $SERVICE_OUTPUT"
echo ""
echo "Note: Python binaries cannot be cross-compiled."
echo "To build for other platforms, run this script on those platforms."
```

Make executable:
```bash
chmod +x build-python-binaries.sh
./build-python-binaries.sh
```

## Docker-Based Build

### Using Docker to Build Go Binaries

**Advantages:**
- ✅ No local Go installation needed
- ✅ Consistent build environment
- ✅ All platforms built at once

**Build with Docker:**
```bash
# Build Docker image (includes binary compilation)
docker build -f Dockerfile.go -t zerotrust-dns:latest .

# Extract binaries
docker create --name temp zerotrust-dns:latest
docker cp temp:/opt/zerotrust-dns/binaries/. ./binaries/
docker rm temp

# Verify
ls -lh binaries/
```

## Placing Binaries in Server

### Method 1: Direct Copy (Manual Server)
```bash
# Copy to server binaries directory
sudo mkdir -p /opt/zerotrust-dns/binaries
sudo cp binaries/* /opt/zerotrust-dns/binaries/

# Set permissions
sudo chmod +x /opt/zerotrust-dns/binaries/ZeroTrust-*

# Verify
ls -lh /opt/zerotrust-dns/binaries/
```

### Method 2: Docker Volume Mount
```bash
# Place binaries in local directory
mkdir -p ./custom-binaries
cp binaries/* ./custom-binaries/

# Update docker-compose.yml
volumes:
  - ./custom-binaries:/opt/zerotrust-dns/binaries

# Start container
docker-compose up -d
```

### Method 3: Copy into Running Container
```bash
# Copy binaries to running container
docker cp binaries/. zerotrust-dns:/opt/zerotrust-dns/binaries/

# Verify
docker exec zerotrust-dns ls -lh /opt/zerotrust-dns/binaries/

# Restart container
docker restart zerotrust-dns
```

### Method 4: Build Custom Docker Image

Create `Dockerfile.custom`:
```dockerfile
FROM zerotrust-dns:latest

# Copy your pre-built binaries
COPY ./binaries/ /opt/zerotrust-dns/binaries/

# Make executable
RUN chmod +x /opt/zerotrust-dns/binaries/ZeroTrust-*
```

Build:
```bash
docker build -f Dockerfile.custom -t zerotrust-dns:custom .
docker run -d -p 5001:5001 -p 853:853 -p 8443:8443 zerotrust-dns:custom
```

## Binary Size Optimization

### Go Binary Sizes

**Without optimization:**
```
~15-20 MB per binary
```

**With `-ldflags="-s -w"`:**
```
~5-8 MB per binary (30-40% reduction)
```

**With UPX compression:**
```bash
# Install UPX
sudo apt install upx-ucl  # Linux
brew install upx          # macOS

# Compress binaries
upx --best --lzma binaries/ZeroTrust-*

# Result: ~2-4 MB per binary (50-60% reduction)
# Note: May cause antivirus false positives
```

### Python Binary Sizes

**PyInstaller default:**
```
~15-30 MB per binary (includes Python runtime)
```

**With optimization:**
```bash
pyinstaller --onefile \
  --strip \
  --noupx \
  --exclude-module tkinter \
  --exclude-module matplotlib \
  endpoint.py

# Result: ~12-20 MB per binary (20-30% reduction)
```

## Verification Checklist

After building binaries, verify:

### File Existence
```bash
# Check all 8 files exist
ls binaries/ | wc -l  # Should output: 8

# List all files
ls -1 binaries/
```

### File Sizes
```bash
# Go binaries: 5-8 MB
# Python binaries: 15-30 MB
du -h binaries/*
```

### File Types
```bash
# Check Linux binaries
file binaries/ZeroTrust-Client-x86_64
# Should output: ELF 64-bit LSB executable

file binaries/ZeroTrust-Client-arm64
# Should output: ELF 64-bit LSB executable

# Check Windows binaries
file binaries/ZeroTrust-Client-x64.exe
# Should output: PE32+ executable (console) x86-64
```

### Executable Permissions (Linux)
```bash
# Check permissions
ls -l binaries/ZeroTrust-*-x86_64
ls -l binaries/ZeroTrust-*-arm64

# Should show: -rwxr-xr-x (executable)
```

### Test Execution
```bash
# Test Linux binary (displays help/error without config)
./binaries/ZeroTrust-Client-x86_64
# Should output error about missing config files (expected)

# Test Windows binary with Wine (Linux)
wine binaries/ZeroTrust-Client-x64.exe
# Should output error about missing config files (expected)
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/build-binaries.yml`:
```yaml
name: Build Binaries

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-go:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-go@v4
        with:
          go-version: '1.23'
      
      - name: Build all binaries
        run: |
          chmod +x build-all-binaries.sh
          ./build-all-binaries.sh
      
      - name: Upload binaries
        uses: actions/upload-artifact@v3
        with:
          name: binaries
          path: binaries/
      
      - name: Create release
        if: github.ref == 'refs/heads/main'
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ github.run_number }}
          files: binaries/*
```

### GitLab CI

Create `.gitlab-ci.yml`:
```yaml
stages:
  - build
  - upload

build-binaries:
  stage: build
  image: golang:1.23
  script:
    - chmod +x build-all-binaries.sh
    - ./build-all-binaries.sh
  artifacts:
    paths:
      - binaries/
    expire_in: 1 week

upload-binaries:
  stage: upload
  only:
    - main
  script:
    - curl --upload-file binaries/* https://your-artifact-server/
```

## Troubleshooting

### "go: command not found"

**Solution:**
```bash
# Check if Go is installed
which go

# If not found, install Go
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Verify
go version
```

### "Permission denied" on port 53

The compiled endpoint tries to bind to port 53, which requires elevated privileges.

**Solution:**
```bash
# Linux: Grant capability
sudo setcap cap_net_bind_service=+ep binaries/ZeroTrust-Client-x86_64

# Or run as root
sudo ./ZeroTrust-Client-x86_64

# Endpoint will fall back to port 5353 if 53 is unavailable
```

### Go build fails with "missing go.sum entry"

**Solution:**
```bash
# Clean and reinitialize
rm go.mod go.sum

# Rebuild
./build-all-binaries.sh
```

### PyInstaller "command not found"

**Solution:**
```bash
# Install PyInstaller
pip3 install pyinstaller

# Verify
pyinstaller --version
```

### Binary too large (Go)

The build script uses `-ldflags="-s -w"` to strip debug info.

**Further optimization:**
```bash
# Use UPX compression
upx --best --lzma binaries/ZeroTrust-*

# Result: 50-60% size reduction
# Warning: May trigger antivirus false positives
```

### Binary doesn't run on target platform

**Check architecture:**
```bash
# On target machine
uname -m

# x86_64 → Use x86_64 binary
# aarch64 → Use arm64 binary
# i686 → Not supported (need x86 32-bit build)
```

### Windows Defender flags binary

Go binaries with stripped symbols may trigger false positives.

**Solutions:**
1. Don't use UPX compression
2. Sign binaries with code signing certificate
3. Submit false positive report to Microsoft
4. Add exception in Windows Defender

## Cross-Platform Build Matrix

| Build Platform | Can Build For |
|----------------|---------------|
| **Linux x64** | ✅ All platforms (Go cross-compilation) |
| **macOS** | ✅ All platforms (Go cross-compilation) |
| **Windows** | ✅ All platforms (Go cross-compilation) |
| **Linux ARM64** | ✅ All platforms (Go cross-compilation) |

**Python (PyInstaller):**
| Build Platform | Can Build For |
|----------------|---------------|
| **Linux x64** | ❌ Linux x64 only |
| **Linux ARM64** | ❌ Linux ARM64 only |
| **Windows x64** | ❌ Windows x64 only |
| **Windows ARM64** | ❌ Windows ARM64 only |

**Recommendation:** Use Go for production deployments due to cross-compilation support.

## Summary

### Quick Commands

**Build with Go (recommended):**
```bash
./build-all-binaries.sh
ls -lh binaries/
```

**Build with Python (current platform only):**
```bash
./build-python-binaries.sh
ls -lh binaries/
```

**Build with Docker:**
```bash
docker build -f Dockerfile.go -t zerotrust-dns .
docker cp $(docker create zerotrust-dns):/opt/zerotrust-dns/binaries/. ./binaries/
```

**Deploy to server:**
```bash
sudo cp binaries/* /opt/zerotrust-dns/binaries/
sudo chmod +x /opt/zerotrust-dns/binaries/ZeroTrust-*
```

### File Checklist

After building, you should have:
- [x] ZeroTrust-Client-x64.exe (Windows x64)
- [x] ZeroTrust-Client-ARM64.exe (Windows ARM64)
- [x] ZeroTrust-Client-x86_64 (Linux x64)
- [x] ZeroTrust-Client-arm64 (Linux ARM64)
- [x] ZeroTrust-Service-x64.exe (Windows x64)
- [x] ZeroTrust-Service-ARM64.exe (Windows ARM64)
- [x] ZeroTrust-Service-x86_64 (Linux x64)
- [x] ZeroTrust-Service-arm64 (Linux ARM64)

**Total:** 8 binaries ready for distribution! 🎉

---

For deployment instructions, see **SETUP.md** and **QUICKSTART.md**.