# Anchor-Audit Architecture Documentation

## 🏗️ System Design

### The Two-File System

Anchor-audit uses a **federated policy architecture** with two key files:

#### 1. `constitution.anchor` (Cloud Constitution)

**Location:** Cloud (GitHub Raw URL)  
**Purpose:** Universal FINOS risk catalog  
**Managed By:** FINOS Foundation  
**Immutable:** Banks cannot tamper with this

**Example:**

```yaml
version: "2.1"
rules:
  - id: "RI-24"
    name: "Supply Chain Attack Prevention"
    match:
      type: "import"
      module: "requests"
    message: "Risk RI-24: Raw network access forbidden."
    severity: "blocker"

  - id: "AI-20"
    name: "Model Hallucination Risk"
    match:
      type: "function_call"
      name: "exec"
    message: "Risk AI-20: Dynamic execution forbidden."
    severity: "critical"
```

**Download:** `anchor init` fetches this from cloud

---

#### 2. `policy.anchor` (Local Overrides)

**Location:** Project directory  
**Purpose:** Bank/company-specific rules  
**Managed By:** Individual organizations  
**Extends:** Can add new rules OR override severity

**Example:**

```yaml
version: "2.1"
extends: "https://raw.githubusercontent.com/finos/anchor-rules/main/master.anchor"

rules:
  - id: "BANK-001"
    name: "Internal API Requirement"
    match:
      type: "import"
      module: "external_api"
    message: "Use internal API gateway instead."
    severity: "warning"

  # Override FINOS rule severity
  - id: "RI-24"
    severity: "critical" # Downgrade from blocker to critical
```

---

### Why This Design?

#### ✅ **Security:**

- Banks cannot tamper with FINOS rules (cloud-hosted)
- Local overrides are transparent (version controlled)
- Audit trail: Git history shows who changed what

#### ✅ **Flexibility:**

- Banks can add custom rules for internal policies
- Can adjust severity for specific contexts
- Gradual adoption (start with warnings, escalate to blockers)

#### ✅ **Federation:**

- Single source of truth (FINOS cloud)
- Local customization (policy.anchor)
- Merge strategy: Local rules extend/override cloud rules

---

## 🔄 How It Works

### Step 1: Initialization

```bash
anchor init
```

**What Happens:**

1. Downloads `constitution.anchor` from cloud
2. Creates `policy.anchor` template locally
3. Both files are ready for enforcement

---

### Step 2: Enforcement

```bash
anchor check --dir ./src
```

**Execution Flow:**

1. Load `constitution.anchor` (cloud rules)
2. Load `policy.anchor` (local rules)
3. Merge: Local rules override cloud rules by ID
4. Scan code with tree-sitter AST
5. Report violations

---

### Step 3: GenAI Integration

```bash
anchor check --context threat_model.md --dir ./src
```

**Execution Flow:**

1. Parse `threat_model.md` for Risk IDs (RI-24, AI-20)
2. Filter rules from `constitution.anchor` matching those IDs
3. Merge with `policy.anchor`
4. Enforce only the relevant risks
5. Block build if violations found

---

## 🎯 The `.example` Pattern

### `constitution.anchor.example`

**Purpose:** Reference file (like `.env.example`)  
**Usage:** Shows structure, doesn't affect enforcement  
**Created By:** `anchor init --example`

**Why?**

- New users can see the format
- Doesn't interfere with cloud fetch
- Version controlled for documentation

---

## 🤖 GitHub Actions Integration

### Pre-Commit Checks

```yaml
- name: Run Anchor-Audit
  run: anchor check --dir .
```

**What Happens:**

1. Downloads `constitution.anchor` from cloud
2. Uses project's `policy.anchor`
3. Blocks PR if violations found
4. Comments on PR with violation details

**Similar to:** Apache Beam's Gemini bot

---

## 📊 Architecture Diagram

```
Developer Workstation
├── anchor init
│   ├── Downloads constitution.anchor (cloud)
│   └── Creates policy.anchor (local template)
│
├── anchor check --dir .
│   ├── Loads constitution.anchor
│   ├── Loads policy.anchor
│   ├── Merges rules (local overrides cloud)
│   └── Enforces via tree-sitter
│
└── anchor check --context threat_model.md
    ├── Parses markdown for Risk IDs
    ├── Filters constitution.anchor by Risk IDs
    ├── Merges with policy.anchor
    └── Enforces only relevant risks

GitHub Actions (CI/CD)
├── Checkout code
├── Install anchor-audit
├── Download constitution.anchor (cloud)
├── Run anchor check
└── Block PR if violations found
```

---

## 🔐 Security Model

### Tamper-Proof Design

**Problem:** What if a bank modifies `constitution.anchor` locally?

**Solution:**

1. Cloud file is fetched fresh on every `anchor init`
2. GitHub Actions re-downloads from cloud (not from repo)
3. Checksum verification (future enhancement)
4. Audit logs show which rules were active

**Example Attack Prevention:**

```bash
# Bank tries to remove RI-24 from local constitution.anchor
# GitHub Actions workflow:
curl -o constitution.anchor https://raw.githubusercontent.com/finos/anchor-rules/main/master.anchor
# ↑ This overwrites any local tampering
```

---

## 🎯 Key Takeaways

1. **Two Files, Two Purposes:**
   - `constitution.anchor` = Universal truth (cloud)
   - `policy.anchor` = Local customization (repo)

2. **No Redundant Catalog:**
   - `patterns/risk_catalog.yaml` was a mistake
   - All risks live in `constitution.anchor`

3. **GenAI Integration:**
   - Markdown parser extracts Risk IDs
   - `RiskMapper` filters `constitution.anchor` by those IDs
   - Only relevant rules are enforced

4. **GitHub Actions Ready:**
   - Works like Apache Beam's pre-commit checks
   - Downloads cloud constitution on every run
   - Blocks PRs with violations

---

**This is the architecture you designed. I just needed to understand it correctly.** 🎯
