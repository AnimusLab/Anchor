
# 🏗️ Anchor — Complete System Architecture

> **Two repositories. One governance mesh.**
> `anchor` (Python Package) is the governance engine.
> `anchor-web` (Sovereign Mesh) is the federated control plane.

---

## System Overview

```mermaid
graph TB
    subgraph "📦 anchor (PyPI Package)"
        direction TB
        L1["🔬 Layer 1\nStatic Compliance Engine"]
        L2["🛡️ Layer 2\nRuntime Interceptor"]
        DC["💎 Diamond Cage\nWASM Sandbox"]
        GOV["📜 Governance Federation\n9 Domains · 6 Regulators · 3 Frameworks"]
    end

    subgraph "🌐 anchor-web (Sovereign Mesh)"
        direction TB
        HUB["🔷 Hub Node\nFastAPI Master"]
        SPOKE["🔶 Spoke Node\nEnterprise Local Data Plane"]
        FE["💻 Frontend Portals\n4 React Apps"]
    end

    L1 -->|"AST violations"| GOV
    L2 -->|"runtime audit chain"| GOV
    DC -->|"behavioral verification"| L1
    L2 -->|"HMAC-signed JSONL\n(ANCHOR_LEDGER_URL)"| SPOKE
    SPOKE -->|"WebSocket relay\n(metadata only)"| HUB
    HUB -->|"REST API"| FE

    style L1 fill:#1e293b,stroke:#06b6d4,color:#e2e8f0
    style L2 fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style DC fill:#1e293b,stroke:#a855f7,color:#e2e8f0
    style GOV fill:#0f172a,stroke:#10b981,color:#e2e8f0
    style HUB fill:#0f172a,stroke:#3b82f6,color:#e2e8f0
    style SPOKE fill:#0f172a,stroke:#f97316,color:#e2e8f0
    style FE fill:#0f172a,stroke:#ec4899,color:#e2e8f0
```

---

## Repository Map

### 📦 `d:/Anchor` — Core Governance Engine (`pip install anchor-audit`)

```
anchor/
├── cli.py                    # CLI entry (anchor init / check / heal / sync)
├── schema.py                 # Pydantic AuditEntry schema
│
├── core/                     # ── LAYER 1: Static Compliance ──
│   ├── engine.py             # PolicyEngine — AST scanning + rule evaluation
│   ├── loader.py             # Federation loader (domains + frameworks + regulators)
│   ├── constitution.py       # Remote integrity verification (SHA-256)
│   ├── policy_loader.py      # Local policy.anchor merge (raise-only enforcement)
│   ├── crypto.py             # HMAC-SHA256 chain signing
│   ├── sandbox.py            # 💎 Diamond Cage (WASM sandbox + verify_patch)
│   ├── healer.py             # Auto-fix suggestion engine (anchor heal)
│   ├── verdicts.py           # Architectural drift analysis (Intent Anchoring)
│   ├── model_auditor.py      # ML model weight auditing (safetensors/gguf)
│   ├── risk_mapper.py        # Risk mapping
│   ├── memory.py             # Memory management
│   ├── history.py            # Git history traversal (Intent Anchoring)
│   ├── config.py             # Settings (governance_lock_url, timeouts)
│   ├── contexts.py           # Context management
│   ├── mapper.py             # Rule mapping
│   ├── registry.py           # Language adapter registry
│   └── models.py             # Core data models (IntentAnchor, CallContext)
│
├── runtime/                  # ── LAYER 2: Live Enforcement ──
│   ├── __init__.py           # Public API: activate() / deactivate() / enforce()
│   ├── guard.py              # AnchorGuard — first-party integration API
│   ├── decision_auditor.py   # Cryptographic audit chain + ETH compliance
│   ├── models.py             # AuditEntry with dialect translation (RBI/SEC/EU)
│   └── interceptors/
│       ├── base.py           # AnchorViolationError, InterceptorMode, SessionStats
│       ├── framework.py      # SDK monkey-patches (9 providers via wrapt)
│       ├── http_backstop.py  # Universal HTTP interceptor (requests/httpx)
│       ├── output_scanner.py # Response pattern scanner (RSP rules)
│       └── provider_registry.py  # AI API domain registry (30+ providers)
│
├── adapters/                 # ── LANGUAGE ADAPTERS (tree-sitter) ──
│   ├── base.py               # LanguageAdapter interface
│   ├── python.py             # Python AST adapter
│   ├── typescript.py         # TypeScript/JSX adapter
│   ├── rust.py               # Rust adapter
│   ├── go.py                 # Go adapter
│   └── java.py               # Java adapter
│
├── plugins/                  # ── MODEL FORMAT PLUGINS ──
│   ├── safetensors_plugin.py # SafeTensors weight analysis
│   ├── gguf_plugin.py        # GGUF (LM Studio) weight analysis
│   └── huggingface_plugin.py # HuggingFace model analysis
│
├── governance/               # ── FEDERATED RULE SYSTEM ──
│   ├── constitution.anchor   # Root manifest (v4.1)
│   ├── mitigation.anchor     # Detection patterns + fix guidance
│   ├── policy.anchor         # Project-local private rules (raise-only)
│   ├── domains/              # 9 core domains
│   │   ├── security.anchor   #   SEC — injection, credentials, shell
│   │   ├── ethics.anchor     #   ETH — prohibited proxies, explainability
│   │   ├── privacy.anchor    #   PRV — PII, data sovereignty
│   │   ├── alignment.anchor  #   ALN — guardrails, moderation
│   │   ├── agentic.anchor    #   AGT — cross-agent trust, tool use
│   │   ├── legal.anchor      #   LEG — IP, licensing
│   │   ├── operational.anchor#   OPS — uptime, resilience
│   │   ├── supply_chain.anchor#  SUP — dependency provenance
│   │   └── shared.anchor     #   SHR — cross-domain rules
│   ├── frameworks/           # Industry standards
│   │   ├── FINOS_Framework.anchor  # FINOS AI Governance (Rosetta Stone)
│   │   ├── OWASP_LLM.anchor       # OWASP LLM Top 10 2025
│   │   └── NIST_AI_RMF.anchor     # NIST AI RMF 1.0
│   └── government/           # Government regulators
│       ├── RBI_Regulations.anchor  # RBI FREE-AI Report 2025
│       ├── EU_AI_Act.anchor        # EU AI Act 2024/1689
│       ├── SEC_Regulations.anchor  # SEC 2026 Exam Priorities
│       ├── SEBI_Regulations.anchor # SEBI AI/ML Regulations
│       ├── CFPB_Regulations.anchor # CFPB Regulation B
│       └── FCA_Regulations.anchor  # FCA AI Governance 2024
│
└── utils/
    └── output.py             # Terminal formatting (icons, colors)
```

