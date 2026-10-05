# AnimusLab: Product Studio Architecture & System Topology

AnimusLab operates as a **product studio**, not a monolithic platform.

Each product within the AnimusLab ecosystem was built to solve a concrete, first-principles engineering problem encountered while building real-world AI, financial, and security infrastructure. Every product is independently deployable, standalone in its execution lifecycle, and independently governed. They interoperate by choice and contract, not through hard architectural dependencies.

The unifying engineering principle across AnimusLab is **dogfooding**: we use our own tools inside our other products. When an architectural limitation emerges in one system, we build an isolated, production-grade engine to solve it—releasing it as an open tool for the broader engineering community.

```
                                  AnimusLab
                             (Product Studio Model)
                                       │
      ┌─────────────────┬──────────────┼──────────────┬────────────────┐
      ▼                 ▼              ▼              ▼                ▼
┌───────────┐    ┌─────────────┐ ┌───────────┐ ┌──────────────┐ ┌─────────────┐
│  Anchor   │    │ AnchorGrid  │ │QuantForge │ │ Shadow_Watch │ │    FORGE    │
│ Governance│    │  P2P Hub    │ │ Financial │ │ Behavioral   │ │ File-Based  │
│  Engine   │    │ (Hive Mind) │ │ Ecosystem │ │ Trust Engine │ │ Rust DB     │
└─────┬─────┘    └──────┬──────┘ └─────┬─────┘ └──────┬───────┘ └──────┬──────┘
      │                 │              │              │                │
(Open Engine)    (Federated LoRA) (TUI + Agent) (Silent Trust)    (Cloud Storage
      │                 │              │              │            -> DB Engine)
      ▼                 ▼              ▼              ▼                ▼
 [anchor-web]    [Weight Merges] [Quant-AI API] [Risk Scoring]    [.forge binary]
 (SaaS Control)  (Proof-of-Loss)
```

---

## 1. Product Breakdown & Genesis Narratives

### 1.1 Anchor — AI Governance & Verification Engine
* **Status**: Open Source Core (`anchor-audit` / `anchor_core_rs`) with commercial control plane (`anchor-web`).
* **Origin**: When building the federated training workflows in **AnchorGrid-Hub**, participating institutions could fine-tune base models on proprietary data and submit adapter weight merge requests back to the network. This raised two fundamental questions:
  1. *How do we mathematically verify that incoming weights improve capabilities rather than degrading performance, injecting backdoor triggers, or causing alignment drift?*
  2. *How do we deterministically govern runtime AI tool execution and model outputs against statutory requirements (EU AI Act, RBI FREE-AI, SEC Reg SCI) with zero-latency overhead?*

* **Technical Core**:
  - **Static AST Scanner**: Zero-copy Rust analysis engine parsing code and prompt definitions against formal invariant specifications (`.anchor` dialect files).
  - **Runtime Boundary Enforcement**: Sub-millisecond synchronous intercept gate enforcing hard statutory constraints before LLM calls or tool actions execute.
  - **Decision Audit Chain (DAC)**: Cryptographically signed, hash-chained audit trails providing verifiable evidence for regulatory compliance.
* **Separation Boundary**:
  - The `anchor` CLI and Rust engine are 100% open-source, local-first, and have zero cloud dependencies.
  - `anchor-web` provides the hosted enterprise multi-tenant control plane, Merkle DAG audit indexers, automated regulatory statute sync, and executive audit report generation.

---

### 1.2 AnchorGrid-Hub — Federated P2P Model Marketplace
* **Status**: Active Development.
* **Origin**: Centralized AI hosting requires organizations to transmit sensitive proprietary data to external cloud providers. AnchorGrid-Hub was built to enable decentralized, federated intelligence without data leakage.
* **Technical Core**:
  - **BitTorrent-Style Weight Distribution**: High-efficiency P2P distribution of frozen base models and modular LoRA adapters.
  - **Federated LoRA Training**: Clients train lightweight adapters (~50MB) locally on private data (SEC filings, proprietary trading data) without exposing raw datasets.
  - **Proof-of-Loss Benchmarking**: Incoming adapter submissions are scored against a standardized cross-entropy loss evaluation benchmark before acceptance.
  - **Anchor Integration**: Anchor serves as the optional verification engine on merge pipelines to validate statutory compliance and rule invariants before weights enter the master checkpoint.

---

### 1.3 QuantForge — Financial AI & Developer Workstation
* **Status**: Active Development (Two Independent Components).
* **Origin**: Traditional financial analytics terminals (e.g., Bloomberg Terminal) are expensive, proprietary GUI-locked silos that cannot be programmatically driven by modern AI agents. QuantForge was engineered to deliver a developer-first, terminal-native workspace.
* **Technical Core**:
  - **QuantForge Terminal**: A high-performance TUI (Terminal User Interface) workstation built for developers and quantitative researchers. Fully scriptable, keyboard-driven, and API-accessible.
  - **QuantForge-AI**: Specialized financial reasoning agent trained on SEC filings, macro indicators, and quantitative mechanics.
  - **Symbiotic Execution**: QuantForge Terminal acts as an execution tool for QuantForge-AI, while QuantForge-AI powers contextual assistant capabilities within the terminal. Both function completely independently.

