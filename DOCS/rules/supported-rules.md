# Supported Rules & Categories

This directory outlines the compliance rules supported by Anchor, grouped by their core governance categories. Each category contains descriptions and concrete examples of rule triggers and remediations.

---

## 🛡️ 1. Security (`SEC-` / `OWASP-`)

Focuses on prompt injection, shell command execution, dynamic runtime evaluation, database access safety, and model tampering.

### Key Rules:
*   **`SEC-007` (Shell Injection)**: Bypassing dynamic subshells.
*   **`SEC-009` (SQL Injection)**: String concatenations inside database calls.
*   **`SEC-010` (Unsafe Execution)**: Invoking `eval()` or `exec()`.

### Examples:

#### ❌ Code Violation (Shell Injection)
```python
# Triggers SEC-007
import subprocess
subprocess.call("tar -czf backup.tar.gz " + user_input, shell=True)
```

#### 🟢 Remediation (Safe Execution)
```python
# Passes SEC-007
import subprocess
import shlex
args = shlex.split("tar -czf backup.tar.gz") + [user_input]
subprocess.run(args, check=True, shell=False)
```

---

## ⚖️ 2. Ethics (`ETH-`)

Focuses on demographic proxy bias, explainability auditing, transparency, and decision alignment.

### Key Rules:
*   **`ETH-001` (Proxy Classification)**: Prompt parameters referencing protected classes.
*   **`ETH-002` (Explainability Check)**: Enforcing agents to output decision reasoning paths.
*   **`ETH-004` (Prohibited Proxies)**: Correlation metrics causing indirect bias.

### Examples:

#### ❌ Prompt Violation (Demographic Proxy)
```text
# Triggers ETH-001 / ETH-004
Review the credit profile for applicant.
Demographics: Age 58, ZIP Code 90210, Gender Female.
```

#### 🟢 Remediation (Anonymized Features)
```text
# Passes ETH-001 / ETH-004
Review the credit profile for applicant.
Financials: Debt-to-Income Ratio 0.28, Credit Score 760, Income $120k.
```

---

## 🔒 3. Privacy (`PRV-`)

Focuses on PII leakage, geo-restricted sovereignty boundaries, and log sanitization.

### Key Rules:
*   **`PRV-001` (PII Leakage)**: Intercepting emails, phone numbers, or SSNs in prompts.
*   **`PRV-003` (Sovereignty Boundary)**: Directing European data to non-EU servers.

### Examples:

#### ❌ Prompt Violation (PII Leak)
```python
# Triggers PRV-001
prompt = f"Summarize transaction records for John Doe (john.doe@email.com, SSN: 000-12-3456)."
```

#### 🟢 Remediation (Sanitized Prompt)
```python
# Passes PRV-001
prompt = f"Summarize transaction records for USER_ID_1049 (masked_email, masked_ssn)."
```

---

## 🤖 4. Alignment (`ALN-` / `AGT-`)

Focuses on agent tool validation, recursion loops, guardrail bypasses, and exfiltration prevention.

### Key Rules:
*   **`AGT-001` (Tool Overreach)**: Calling database/terminal commands without user confirmation.
*   **`AGT-003` (Loop Recursion Boundary)**: Recursive conversational loops.

### Examples:

#### ❌ Code Violation (Tool Overreach)
```python
# Triggers AGT-001
# Agent invokes database execution directly
db.execute_raw(agent_completion.tool_args)
```

#### 🟢 Remediation (Gated Tool Execution)
```python
# Passes AGT-001
if is_safe_action(agent_completion.tool_args) and get_user_approval():
    db.execute_raw(agent_completion.tool_args)
```

---

## 📦 5. Supply Chain (`SUP-`)

Focuses on dependency provenance, package verification, and model weight hashing.

### Key Rules:
*   **`SUP-001` (Model Hash Mismatch)**: Loading untracked or compromised weights.
*   **`SUP-003` (Unvetted Dependency)**: Importing libraries without pinned hashes.

### Examples:

#### ❌ Code Violation (Untracked Model Weights)
```python
# Triggers SUP-001
# Loads model from unverified source
model = AutoModel.from_pretrained("untrusted_user/compromised_model")
```

#### 🟢 Remediation (Signed Model Load)
```python
# Passes SUP-001
# Loads verified, SHA-256 matched local model
verify_model_hash("models/llama-3b.safetensors", expected_hash="8a2f4c9b...")
model = load_secure_model("models/llama-3b.safetensors")
```

---

## ⚙️ 6. Operational (`OPS-`)

Focuses on API timeouts, model fallbacks, rate limiting, and failure containment.

### Key Rules:
*   **`OPS-001` (Missing Fallbacks)**: Instantiating AI requests without failover handlers.

### Examples:

#### ❌ Code Violation (Direct Call Without Fallback)
```python
# Triggers OPS-001
response = openai_client.completions.create(prompt=prompt)
```

#### 🟢 Remediation (Fallback Handler)
```python
# Passes OPS-001
try:
    response = openai_client.completions.create(prompt=prompt)
except Exception:
    response = local_backup_model.generate(prompt=prompt)
```

---

## ⚖️ 7. Legal (`LEG-`)

Focuses on software licenses, copyrighted code ingestion, and intellectual property limits.

### Key Rules:
*   **`LEG-001` (Copyleft Ingestion)**: Ingesting GPL-licensed components into private commercial projects.

### Examples:

#### ❌ Import Violation (Copyleft)
```python
# Triggers LEG-001 inside commercial workspace
import gpl_licensed_helper_library
```

#### 🟢 Remediation (Permissive License)
```python
# Passes LEG-001
import mit_licensed_helper_library
```
