# Anchor Case Studies

Anchor's governance models have been validated across several large-scale, real-world codebases and ecosystem platforms. Below is the registry of our core case studies and benchmarks.

---

## 🏛️ 1. Django Framework Audit

*   **Repository**: `django/django`
*   **Focus**: Intent Anchoring and historical API drift evaluation.
*   **Objective**: Test Anchor's ability to extract **Intent Anchors** from 15+ years of git history.
*   **Key Findings**:
    *   Anchor successfully parsed history and resolved frozen creation intent for 11 core Django symbols (e.g. `authenticate()`, `Form`, `login()`, `UserManager`).
    *   Demonstrated how framework exports acquire multiple semantic roles over time (e.g., `authenticate()` drifting into session validation, token checks, and OAuth handling).
    *   Validated the *Validation Paradox* boundary: highlighting how framework-level code requires external ecosystem analysis (scanning DRF, third-party libraries) to cluster all call contexts accurately.

---

## 🤝 2. HuggingFace Registry Audit

*   **Ecosystem**: HuggingFace Model Hub
*   **Focus**: Model weight integrity and supply chain defense.
*   **Objective**: Detect model substitution, weight tampering, and backdoor attacks in model registries.
*   **Key Findings**:
    *   Audited `.safetensors` model headers against local signature manifests to prevent weights tampering.
    *   Verified HuggingFace API commit hashes against local caches to block remote supply chain modifications.
    *   Blocked unvetted model loads using policy rule `SUP-001`.

---

## 🎮 3. Google DeepMind OpenSpiel Audit

*   **Repository**: `google-deepmind/open_spiel`
*   **Focus**: Multi-agent loops and tool boundary containment.
*   **Objective**: Prevent recursive agent execution crashes and tool-overreach in complex game-theory environments.
*   **Key Findings**:
    *   Configured recursion boundaries to monitor interaction loops, aborting execution when token usage exceeded target thresholds.
    *   Intercepted dynamic game environment tool calls to block command execution prompts.

---

## 🏗️ 4. Architecture-as-Code Audit

*   **Focus**: Static compliance and structural code validation.
*   **Objective**: Ensure that enterprise systems do not experience structural code drift (e.g., unauthorized network APIs or bypassed middleware).
*   **Key Findings**:
    *   Configured `policy.anchor` to enforce strict import restrictions (such as blocking raw `requests` calls in database controllers).
    *   Scanned configurations using Tree-sitter AST queries to verify middleware registration sequences.

---

## ⚓ 5. Anchor Self-Audit

*   **Repository**: `Tanishq1030/anchor` (This Repository)
*   **Focus**: Self-contained static and runtime validation.
*   **Objective**: Ensure the Anchor governance CLI and runtime do not violate their own security, compliance, or privacy domains.
*   **Key Findings**:
    *   Audited CLI parameter parsing logic for raw subprocess executions.
    *   Verified that all inline ignores mapping to system APIs are cryptographically blamed and logged.
    *   Validated database isolation rules: ensuring that the audit engine never exports raw prompt variables or codebase text logs to the Hub control plane.