### 🌐 `d:/anchor-web` — Sovereign Identity Mesh

```
anchor-web/
├── server/                   # ── HUB NODE (FastAPI) ──
│   ├── proxy.py              # Main API server (v5.0.0 Master Node)
│   ├── auth.py               # Enterprise auth + registration (hub_id)
│   ├── oversight_auth.py     # Regulator auth (TOTP-based)
│   ├── models.py             # SQLAlchemy models (Organization, Fleet, User, Ledger)
│   ├── database.py           # SQLite + migrations (hub_id schema)
│   ├── relay_protocol.py     # Hub ↔ Spoke WebSocket protocol
│   ├── spoke_node.py         # Spoke Node server (enterprise data plane)
│   ├── dispatch_manager.py   # Webhook dispatcher (multi-dialect)
│   ├── master_config.py      # Root admin configuration
│   ├── mail.py               # Email verification (Resend API)
│   ├── security.py           # AES-256 encryption helpers
│   └── jurisdictions.json    # Jurisdiction metadata (USA, UK, IN, EU)
│
├── dashboard/src/            # ── ENTERPRISE PORTAL (React/Vite) ──
│   ├── AuthPortal.jsx        # Login + Onboarding (hub_id)
│   ├── PrivateDashboard.jsx  # Post-auth dashboard
│   ├── GlobeWidget.jsx       # 3D globe component
│   └── pages/
│       ├── DashboardLayout.jsx
│       ├── Ledger.jsx        # Audit chain viewer
│       ├── Connect.jsx       # SDK connection guide
│       └── Profile.jsx       # Organization profile
│
├── oversight/src/            # ── OVERSIGHT PORTAL (React/Vite) ──
│   └── pages/
│       ├── LoginPage.jsx     # Regulator login (TOTP)
│       └── Dashboard.jsx     # Evidence vault + forensic viewer
│
├── root-admin/src/           # ── ROOT ADMIN PORTAL (React/Vite) ──
│   ├── App.jsx               # System-wide admin console
│   └── pages/                # Org management, user approval, etc.
│
├── mesh/                     # ── MESH DASHBOARD ──
│   └── index.html            # 3D Terminal Mesh (Globe.gl hex-grid)
│
├── landing/                  # ── PUBLIC LANDING PAGE ──
│   └── index.html            # Marketing / product page
│
├── anchor_sdk.py             # Python SDK for Spoke integration
├── aegis_bot.py              # Discord bot for governance alerts
└── Dockerfile                # Hub deployment container
```

