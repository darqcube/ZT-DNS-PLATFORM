# ZeroTrust DNS - Deployment Options Guide

## Overview

This guide helps you choose the right deployment method for your ZeroTrust DNS Platform based on your requirements, infrastructure, and expertise level.

## Available Documentation

We provide three deployment guides, each optimized for different use cases:

1. **QUICKSTART.md** - Fast deployment for testing and demos
2. **SETUP.md** - Complete production deployment on bare metal
3. **DOCKER_BUILD.md** - Container-based deployment with Docker/Kubernetes

## Quick Comparison

| Feature | QUICKSTART | SETUP | DOCKER_BUILD |
|---------|-----------|-------|--------------|
| **Time to Deploy** | 5 minutes | 1-2 hours | 15-30 minutes |
| **Complexity** | Low | High | Medium |
| **Production Ready** | ❌ No | ✅ Yes | ✅ Yes |
| **Best For** | Testing/Demo | Bare Metal | Containers |
| **Systemd Service** | ❌ | ✅ | ❌ (Docker handles) |
| **Firewall Config** | ❌ | ✅ | ⚠️ Basic |
| **Backup Strategy** | ❌ | ✅ | ⚠️ Volume backups |
| **Binary Compilation** | ⚠️ Via Docker | ✅ Manual | ✅ In Docker |
| **Monitoring** | ❌ | ✅ | ⚠️ Container logs |
| **Security Hardening** | ❌ | ✅ | ⚠️ Container isolation |
| **Multi-Server** | ❌ | ✅ | ✅ (orchestration) |
| **Bare Metal** | ❌ | ✅ | ❌ |
| **Container Deploy** | ✅ | ❌ | ✅ |
| **CI/CD Examples** | ❌ | ❌ | ✅ |
| **Development Use** | ✅ Perfect | ⚠️ Overkill | ✅ Good |
| **Enterprise Use** | ❌ | ✅ | ✅ |

## Deployment Guide Details

### QUICKSTART.md

**Purpose:** Get running in 5 minutes  
**Target Audience:** Developers, testers, evaluators  
**Deployment Method:** Docker Compose

**What's Included:**
- ✅ One-line Docker command to start
- ✅ Basic client/service creation via web UI
- ✅ Simple connection testing
- ✅ Common troubleshooting tips
- ✅ Example scenarios (PostgreSQL, API, Redis)
- ❌ No systemd service setup
- ❌ No security hardening
- ❌ No backup procedures
- ❌ No production optimizations

**Typical Flow:**
```bash
# 1. Start server (30 seconds)
docker-compose up -d

# 2. Create service via web UI (2 minutes)
open http://localhost:5001

# 3. Create client via web UI (1 minute)

# 4. Test connection (1 minute)
psql "host=db.internal.corp port=8443 user=admin"

# Total: ~5 minutes
```

**Use When:**
- ✓ First time trying ZeroTrust DNS
- ✓ Evaluating if it fits your needs
- ✓ Creating a demo for stakeholders
- ✓ Development/testing environment
- ✓ Learning how the system works
- ✓ Quick proof of concept

**Don't Use When:**
- ✗ Deploying to production
- ✗ Need high availability
- ✗ Require backup/recovery
- ✗ Security compliance needed
- ✗ Enterprise deployment

---

### SETUP.md

**Purpose:** Complete production deployment on bare metal  
**Target Audience:** System administrators, DevOps engineers, production deployments  
**Deployment Method:** Manual installation with systemd

**What's Included:**
- ✅ System dependencies installation
- ✅ Go installation and setup
- ✅ Manual binary compilation
- ✅ Directory structure setup
- ✅ Systemd service configuration
- ✅ Firewall configuration (ufw/iptables)
- ✅ Backup strategy and scripts
- ✅ Log rotation configuration
- ✅ Monitoring and health checks
- ✅ Security hardening procedures
- ✅ Performance tuning (kernel, Python)
- ✅ Multi-service configuration
- ✅ Certificate management
- ✅ Troubleshooting guides
- ✅ Production checklist

