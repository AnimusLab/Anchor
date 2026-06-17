# False Positive Analysis

## The Philosophy of Compliance Fatigue
For security and compliance tooling, **noise is fatal**. If a compliance checker regularly flags non-violating code changes, developers will experience compliance fatigue, leading them to:
1.  Apply bulk suppressions (e.g. `# anchor: ignore SEC-007`).
2.  Downgrade severities globally in local configurations.
3.  Lobby to disable the compliance checks entirely in build pipelines.

To prevent this decay of developer trust, Anchor is built on a conservative core guideline: **Prefer false negatives over false positives.** It is better to miss a boundary compliance drift (which can be caught dynamically at runtime by Layer 2) than to block a developer's deployment pipeline with a false alarm.

---

## Noise Reduction Mechanisms

Anchor utilizes three structural designs to minimize false positives:

### 1. Abstract Syntax Tree (AST) Precision
Traditional grep-based scanners search for text strings (e.g., matching the term `subprocess`). This flags:
*   Comments discussing subprocesses.
*   Print statements or documentation strings containing the word.
*   Inactive, dead code blocks.

Anchor compiles code into AST structures via Tree-sitter. A rule targeting unsandboxed command execution (like `SEC-007`) only fires if a call node is verified inside the syntax tree (e.g. `call_expression` targeting `subprocess.Popen`), completely ignoring comments and string values.

### 2. Context-Aware Scope Filters
Scanners often trigger false alarms on mock utilities and test files. Anchor applies path-based exemptions:
*   **Test Folders**: If a dangerous call (like raw file writes or direct network queries) is located inside files matching `test_*.py` or `*_test.go`, the severity is automatically downgraded to `info` or skipped.
*   **Excluded Directories**: The scanner prunes third-party directories (like `node_modules` or `.venv`) natively to avoid evaluating dependencies outside the developer's ownership.

### 3. Local Severity Customization
Every rule defined in the root constitution can have its enforcement customized inside the repository's `policy.anchor` file. If a rule triggers false alarms due to unique legacy architectures, teams can override the severity:
```yaml
# Downgrade strict network check to warning to avoid blocking deployment
rules:
  - id: "SEC-006"
    severity: "warning"
```
This moves the burden of resolution from build blockage to audit tracking.