---

## Layer 1 — Static Compliance Engine

```mermaid
graph LR
    subgraph "Developer Pipeline"
        GIT["git commit"]
        HOOK["Pre-Commit Hook"]
    end

    subgraph "PolicyEngine (engine.py)"
        TS["tree-sitter\nAST Parser"]
        ADAPT["Language Adapters\nPython · TS · Rust · Go · Java"]
        RULES["Rule Evaluation\n(Mode A: Smart AST)\n(Mode B: Regex Fallback)"]
        AGG["ID Aggregation\nSEC-007 + OWASP-LLM-02\n+ EU-ART-15"]
    end

    subgraph "Governance Federation"
        CONST["constitution.anchor\n(Root Manifest)"]
        DOM["9 Domains\nSEC · ETH · PRV · ALN\nAGT · LEG · OPS · SUP · SHR"]
        FW["3 Frameworks\nFINOS · OWASP · NIST"]
        GOV["6 Regulators\nRBI · SEC · EU · SEBI · CFPB · FCA"]
        POL["policy.anchor\n(Client Private Rules)\n⬆️ RAISE ONLY"]
        MIT["mitigation.anchor\nDetection Patterns"]
    end

    subgraph "Outputs"
        RPT["governance_violations.txt"]
        JSON["anchor-report.json\n(CI Pipeline)"]
        HEAL["anchor heal\nAuto-Fix Suggestions"]
        SUPP["Suppression Tracking\n# anchor: ignore SEC-007\n(git blame audit)"]
    end

    GIT --> HOOK
    HOOK --> TS
    TS --> ADAPT
    ADAPT --> RULES
    CONST --> DOM --> RULES
    CONST --> FW --> RULES
    CONST --> GOV --> RULES
    POL -->|"merge (raise-only)"| RULES
    MIT -->|"detection patterns"| RULES
    RULES --> AGG
    AGG --> RPT
    AGG --> JSON
    AGG --> HEAL
    RULES --> SUPP

    style POL fill:#422006,stroke:#f59e0b,color:#fef3c7
    style CONST fill:#0c4a6e,stroke:#06b6d4,color:#e0f2fe
```

---

## Layer 2 — Runtime Interceptor

```mermaid
graph TB
    subgraph "Application Code"
        APP["Developer's AI App\nimport anchor.runtime"]
    end

    subgraph "Layer 1: SDK Patches (framework.py)"
        OAI["openai.chat.completions.create"]
        ANT["anthropic.messages.create"]
        GEM["google.generativeai.generate_content"]
        LC["langchain.BaseLanguageModel.invoke"]
        OLL["ollama.chat"]
        GRQ["groq.chat.completions.create"]
        COH["cohere.Client.chat"]
        MIS["mistralai.MistralClient.chat"]
        HF["transformers.Pipeline.__call__"]
    end

    subgraph "Layer 2: HTTP Backstop (http_backstop.py)"
        REQ["requests.Session.send"]
        HTTPX["httpx.Client.send"]
        REG["Provider Registry\n30+ AI API domains"]
    end

    subgraph "Scan Pipeline"
        PS["Prompt Scanner\nInjection · Jailbreak · PII\nCredentials · Exfiltration"]
        RS["Response Scanner\nSecrets · Shell · SQL\nPII · Insecure Code"]
        ETH["ETH Compliance\nAho-Corasick prohibited proxies\nExplainability (ETH-002)"]
    end

    subgraph "Enforcement Modes"
        BLK["🔴 BLOCK\nraise AnchorViolationError\n(payload blocked, session alive)"]
        WRN["🟡 WARN\nlogger.warning()\n(call proceeds)"]
        AUD["🟢 AUDIT\nsilent recording\n(never interrupts)"]
    end

    subgraph "Cryptographic Audit Chain"
        DA["DecisionAuditor\n(Singleton, RAM-cached)"]
        HASH["SHA-256 → chain_hash\nprev_hash + findings_hash"]
        HMAC["HMAC-SHA256 Signature\n(ANCHOR_SECRET_KEY)"]
        JSONL[".anchor/runtime_chain.jsonl"]
        LEDGER["ANCHOR_LEDGER_URL\n(Hub Webhook)"]
    end

    subgraph "Dialect Translation"
        RBI["to_rbi_json()\nFREE-AI Pillar 2\nSeven Sutras"]
        SEC["to_sec_json()\nReg S-K / Item 1.05\nMateriality Signal"]
        EU["to_eu_article12_json()\nArticle 12.2\nAutomatic Event Logging"]
    end

    APP --> OAI & ANT & GEM & LC & OLL & GRQ & COH & MIS & HF
    APP --> REQ & HTTPX
    REQ & HTTPX --> REG

    OAI & ANT & GEM & LC & OLL & GRQ & COH & MIS & HF --> PS
    REG --> PS
    PS -->|"blocker/error"| BLK
    PS -->|"warning"| WRN
    PS -->|"any mode"| AUD

    OAI & ANT & GEM & LC & OLL --> RS
    RS --> ETH
    ETH --> DA
    DA --> HASH --> HMAC
    HMAC --> JSONL
    HMAC --> LEDGER
    DA --> RBI & SEC & EU

    style BLK fill:#7f1d1d,stroke:#ef4444,color:#fecaca
    style WRN fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style AUD fill:#14532d,stroke:#22c55e,color:#dcfce7
```

