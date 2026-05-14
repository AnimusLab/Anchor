# Anchor — System Architecture (Kernel v5.0.2)

> **`anchor`** = The Cryptographic Enforcement Kernel for Agentic AI

---

## 01. System Overview

```mermaid
graph TD
    A["🔬 Layer 1: Static Engine\n(AST Scanning)"]
    B["🛡️ Layer 2: Runtime\n(Live Interceptor)"]
    C["💎 Diamond Cage\n(WASM Sandbox)"]
    D["📜 Governance\n(9 Domains · 6 Regulators)"]
    E["🖋️ Decision Auditor\n(Crypto Audit Chain)"]

    A --> D
    B --> D
    C --> A
    B -->|"audit chain"| E

    style A fill:#1e293b,stroke:#06b6d4,color:#e2e8f0
    style B fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style C fill:#1e293b,stroke:#a855f7,color:#e2e8f0
    style D fill:#0f172a,stroke:#10b981,color:#e2e8f0
    style E fill:#0f172a,stroke:#f97316,color:#e2e8f0
```

---

## 02. Repo Structure: `anchor` (Core Kernel)

```
anchor/
├── cli.py                       # anchor init / check / heal / sync
├── core/
│   ├── engine.py                # PolicyEngine (AST + regex scan)
│   ├── loader.py                # Federation loader
│   ├── constitution.py          # Remote SHA-256 integrity
│   ├── crypto.py                # HMAC-SHA256 signing
│   ├── sandbox.py               # Diamond Cage (WASM)
│   ├── healer.py                # Auto-fix suggestions
│   ├── verdicts.py              # Architectural drift
│   ├── model_auditor.py         # ML weight auditing
│   └── policy_loader.py         # policy.anchor merge
├── runtime/
│   ├── __init__.py              # activate() / enforce()
│   ├── guard.py                 # AnchorGuard API
│   ├── decision_auditor.py      # Crypto audit chain
│   ├── models.py                # AuditEntry (RBI/SEC/EU dialects)
│   └── interceptors/
│       ├── framework.py         # 9 SDK patches (wrapt)
│       ├── http_backstop.py     # requests/httpx catch-all
│       ├── output_scanner.py    # Response scanner
│       └── provider_registry.py # 30+ AI API domains
├── adapters/                    # tree-sitter (Py/TS/Rust/Go/Java)
├── plugins/                     # safetensors / gguf / huggingface
└── governance/
    ├── constitution.anchor      # Root manifest
    ├── mitigation.anchor        # Detection patterns
    ├── domains/ (9)             # SEC·ETH·PRV·ALN·AGT·LEG·OPS·SUP·SHR
    ├── frameworks/ (3)          # FINOS · OWASP · NIST
    └── government/ (6)          # RBI · EU · SEC · SEBI · CFPB · FCA
```

---

## 03. Layer 1 — Static Engine

```mermaid
graph TD
    A["git commit"] --> B["Pre-Commit Hook"]
    B --> C["tree-sitter\nAST Parser"]
    C --> D["5 Language Adapters\nPy · TS · Rust · Go · Java"]
    D --> E["Rule Evaluation"]
    F["constitution.anchor\n+ 9 Domains"] --> E
    G["policy.anchor\n⬆️ Raise Only"] -->|"merge"| E
    H["mitigation.anchor\nDetection Patterns"] --> E
    E --> I["ID Aggregation\nSEC + OWASP + EU"]
    I --> J["violations.txt\n+ anchor-report.json"]

    style G fill:#422006,stroke:#f59e0b,color:#fef3c7
    style F fill:#0c4a6e,stroke:#06b6d4,color:#e0f2fe
```

> [!NOTE]
> **`policy.anchor`** lets each client add private rules and raise severity thresholds — but can **never lower** the constitutional floor. The governance baseline is absolute. (`enforce_raise_only: true`)

---

## 04. Layer 2 — SDK Interception

```mermaid
graph TD
    A["Developer's App\nimport anchor.runtime"] --> B
    B["SDK Patches\n(9 providers via wrapt)"]
    B --> C["Prompt Scanner"]
    A --> D["HTTP Backstop\nrequests · httpx"]
    D --> E["Provider Registry\n30+ AI API domains"]
    E --> C

    C -->|"blocker/error"| F["🔴 BLOCK\nAnchorViolationError"]
    C -->|"warning"| G["🟡 WARN\nlog + pass through"]
    C -->|"any"| H["🟢 AUDIT\nsilent record"]

    style F fill:#7f1d1d,stroke:#ef4444,color:#fecaca
    style G fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style H fill:#14532d,stroke:#22c55e,color:#dcfce7
```

**Patched SDKs:** OpenAI · Anthropic · Google Gemini · LangChain · Ollama · Groq · Cohere · Mistral · HuggingFace

> [!IMPORTANT]
> **BLOCK does NOT kill the session.** It raises a catchable `AnchorViolationError` — blocks the specific payload but keeps the application alive. The developer catches the exception and substitutes a safe response.

---

## 05. Layer 2 — Audit Chain (DAC)

```mermaid
graph TD
    A["Response Scanner\nSecrets · Shell · SQL · PII"]
    A --> B["ETH Compliance\nAho-Corasick proxies\nExplainability check"]
    B --> C["DecisionAuditor"]
    C --> D["SHA-256\nfindings_hash + prev_hash\n→ chain_hash"]
    D --> E["HMAC-SHA256\nSigned with\nANCHOR_SECRET_KEY"]
    E --> F["Local JSONL Ledger"]

    C --> G["Dialect Translation"]
    G --> H["RBI\nSeven Sutras"]
    G --> I["SEC\n8-K Materiality"]
    G --> J["EU\nArt. 12 Logging"]

    style E fill:#0c4a6e,stroke:#06b6d4,color:#e0f2fe
```

---

## 06. Diamond Cage (WASM Sandbox)

```mermaid
graph TD
    A["anchor check --sandbox"] --> B["DiamondCage\nWasmEdge + Python WASM"]
    B --> C["Isolation\nFS: /app only\nNetwork: Blocked\nEnv: Stripped"]
    B --> D["Run Original\n→ Snapshot A"]
    B --> E["Run Patched\n→ Snapshot B"]
    D --> F["Compare\nstdout · stderr\nexit code · timing"]
    E --> F
    F --> G["✅ PROVED_SAFE"]
    F --> H["⚠️ CHANGED"]
    F --> I["🔴 MALICIOUS"]

    style G fill:#14532d,stroke:#22c55e,color:#dcfce7
    style I fill:#7f1d1d,stroke:#ef4444,color:#fecaca
```

---

## Key Principles

| Principle | How |
|---|---|
| **Constitutional Floor** | `policy.anchor` can only RAISE severity, never lower |
| **Federated ID** | SEC-007 → OWASP-LLM-02 → EU-ART-15 via alias chains |
| **Surgical Containment** | `AnchorViolationError` blocks payload, keeps session alive |
| **Multi-Dialect** | One AuditEntry → RBI Sutras / SEC 8-K / EU Art.12 |
| **Zero Intent Drift** | Mathematical enforcement of initial intent via cryptographic sealing |

---

**AnimusLab** // *System Witness* // 2026
