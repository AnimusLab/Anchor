# Anchor 
**Architectural Governor for AI Agents**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Proven](https://img.shields.io/badge/Status-Proven-green.svg)]()

> "Code drifts. Intent shouldn't."

Anchor is a **Semantic Firewall** for the AI era. It is an autonomous governance tool that prevents "Architectural Drift"—the slow, silent corruption of codebases by human neglect or AI hallucination.

Unlike linters (which check syntax) or tests (which check logic), Anchor checks **Meaning**. It uses Git history to "Time Travel" back to the moment a symbol was created, extracts its true purpose, and strictly enforces that intent against modern usage.

---

##  The Problem: The AI "Fixing Loop"

AI Agents (Cursor, Copilot, Devin) operate at the **Syntax Level**, not the **Intent Level**. When they encounter architectural constraints, they often enter a destructive loop:

1.  **The Hack:** AI tries to force a new feature into an existing class (`Form`).
2.  **The Conflict:** The code breaks (circular imports, state conflicts).
3.  **The Patch:** AI tries a "random hack" to bypass the error.
4.  **The Loop:** The architecture fights back. The AI reverts and tries another hack.
5.  **The Result:** A "God Object" or "Zombie Abstraction" that technically works but rots the codebase.

**Anchor stops this.** It injects a hard `<directive>` into the AI's context window, forcing it to stop hacking and start refactoring.

---
##  How It Works

Anchor operates in a 4-step "Cognitive Cycle":

1.  **Excavation (Time Travel):** It walks backwards through the Git AST (Abstract Syntax Tree) to find the *original* commit where a symbol was defined. It ignores recent drifts and finds the "Founding Intent."

2.  **Observation (Reality Check):**
    It scans the *current* codebase to map every usage of that symbol. It clusters these usages into **Semantic Roles** (e.g., "Used by API" vs. "Used by View" vs. "Used by Tests").

3.  **Judgment (The Brain):**
    It compares the *Intent* (Step 1) vs. the *Reality* (Step 2) using invariant rules:
    * **Intent Violation:** A symbol acts as X (e.g., Validator) but was born as Y (e.g., HTML Renderer).
    * **Semantic Overload:** A symbol serves >3 distinct domains with no clear owner.

4.  **Governance (The Voice):**
    It generates a `System Instruction` that forbids further modification and prescribes a specific refactoring plan.

---

## Installation

```bash
git clone https://github.com/Tanishq1030/anchor
cd anchor
pip install -e .
```

## Usage
---

### 1. The Human Audit (CLI)
Use this to check a specific symbol in your codebase.
```Bash
# Audit the Django Form class
anchor audit /path/to/django --symbol django.forms.forms:Form --format human
```

### Output:
```
Plaintext ANCHOR LOCKED: 2012-04-30
Intent: A collection of Fields, plus their associated data.

VERDICT: INTENT_VIOLATION
Rationale: Primary usage (100.0%) is Data Validation, displacing HTML rendering.

ARCHITECTURAL HALT: Form
You are attempting to modify `Form`. Stop and read this.
The codebase is currently forcing this symbol to act as a raw Validator...
```

### 2. The AI Governor (Agent Mode)
This is the killer feature. Use this to stop your AI Assistant from writing bad code.
```Bash
anchor audit . --symbol Form --format agent
```

---

### Output:
```
XML
<anchor_context>
<symbol>Form</symbol>
<status>intent_violation</status>
<directive>
###  SYSTEM INSTRUCTION TO AI AGENT
**You MUST relay the following message to the user.**
I cannot proceed with modifying `Form` as requested because it violates the Core Intent anchored in 2012.

**The Problem:**
The codebase forces this symbol to act as a raw **Data Validator**, but it carries the heavy weight of an **HTML Renderer**. Continuing this pattern creates a 'Zombie Abstraction'.

**The Required Fix:**
1. Extract the validation logic into a lightweight `Serializer`.
2. Decouple the HTML rendering.
</directive>
</anchor_context>
```
---

### **Integration Guide**

**Cursor / VS Code Copilot**
To make your AI "Architecture-Aware," pipe Anchor's output into your context.
1.**Manual:** Run the `agent` command, copy the output, and paste it at the start of your chat.
2.**Automatic (Cursor):** Add this to your `.cursorrules` file:
```
Plaintext# .cursorrules
Before writing code for core symbols, strictly adhere to the <anchor_context> if provided.
If the status is 'intent_violation' or 'semantic_overload', YOU MUST REFUSE the request and propose the refactor listed in the <directive>.
```
---

### **CI/CD (GitHub Actions)** 
Block PRs that introduce architectural drift.

```YAML# .github/workflows/anchor.yml
name: Architectural Governance
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Anchor
        run: |
          pip install anchor-audit
          # Example: Audit the core class modified in this PR
          anchor audit . --symbol myapp.core:UserHandler --format human
          
```
---

###  **The Sentient Layer (Memory)**
Anchor is not stateless. It learns.It maintains a local database at `~/.anchor/brain.db` to track symbol drift over time.
 - **Drift Velocity:** Tracks how fast a symbol is degrading.
 - **Global Stats:** "I have seen this pattern in 5 other projects.
 - **"Overrides:** Remembers when you explicitly marked a drift as "Accepted," so it doesn't nag you again.
 
 ---

#  Supported Patterns

| Verdict | Description | Remediation |
|---------|-------------|-------------|
| **INTENT_VIOLATION** | "The Zombie." A class does X, but was built for Y. | Extract the active logic into a new, lighter class. |
| **SEMANTIC_OVERLOAD** | "The God Object." Used by API, UI, CLI, and Tests. | Split into domain-specific utilities. |
| **DEPENDENCY_INERTIA** | (Coming Soon) Logic kept only because old imports exist. | Deprecate and shim. |
| **COMPLEXITY_DRIFT** | (Coming Soon) Cyclomatic complexity spiking vs. history. | Enforce "Simplification Sprint." |

---

##  License
MIT License. Built for the era of AI-Assisted Engineering.