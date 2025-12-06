# ZeroTrust DNS Platform - Complete Production Level Setup Guide

## Prerequisites

### Server Requirements
- Linux/Unix system (Ubuntu 20.04+ recommended)
- Python 3.8+
- OpenSSL
- Root access (for ports 853, 8443)
- 2GB RAM minimum
- 10GB disk space

### For Binary Compilation
- **Go version:** Go 1.19+ (recommended for building binaries)
- **Python version:** Python 3.8+ with PyInstaller (alternative)

### Network Requirements
- Public IP or accessible server
- Ports available: 5001 (Web UI), 853 (DNS), 8443 (Proxy)
- Firewall access for clients

## Step-by-Step Installation

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip openssl git wget

# Install Go (for binary compilation)
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
go version
```

#### CentOS/RHEL
```bash
# Update system
sudo yum update -y

# Install required packages
sudo yum install -y python3 python3-pip openssl git wget

# Install Go
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
```

### 2. Install Python Dependencies
```bash
# Create project directory
sudo mkdir -p /opt/zerotrust-dns
cd /opt/zerotrust-dns

# Clone or copy project files here
# (Copy all files from your repository)

# Install Python dependencies
pip3 install -r requirements.txt

# Verify installation
python3 -c "import flask, jwcrypto, dnslib, httpx; print('✓ All dependencies installed')"
```

### 3. Set Up Directory Structure
```bash
# Create necessary directories
sudo mkdir -p /opt/zerotrust-dns/{certs,data,binaries,templates,static}

# Set permissions
sudo chown -R $USER:$USER /opt/zerotrust-dns

# Verify structure
tree -L 1 /opt/zerotrust-dns
```

Expected structure:
```
/opt/zerotrust-dns/
├── server.py
├── endpoint.go
├── endpoint.py
├── go.mod
├── go.sum
├── requirements.txt
├── build-all-binaries.sh
├── templates/
├── static/
├── certs/          (auto-generated)
├── data/           (auto-generated)
└── binaries/       (after build)
```

### 4. Compile Endpoint Binaries
```bash
cd /opt/zerotrust-dns

# Make build script executable
chmod +x build-all-binaries.sh

# Build all platform binaries (takes ~1-2 minutes)
./build-all-binaries.sh

# Verify binaries were created
ls -lh binaries/
```

Expected output:
```
ZeroTrust-Client-x64.exe       (5.2M)
ZeroTrust-Client-ARM64.exe     (5.0M)
ZeroTrust-Client-x86_64        (5.3M)
ZeroTrust-Client-arm64         (5.1M)
ZeroTrust-Service-x64.exe      (5.2M)
ZeroTrust-Service-ARM64.exe    (5.0M)
ZeroTrust-Service-x86_64       (5.3M)
ZeroTrust-Service-arm64        (5.1M)
```

### 5. Start the Server

#### Option A: Manual Start (for testing)
```bash
cd /opt/zerotrust-dns

# Start server (will auto-generate CA certificates on first run)
sudo python3 server.py
```

Expected output:
```
Generating CA and server certificates...
✓ Certificates generated
ZeroTrust DNS Server detected IP: 203.0.113.50
  - DNS over TLS: 203.0.113.50:853
  - Service Proxy: 203.0.113.50:8443
✓ DNS over TLS server started on port 853
✓ TLS Proxy/Router started on port 8443

============================================================
✓ ZeroTrust DNS Platform Running
============================================================
  Web UI:         http://127.0.0.1:5001
  DNS over TLS:   203.0.113.50:853
  Service Proxy:  203.0.113.50:8443
============================================================
```

#### Option B: Systemd Service (for production)

Create service file:
```bash
sudo nano /etc/systemd/system/zerotrust-dns.service
```

Add content:
```ini
[Unit]
Description=ZeroTrust DNS Server with TLS Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/zerotrust-dns
ExecStart=/usr/bin/python3 /opt/zerotrust-dns/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable zerotrust-dns

# Start service
sudo systemctl start zerotrust-dns

# Check status
sudo systemctl status zerotrust-dns

# View logs
sudo journalctl -u zerotrust-dns -f
```

### 6. Configure Firewall
```bash
# Allow DNS over TLS (port 853)
sudo ufw allow 853/tcp comment 'ZeroTrust DNS over TLS'

# Allow TLS Proxy (port 8443)
sudo ufw allow 8443/tcp comment 'ZeroTrust TLS Proxy'

# Allow Web UI (port 5001) - Optional for remote access
sudo ufw allow 5001/tcp comment 'ZeroTrust Web UI'

# Enable firewall if not already enabled
sudo ufw enable

# Verify rules
sudo ufw status numbered
```

### 7. Access Web Interface

Open browser to: `http://YOUR-SERVER-IP:5001`