---

## Diamond Cage — WASM Sandbox

```mermaid
graph LR
    subgraph "Pre-Deployment (anchor check --sandbox)"
        FILE["Suspect Python File"]
        CAGE["DiamondCage\nWasmEdge + Python 3.11 WASM"]
    end

    subgraph "Isolation Guarantees"
        FS["Filesystem: /app mount only"]
        NET["Network: Blocked"]
        ENV["Environment: Stripped"]
        TIME["Timeout: Enforced (DoS)"]
    end

    subgraph "V3: Differential Verification"
        ORIG["Original Script\n→ BehaviorSnapshot A"]
        PATCH["Patched Script\n→ BehaviorSnapshot B"]
        CMP["Compare:\n• stdout signature\n• stderr diff\n• exit code\n• timing anomaly"]
    end

    subgraph "Verdicts"
        SAFE["✅ PROVED_SAFE\nBehavioral equivalence confirmed"]
        CHANGED["⚠️ BEHAVIOUR_CHANGED\nObservable output differs"]
        MALICIOUS["🔴 MALICIOUS_HALLUCINATION\nPatch attempts unauthorized access"]
        CAGE_ERR["❌ CAGE_ERROR\nTimeout or sandbox failure"]
    end

    FILE --> CAGE
    CAGE --> FS & NET & ENV & TIME
    CAGE --> ORIG
    CAGE --> PATCH
    ORIG --> CMP
    PATCH --> CMP
    CMP --> SAFE & CHANGED & MALICIOUS & CAGE_ERR

    style MALICIOUS fill:#7f1d1d,stroke:#ef4444,color:#fecaca
    style SAFE fill:#14532d,stroke:#22c55e,color:#dcfce7
```

---

## Hub ↔ Spoke — Sovereign Relay Protocol

```mermaid
sequenceDiagram
    participant SDK as Anchor SDK<br/>(Developer's Code)
    participant SPOKE as Spoke Node<br/>(Enterprise Perimeter)
    participant HUB as Hub Node<br/>(Master Control)
    participant AUDIT as Auditor<br/>(Regulatory Portal)

    Note over SDK,SPOKE: 🔒 Enterprise Data Plane (On-Premise)
    Note over HUB,AUDIT: 🌐 Sovereign Control Plane (Cloud)

    SDK->>SPOKE: POST /api/spoke/ingest<br/>{entity_id, mat, audit_data}
    SPOKE->>SPOKE: Store FULL payload<br/>in local SQLite

    SPOKE->>HUB: WebSocket: AUDIT_HEADER<br/>{entry_id, chain_hash, is_compliant}<br/>⚡ metadata only — NO raw data

    HUB->>HUB: Store header in<br/>Hub Ledger (SQLite/Neon)

    AUDIT->>HUB: Request forensic details<br/>for entry_id
    HUB->>SPOKE: WebSocket: FORENSIC_PULL<br/>{entry_id, auditor_id}

    SPOKE->>SPOKE: Fetch from local SQLite<br/>Encrypt with AES-256-GCM
    SPOKE->>HUB: WebSocket: FORENSIC_RESPONSE<br/>{encrypted_payload, nonce}

    HUB->>HUB: Decrypt with<br/>ANCHOR_MASTER_KEY
    HUB->>AUDIT: Serve decrypted<br/>forensic payload
```

