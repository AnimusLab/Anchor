# Contributing to Anchor

Thank you for your interest in contributing to Anchor. This guide covers everything you need to get started.

🌐 **[anchorgovernance.tech](https://anchorgovernance.tech)** · ✉️ [tan@anchorgovernance.tech](mailto:tan@anchorgovernance.tech)

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/<your-username>/Anchor.git
cd Anchor
```

### 2. Set Up Development Environment

```bash
python -m venv anchor_dev

# Windows
anchor_dev\Scripts\activate

# macOS/Linux
source anchor_dev/bin/activate

pip install -e .
```

### 3. Verify Installation

```bash
anchor --help
anchor check --dir . --verbose
```

---

## Project Architecture

```
anchor/
├── cli.py              # CLI entry point (Click)
├── core/
│   ├── engine.py       # PolicyEngine — tree-sitter AST scanning
│   ├── constitution.py # SHA-256 integrity verification
│   ├── config.py       # Pydantic settings (.env loading)
│   ├── loader.py       # Federated policy merger
│   └── mapper.py       # Threat Model → Rule mapper
├── adapters/           # Language-specific tree-sitter adapters
└── plugins/            # Extensible plugin system
```

### Key Concepts

- **Constitution** (`constitution.anchor`): Defines WHAT risks exist. SHA-256 sealed via remote `GOVERNANCE.lock`. Do NOT edit directly — changes go through a PR with hash updates.
- **Mitigation Catalog** (`mitigation.anchor`): Defines HOW to detect risks. This is where most pattern contributions go.
- **Policy** (`policy.anchor`): Local project overrides. Not part of the universal package.

---

## Types of Contributions

### 1. Adding Detection Patterns (Most Common)

Add a new regex or AST pattern to `mitigation.anchor`:

```yaml
# Example: New pattern for ANC-009 (Prompt Injection)
- id: "MIT-009-D"
  rule_id: "ANC-009"
  name: "Jinja Template in Prompt"
  match:
    type: "regex"
    pattern: 'render_template\s*\(.*prompt'
  message: "Jinja template used in prompt construction. Risk of template injection."
  severity: "error"
```

**Pattern Guidelines:**

| Rule | Why |
|---|---|
| Use context-aware patterns | Don't match every f-string — scope to prompt/LLM variables |
| Prefer regex over AST | Regex is faster and more portable across languages |
| Include `severity` | One of: `info`, `warning`, `error`, `blocker` |
| Test on real code | Run `anchor check --dir ./tests --verbose` before submitting |

### 2. Improving Existing Patterns

If a pattern produces false positives:

1. Open an issue describing the false positive with a minimal reproduction.
2. Propose a refined pattern in a PR.
3. Include a test fixture in `tests/fixtures/` showing the fix.

### 3. Adding Language Support

Anchor uses `tree-sitter` for AST parsing. To add a new language:

1. Install the tree-sitter grammar: `pip install tree-sitter-<language>`
2. Create an adapter in `anchor/adapters/`
3. Register the file extension mapping in `anchor/core/registry.py`

**Capture name standardization** (required):

| Capture | Use For |
|---|---|
| `@func_name` | Function calls |
| `@import_name` | Import statements |
| `@parent_name` | Inheritance / embedding |

### 4. Case Studies

Document real-world audits in `case-studies/governance_audits/<project>/`. Include:

- `governance_violations.txt` — raw violation output
- `governance_audit.md` — formatted audit report

### 5. Bug Fixes & Feature Development

1. Check [open issues](https://github.com/Tanishq1030/Anchor/issues) for existing reports.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and test thoroughly.
4. Submit a PR with a clear description.

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run compliance test (validates 43-rule detection)
python tests/compliance_test.py

# Quick self-audit
anchor check --dir . --verbose
```

### Adding Test Fixtures

```
tests/
├── fixtures/
│   ├── vulnerable_prompt.py    # Should trigger ANC-009
│   └── safe_prompt.py          # Should NOT trigger ANC-009
├── compliance_test.py
└── test_integration.py
```

---

## Security-Sensitive Changes

### Modifying `constitution.anchor` or `mitigation.anchor`

These files are **SHA-256 sealed**. If your PR modifies them:

1. Update the file content.
2. Recompute the hash:
   ```bash
   python -c "import hashlib; print(hashlib.sha256(open('mitigation.anchor','rb').read()).hexdigest().upper())"
   ```
3. Update the hash in `anchor/core/constitution.py`.
4. Clearly document why the change is needed in the PR description.

> **Note**: Hash changes are reviewed with extra scrutiny to prevent weakening of security rules.

### Using Suppression Comments

```python
# Governance tool legitimately using subprocess
result = subprocess.run(cmd, capture_output=True)  # anchor: ignore ANC-018
```

**Suppression guidelines:**

| Rule | Why |
|---|---|
| Use per-rule suppression | `# anchor: ignore ANC-XXX`, not `# anchor: ignore-all` |
| Add a justification comment | Explain **why** the suppression is needed on the line above |
| Never suppress in test fixtures | Test files should trigger rules intentionally |
| Suppressions are git-blamed | Your name is permanently attached to the suppression |

---

## PR Checklist

- [ ] Code follows the existing project style
- [ ] New patterns are context-aware (no overly broad matching)
- [ ] Tests pass: `python -m pytest tests/ -v`
- [ ] SHA-256 hashes updated if governance files were modified
- [ ] Suppressions use `# anchor: ignore ANC-XXX` (not `ignore-all`)
- [ ] CHANGELOG.md entry added
- [ ] PR description explains the change and its rationale

---

## Code of Conduct

Be respectful and constructive. We are building tools that govern AI safety — the same principles of trust and integrity apply to our community.

---

## Questions?

- Open a [Discussion](https://github.com/Tanishq1030/Anchor/discussions)
- File an [Issue](https://github.com/Tanishq1030/Anchor/issues)
- Email: [tan@anchorgovernance.tech](mailto:tan@anchorgovernance.tech)

---

_Thank you for helping make AI governance better for everyone._