You should see:
- ✅ Client creation form
- ✅ Service creation form
- ✅ Empty endpoints table
- ✅ No binary warnings (if binaries built successfully)

## Creating Your First Client

### Via Web UI

1. Navigate to `http://YOUR-SERVER:5001`
2. Fill in **User Client** form:
   - **Name:** `Admin Laptop`
   - **Platform:** `Linux x86_64` (or your platform)
3. Click **Generate Client**
4. Download ZIP package
5. Extract on client machine

### Client Package Contents
```
ZeroTrust-Client-x86_64     ← The endpoint binary
endpoint.crt                ← Client certificate
endpoint.key                ← Client private key
ca.crt                      ← CA certificate
config.zt                   ← JWT-signed configuration
README.txt                  ← Instructions
```

### Deploy Client

**On Linux:**
```bash
# Extract package
unzip c1234abcd5678-client.zip -d ~/zerotrust-client
cd ~/zerotrust-client

# Make executable
chmod +x ZeroTrust-Client-x86_64

# Run as root (for port 53)
sudo ./ZeroTrust-Client-x86_64

# Expected output:
# 2024/12/05 10:30:45 ZeroTrust CLIENT Endpoint Active → 203.0.113.50:853
# 2024/12/05 10:30:45 Local DNS listening on 127.0.0.1:53
```

**On Windows:**
```powershell
# Extract ZIP
# Right-click ZeroTrust-Client-x64.exe → Run as Administrator

# Expected output in console:
# 2024/12/05 10:30:45 ZeroTrust CLIENT Endpoint Active → 203.0.113.50:853
# 2024/12/05 10:30:45 Local DNS listening on 127.0.0.1:53
```

### Configure System DNS

**Linux:**
```bash
# Edit resolv.conf
sudo nano /etc/resolv.conf

# Add this line at the top
nameserver 127.0.0.1

# Save and exit

# Test DNS
dig google.com @127.0.0.1
nslookup google.com 127.0.0.1
```

**Windows:**
1. Open Network Settings
2. Change Adapter Options
3. Right-click network → Properties
4. IPv4 → Properties
5. Set DNS: `127.0.0.1`
6. Click OK

**macOS:**
```bash
# System Preferences → Network → Advanced → DNS
# Add: 127.0.0.1
# Click OK
```

### Test Client Connection
```bash
# Test public DNS (should work)
nslookup google.com 127.0.0.1

# Expected: Google's IP addresses
```

## Creating Your First Service

### Via Web UI

1. Navigate to `http://YOUR-SERVER:5001`
2. Fill in **Internal Service + DNS Zone** form:
   - **Service Name:** `PostgreSQL Production`
   - **Service Host:** `10.10.10.50` (actual service server IP)
   - **Service Port:** `5432`
   - **Domains:** `db.internal.corp, postgres.internal.corp`
   - **DNS Records:**
```
     @ A 10.10.10.50
     replica A 10.10.10.51
     * A 10.10.10.50
```
   - **Platform:** `Linux x86_64`
3. Click **Generate Service + Zone**
4. Download ZIP package

### Service Package Contents
```
ZeroTrust-Service-x86_64    ← The endpoint binary
endpoint.crt                ← Service certificate
endpoint.key                ← Service private key
ca.crt                      ← CA certificate
config.zt                   ← JWT-signed configuration
README.txt                  ← Instructions
```

### Deploy Service

**On service server (10.10.10.50):**
```bash
# Extract package
unzip s1234abcd5678-service.zip -d ~/zerotrust-service
cd ~/zerotrust-service

# Make executable
chmod +x ZeroTrust-Service-x86_64

# Run as root
sudo ./ZeroTrust-Service-x86_64 &

# Expected output:
# 2024/12/05 10:35:00 ZeroTrust SERVICE Endpoint Active → 203.0.113.50:853
# 2024/12/05 10:35:00 Authorized domains: [db.internal.corp postgres.internal.corp]
# 2024/12/05 10:35:00 Local DNS listening on 127.0.0.1:53
```

### Understanding the Architecture

**What just happened:**
1. **DNS Server** created zone: `db.internal.corp → 203.0.113.50` (proxy IP!)
2. **Routing Table** created: `db.internal.corp → 10.10.10.50:5432` (real service)
3. **Client** will query DNS, get proxy IP
4. **Client** will connect to proxy
5. **Proxy** will route to real service
6. **Result:** Client never sees 10.10.10.50!

## Testing the Complete Setup

### Test 1: DNS Resolution

**On client machine:**
```bash
# Test private domain resolution
nslookup db.internal.corp 127.0.0.1

# Expected output:
# Server:  127.0.0.1
# Address: 127.0.0.1#53
# 
# Name:    db.internal.corp
# Address: 203.0.113.50    ← Proxy IP, not 10.10.10.50!
```

