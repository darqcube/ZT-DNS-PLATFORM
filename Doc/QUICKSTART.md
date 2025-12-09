# ZeroTrust DNS - 5-Minute Quick Start

## What You'll Have in 5 Minutes

✅ DNS server running on port 853 (with mTLS)  
✅ TLS proxy/router on port 8443  
✅ Web UI to manage services and clients  
✅ Everything inside Docker (no dependencies to install)  

## Step 1: Start Server (1 minute)

```bash
# Clone and navigate
git clone <repo-url>
cd ZT-DNS-PLATFORM

# Start with Docker
docker compose up -d

# Verify it's running
docker compose logs -f
```

**Expected output:**
```
✓ Certificates generated
✓ ZeroTrust DNS Platform Running
  Web UI:         http://127.0.0.1:5001
  DNS over TLS:   <your-ip>:853
  Service Proxy:  <your-ip>:8443
```

## Step 2: Create a Service (2 minutes)

1. Open **http://localhost:5001** in browser
2. Click **"Internal Service + DNS Zone"**
3. Fill in:
   - **Service Name:** `My Database`
   - **Service Host:** `10.10.10.50` (your real server IP)
   - **Service Port:** `5432` (PostgreSQL, MySQL, etc.)
   - **Domains:** `db.internal.corp`
4. Click **"Generate Service + Zone"**
5. **Download ZIP**

**What happens internally:**
- DNS resolves `db.internal.corp` → `<your-ip>:8443` (proxy, not real IP!)
- Proxy routes to actual service at `10.10.10.50:5432`

## Step 3: Create a Client (1 minute)

1. Click **"User Client"**
2. Fill in:
   - **Name:** `My Laptop`
   - **Platform:** `Linux x86_64` (or Windows/ARM64)
3. Click **"Generate Client"**
4. **Download ZIP**

## Step 4: Use the Client (1 minute)

**On your client machine:**

```bash
# Extract the ZIP
unzip my-laptop.zip
cd my-laptop

# Run the client
sudo ./ZeroTrust-Client-x86_64

# Expected output:
# ✓ ZeroTrust CLIENT Endpoint Active
# ✓ Local DNS listening on 127.0.0.1:53
```

**Configure your system DNS to 127.0.0.1**

Linux:
```bash
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
```

Windows (PowerShell as Admin):
```powershell
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("127.0.0.1")
```

macOS:
```bash
# System Preferences → Network → DNS → Add 127.0.0.1
```

## Test It Works

```bash
# Test DNS resolution
nslookup db.internal.corp
# Should return: <your-server-ip>

# Connect to service through proxy
psql -h db.internal.corp -p 8443 -U postgres
# (username and password depend on your actual database)
```

## Architecture Flow

```
Your App
   ↓ "connect to db.internal.corp"
Local Client Endpoint (127.0.0.1:53)
   ↓ mTLS to server
ZeroTrust DNS Server (validates client)
   ↓ returns <your-ip>:8443
Your App connects to <your-ip>:8443
   ↓ mTLS to proxy
ZeroTrust Proxy (validates client)
   ↓ reads where to route
Routes to real service (10.10.10.50:5432)
```

**Key point:** Your app never knows the real IP! It only knows the proxy address.

## Stopping

```bash
# Stop the server
docker compose down

# Stop client
sudo pkill ZeroTrust-Client
```

## Next Steps

- 📖 Read **ARCHITECTURE.md** for detailed flow
- 🔧 Read **SETUP.md** for production deployment
- 🐳 Read **DOCKER_BUILD.md** for Docker details

## Troubleshooting

### "Connection refused" on port 5001
```bash
# Check if container is running
docker ps

# Check logs
docker logs zerotrust-dns
```

### DNS not working
```bash
# Verify DNS is running
nslookup db.internal.corp 127.0.0.1 -port 53

# Check client logs
journalctl -u zerotrust-client -f
```

### Certificate errors
```bash
# Certificates are auto-generated
# Check container has them
docker exec zerotrust-dns ls -la /opt/zerotrust-dns/certs/
```

**Done-f go.mod.old go.sum.old* You now have a working ZeroTrust DNS setup with TLS encryption 🎉
