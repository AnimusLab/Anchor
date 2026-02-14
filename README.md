# Anchor — The Federated Governance Engine for AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Production](https://img.shields.io/badge/Status-Production-green.svg)]()
[![Version: 2.8.1](https://img.shields.io/badge/Version-2.8.1-blue.svg)]()

> "Code drifts. Intent shouldn't. Governance must scale."

Anchor is an **autonomous governance platform** for the AI-Native era. It ensures that your **Code**, **AI Models**, and **Agent Pipelines** comply with universal standards ([FINOS AI Risk Taxonomy](https://www.finos.org/)) and local company policies — all enforced deterministically via AST analysis, with zero LLM cost.

---

## What's New in v2.8.1

- **23-Risk Coverage**: Full mapping of the [FINOS AI Risk & Controls](https://www.finos.org/) taxonomy to `ANC-001` through `ANC-023`.
- **Dual-File Governance Architecture**: Separated **WHAT** risks exist (`constitution.anchor`) from **HOW** to detect them (`mitigation.anchor`).
- **Context-Aware Detection**: Refined mitigation patterns that avoid false positives (e.g., only flagging f-strings in prompt variables, not CLI output).
- **SHA-256 Tamper-Proofing**: Both governance files are cryptographically sealed. Any local edit to the cached rules blocks the audit.
- **Governance Joiner**: Runtime merger of constitution rules with mitigation patterns into executable enforcement policies.

---

## The Federated Model

Anchor operates on a three-layer architecture inspired by Constitutional Law:

| Layer                  | File                  | Purpose                                                                                       |
| ---------------------- | --------------------- | --------------------------------------------------------------------------------------------- |
| **Constitution**       | `constitution.anchor` | Defines **WHAT** risks exist (23 FINOS risks -> `ANC-XXX` IDs). Cloud-synced, SHA-256 sealed. |
| **Mitigation Catalog** | `mitigation.anchor`   | Defines **HOW** to detect each risk (regex + AST patterns). Cloud-synced, SHA-256 sealed.     |
| **State Law**          | `policy.anchor`       | **Your** local overrides. Change severity, add company-specific rules. Fully editable.        |

**Merge Strategy**: State Law overrides Constitution by rule ID, **but only within the constitutional floor**. Each rule has a `min_severity` — the absolute minimum that no local policy can go below. Critical security rules (e.g., `ANC-007`, `ANC-022`) are locked at `blocker`. Companies can add entirely new rules or make existing rules stricter.

---

## Key Capabilities

### 1. Code Enforcement (v2.8)

Turns the FINOS AI Risk Taxonomy into executable CI/CD blockers using high-speed AST analysis (`tree-sitter`).

- **23-Risk Coverage**: Prompt injection, hallucination, data poisoning, model tampering, credential harvesting, and 18 more.
- **Bridge Mode**: Parse Markdown Threat Models and activate only the relevant rules dynamically.
- **Context-Aware Patterns**: Detection rules scoped to LLM-specific contexts (prompt variables, API calls), not generic code.

### 2. Model Auditing (Diamond Cage)

A vendor-agnostic plugin system to validate LLM model weights (GGUF, SafeTensors) inside a **WASM-based sandbox**.

- **Verify Provenance**: Ensure training data sources are license-compliant.
- **Analyze Weights**: Detect potential backdoors or corruption in model files.

### 3. The "Hybrid Healer" (v3 Vision)

Moves from "Blocking" to "Fixing." Deterministic AST patching replaces dangerous code with secure alternatives, verified inside the Diamond Cage.

[**View v3 Technical Roadmap**](V3_TECHNICAL_ROADMAP.md)

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/Tanishq1030/Anchor.git
cd Anchor
pip install -e .
```

### 2. Initialize

Sets up `.anchor/`, syncs the constitution & mitigation catalog, and installs the Git pre-commit hook.

```bash
anchor init
```

### 3. Scan Your Code

```bash
anchor check --dir ./src --verbose
```

### 4. Audit a Model

```bash
anchor check --model ./my-model.gguf --metadata ./metadata.json
```

**Full command reference**: [USAGE.md](USAGE.md)

---

## Suppressing Findings

When a finding is a **justified use** (e.g., your governance tool legitimately needs `subprocess`), suppress it with an inline comment:

### Suppress a Specific Rule

```python
result = subprocess.run(cmd, capture_output=True)  # anchor: ignore ANC-018
```

### Suppress All Rules on a Line

```python
os.environ.get("SECRET_KEY")  # anchor: ignore-all
```

### How It Works

| Feature         | Details                                                                       |
| --------------- | ----------------------------------------------------------------------------- |
| **Syntax**      | `# anchor: ignore ANC-XXX` (per-rule) or `# anchor: ignore-all`               |
| **Scope**       | Line-level only — the comment must be on the same line as the flagged code    |
| **Audit Trail** | Anchor uses `git blame` to record **who** authorized each suppression         |
| **Visibility**  | Suppressed findings appear in the report as "suppressed" with the author name |

> **Important**: Suppressions are tracked. Every suppressed finding is logged with the git blame author so your security team can audit who bypassed which rule and when.

### Example Report Output

```
TOTAL FINDINGS: 2 active violations.
6 suppressed findings (See report for audit trail)
```

---

## CI/CD Integration

Anchor acts as the "Gatekeeper" in GitHub Actions. If a PR violates the constitution, Anchor blocks the merge with a detailed violation report.

```yaml
# .github/workflows/anchor-audit.yml
- name: Run Governance Check
  run: |
    pip install anchor-audit
    anchor check --dir ./src --severity error --json-report --github-summary
```

---

## Project Structure

```
Anchor/
├── anchor/                     # Core package
│   ├── cli.py                  # CLI entry point (click)
│   ├── core/
│   │   ├── engine.py           # PolicyEngine — AST scanning via tree-sitter
│   │   ├── constitution.py     # SHA-256 integrity verification
│   │   ├── config.py           # Pydantic-validated settings (.env)
│   │   ├── policy_loader.py    # Federated policy merger
│   │   ├── mapper.py           # GenAI threat model -> rule mapper
│   │   ├── model_auditor.py    # Model weight validation (Diamond Cage)
│   │   ├── sandbox.py          # WASM sandbox (Wasmtime)
│   │   └── resources/          # Bundled .example reference files
│   ├── adapters/               # Language-specific tree-sitter adapters
│   └── plugins/                # Extensible plugin system
├── tests/                      # Test suite
│   ├── compliance_test.py      # 23-risk compliance validation
│   ├── test_integration.py     # Integration tests
│   └── fixtures/               # Test fixtures
├── constitution.anchor         # Universal Constitution (23 FINOS risks)
├── mitigation.anchor           # Mitigation Catalog (detection patterns)
├── .env.example                # Environment variable reference
├── setup.py                    # Package configuration (v2.8.1)
├── case-studies/               # Real-world audit case studies
├── docs/                       # Documentation
└── V3_TECHNICAL_ROADMAP.md     # v3 "Sovereign Scalpel" roadmap
```

---

## Security Architecture

### Tamper-Proofing

The universal `constitution.anchor` and `mitigation.anchor` are **cloud-fetched** and **SHA-256 sealed**:

```
┌─────────────────────────────────────────────────┐
│  GitHub Raw (Source of Truth)                    │
│  constitution.anchor  ->  SHA-256: 3745014B...  │
│  mitigation.anchor    ->  SHA-256: E3E32531...  │
└────────────────┬────────────────────────────────┘
                 │ fetch + verify
┌────────────────▼────────────────────────────────┐
│  .anchor/cache/ (Local)                         │
│  Hash mismatch -> INTEGRITY VIOLATION           │
│  Hash match    -> Proceed with audit            │
└─────────────────────────────────────────────────┘
```

No developer can weaken the rules to pass the audit. The hashes are baked into the Python package itself.

---

## Configuration

All settings are optional and loaded from `.env` or environment variables:

| Variable                  | Default        | Description                           |
| ------------------------- | -------------- | ------------------------------------- |
| `ANCHOR_CONSTITUTION_URL` | GitHub Raw URL | Override for air-gapped/mirror setups |
| `ANCHOR_MITIGATION_URL`   | GitHub Raw URL | Override for the mitigation catalog   |
| `ANCHOR_VERBOSE`          | `false`        | Enable detailed debug output          |
| `ANCHOR_FETCH_TIMEOUT`    | `10`           | Timeout (seconds) for cloud sync      |

See [`.env.example`](.env.example) for a full reference.

---

## Contributing

We welcome contributions! Whether it's new detection patterns, bug fixes, or documentation improvements.

**Quick links:**

- [Contributing Guide](CONTRIBUTING.md)
- [Open an Issue](https://github.com/Tanishq1030/Anchor/issues)
- [Discussions](https://github.com/Tanishq1030/Anchor/discussions)

### Ways to Contribute

1. **Add Mitigation Patterns** — Propose new detection rules for the 23 FINOS risks via PR to `mitigation.anchor`.
2. **Improve Detection** — Refine existing patterns to reduce false positives.
3. **Language Adapters** — Add tree-sitter support for new languages (Go, Rust, Java).
4. **Case Studies** — Document real-world audits in `case-studies/`.

---

## Risk Coverage Summary

Anchor v2.8.1 covers the complete FINOS AI Risk Taxonomy:

| Tier                            | Risks                                                                    | Coverage                      |
| ------------------------------- | ------------------------------------------------------------------------ | ----------------------------- |
| **Tier 1** — Code-Scannable     | Prompt Injection, Data Poisoning, Model Tampering, Credential Harvesting | Direct AST/Regex detection    |
| **Tier 2** — Model Audit        | Model Leakage, Weight Corruption, Versioning Drift                       | Diamond Cage inspection       |
| **Tier 3** — Mitigation Absence | Hallucination, Bias, Explainability, Availability                        | "Missing safeguard" detection |

Full risk mapping: `ANC-001` through `ANC-023` in [`constitution.anchor`](constitution.anchor).

---

## License

MIT License. Built for the era of AI-Assisted Engineering and Automated Governance.

---

_Anchor v2.8.1 — Zero-Trust Governance for the AI-Native Stack._