### Test 2: Public DNS Still Works
```bash
nslookup google.com 127.0.0.1

# Should return Google's IP (forwarded to 1.1.1.1)
```

### Test 3: Service Connection

**On client machine:**
```bash
# Test PostgreSQL connection
psql "host=db.internal.corp port=8443 user=admin dbname=production"

# Connection flow:
# Client → 203.0.113.50:8443 (proxy) → 10.10.10.50:5432 (service)
```

### Test 4: HTTP Service
```bash
# If you have a web service
curl https://api.internal.corp:8443/health

# Connection flow:
# Client → Proxy (validates cert) → Real API server
```

## Advanced Configuration

### 1. Multiple Services

Create multiple services with different domains:
```
Service 1: PostgreSQL
- Host: 10.10.10.50:5432
- Domains: db.internal.corp

Service 2: Redis
- Host: 10.10.10.60:6379
- Domains: cache.internal.corp

Service 3: API
- Host: 10.20.30.40:443
- Domains: api.internal.corp
```

Each service gets its own routing entry. Clients can access all authorized services.

### 2. Client Authorization

To give a client access to specific services:

**Option A: Via Web UI**
1. Recreate client with same name
2. System will issue new certificate

**Option B: Manual Zone Editing**
```bash
# Edit zones file
sudo nano /opt/zerotrust-dns/data/zones.json

# Add client CN to allowed_endpoints array
{
  "db.internal.corp": {
    "records": {...},
    "allowed_endpoints": ["c1234abcd", "c5678efgh"],  ← Add client CN
    "service_cn": "s1234abcd"
  }
}

# Restart server
sudo systemctl restart zerotrust-dns
```

### 3. Service Migration

To move a service to a new server:
```bash
# Edit routing table
sudo nano /opt/zerotrust-dns/data/routes.json

# Update host/port
{
  "s1234abcd": {
    "host": "10.10.10.99",  ← Changed from 10.10.10.50
    "port": 5432,
    "domains": ["db.internal.corp"],
    "name": "PostgreSQL Production"
  }
}

# Restart server
sudo systemctl restart zerotrust-dns

# Clients don't need any updates!
```

### 4. Custom DNS Records

Edit service form to add custom records:
```
# Multiple A records
@ A 10.10.10.50
replica A 10.10.10.51
backup A 10.10.10.52

# CNAME records
www CNAME db.internal.corp
admin CNAME db.internal.corp

# Wildcard
* A 10.10.10.50
```

### 5. Certificate Expiry

Default certificate lifetime: 10 years (3650 days)

To change, edit `server.py`:
```python
# Line ~115 and ~180
"-days", "3650",  # Change to desired days
```

Then regenerate certificates:
```bash
# Delete existing CA
sudo rm /opt/zerotrust-dns/certs/ca.*

# Restart server (will regenerate)
sudo systemctl restart zerotrust-dns
```

## Backup Strategy

### What to Backup
```bash
# Critical files
/opt/zerotrust-dns/certs/ca.key     ← CA private key (CRITICAL!)
/opt/zerotrust-dns/certs/ca.crt     ← CA certificate
/opt/zerotrust-dns/certs/server.key ← Server private key
/opt/zerotrust-dns/certs/server.crt ← Server certificate
/opt/zerotrust-dns/data/endpoints.json  ← Endpoint database
/opt/zerotrust-dns/data/zones.json      ← DNS zones
/opt/zerotrust-dns/data/routes.json     ← Routing table
```

### Backup Script
```bash
#!/bin/bash
# backup-zerotrust.sh

BACKUP_DIR="/backup/zerotrust-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical data
sudo cp -r /opt/zerotrust-dns/certs "$BACKUP_DIR/"
sudo cp -r /opt/zerotrust-dns/data "$BACKUP_DIR/"
sudo cp /opt/zerotrust-dns/server.py "$BACKUP_DIR/"

# Create tarball
tar -czf "$BACKUP_DIR.tar.gz" -C /backup "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "✓ Backup created: $BACKUP_DIR.tar.gz"
```

### Restore Procedure
```bash
# Extract backup
tar -xzf zerotrust-20241205-120000.tar.gz -C /tmp/

# Stop server
sudo systemctl stop zerotrust-dns

# Restore files
sudo cp -r /tmp/zerotrust-20241205-120000/certs/* /opt/zerotrust-dns/certs/
sudo cp -r /tmp/zerotrust-20241205-120000/data/* /opt/zerotrust-dns/data/

# Start server
sudo systemctl start zerotrust-dns
```

## Monitoring & Logging

### View Live Logs
```bash
# Systemd logs
sudo journalctl -u zerotrust-dns -f

# Or if running manually
tail -f /var/log/zerotrust-dns.log
```

