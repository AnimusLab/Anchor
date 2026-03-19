# Anchor CLI Command Reference

Anchor v4.0.0 provides a unified interface for security auditing, architectural drift analysis, autonomous remediation, and runtime governance.

---

## 1. **anchor init**

Initializes the Anchor governance environment in the current directory.

```bash
anchor init [OPTIONS]
```

### Options

| Flag                 | Description                                                          |
| -------------------- | -------------------------------------------------------------------- |
| `--domains`          | Comma-separated domains (all core domains load by default: SEC, ETH, SHR, ALN, AGT, PRV, LEG, OPS, SUP) |
| `--frameworks`       | Comma-separated frameworks (finos, owasp, nist, all)                 |
| `--regulators`       | Comma-separated regulators (rbi, eu, sebi, cfpb, fca, sec, all)      |
| `--all`              | Install all available domains, frameworks, and regulators            |
| `--sandbox`          | Installs the **Diamond Cage** (WASM sandbox) for secure model audits |
| `--policy-name TEXT` | Name for your local policy file. Default: `policy.anchor`            |

### What It Does

1. Creates the `.anchor/` workspace with standard subdirectories:
   - `violations/`: For detailed text results (`governance_violations.txt`, `drift_violations.txt`).
   - `reports/`: For markdown documentation (`governance_audit.md`, `drift_audit.md`).
   - `telemetry/`: For CI/CD JSON exports (`governance_report.json`, `drift_report.json`).
2. Deploys reference copies of the Constitution and Mitigation Catalog; installs all core domains by default (SEC, ETH, SHR, ALN, AGT, PRV, LEG, OPS, SUP).
3. Generates a boilerplate local `policy.anchor` for project-specific overrides.
4. Installs a Git pre-commit hook to prevent violations from being committed.
5. Fetches `GOVERNANCE.lock` unless `--no-sign` is passed; `anchor sync --restore` verifies integrity later in CI.

---

### Core Options

| Flag                          | Description                                             |
| ----------------------------- | ------------------------------------------------------- |
| `-d, --dir, --directory PATH` | Directory to scan for code violations                   |
| `-m, --model PATH`            | Path to LLM model weights (GGUF, SafeTensors)           |
| `-c, --context PATH`          | Path to a Markdown Threat Model for dynamic enforcement |

### Reporting

Anchor V4 automatically generates human-readable reports and machine-readable telemetry in the `.anchor/` folder, including severity breakdowns (blocker/error/warning/info) in terminal output.

| Flag                | Description                                        |
| ------------------- | -------------------------------------------------- |
| `-j, --json-report` | Force generation of JSON telemetry (auto-on in CI) |
| `-v, --verbose`     | Shows detailed sync, loading, and scanning logs    |

---

## 3. **anchor check drift**

Analyzes the architectural integrity of the codebase.

```bash
anchor check drift [PATH]
```

### What It Does

1. Analyzes symbols (classes, functions) to determine if their usage matches their original intent.
2. Assigns a verdict: **Aligned**, **Semantic Overload**, **Intent Violation**, or **Dependency Inertia**.
3. Generates `drift_violations.txt` and `drift_audit.md`.

---

## 4. **anchor heal**

The "Sovereign Scalpel" — autonomous remediation of security violations.

```bash
anchor heal [OPTIONS] [PATH]
```

### Options

| Flag       | Description                                           |
| ---------- | ----------------------------------------------------- |
| `--apply`  | Automatically applies all suggested fixes to the code |
| `--status` | Shows a summary of fixed vs. pending violations       |

### What It Does

1. Reads the latest `governance_violations.txt`.
2. Proposes deterministic AST patches for high-confidence violations.
3. Provides an interactive diff for developer review.

---

## Governance Pipeline

When you run `anchor check`, the following pipeline executes:

