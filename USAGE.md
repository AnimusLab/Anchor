# Anchor CLI — Command Reference

Anchor V5.0.1 — Deterministic Governance for the AI-Native Stack.

🌐 **[anchorgovernance.tech](https://anchorgovernance.tech)**

---

## Installation

```bash
# From PyPI (recommended)
pip install anchor-audit

# Or from source
git clone https://github.com/Tanishq1030/Anchor.git
cd Anchor && pip install -e .
```

---

## Cryptographic Identity & Provisioning (v5.0+)

Anchor v5.0 introduces a **Hierarchical Identity** model. Every project code-base must be cryptographically linked to a parent Organization via a secure `.env` configuration.

### 1. Provision Your Keys
Log in to your **Company Dashboard** at [app.anchorgovernance.tech](https://app.anchorgovernance.tech) and create a new project. You will receive:
- `ANCHOR_ENTITY_ID`: A unique, organization-prefixed project identifier.
- `ANCHOR_SECRET_KEY`: A high-entropy cryptographic secret.

### 2. Configure Your Environment
Create a `.env` file in your project root:

```env
ANCHOR_ENTITY_ID="your-org-prefix-project-name"
ANCHOR_SECRET_KEY="your-secret-key-from-dashboard"
ANCHOR_NETWORK_PROXY="https://app.anchorgovernance.tech/api"
```

### 3. Initialize & Link
Run `anchor init` to bind your local workspace to the mesh. This will verify your credentials and sync your organization's custom policies.

---

## 1. `anchor init`

Initializes the Anchor governance environment in the current directory.

```bash
anchor init [OPTIONS]
```

### Options

| Flag | Description |
|---|---|
| `--domains` | Comma-separated domains (all 9 core domains load by default: SEC, ETH, SHR, ALN, AGT, PRV, LEG, OPS, SUP) |
| `--frameworks` | Comma-separated frameworks: `finos`, `owasp`, `nist`, `all` |
| `--regulators` | Comma-separated regulators: `rbi`, `eu`, `sebi`, `cfpb`, `fca`, `sec`, `all` |
| `--all` | Install all available domains, frameworks, and regulators |
| `--sandbox` | Installs the **Diamond Cage** (WASM sandbox) for behavioral verification |
| `--no-sign` | Skips remote GOVERNANCE.lock fetch for offline initialisation |
| `--policy-name TEXT` | Name for your local policy file (default: `policy.anchor`) |

### What It Does

1. Creates the `.anchor/` workspace:
   - `domains/` — core domain rule files
   - `frameworks/` — FINOS, OWASP, NIST
   - `government/` — RBI, EU AI Act, SEBI, CFPB, FCA, SEC
   - `violations/` — `governance_violations.txt`, `drift_violations.txt`
   - `reports/` — `governance_audit.md`, `drift_audit.md`
   - `telemetry/` — `governance_report.json`, `drift_report.json`
2. Deploys and verifies the Constitution and Mitigation Catalog.
3. Generates a boilerplate `policy.anchor` for project-specific overrides.
4. Installs a Git pre-commit hook to prevent violations from being committed.
5. Fetches `GOVERNANCE.lock` for integrity verification (unless `--no-sign`).

---

## 2. `anchor check`

Runs the full governance audit pipeline.

```bash
anchor check [OPTIONS] [PATH]
```

### Core Options

| Flag | Description |
|---|---|
| `-d, --dir PATH` | Directory to scan for code violations |
| `-m, --model PATH` | Path to LLM model weights (GGUF, SafeTensors) |
| `-c, --context PATH` | Path to a Markdown Threat Model for dynamic rule activation |
| `--severity LEVEL` | Minimum severity to report: `info`, `warning`, `error`, `blocker` |

### Reporting

| Flag | Description |
|---|---|
| `-j, --json-report` | Force generation of JSON telemetry (auto-on in CI) |
| `--github-summary` | Write a Markdown summary to `$GITHUB_STEP_SUMMARY` |
| `-v, --verbose` | Shows detailed sync, loading, and scanning logs |

---

## 3. `anchor check drift`

Analyzes the architectural integrity of the codebase.

```bash
anchor check drift [PATH]
```

Analyzes symbols (classes, functions) to determine if usage matches original intent. Verdict: **Aligned**, **Semantic Overload**, **Intent Violation**, or **Dependency Inertia**. Generates `drift_violations.txt` and `drift_audit.md`.

---

## 4. `anchor heal`

The "Sovereign Scalpel" — autonomous remediation of security violations.

```bash
anchor heal [OPTIONS] [PATH]
```

| Flag | Description |
|---|---|
| `--apply` | Automatically applies all suggested fixes to the code |
| `--status` | Shows a summary of fixed vs. pending violations |

Reads `governance_violations.txt`, proposes deterministic AST patches, and provides an interactive diff before applying.

---

## 5. `anchor sync --restore`

Fetches authoritative governance files from the Anchor registry and restores any tampered or modified files. Logs all restores to `.anchor/logs/sync.log` with a chain hash.

```bash
anchor sync --restore
```

---

## Governance Pipeline

When you run `anchor check`, the following pipeline executes:

```
┌──────────────────────────────────────────────────────────┐
│  1. SYNC  — Fetch constitution + mitigation catalog      │
│             from cloud. Verify SHA-256 integrity.        │
├──────────────────────────────────────────────────────────┤
│  2. JOIN  — Merge constitution risks (WHAT) with         │
│             mitigation patterns (HOW) → Executable Rules │
├──────────────────────────────────────────────────────────┤
│  3. MERGE — Apply local policy.anchor overrides          │
│             (State Law overrides Constitution by rule ID) │
├──────────────────────────────────────────────────────────┤
│  4. SCAN  — Run PolicyEngine with tree-sitter AST +      │
│             regex patterns against target directory      │
├──────────────────────────────────────────────────────────┤
│  5. CAGE  — Diamond Cage behavioral verification         │
│             (WASM sandbox, proves security invariants)   │
├──────────────────────────────────────────────────────────┤
│  6. REPORT— Generate violation report, exit 0 (pass)     │
│             or 1 (fail)                                  │
└──────────────────────────────────────────────────────────┘
```

---

## Common Use Cases

### A. CI/CD Pipeline Enforcement

```bash
anchor check --dir ./src --severity error --json-report --github-summary
```

### B. Full Regulatory Audit (all frameworks + regulators)

```bash
anchor init --all && anchor check ./src --verbose
```

### C. Bridge Mode (Threat Model → Enforcement)

Enforce only the rules identified in an AI-generated threat model:

```bash
anchor check --context docs/threat_model.md --dir ./src
```

### D. Secure Model Onboarding

Validate a downloaded model before allowing it into production:

```bash
anchor check --model models/mistral-7b.gguf --generate-report
```

### E. Local Dev Scan

```bash
anchor check --dir . --severity warning
```

---

## Governance Status Codes

| Exit Code | Meaning |
|---|---|
| `0` | **Passed** — No blocking violations found |
| `1` | **Failed** — Critical security or compliance violations detected |

---

## Suppressing Findings

```python
# Suppress a specific rule
result = subprocess.run(cmd)  # anchor: ignore ANC-018

# Suppress all rules on this line
os.environ.get("KEY")  # anchor: ignore-all
```

- **Line-level only** — the comment must be on the same line as the violation.
- **Git-blamed** — Anchor records who added each suppression via `git blame`.
- **Auditable** — Suppressed findings appear in the report with the author name.

---

## Floor Severity (Override Protection)

Each constitution rule has a `min_severity` — the floor that `policy.anchor` overrides cannot go below:

```yaml
# Your policy.anchor — REJECTED because floor is 'error'
- id: "ANC-009"
  severity: "warning"
```

```
Override REJECTED for ANC-009: Cannot downgrade severity to 'warning'.
Constitutional floor is 'error'.
```

| Floor | Allowed Overrides | Blocked Overrides |
|---|---|---|
| `blocker` | None (locked) | Everything |
| `error` | `error`, `blocker` | `warning`, `info` |
| `warning` | `warning`+ | `info` |
| `info` | Full freedom | — |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANCHOR_CONSTITUTION_URL` | GitHub Raw URL | Override constitution source |
| `ANCHOR_MITIGATION_URL` | GitHub Raw URL | Override mitigation catalog source |
| `ANCHOR_VERBOSE` | `false` | Enable debug output |
| `ANCHOR_FETCH_TIMEOUT` | `10` | Cloud sync timeout (seconds) |

---

_Anchor V4.3.5 · [anchorgovernance.tech](https://anchorgovernance.tech) · Apache 2.0_