### Log Rotation

Create `/etc/logrotate.d/zerotrust-dns`:
```
/var/log/zerotrust-dns.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
```

### Monitoring Endpoints
```bash
# List all endpoints
cat /opt/zerotrust-dns/data/endpoints.json | jq .

# List all zones
cat /opt/zerotrust-dns/data/zones.json | jq .

# List all routes
cat /opt/zerotrust-dns/data/routes.json | jq .

# Check active connections
sudo netstat -an | grep -E "853|8443" | grep ESTABLISHED
```

### Health Checks
```bash
# Check if server is running
curl -f http://localhost:5001 || echo "Server down!"

# Check DNS port
nc -zv localhost 853

# Check proxy port
nc -zv localhost 8443

# Full health check script
#!/bin/bash
curl -f http://localhost:5001 > /dev/null 2>&1 || exit 1
nc -zv localhost 853 > /dev/null 2>&1 || exit 1
nc -zv localhost 8443 > /dev/null 2>&1 || exit 1
echo "✓ All services healthy"
```

## Performance Tuning

### System Limits
```bash
# Increase file descriptors
sudo nano /etc/security/limits.conf

# Add:
* soft nofile 65536
* hard nofile 65536

# Apply immediately
ulimit -n 65536
```

### Python Optimization
```bash
# Use production WSGI server (optional)
pip3 install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 server:app
```

### Kernel Tuning
```bash
# Edit sysctl
sudo nano /etc/sysctl.conf

# Add:
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65000

# Apply
sudo sysctl -p
```

## Security Hardening

### 1. Restrict Web UI Access
```bash
# Use firewall to limit web UI access
sudo ufw delete allow 5001/tcp
sudo ufw allow from 10.0.0.0/8 to any port 5001 proto tcp

# Or use Nginx reverse proxy with authentication
```

### 2. Enable HTTPS for Web UI
```bash
# Install Nginx
sudo apt install nginx

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/zerotrust-dns

# Add SSL configuration
server {
    listen 443 ssl;
    server_name zerotrust.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/zerotrust.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zerotrust.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Regular Updates
```bash
# Update server code
cd /opt/zerotrust-dns
git pull

# Rebuild binaries
./build-all-binaries.sh

# Restart server
sudo systemctl restart zerotrust-dns
```

### 4. Audit Logs
```bash
# Enable detailed logging
sudo journalctl -u zerotrust-dns --since "1 hour ago" | grep -E "Proxy|DNS"

# Look for:
# - Failed authentication attempts
# - Unusual connection patterns
# - Certificate errors
```

## Troubleshooting

### Server won't start
```bash
# Check if ports are in use
sudo netstat -tlnp | grep -E "853|8443|5001"

# Check logs
sudo journalctl -u zerotrust-dns -n 50

# Check Python errors
python3 server.py
```

### Binaries not building
```bash
# Check Go installation
go version

# Clean and rebuild
rm -rf binaries/ go.mod go.sum
./build-all-binaries.sh

# Check for errors
echo $?  # Should be 0
```

### Client can't connect
```bash
# From client, test connectivity
telnet YOUR-SERVER 853
openssl s_client -connect YOUR-SERVER:853

# Check firewall
sudo ufw status

# Check server logs
sudo journalctl -u zerotrust-dns | grep "client_cn"
```

### DNS not resolving
```bash
# Check if endpoint is running
ps aux | grep ZeroTrust

# Test DNS directly
dig @127.0.0.1 google.com

# Check certificate
openssl x509 -in endpoint.crt -noout -dates
```

### Proxy connection fails
```bash
# Check routing table
cat /opt/zerotrust-dns/data/routes.json

# Test service reachability FROM server
telnet 10.10.10.50 5432

# Check proxy logs
sudo journalctl -u zerotrust-dns | grep Proxy
```

## Summary Checklist

Before going to production:

- [ ] Server installed and running
- [ ] Binaries compiled for all platforms
- [ ] Firewall configured (ports 853, 8443)
- [ ] Test client created and working
- [ ] Test service created and accessible
- [ ] DNS resolution tested (public and private)
- [ ] Proxy routing tested
- [ ] Systemd service enabled
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Logs rotating properly
- [ ] Documentation updated for your environment

## Next Steps

1. ✅ Create more clients for your team
2. ✅ Add internal services (databases, APIs)
3. ✅ Set up monitoring dashboard
4. ✅ Implement backup automation
5. ✅ Document your DNS zones
6. ✅ Train users on the system

---

**Congratulations!** Your ZeroTrust DNS Platform with TLS Proxy is now fully deployed! 🎉

For more information:
- **QUICKSTART.md** - Quick setup guide
- **ARCHITECTURE.md** - How the TLS proxy works
- **DOCKER_BUILD.md** - Docker deployment