**Typical Flow:**
```bash
# 1. Install system dependencies (10 minutes)
sudo apt install python3 python3-pip openssl git wget

# 2. Install Go (5 minutes)
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# 3. Setup directory structure (2 minutes)
sudo mkdir -p /opt/zerotrust-dns/{certs,data,binaries}
sudo chown -R $USER:$USER /opt/zerotrust-dns

# 4. Build binaries (5 minutes)
./build-all-binaries.sh

# 5. Create systemd service (10 minutes)
sudo nano /etc/systemd/system/zerotrust-dns.service
sudo systemctl enable --now zerotrust-dns

# 6. Configure firewall (5 minutes)
sudo ufw allow 853/tcp
sudo ufw allow 8443/tcp
sudo ufw allow 5001/tcp

# 7. Setup backup procedures (15 minutes)
# Create backup scripts
# Configure cron jobs

# 8. Configure monitoring (15 minutes)
# Setup health checks
# Configure log rotation

# 9. Security hardening (20 minutes)
# Restrict web UI access
# Enable HTTPS for web UI
# Configure audit logging

# 10. Test everything (15 minutes)
# Create test client and service
# Verify connections

# Total: 1-2 hours
```

**Use When:**
- ✓ Deploying to production bare metal servers
- ✓ Maximum control and customization needed
- ✓ Docker/containers not allowed by policy
- ✓ Custom OS or distribution
- ✓ Integration with existing infrastructure
- ✓ Security compliance requirements (HIPAA, PCI-DSS)
- ✓ Need systemd integration
- ✓ Manual backup procedures required
- ✓ Enterprise deployment
- ✓ High-availability setup

**Don't Use When:**
- ✗ Quick testing/evaluation (use QUICKSTART)
- ✗ Using Docker/Kubernetes (use DOCKER_BUILD)
- ✗ Want simple deployment (use QUICKSTART)
- ✗ Limited time for setup

---

### DOCKER_BUILD.md

**Purpose:** Container-based deployment with Docker and Kubernetes  
**Target Audience:** Docker users, DevOps engineers, cloud deployments  
**Deployment Method:** Docker containers and orchestration

**What's Included:**
- ✅ Dockerfile explanations (Go and Python versions)
- ✅ Docker Compose configurations
- ✅ Multi-stage build strategies
- ✅ Binary extraction from images
- ✅ Volume management and persistence
- ✅ Custom image creation
- ✅ Multi-platform builds (buildx)
- ✅ Container networking setup
- ✅ Resource limits and constraints
- ✅ Health checks
- ✅ Log management
- ✅ CI/CD integration (GitHub Actions, GitLab CI)
- ✅ Production configurations
- ✅ Kubernetes deployment examples
- ❌ Not focused on bare-metal installation

**Typical Flow:**
```bash
# Option 1: Docker Compose (5 minutes)
docker-compose up -d
# Done!

# Option 2: Manual Docker (10 minutes)
# Build image
docker build -f Dockerfile.go -t zerotrust-dns .

# Run container
docker run -d \
  -p 5001:5001 -p 853:853 -p 8443:8443 \
  -v ./data:/opt/zerotrust-dns/data \
  --name zerotrust-dns \
  zerotrust-dns

# Option 3: Kubernetes (30 minutes)
# Create deployment manifests
# Deploy to cluster
kubectl apply -f zerotrust-dns-deployment.yaml

# Total: 5-30 minutes depending on method
```

**Use When:**
- ✓ Using Docker or Kubernetes
- ✓ Container-based infrastructure
- ✓ Need portable deployment packages
- ✓ CI/CD pipeline integration
- ✓ Multi-environment deployments (dev/staging/prod)
- ✓ Cloud deployments (AWS ECS, Azure Container Instances, GCP Cloud Run)
- ✓ Want easy scaling and orchestration
- ✓ Prefer container isolation
- ✓ Microservices architecture
- ✓ GitOps workflows

**Don't Use When:**
- ✗ Docker not available/allowed
- ✗ Need bare metal installation (use SETUP)
- ✗ Want systemd integration (use SETUP)
- ✗ Maximum performance required (bare metal is faster)

---

## Decision Tree
```
┌─────────────────────────────────────┐
│    What's your primary goal?        │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    Testing?          Production?
        │                   │
        ↓                   │
  QUICKSTART.md             │
   (5 minutes)              │
                            │
                  ┌─────────┴─────────┐
                  │                   │
            Using Docker?         Bare Metal?
                  │                   │
                  ↓                   ↓
          DOCKER_BUILD.md        SETUP.md
           (15-30 min)         (1-2 hours)
```

## Detailed Decision Matrix

