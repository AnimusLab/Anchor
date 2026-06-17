# Policy Configuration Guide

Anchor policies determine which files are scanned, what rules are active, and what severity levels lead to build rejections. This guide covers project-level customization using `policy.anchor`.

---

## 🏛️ The Rule Inheritance Hierarchy

Anchor uses a **federated configuration model** where local overrides inherit from a central baseline.

```
constitution.anchor (Universal Root Baseline)
   └── policy.anchor (Project Overrides & Custom Rules) [RAISE ONLY]
```

### The Constitutional Floor (Raise-Only)
The global `constitution.anchor` establishes the mandatory safety baseline for all repositories. In `policy.anchor`, developers can override rule configurations subject to a strict **Raise-Only** check:
*   **Allowed**: Elevating severity from `warning` to `error` or `blocker`.
*   **Prevented**: Lowering severity from `blocker` to `warning` or `info`. If attempted, Anchor logs an audit warning and enforces the higher baseline severity.

*Exception:* Local inline suppressions using `# anchor: ignore <ID>` are allowed, but they trigger a cryptographic Git-blame audit entry mapping the dev's username to the suppression in the final compliance report.

---

## 📁 `policy.anchor` Schema

A standard `policy.anchor` lives in the repository root and overrides or extends rules:

```yaml
version: "2.1"
extends: "https://raw.githubusercontent.com/anchor/anchor-rules/main/master.anchor"

overrides:
  - id: "SEC-007"
    severity: "blocker" # Escalate from error to blocker
    reason: "Strict SOC2 Compliance mandates no raw subprocesses."

custom_rules:
  - id: "JPMC-001"
    name: "Internal API Gateway Enforced"
    severity: "error"
    match:
      type: "import"
      module: "external_api"
    message: "Obsolete import. Use 'internal_gateway' instead."

  - id: "JPMC-002"
    name: "Sanitize SQL Raw Query"
    severity: "blocker"
    match:
      type: "function_call"
      name: "raw_execute"
    message: "Avoid calling raw_execute. Wrap in prep_statement()."
```

---

## 🛠️ Defining Custom Rules

Custom rules can be added under the `custom_rules` section in `policy.anchor`. There are two main rule matching strategies:

### 1. AST Queries (Abstract Syntax Tree)
AST rules parse the code structure using [Tree-sitter](https://github.com/tree-sitter/tree-sitter). They are fast, reliable, and immune to formatting variance.

Supported AST match types:
*   **`import`**: Identifies import namespaces.
    ```yaml
    match:
      type: "import"
      module: "requests"
    ```
*   **`function_call`**: Identifies specific functions invoked.
    ```yaml
    match:
      type: "function_call"
      name: "eval"
    ```
*   **`class_instantiation`**: Captures instances of unsafe classes.
    ```yaml
    match:
      type: "class_instantiation"
      class: "RawConnection"
    ```

### 2. Regular Expressions (Fallback)
If AST parsing is not supported for a file type, Anchor falls back to evaluating regular expressions:

```yaml
custom_rules:
  - id: "SEC-ENV"
    name: "Raw Environment Variable Pull"
    severity: "warning"
    match:
      type: "regex"
      pattern: 'os\.environ\["[A-Z0-9_]+"\]'
    message: "Do not pull variables directly. Use config.get_key()."
```

---

## 🔐 Inline Audited Suppressions

If a developer must bypass a policy rule for a legitimate reason, they can add an inline comment:

```python
# anchor: ignore SEC-007
import subprocess  # Allowed, but cryptographically blamed
```

### The Suppression Audit Trail:
When Anchor parses an ignore tag, it does not hide the violation. Instead:
1.  Allows the scan to pass (preventing a blocker exit code).
2.  Runs a `git blame` on the file to extract the author, commit hash, and time.
3.  Appends this metadata to the tamper-evident JSONL audit ledger.
4.  Reports the suppression name in the final audit dashboard to CISO teams.