> [!IMPORTANT]
> **Data Sovereignty Guarantee**: Raw forensic payloads NEVER leave the enterprise perimeter via REST. They only travel over the brokered WebSocket relay, AES-256-GCM encrypted, and only when an authorized auditor explicitly requests them.

---

## Database Schema

```mermaid
erDiagram
    Organization ||--o{ Fleet : "has projects"
    Organization ||--o{ User : "has members"
    Organization ||--o{ OrgInvite : "has invites"
    Fleet ||--o{ WebhookSubscription : "has webhooks"
    Fleet ||--o{ LedgerEntry : "has audit entries"
    LedgerEntry ||--o{ LedgerEntry : "parent chain"

    Organization {
        string id PK "org_a1b2..."
        string hub_id UK "animuslab"
        string display_name "Animus Global"
        string domain UK "animuslab.ai"
        string region "India"
        string org_type "enterprise | regulator"
        string master_key_hash "SHA-256"
        string status "active | suspended"
    }

    Fleet {
        string entity_id PK "animuslab-marcus"
        string org_id FK
        string name "Marcus Trading Bot"
        string tier "enterprise | pro"
        string key_hash "SDK MAT hash"
    }

    User {
        string id PK "usr_a1b2..."
        string email UK
        string org_id FK
        string role "owner | admin | lead | member | regulator"
        string totp_secret "TOTP for regulators"
        string clearance_id "SEC-JHONDOC-2604"
        string jurisdiction "US | IN | EU"
        string status "pending | active"
    }

    LedgerEntry {
        string id PK
        string entity_id FK
        string parent_entry_id FK
        string type "runtime_check | runtime_violation"
        string chain_hash "0x..."
        string signature "HMAC-SHA256"
        text payload "Full audit JSON"
    }

    WebhookSubscription {
        string id PK
        string entity_id FK
        string dialect "RBI | SEC | EU"
        string webhook_url
        boolean is_active
    }

    OrgInvite {
        string id PK "UUID token"
        string org_id FK
        string invited_email
        string role "admin | lead | member"
        string status "pending | accepted | expired"
    }
```

---

## Frontend Portal Architecture

```mermaid
graph TB
    subgraph "Public"
        LAND["🌐 Landing Page\nlanding/index.html\nStatic HTML"]
        MESH["🌍 Mesh Dashboard\nmesh/index.html\nGlobe.gl Terminal Hex-Grid"]
    end

    subgraph "Enterprise"
        EAUTH["🔐 AuthPortal.jsx\nLogin + Onboarding\n(hub_id registration)"]
        EDASH["📊 PrivateDashboard.jsx\nPost-auth workspace"]
        ELEDG["📒 Ledger.jsx\nAudit chain viewer"]
        ECONN["🔌 Connect.jsx\nSDK setup guide"]
        EPROF["👤 Profile.jsx\nOrg settings"]
    end

    subgraph "Regulatory Oversight"
        RAUTH["🔐 LoginPage.jsx\nTOTP-based login\n(Clearance ID)"]
        RDASH["🏛️ Dashboard.jsx\nEvidence Vault\nForensic Viewer"]
    end

    subgraph "Root Admin"
        RADM["⚡ App.jsx\nSystem-wide control\nOrg approval · User management"]
    end

    subgraph "Backend API (FastAPI)"
        AUTH_API["/api/auth/*\nregister/org\nregister/auditor\nlogin · verify"]
        OVER_API["/api/oversight/*\nTOTP verify\nForensic pull"]
        FLEET_API["/api/fleet/*\nProject CRUD\nWebhook config"]
        LEDGER_API["/api/ledger/*\nIngress · Query\nChain verification"]
        WS_API["WebSocket /ws/spoke\nHub ↔ Spoke relay"]
    end

    LAND --> EAUTH
    LAND --> RAUTH
    EAUTH -->|"POST /api/auth/register/org"| AUTH_API
    EAUTH -->|"POST /api/auth/login"| AUTH_API
    RAUTH -->|"POST /api/auth/register/auditor"| AUTH_API
    RAUTH -->|"POST /api/oversight/verify-totp"| OVER_API
    EDASH --> FLEET_API
    ELEDG --> LEDGER_API
    RDASH -->|"Forensic Pull"| OVER_API
    RADM --> AUTH_API & FLEET_API

    style EAUTH fill:#1e293b,stroke:#06b6d4,color:#e2e8f0
    style RAUTH fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style RADM fill:#1e293b,stroke:#ef4444,color:#e2e8f0
```