### Choose QUICKSTART.md if you answer YES to:

- [ ] Is this your first time using ZeroTrust DNS?
- [ ] Do you want to test if it works for your use case?
- [ ] Are you creating a demo for your team?
- [ ] Is this for development/testing only?
- [ ] Do you want to get running in under 5 minutes?
- [ ] Are you okay with Docker?
- [ ] Is this NOT for production use?

**If 4+ YES → Use QUICKSTART.md**

---

### Choose SETUP.md if you answer YES to:

- [ ] Is this a production deployment?
- [ ] Do you need to deploy on bare metal servers?
- [ ] Are containers (Docker) not allowed/available?
- [ ] Do you need maximum control over the system?
- [ ] Do you need systemd integration?
- [ ] Are you required to follow specific security compliance?
- [ ] Do you need custom OS integration?
- [ ] Is this for an enterprise environment?
- [ ] Do you have 1-2 hours for initial setup?
- [ ] Do you need manual backup procedures?

**If 5+ YES → Use SETUP.md**

---

### Choose DOCKER_BUILD.md if you answer YES to:

- [ ] Are you using Docker or Kubernetes?
- [ ] Is your infrastructure container-based?
- [ ] Do you need portable deployments?
- [ ] Are you deploying to cloud (AWS, Azure, GCP)?
- [ ] Do you have CI/CD pipelines?
- [ ] Do you need multiple environments (dev/staging/prod)?
- [ ] Do you want easy scaling?
- [ ] Is container isolation important?
- [ ] Are you familiar with Docker?

**If 5+ YES → Use DOCKER_BUILD.md**

---

## Real-World Scenarios

### Scenario 1: Startup Company (5-person team)

**Situation:**
- Small development team
- Cloud-based infrastructure (AWS)
- Need fast deployment
- Limited DevOps resources

**Recommended Path:**
1. **QUICKSTART.md** - Test locally on developer machines
2. **DOCKER_BUILD.md** - Deploy to AWS ECS or EC2 with Docker
3. Use Docker Compose for simplicity

**Why:**
- Fast to deploy
- Easy to maintain
- Scales with business growth
- No specialized DevOps knowledge needed

**Timeline:**
- Day 1: Test with QUICKSTART (30 minutes)
- Day 2: Deploy to staging with DOCKER_BUILD (1 hour)
- Day 3: Deploy to production (30 minutes)

---

### Scenario 2: Enterprise Corporation (1000+ employees)

**Situation:**
- Large IT department
- Security compliance requirements (HIPAA)
- Existing bare metal infrastructure
- Custom monitoring and backup systems

**Recommended Path:**
1. **QUICKSTART.md** - Proof of concept (1 week testing)
2. **SETUP.md** - Production deployment on bare metal (2-4 weeks)
3. **DOCKER_BUILD.md** - Optional for dev/staging environments

**Why:**
- Maximum control for compliance
- Integration with existing systems
- Security audit requirements
- Custom backup procedures

**Timeline:**
- Week 1: POC with QUICKSTART
- Week 2-3: Security review and planning
- Week 4-5: Production deployment with SETUP
- Week 6: Testing and validation

---

### Scenario 3: Cloud-Native SaaS Company

**Situation:**
- Kubernetes-based infrastructure
- Multiple environments (dev/staging/prod)
- CI/CD pipelines (GitHub Actions)
- Rapid deployment cycles

**Recommended Path:**
1. **QUICKSTART.md** - Local development testing
2. **DOCKER_BUILD.md** exclusively for all environments
3. Kubernetes deployment with Helm charts

**Why:**
- Container-native approach
- Easy scaling
- GitOps workflows
- Multi-environment support

**Timeline:**
- Day 1: Local testing with QUICKSTART
- Day 2: Create Kubernetes manifests
- Day 3: Deploy to dev/staging
- Day 4: Production deployment

---

### Scenario 4: Freelance Consultant

**Situation:**
- Multiple clients
- Need quick demos
- Various deployment environments
- Limited time per client

**Recommended Path:**
1. **QUICKSTART.md** for client demos (always)
2. **DOCKER_BUILD.md** for client deployments (most cases)
3. **SETUP.md** only if client requires bare metal

**Why:**
- Fast demos win clients
- Docker is portable across clients
- Easy to replicate
- Minimal support overhead

