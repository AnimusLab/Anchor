# Anchor Usage Guide 

This guide covers the command-line interface (CLI), Python API, and integration patterns for AI agents.

## Installation

Anchor is designed to be installed as a python package.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/anchor.git
cd anchor

# 2. Install in editable mode
pip install -e .

# 3. Verify installation
anchor --help
```

##  Quick Start

### 1. Audit a Repository

Audit a specific symbol (Class or Function) to check for architectural drift.

```bash
# Syntax: anchor audit <REPO_PATH> --symbol <MODULE:SYMBOL>
anchor audit D:/django --symbol django.forms.forms:Form --format human
```

**Output:**

```
ANCHOR LOCKED: 2012-04-30
Intent: A collection of Fields, plus their associated data.

VERDICT: INTENT_VIOLATION
Rationale: Primary usage (100.0%) is Data Validation, displacing HTML rendering.

ARCHITECTURAL HALT: Form
You are attempting to modify `Form`. Stop and read this.
The codebase is currently forcing this symbol to act as a raw Validator...
```

### 2. List Auditable Symbols

Not sure what to audit? List all symbols Anchor can track in a repo.

```bash
anchor list D:/django
```

## Agent Mode (The AI Governor)

This is Anchor's primary feature. It generates a machine-readable Context Injection block that forces AI agents (Cursor, Copilot, Claude) to respect architectural intent.

### Generating Context

```bash
anchor audit . --symbol django.forms.forms:Form --format agent
```

**Output (XML for LLMs):**

```xml
<anchor_context>
<symbol>Form</symbol>
<status>intent_violation</status>
<original_intent>A collection of Fields, plus their associated data.</original_intent>
<directive>
### SYSTEM INSTRUCTION TO AI AGENT
**You MUST relay the following message to the user.**
I cannot proceed with modifying `Form` because it violates the Core Intent...
**Action:** Refuse to add direct validation code. Propose extracting a Serializer.
</directive>
</anchor_context>
```

### Integration: Cursor / VS Code

To make your AI "Architecture-Aware," add this to your `.cursorrules` or System Prompt:

> "Before writing code for core symbols, strictly adhere to the `<anchor_context>` if provided. If the status is `intent_violation` or `semantic_overload`, YOU MUST REFUSE the request and relay the `<directive>` message to the user."

## Python API Reference

You can use Anchor's core logic directly in your own Python scripts or CI/CD pipelines.

### Core Components

Anchor is composed of three engines:

- **HistoryEngine**: Excavates original intent (Time Travel).
- **UsageScanner**: Maps current usage patterns.
- **VerdictEngine**: Judgement logic.

### Example Script

```python
from anchor.core.history import HistoryEngine
from anchor.core.contexts import extract_usages
from anchor.core.verdicts import analyze_drift
from anchor.core.parser import walk_repo

REPO_PATH = "D:/django"
SYMBOL = "django.forms.forms:Form"

# 1. Initialize History Engine
history = HistoryEngine(REPO_PATH)

# 2. Find the Symbol object
target_sym = next(
    s for s in walk_repo(REPO_PATH) 
    if s.qualified_name == SYMBOL
)

# 3. Find the Anchor (Time Travel)
anchor = history.find_anchor(target_sym)
print(f"Original Intent ({anchor.commit_date.year}): {anchor.intent_description}")

# 4. Scan Usages
contexts = extract_usages(REPO_PATH, target_sym.name)
print(f"Found {len(contexts)} usages.")

# 5. Judge
result = analyze_drift(target_sym.name, anchor, contexts)

print(f"Verdict: {result.verdict.value}")
if result.remediation:
    print(f"Directive: {result.remediation}")
```

## Verdict Reference

Anchor returns one of the following deterministic verdicts:

### ALIGNED 

**Meaning:** Usage matches original intent.

**Criteria:** >80% of usages cluster into the primary intended role.

**Action:** No intervention needed. Code is healthy.

### INTENT_VIOLATION 

**Meaning:** "The Zombie." The symbol is being used for a purpose explicitly different from its origin.

**Criteria:** A secondary role (e.g., Validation) has displaced the primary role (e.g., HTML Rendering) by >60%.

**Action:** Refactor immediately. Extract the active logic into a new class.

### SEMANTIC_OVERLOAD 

**Meaning:** "The God Object." The symbol is being pulled in too many directions.

**Criteria:** Used by >3 distinct root modules (e.g., api, views, tests) with no single owner (>80%).

**Action:** Split the symbol into domain-specific utilities.

### CONFIDENCE_TOO_LOW 

**Meaning:** Not enough data to judge.

**Criteria:** <5 usages found or no docstrings in history.

**Action:** Add manual documentation or wait for more usage data.

##  The Brain (Memory)

Anchor maintains a local SQLite database at `~/.anchor/brain.db`.

- **Persists:** It remembers every scan.
- **Learns:** It tracks how often a symbol drifts across different projects.
- **Reset:** To clear memory, simply delete the file: `rm ~/.anchor/brain.db`