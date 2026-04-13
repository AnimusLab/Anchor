# Anchor — Governance Engine for AI

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-anchor--audit-gold.svg)](https://pypi.org/project/anchor-audit/)
[![Version: 5.0.1](https://img.shields.io/badge/Version-5.0.1-emerald.svg)]()

> "Governance without enforcement is documentation."

Anchor is the **surveillance and enforcement layer for AI**. It audits AI-adjacent code against a cryptographically sealed constitutional rule set, mapping every violation to the exact statute it breaches — enforced deterministically via AST analysis, runtime interceptors, and behavioral verification (Diamond Cage).

🌐 **[anchorgovernance.tech](https://anchorgovernance.tech)**

---

## Why Anchor Exists

| Event | Date | Amount |
|---|---|---|
| Goldman Sachs CFPB enforcement — AI explainability failure | Oct 2024 | **$45M** |
| EU AI Act full enforcement begins — credit scoring, AML, fraud | Aug 2026 | Mandatory |
| SEC AI Governance — named #1 examination priority, above crypto | 2026 | Mandatory |
| RBI FREE-AI — 26 mandatory recommendations, per-decision audit trails | Aug 2025 | Mandatory |

The regulators have started counting. Anchor enforces.

---

## What Anchor Does

- **Sovereign Multi-Tenancy (Layer 05)** — [NEW in v5.0] Decentralized identity for the enterprise. Organizations (Sovereign Hubs) manage their own staff and sub-projects via the Anchor Master Node, ensuring strict data isolation and regulatory jurisdiction (IN, EU, US).
- **Static Code Analysis (Layer 01)** — Tree-sitter AST scanning against a cryptographically sealed constitutional rule set. Every violation gets a `violation_id` mapped to the exact regulation it breaches.
- **Diamond Cage (Layer 02)** — WASM-based behavioral verification sandbox. Proves security invariants at scan time, not just static pattern matching. Reports as `Diamond Cage: ACTIVE`.
- **Hybrid Healer (Sovereign Scalpel)** — Goes beyond detection to remediation. Proposes file-specific AST patches, applied via `anchor heal --apply`.
- **Interceptor SDK** — First-party support for 20+ LLM providers. Secure prompts and responses mid-flight with `AnchorGuard`.
- **Federated Governance Workspace** — Structured `.anchor/` directory with mandatory core domains and opt-in frameworks/regulators declared in `constitution.anchor`.

---

## The Federated Model

Anchor operates on a three-layer constitutional architecture:

| Layer | File | Purpose |
|---|---|---|
| **Constitution** | `constitution.anchor` | Defines **WHAT** risks exist. Domain + framework + regulator manifest. SHA-256 sealed via remote `GOVERNANCE.lock`. |
| **Mitigation Catalog** | `mitigation.anchor` | Defines **HOW** to detect each risk. Regex + AST patterns. Cloud-synced. |
| **State Law** | `policy.anchor` | **Your** local overrides. Change severity, add company-specific rules. |

**Merge Strategy**: State Law overrides Constitution by rule ID, but only within the constitutional floor. Critical security rules (e.g., `ANC-007`) are locked at `blocker`. Local policy can make rules stricter, never weaker.

---

## Coverage — V4.3.5

| Tier | Content | Count |
|---|---|---|
| **Domain Rules** | SEC, ETH, PRV, ALN, AGT, LEG, OPS, SUP, SHR | 43 rules |
| **Standards Bodies** | FINOS AI Governance, OWASP LLM Top 10 · 2025, NIST AI RMF 1.0 | 3 frameworks |
| **Government Regulators** | RBI FREE-AI 2025, EU AI Act 2024/1689, SEBI AI/ML 2025, CFPB Reg B, FCA 2024, SEC 2026 | 6 regulators |
| **Total Regulatory Mappings** | | **170 mappings** |

---

## Quick Start

### Install from PyPI

```bash
pip install anchor-audit
```

### Or install from source

```bash
git clone https://github.com/Tanishq1030/Anchor.git
cd Anchor
pip install -e .
```

### Initialize your project

```bash
anchor init
```

Sets up `.anchor/`, syncs the constitution & mitigation catalog, and installs the Git pre-commit hook.

### Scan your code

```bash
# Full governance audit
anchor check ./src

# Scan with all frameworks and regulators
anchor init --all && anchor check ./src
```

### Review and apply fixes

```bash
anchor heal          # Review suggested fixes
anchor heal --apply  # Apply all auto-fixable issues
```

**Full command reference**: [USAGE.md](USAGE.md)

---

## CI/CD Integration

Anchor acts as the enforcement gate in GitHub Actions. If a PR violates the constitution, Anchor blocks the merge with a detailed violation report.

```yaml
# .github/workflows/anchor-audit.yml
- name: Run Governance Check
  run: |
    pip install anchor-audit
    anchor check --dir ./src --severity error --json-report --github-summary
```

---

## Suppressing Findings

When a finding is a justified use (e.g., your governance tool legitimately needs `subprocess`), suppress it with an inline comment:

```python
# Per-rule suppression
result = subprocess.run(cmd, capture_output=True)  # anchor: ignore ANC-018

# Suppress all rules on a line
os.environ.get("SECRET_KEY")  # anchor: ignore-all
```

| Feature | Details |
|---|---|
| **Scope** | Line-level only |
| **Audit Trail** | Anchor uses `git blame` to record who authorized each suppression |
| **Visibility** | Suppressed findings appear in the report with the author's name |

---

## Project Structure

```
Anchor/
├── anchor/                     # Core package
│   ├── cli.py                  # CLI entry point (click)
│   ├── core/
│   │   ├── engine.py           # PolicyEngine — AST scanning via tree-sitter
│   │   ├── healer.py           # Hybrid Healer — fix suggestion and patching
│   │   ├── constitution.py     # SHA-256 integrity verification
│   │   ├── loader.py           # Federated policy merger
│   │   └── mapper.py           # GenAI threat model → rule mapper
│   ├── runtime/                # Interceptor SDK
│   │   ├── guard.py            # AnchorGuard application safety API
│   │   └── interceptors/       # SDK and HTTP library patches
│   └── adapters/               # Language-specific tree-sitter adapters
├── tests/                      # Test suite
├── .anchor/                    # Governance workspace (committed)
│   ├── domains/                # Core domain rules (SEC, ETH, PRV ...)
│   ├── frameworks/             # FINOS, OWASP, NIST
│   └── government/             # RBI, EU AI Act, SEBI, CFPB, FCA, SEC
├── constitution.anchor         # Active framework/regulator manifest
├── mitigation.anchor           # Detection pattern catalog
├── case-studies/               # Real-world audit case studies
└── docs/                       # Architecture documentation
```

---

## Security Architecture — SHA-256 Tamper Proofing

```
┌─────────────────────────────────────────────────┐
│  GitHub Raw (Source of Truth)                    │
│  constitution.anchor  →  SHA-256: 3745014B...   │
│  mitigation.anchor    →  SHA-256: E3E32531...   │
└────────────────┬────────────────────────────────┘
                 │ fetch + verify
┌────────────────▼────────────────────────────────┐
│  .anchor/cache/ (Local)                         │
│  Hash mismatch → INTEGRITY VIOLATION            │
│  Hash match    → Proceed with audit             │
└─────────────────────────────────────────────────┘
```

No developer can weaken the rules to pass the audit. The hashes are baked into the Python package itself.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANCHOR_CONSTITUTION_URL` | GitHub Raw URL | Override for air-gapped/mirror setups |
| `ANCHOR_MITIGATION_URL` | GitHub Raw URL | Override for the mitigation catalog |
| `ANCHOR_VERBOSE` | `false` | Enable detailed debug output |
| `ANCHOR_FETCH_TIMEOUT` | `10` | Timeout (seconds) for cloud sync |

---

## Contributing

- [Contributing Guide](CONTRIBUTING.md)
- [Open an Issue](https://github.com/Tanishq1030/Anchor/issues)
- [PyPI Package](https://pypi.org/project/anchor-audit/)
- ✉️ [tan@anchorgovernance.tech](mailto:tan@anchorgovernance.tech)

---

## License

Apache 2.0 — Open source. Built for the era of AI-Assisted Engineering.

---

_Anchor V4.3.5 · [anchorgovernance.tech](https://anchorgovernance.tech) · Apache 2.0_