---

## Connection: How `anchor` ↔ `anchor-web` Talk

```mermaid
graph LR
    subgraph "Developer's Machine"
        CODE["import anchor.runtime\nguard.scan_prompt()\nguard.scan_response()"]
        CHAIN[".anchor/runtime_chain.jsonl\nLocal HMAC-signed audit chain"]
    end

    subgraph "Enterprise Perimeter"
        SPOKE_SRV["Spoke Node\n(Docker · port 8001)\nFull forensic storage"]
    end

    subgraph "Anchor Cloud"
        HUB_SRV["Hub Node\n(api.anchorgovernance.tech)\nMetadata-only registry"]
        ENT_DASH["Enterprise Portal\n(dashboard)"]
        REG_DASH["Oversight Portal\n(oversight)"]
        MESH_VIZ["Mesh Dashboard\n(mesh)"]
    end

    CODE -->|"1. decision_auditor.audit()\nwrites locally"| CHAIN
    CODE -->|"2. ANCHOR_LEDGER_URL\nHTTP POST (fire-and-forget)"| SPOKE_SRV
    SPOKE_SRV -->|"3. WebSocket AUDIT_HEADER\n(~200 bytes, metadata only)"| HUB_SRV
    HUB_SRV -->|"4. REST API"| ENT_DASH
    HUB_SRV -->|"5. REST API"| REG_DASH
    HUB_SRV -->|"6. Status feed"| MESH_VIZ
    REG_DASH -->|"7. FORENSIC_PULL\n(on-demand, encrypted)"| HUB_SRV
    HUB_SRV -->|"8. Relay to Spoke"| SPOKE_SRV

    style CODE fill:#1e293b,stroke:#06b6d4,color:#e2e8f0
    style SPOKE_SRV fill:#422006,stroke:#f97316,color:#fed7aa
    style HUB_SRV fill:#0c4a6e,stroke:#3b82f6,color:#bfdbfe
```

### The Data Flow (Numbered)

1. **Local Audit**: `DecisionAuditor.audit()` writes every decision to `.anchor/runtime_chain.jsonl` with HMAC-SHA256 chain linking
2. **Spoke Ingress**: If `ANCHOR_LEDGER_URL` is set, the full payload is HTTP POST'd to the enterprise's local Spoke node
3. **Hub Header**: Spoke pushes a lightweight `AUDIT_HEADER` (~200 bytes) over persistent WebSocket — **no raw data crosses the perimeter**
4. **Enterprise Dashboard**: Enterprise users see their audit chain, fleet status, and compliance scores via REST API
5. **Oversight Dashboard**: Regulators see aggregated compliance metadata and can request forensic details
6. **Mesh Visualization**: The 3D Terminal Mesh globe shows active nodes and relay status
7. **Forensic Pull**: When a regulator needs the raw payload, they trigger a `FORENSIC_PULL` through the Hub
8. **Encrypted Relay**: Hub relays the request to the Spoke, which encrypts the payload with AES-256-GCM and sends it back

---

## Key Design Principles

| Principle | Implementation |
|---|---|
| **Constitutional Floor** | `constitution.anchor` defines immutable severity baselines. `policy.anchor` can only RAISE, never lower. |
| **Federated Identity** | Each rule has a canonical ID (e.g. `SEC-007`) that maps through alias chains to FINOS, OWASP, and regulator rules |
| **Data Sovereignty** | Raw forensic data stays on the enterprise's Spoke node. Only cryptographic metadata flows to the Hub. |
| **Audit-Not-Block** | The `@enforce` decorator records violations without interrupting the application. Block mode is opt-in. |
| **Surgical Containment** | `AnchorViolationError` blocks the specific payload but keeps the application session alive. |
| **Zero-Knowledge Proof** | Regulators verify compliance via `chain_hash` + `signature` without needing access to raw prompts/responses. |
| **Multi-Dialect Export** | One `AuditEntry` can be exported as RBI (Sutras), SEC (8-K), or EU AI Act (Article 12) format. |

---

> *Version: v4.3.5 (engine) · v5.1.1 (sovereign mesh) · Last updated: 2026-04-27*