---

### 1.4 Shadow_Watch — Continuous Behavioral Trust Engine
* **Status**: Active Standalone Python/FastAPI Library (`shadowwatch`).
* **Origin**: Traditional multi-factor authentication (TOTP codes, SMS OTPs, repetitive hardware prompts) introduces high operational friction in developer and quantitative trading workflows. Shadow_Watch was created to establish frictionless, continuous behavioral security.
* **Technical Core**:
  - **Ensemble Multi-Signal Trust Scorer**:
    $$\text{Trust} = 0.30 \cdot S_{\text{IP}} + 0.25 \cdot S_{\text{Device}} + 0.20 \cdot S_{\text{Behavior}} + 0.15 \cdot S_{\text{Time}} + 0.10 \cdot S_{\text{API}}$$
  - **Localized Behavioral Anomaly Model**: Evaluates interaction patterns using Laplace-smoothed Kullback-Leibler (KL) divergence on action-type distributions, velocity z-scores, and entity novelty rates.
  - **Jaccard Entity Fingerprinting**: Tracks asset/symbol interaction continuity to immediately detect silent account takeovers or scraping activity.
  - **Frictionless Decision Gate**: Trust scores $\ge 0.80$ allow silent access; step-up challenges (`require_mfa` / `block`) are triggered only when anomaly boundaries are breached.

---

### 1.5 FORGE — File-Oriented Rust Grade Storage Engine
* **Status**: Active Rust Engine (`forge`).
* **Origin**: Prototyping modern applications typically incurs the overhead and recurring cost of provisioning dedicated cloud database instances (PostgreSQL, Supabase, Neon). FORGE was engineered to turn existing, unmetered cloud file storage into an authenticated, queryable relational/document database.
* **Technical Core**:
  - **Custom `.forge` Binary Spec**: Custom 64-byte binary header (`FORGE001` magic bytes, schema hash, row counts), schema definition block, indexing offset table, and binary-encoded record blocks.
  - **In-Memory Query Engine & WAL**: Rust async runtime (`axum`, `tokio`) with Write-Ahead Logging (WAL) and idempotency tracking.
  - **Universal Storage Adapter**: Interfaces with Google Drive, Cloudflare R2, AWS S3, or generic HTTP storage backends to persist `.forge` binary assets via clean `/v1/data/:collection` REST APIs.

---

## 2. Interoperability & Dogfooding Matrix

The table below details how AnimusLab products integrate internally. **Every integration is an optional consumer contract, not a mandatory runtime dependency:**

| Host System | Integrated Tool | Nature of Integration | Operational Without Tool? |
|---|---|---|---|
| **AnchorGrid-Hub** | **Anchor** | Adapter merge request validation & safety gate | **Yes** (Runs standard Proof-of-Loss checks without AST governance) |
| **AnchorGrid-Hub** | **Shadow_Watch** | Continuous behavioral authentication for trading/API endpoints | **Yes** (Falls back to standard token/password auth) |
| **QuantForge Terminal** | **QuantForge-AI** | Embedded quantitative reasoning agent | **Yes** (Operates as standalone manual financial TUI) |
| **QuantForge-AI** | **QuantForge Terminal** | Market data fetching and scriptable analysis execution | **Yes** (Can interface with external Python/HTTP APIs) |
| **anchor-web** | **Shadow_Watch** | Zero-friction session continuity and anomaly detection | **Yes** (Operates with standard JWT / TOTP clearance auth) |
| **Animus Tooling** | **FORGE** | Zero-cost prototype persistence layer | **Yes** (Can connect to standard PostgreSQL/SQLite instances) |

---

## 3. Operational Independence Guarantee

1. **No Shared Monolithic Runtime**: There is no centralized daemon or omnibus runtime required across projects.
2. **Zero Vendor Lock-In**: Anchor can audit any LLM stack (LangChain, LlamaIndex, raw OpenAI/Anthropic/vLLM clients) without requiring QuantForge or AnchorGrid.
3. **Standalone Open-Source Repositories**: Each tool maintains its own test suites, dependency trees, and release cycles.

---

## 4. Evaluation Guidance for Technical Auditors

When auditing AnimusLab technologies for regulatory compliance or institutional deployment:
- **Audit Anchor & `anchor-web`** for AST policy compilation, statutory dialects (EU AI Act, RBI FREE-AI, SEC Reg SCI), runtime guard performance, and Decision Audit Chain (DAC) cryptographic integrity.
- **Audit Shadow_Watch** for continuous behavioral anomaly detection and trust scoring algorithms.
- **Audit FORGE** for custom binary parsing safety and WAL persistence guarantees.

*Maintained by AnimusLab Engineering.*
