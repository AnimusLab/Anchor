# Use Case: Enterprise CI/CD Governance Guardrails

Enterprise codebases require automated compliance auditing to enforce security baselines without slowing down developers. This use case covers how Anchor fits into automated git-flows and pre-merge build steps.

---

## 🔒 Automated Pre-Commit Hook Audits

Rather than waiting for code to reach the main branch, Anchor stops compliance violations on the developer's local workstation.

```
git commit
   ↓
Pre-commit hook parses STAGED files
   ↓
Evaluates Tree-sitter AST queries
   ↓
Fail: displays blocker reasons & aborts commit
Pass: executes commit successfully
```

### Git Hook Integration:
During `anchor init`, Anchor configures the standard `pre-commit` framework configuration (`.pre-commit-config.yaml`):
*   Determines which files are staged (`git diff --cached --name-only`).
*   Runs the `anchor-governance` hook from the `https://github.com/AnimusLab/Anchor` repository over changed files only.
*   If a developer violates a rule (such as writing raw SQL concatenation or checking in an unproxied requests call), the commit is blocked.

---

## 🖋️ Auditable Suppressions with Git Blame

Large organizations frequently encounter legitimate boundary conditions where a global security rule must be temporarily bypassed. 

While traditional governance tools block everything or require manual administrator approvals, Anchor provides **Inline Audited Suppressions**:

```python
# app.py
# anchor: ignore SEC-007
import subprocess # Triggering node
```

### The Accountability Mechanics:
1.  **Non-Blocking Scans**: The presence of the comment bypasses blocker checks, allowing the build pipeline to succeed.
2.  **Git Blame Association**: During analysis, Anchor reads the file history using Git. It identifies the developer's name, commit SHA, and time signature associated with the line containing the `ignore` comment.
3.  **Audit Ledger Logging**: The developer's details are written directly into the HMAC-signed compliance ledger:
    ```json
    {
      "rule_id": "SEC-007",
      "status": "ignored",
      "ignored_by": "Developer <dev@enterprise.com>",
      "ignore_commit": "8a2f4c9b"
    }
    ```
4.  **Oversight Telemetry**: In the CISO dashboard, suppressions are flagged and attributed, turning anonymous bypasses into a transparent audit trail.

---

## 🛡️ Tamper-Proof Centralized Governance

To prevent developers or team owners from modifying policy configurations to hide violations, Anchor enforces **Federated Integrity**:

*   The master CI/CD runner downloads `constitution.anchor` directly from an authoritative secure raw HTTPS endpoint during initialization.
*   The check sequence reads `.anchor.lock` signatures to verify that local configurations have not been modified.
*   Even if a developer changes their local rules, the CI/CD pipeline evaluates checks against the baseline, ensuring universal policies are strictly enforced.
