# Comprehensive Installation & Deployment Guide

This guide covers the deployment models of Anchor, including developer workstation CLI configuration, Diamond Cage sandbox installation, and enterprise Sovereign Spoke node container setup.

---

## 💻 1. Developer CLI Installation

Install the Anchor governance client on macOS, Linux, or Windows.

### Requirements:
*   Python 3.8 to 3.12
*   Git (required for drift auditing)

### Installation:
```bash
pip install anchor-audit
```

### Initializing rule structures:
```bash
cd your-repository/
anchor init --all
```

---

## 💎 2. Diamond Cage WASM Sandbox Installation

The Diamond Cage runs potentially unsafe generated code inside a WasmEdge sandbox environment.

### Steps:
Ensure you initialize the sandbox during setup:

```bash
anchor init --sandbox
```

Or install it explicitly at any time:

```bash
python -c "from anchor.core.sandbox import install_diamond_cage; install_diamond_cage(verbose=True)"
```

### Verification:
Run the check command with verbose mode to confirm the WasmEdge engine is active:

```bash
anchor check . --verbose
```

---

## 🔶 3. Enterprise Spoke Node Deployment

For enterprise deployments utilizing the **Sovereign Mesh** architecture, you must deploy a Spoke node within your private network (VPC). The Spoke node runs as a Docker container.

### A. Environment Configuration
Create a `.env` file within your Spoke node directory:

```ini
# Secret HMAC key used to verify local decision logs
ANCHOR_SECRET_KEY=y0ur_hMac_s3cr3t_k3y_h3r3

# Master key used to encrypt payloads before WebSocket routing
ANCHOR_MASTER_KEY=y0ur_master_aeS_cIph3r_k3y

# WebSocket connection URL to the SaaS Hub Control Plane
ANCHOR_HUB_WS_URL=wss://api.anchorgovernance.tech/ws/spoke

# Unique credentials assigned to your hub by AnimusLab
ANCHOR_ORG_ID=org_animuslab
ANCHOR_HUB_ID=animuslab-mumbai
```

### B. Docker Compose Configuration
Write a `docker-compose.yml` to spin up the local database and API listener:

```yaml
version: "3.8"

services:
  spoke:
    image: animuslab/anchor-spoke:latest
    ports:
      - "8001:8001"
    environment:
      - ANCHOR_SECRET_KEY=${ANCHOR_SECRET_KEY}
      - ANCHOR_MASTER_KEY=${ANCHOR_MASTER_KEY}
      - ANCHOR_HUB_WS_URL=${ANCHOR_HUB_WS_URL}
      - ANCHOR_ORG_ID=${ANCHOR_ORG_ID}
      - ANCHOR_HUB_ID=${ANCHOR_HUB_ID}
    volumes:
      - spoke-db:/app/data
    restart: always

volumes:
  spoke-db:
```

Launch the service:
```bash
docker compose up -d
```

---

## 🔌 4. Connecting Your Application

Once the Spoke is running, direct your application's Anchor runtime to send telemetry events to the local Spoke endpoint:

```bash
export ANCHOR_LEDGER_URL="http://localhost:8001/api/spoke/ingest"
export ANCHOR_MAT="mat_development_credentials_token"
```

In your application code, initialize the runtime interceptor:

```python
import anchor.runtime
anchor.runtime.activate()
```

Anchor will now intercept all outbound LLM request parameters, enforce local rules, link entries in your local audit chain, and stream ZK-metadata headers asynchronously to the cloud-hosted Oversight Hub.