```
┌──────────────────────────────────────────────────────────┐
│  1. SYNC — Fetch constitution.anchor + mitigation.anchor │
│     from cloud (GitHub Raw). Verify SHA-256 integrity.   │
├──────────────────────────────────────────────────────────┤
│  2. JOIN — Merge constitution risks (WHAT) with          │
│     mitigation patterns (HOW) -> Executable Rules.       │
├──────────────────────────────────────────────────────────┤
│  3. MERGE — Apply local policy.anchor overrides          │
│     (State Law overrides Constitution by rule ID).       │
├──────────────────────────────────────────────────────────┤
│  4. SCAN — Run PolicyEngine with tree-sitter AST +       │
│     regex patterns against target directory.             │
├──────────────────────────────────────────────────────────┤
│  5. REPORT — Generate violation report, exit with        │
│     code 0 (pass) or 1 (fail).                           │
└──────────────────────────────────────────────────────────┘
```

---

## Common Use Cases

### A. CI/CD Pipeline Enforcement

Block insecure code from being merged via GitHub Actions.

```bash
anchor check --dir ./src --severity error --json-report --github-summary
```

### B. Bridge Mode (Threat Model -> Enforcement)

Enforce only the rules identified in an AI-generated threat model.

```bash
anchor check --context docs/threat_model.md --dir ./src
```

### C. Secure Model Onboarding

Validate a downloaded model before allowing it into production.

```bash
anchor check --model models/mistral-7b.gguf --metadata data/provenance.json --generate-report
```

### D. Local Code Audit

Scan your repository against the full 23-risk constitution.

```bash
anchor check --dir . --verbose
```

### E. Custom Severity Threshold

Only fail on critical issues during development, but block everything in CI.

```bash
# Development (permissive)
anchor check --dir . --severity error

# CI/CD (strict)
anchor check --dir . --severity warning --json-report
```

---

## Governance Status Codes

| Exit Code | Meaning                                                          |
| --------- | ---------------------------------------------------------------- |
| `0`       | **Passed** — No blocking violations found                        |
| `1`       | **Failed** — Critical security or compliance violations detected |

---

## Suppressing Findings

Suppress justified findings with inline comments:

```python
# Suppress a specific rule
result = subprocess.run(cmd)  # anchor: ignore ANC-018

# Suppress all rules on this line
os.environ.get("KEY")  # anchor: ignore-all
```

**Key behavior:**

- **Line-level only** — the comment must be on the same line as the violation.
- **Git-blamed** — Anchor records who added each suppression via `git blame`.
- **Auditable** — Suppressed findings appear in the report as "suppressed" with the author name.

---

## Floor Severity (Override Protection)

Each constitution rule has a `min_severity` — the floor that local `policy.anchor` overrides cannot go below:

```yaml
# Your policy.anchor
- id: "ANC-009"
  severity: "warning" # REJECTED — floor is "error"
```

```
Override REJECTED for ANC-009: Cannot downgrade severity to 'warning'.
Constitutional floor is 'error'.
```

| Floor     | Allowed Overrides  | Blocked Overrides |
| --------- | ------------------ | ----------------- |
| `blocker` | None (locked)      | Everything        |
| `error`   | `error`, `blocker` | `warning`, `info` |
| `warning` | `warning`+         | `info`            |
| `info`    | Full freedom       | —                 |

---

## Environment Variables

All optional. See [`.env.example`](.env.example) for a full reference.

| Variable                  | Default        | Description                        |
| ------------------------- | -------------- | ---------------------------------- |
| `ANCHOR_CONSTITUTION_URL` | GitHub Raw URL | Override constitution source       |
| `ANCHOR_MITIGATION_URL`   | GitHub Raw URL | Override mitigation catalog source |
| `ANCHOR_VERBOSE`          | `false`        | Enable debug output                |
| `ANCHOR_FETCH_TIMEOUT`    | `10`           | Cloud sync timeout (seconds)       |

---

_Anchor v3.0.0-alpha | Deterministic Governance for the AI-Native Stack._
