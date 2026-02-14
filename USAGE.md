# Anchor CLI Command Reference

Anchor v2.8.1 provides a unified interface for code auditing, model weight validation, and governance management.

---

## 1. **anchor init**

Initializes the Anchor governance environment in the current directory.

```bash
anchor init [OPTIONS]
```

### Options

| Flag                 | Description                                                          |
| -------------------- | -------------------------------------------------------------------- |
| `--sandbox`          | Installs the **Diamond Cage** (WASM sandbox) for secure model audits |
| `--policy-name TEXT` | Name for your local policy file. Default: `policy.anchor`            |

### What It Does

1. Creates `.anchor/` directory for caching rules and storing local policies.
2. Deploys reference copies of the **Constitution** (`constitution.anchor.example`) and **Mitigation Catalog** (`mitigation.anchor.example`).
3. Generates a boilerplate local `policy.anchor` for project-specific overrides.
4. Auto-configures `.gitignore` to protect sensitive local policies.
5. Installs a **Git Pre-Commit Hook** to prevent violations from being committed.

---

## 2. **anchor check**

The universal enforcement command for code repositories and AI models.

```bash
anchor check [OPTIONS] [PATH]
```

### Core Options

| Flag                          | Description                                                 |
| ----------------------------- | ----------------------------------------------------------- |
| `-d, --dir, --directory PATH` | Directory to scan for code violations                       |
| `-m, --model PATH`            | Path to LLM model weights (GGUF, SafeTensors)               |
| `--metadata PATH`             | Path to training metadata JSON for model audits             |
| `-c, --context PATH`          | Path to a **Markdown Threat Model** for dynamic enforcement |

### Reporting Options

| Flag                | Description                                         |
| ------------------- | --------------------------------------------------- |
| `--generate-report` | Generates `anchor_audit_report.md` (human-readable) |
| `-j, --json-report` | Generates `anchor-report.json` for CI/CD pipelines  |
| `--github-summary`  | Generates GitHub Actions Step Summary output        |
| `-v, --verbose`     | Shows detailed sync, loading, and scanning logs     |

### Advanced Options

| Flag                                             | Description                                       |
| ------------------------------------------------ | ------------------------------------------------- |
| `-p, --policy PATH`                              | Apply additional specific policy files            |
| `-s, --severity [info\|warning\|error\|blocker]` | Minimum severity level to report. Default: `info` |
| `--exclude PATH`                                 | Paths to exclude from scan (repeatable)           |
| `--no-sandbox`                                   | Disables Diamond Cage WASM sandbox                |
| `--server-mode`                                  | Optimized for server-side environments            |

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

_Anchor v2.8.1 | Zero-Trust Governance for the AI-Native Stack._
