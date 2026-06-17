# Example: First Scan Output

This document shows a simulation of what you will actually see in your terminal when running Anchor over a codebase with policy violations.

---

## 🚀 Step 1: Run the Scanner

After running `anchor init --all` to load the default governance policies, execute a workspace-wide check:

```bash
anchor check .
```

---

## 🖥️ Simulated Terminal Output

Here is the exact terminal printout generated when Anchor detects a compliance check failure:

```text
⚓ [Anchor V5.0.8] Codebase Compliance Scan
────────────────────────────────────────────────────────────────────────────────

📁 Scanning directory: .
🔎 Parsing 121 source files using Tree-sitter adapters...

[FAIL] services/chat.py:42 - Rule OWASP-LLM-001: Direct/Raw LLM API call detected.
       Severity: error
       Namespace: OWASP
       Message: Direct calls to api.openai.com bypass enterprise governance wrappers.
       Recommendation: Route through approved governance wrapper or use anchor.runtime.activate().

[WARN] utils/logger.py:12 - Rule PRV-001: PII Logging Risk.
       Severity: warning
       Namespace: PRV
       Message: Potential email parsing in logs without sanitization wrapper.
       Recommendation: Mask output using a PII scrubbing utility.

[WARN] agents/trading.py:89 - Rule AGT-001: Tool overreach risk.
       Severity: warning
       Namespace: AGT
       Message: Agent invokes dynamic shell execution tool without confirmation gate.
       Recommendation: Bind tool trigger to a human-in-the-loop callback.

[WARN] config/settings.py:8 - Rule SEC-004: Direct environment access.
       Severity: warning
       Namespace: SEC
       Message: Raw os.environ fetch bypasses configuration audit manager.
       Recommendation: Refactor to settings.get_key() or use Vault integration.

────────────────────────────────────────────────────────────────────────────────
📊 Compliance Audit Summary
────────────────────────────────────────────────────────────────────────────────

  🔴 Errors:     1 (Build Blocked)
  🟡 Warnings:   3
  🟢 Passed:     117

Audit Verdict: FAILED (Exit Code 1)
  See .anchor/violations/governance_violations.txt for the full report.
  Run "anchor heal ." to view and apply automatic code fixes.
```

---

## 🔍 How to Interpret the Output

1.  **Exit Status**: If any **Error** or **Blocker** level violations are found, the CLI returns an exit code of `1` (which automatically fails CI/CD pipelines). If only **Warning** or **Info** entries are found, the scan passes (exit code `0`).
2.  **Violations Breakdown**:
    *   **Rule ID**: The canonical compliance ID (e.g. `OWASP-LLM-001`).
    *   **File and Line**: The exact location where Tree-sitter parsed the violating node.
    *   **Recommendation**: Practical guidance on how to fix the issue.
3.  **Healer Integration**: You can immediately run `anchor heal` to see diff-style code fixes for these violations and apply them automatically.