**Timeline:**
- Demo: 5 minutes with QUICKSTART
- Client deployment: 30 minutes with DOCKER_BUILD
- Training: 1 hour

---

### Scenario 5: Educational Institution

**Situation:**
- Teaching Zero Trust concepts
- Students need hands-on experience
- Limited infrastructure
- Various skill levels

**Recommended Path:**
1. **QUICKSTART.md** for all students (easiest)
2. **ARCHITECTURE.md** for understanding concepts
3. **SETUP.md** for advanced students (optional)

**Why:**
- Students can set up in 5 minutes
- Focus on concepts, not infrastructure
- Works on any laptop
- Easy to reset and retry

**Timeline:**
- Lecture: 1 hour (ARCHITECTURE.md)
- Lab setup: 5 minutes (QUICKSTART.md)
- Lab exercises: 2 hours

---

## Reading Order Recommendations

### For Absolute Beginners:

1. **README.md** - Project overview (5 min)
2. **QUICKSTART.md** - Get it running (5 min)
3. **ARCHITECTURE.md** - Understand how it works (15 min)
4. **COMPARISON.md** - Understand the benefits (10 min)
5. Choose deployment path for production

**Total Time:** 35 minutes to understand + deploy test environment

---

### For Production Deployment:

#### If using Docker/Kubernetes:
1. **QUICKSTART.md** - Quick test (5 min)
2. **ARCHITECTURE.md** - Deep understanding (15 min)
3. **DOCKER_BUILD.md** - Production deployment (30 min - 2 hours)
4. **BINARIES.md** - If building custom binaries (optional)

**Total Time:** 1-3 hours

#### If using Bare Metal:
1. **QUICKSTART.md** - Quick test (5 min)
2. **ARCHITECTURE.md** - Deep understanding (15 min)
3. **SETUP.md** - Complete installation (1-2 hours)
4. **BINARIES.md** - Binary compilation (15 min)

**Total Time:** 2-3 hours

---

### For DevOps Engineers:

1. **ARCHITECTURE.md** - System design (15 min)
2. **DOCKER_BUILD.md** - Container deployment (30 min)
3. **SETUP.md** - Bare metal alternative (skim for reference)
4. **BINARIES.md** - CI/CD integration (15 min)

**Total Time:** 1 hour

---

### For Security Teams:

1. **ARCHITECTURE.md** - Security model (15 min)
2. **SETUP.md** - Security hardening sections (30 min)
3. **COMPARISON.md** - vs VPN and other solutions (10 min)
4. Test deployment with **QUICKSTART.md** (5 min)

**Total Time:** 1 hour

---

## Feature Comparison Details

### Installation Time

**QUICKSTART.md:**
```
Prerequisites: Docker installed
Setup time: 5 minutes
  - docker-compose up -d: 1 minute
  - Create service via UI: 2 minutes
  - Create client via UI: 1 minute
  - Test connection: 1 minute
```

**SETUP.md:**
```
Prerequisites: None (installs everything)
Setup time: 1-2 hours
  - Install dependencies: 15 minutes
  - Install Go: 10 minutes
  - Build binaries: 5 minutes
  - Configure systemd: 10 minutes
  - Configure firewall: 5 minutes
  - Setup backup: 15 minutes
  - Configure monitoring: 15 minutes
  - Security hardening: 20 minutes
  - Testing: 15 minutes
```

**DOCKER_BUILD.md:**
```
Prerequisites: Docker installed
Setup time: 15-30 minutes
  - Build Docker image: 5 minutes
  - Configure volumes: 2 minutes
  - Run container: 1 minute
  - Configure CI/CD: 10-20 minutes (optional)
  - Testing: 5 minutes
```

---

### Maintenance Overhead

**QUICKSTART.md:**
```
Daily: None (auto-restarts)
Weekly: Check logs
Monthly: Update Docker image
Complexity: Low
```

**SETUP.md:**
```
Daily: Monitor systemd status
Weekly: Check logs, review connections
Monthly: Security updates, backup verification
Complexity: High
```

**DOCKER_BUILD.md:**
```
Daily: None (auto-restarts)
Weekly: Check container logs
Monthly: Update Docker image
Complexity: Medium
```

---

### Scaling Approach

**QUICKSTART.md:**
```
Scaling: Not designed for scaling
Max recommendation: Single server, <50 clients
```

