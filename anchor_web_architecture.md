# Anchor Web Portal: System & Directory Architecture

This document provides a technical deep-dive into the codebase structure, server design, and database configurations of the **`anchor-web`** platform, which powers the unified enterprise and oversight portals.

---

## 1. Repository Directory Structure

The `anchor-web` repository is split into frontend interfaces (React/Vite apps) and a backend management server (FastAPI/Python):

```text
anchor-web/
├── server/                     # Backend API & Authentication Services
│   ├── config.py               # Environment variables & feature flags
│   ├── auth.py                 # JWT token generation & role mapping
│   ├── spoke_node.py           # Spoke Node lifecycle management
│   ├── relay_protocol.py       # Spoke ↔ Hub WebSocket protocol handlers
│   ├── database.py             # SQLite/SQLAlchemy schema bindings
│   └── main.py                 # FastAPI routing & middleware bootstrapper
│
├── dashboard/                  # Unified Enterprise Dashboard (React/Vite)
│   ├── src/components/         # Gated UI blocks (Policy Editor, Agent Creator)
│   └── src/hooks/              # Permission gate checks
│
├── oversight/                  # Unified Oversight Dashboard (React/Vite)
│   ├── src/components/         # Auditor Views (Heatmaps, Notices panel)
│   └── src/hooks/              # Clearance-gated hooks
│
├── root-admin/                 # Platform Master Admin portal (React/Vite)
├── mesh/                       # Real-time WebGL global network topology visualizer
├── landing/                    # Public landing pages
│
├── ANCHOR_CONSTITUTIONAL_INVARIANTS_v1.md  # Governance compliance rules
├── GOVERNANCE_ACCESS_MATRIX.md             # Role & permission bindings
└── GOVERNANCE_PORTAL_ARCHITECTURE.md        # Portal domain design specs
```

---

## 2. API & Endpoint Registry

All communications are managed via `server/main.py`. The routing system gates features dynamically:

### Public / Authentication Endpoints
*   `POST /api/auth/login` — Resolves credentials (OAuth/MFA) and issues JWT containing role, scope, and jurisdiction claims.
*   `POST /api/auth/register` — Registers new organizations or independent auditors.

### Enterprise Operations (app.*)
*   `GET /api/hubs` — List organization-scoped hubs.
*   `POST /api/hubs/provision` — Provision new edge spoke credentials. (Owner only)
*   `POST /api/agents/create` — Registers a new AI agent. (Owner/Developer only)
*   `GET /api/agents` — Lists active agents for the authenticated hub.
*   `POST /api/policies/override` — Saves local adjustments to the policy schema. (Owner only)

### Oversight Operations (oversight.*)
*   `GET /api/oversight/violations` — Lists compliance violations (jurisdiction-scoped).
*   `POST /api/oversight/replays/request` — Requests a forensic session decryption. (Auditors/Devs)
*   `POST /api/oversight/replays/approve` — Approves a forensic decryption ticket. (Owner only)
*   `POST /api/oversight/notices` — Issues regulatory remediation warning alerts. (Regulatory Auditor only)

---

## 3. Database Schema Mapping

Anchor Web uses a relational database model (`anchor.db`) managed via SQLAlchemy. Key entities include:

### Entity Visibility & Taxonomy Types
As verified in `test_entity_visibility_advanced.py`, the system tracks eight core entity types:
1.  `AI_AGENT` — Active AI models, wrappers, and deployments.
2.  `CODEBASE` — Source repositories containing static check footprints.
3.  `GATEWAY` — Network APIs routing request traffic.
4.  `MESH_NODE` — Sovereign hub and spoke servers.
5.  `POLICY` — Evaluated rulesets and custom configurations.
6.  `PROCESS` — Automated pipelines (e.g. CI/CD runs).
7.  `DATABASE` — Data enclaves (restricted from audit views).
8.  `WEBHOOK` — Callbacks routing telemetry payloads.

### SQL Entity Structures

#### Hubs Table
```sql
CREATE TABLE hubs (
    id VARCHAR(50) PRIMARY KEY,       -- e.g. "AN-IN-SOL01"
    name VARCHAR(100),
    organization VARCHAR(50),         -- e.g. "animuslab"
    jurisdiction VARCHAR(10) NOT NULL, -- e.g. "IN", "EU"
    created_at TIMESTAMP
);
```

#### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    role VARCHAR(20) NOT NULL,        -- 'owner', 'developer', 'auditor', 'admin_root'
    auditor_type VARCHAR(30),         -- 'standard_auditor', 'cross_hub_auditor', 'regulatory_auditor'
    assigned_hub VARCHAR(50),
    assigned_org VARCHAR(50),
    jurisdiction VARCHAR(10),
    secret_key_totp VARCHAR(100)      -- MFA requirement
);
```

#### Audits Table (The Decision Chain)
```sql
CREATE TABLE audits (
    entry_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hub_id VARCHAR(50) REFERENCES hubs(id),
    provider VARCHAR(50),             -- 'openai', 'custom', etc.
    is_compliant BOOLEAN,
    prev_chain_hash VARCHAR(64),
    chain_hash VARCHAR(64) UNIQUE,     -- Tamper-evident link
    signature VARCHAR(128),            -- HMAC signed
    telemetry_json TEXT                -- Context, metadata, and violations
);
```