**SETUP.md:**
```
Scaling: Manual server provisioning
Method: Deploy to multiple servers, load balance
Max recommendation: 1000+ clients per server
```

**DOCKER_BUILD.md:**
```
Scaling: Container orchestration (K8s, ECS)
Method: Horizontal pod autoscaling
Max recommendation: Unlimited with proper orchestration
```

---

## Migration Paths

### From QUICKSTART to Production

**Path 1: QUICKSTART → DOCKER_BUILD (Recommended for most)**
```bash
# 1. Export data from QUICKSTART
docker cp zerotrust-dns:/opt/zerotrust-dns/data ./backup/

# 2. Build production Docker image
docker build -f Dockerfile.go -t zerotrust-dns:prod .

# 3. Deploy with production compose file
docker-compose -f docker-compose.prod.yml up -d

# 4. Restore data
docker cp ./backup/data/. zerotrust-dns:/opt/zerotrust-dns/data/

# 5. Restart
docker restart zerotrust-dns
```

**Path 2: QUICKSTART → SETUP (For bare metal production)**
```bash
# 1. Export data from QUICKSTART
docker cp zerotrust-dns:/opt/zerotrust-dns/data ./backup/
docker cp zerotrust-dns:/opt/zerotrust-dns/certs ./backup/

# 2. Follow SETUP.md on production server

# 3. Copy data to production
scp -r backup/* production-server:/opt/zerotrust-dns/

# 4. Start production server
ssh production-server
sudo systemctl start zerotrust-dns
```

---

### From SETUP to DOCKER

**Migration Path:**
```bash
# 1. Backup bare metal deployment
sudo tar -czf zerotrust-backup.tar.gz /opt/zerotrust-dns/

# 2. Copy to Docker host
scp zerotrust-backup.tar.gz docker-host:/tmp/

# 3. Extract and mount in Docker
tar -xzf zerotrust-backup.tar.gz
docker-compose up -d

# 4. Verify and cutover DNS
# 5. Decommission bare metal
```

---

## Cost Comparison

### QUICKSTART.md
```
Infrastructure: $0 (local laptop) or $5-10/month (small VPS)
Time investment: 5 minutes
Maintenance: Minimal
Best for: Testing, development
```

### SETUP.md
```
Infrastructure: $20-200/month (depending on server specs)
Time investment: 2-4 hours initial, 1-2 hours/month maintenance
Maintenance: High (manual updates, monitoring)
Best for: Enterprise, custom requirements
```

### DOCKER_BUILD.md
```
Infrastructure: $10-100/month (container hosting)
Time investment: 1 hour initial, 30 min/month maintenance
Maintenance: Medium (container updates)
Best for: Most production deployments
```

---

## Summary

### Quick Reference

| Your Situation | Use This Guide | Time Required |
|----------------|----------------|---------------|
| "Just trying it out" | QUICKSTART.md | 5 minutes |
| "Docker/K8s production" | DOCKER_BUILD.md | 30 minutes |
| "Bare metal production" | SETUP.md | 2 hours |
| "Need to demo quickly" | QUICKSTART.md | 5 minutes |
| "Enterprise with compliance" | SETUP.md | 2-4 hours |
| "Cloud-native SaaS" | DOCKER_BUILD.md | 1 hour |
| "Educational lab" | QUICKSTART.md | 5 minutes |
| "Custom integration" | SETUP.md | 2-4 hours |

### Final Recommendations

**For 90% of users:** Start with **QUICKSTART.md**, then use **DOCKER_BUILD.md** for production.

**For enterprises:** Start with **QUICKSTART.md** for POC, then use **SETUP.md** for production.

**For developers:** Use **QUICKSTART.md** for local dev, **DOCKER_BUILD.md** for staging/prod.

---

## Getting Started

Based on your needs, jump to the appropriate guide:

- 📚 **[QUICKSTART.md](QUICKSTART.md)** - 5-minute deployment for testing
- 📚 **[SETUP.md](SETUP.md)** - Complete production setup on bare metal
- 📚 **[DOCKER_BUILD.md](DOCKER_BUILD.md)** - Container-based deployment

**Still not sure?** Start with QUICKSTART.md - it takes only 5 minutes and will help you understand the system! 🚀

---

**Questions? Issues? Feedback?**
- Open an issue on GitHub
- Check existing documentation
- Join community discussions