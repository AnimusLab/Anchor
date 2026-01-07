# anchor

**Verify that code still means what it was supposed to mean.**

---

## The Problem

Modern codebases do not fail primarily due to syntax errors, bugs, or missing tests.  
They fail due to **intent decay**.

Over time:

- Abstractions accumulate responsibilities  
- Functions serve multiple unrelated purposes  
- Interfaces survive long after their justification has disappeared  

The code still works.  
Tests still pass.  
Metrics look acceptable.  

But **meaning erodes**.

Existing tooling does not detect this failure mode.

---

## What `anchor` Is

`anchor` is a **deterministic auditor** that analyzes a codebase to determine whether its current structure still aligns with its **original intent**.

It does **not**:

- Lint code  
- Check correctness  
- Optimize performance  
- Generate or refactor code  

It **judges alignment between intent and evolution**.

---

## Core Insight

Codebases degrade not because they change, but because **change is not constrained by original intent**.

Most tools treat change as neutral.  
`anchor` treats **misaligned change as a first-class risk**.

---

## What `anchor` Detects

### Semantic Overload

Symbols that serve multiple unrelated semantic roles.

```text
⚠ process_user()
  Anchored to: authentication pipeline
  Current roles: auth, billing, analytics

  Verdict: Semantic overload
  This function serves 3 unrelated responsibilities.
```
### Intent Violation

Symbols whose current behavior contradict their original intent.

```text
⚠ django.forms.Form
  Anchored to: HTML form generation and validation
  Current usage: 60% API validation, 20% HTML, 20% admin
  
  Verdict: Intent violation
  Primary usage no longer matches original design.
```
### Dependency Inertia

Interfaces that persist due to risk aversion rather than necessity.

```text
⚠ LegacyAuthInterface
  Dependents: 47 modules
  Last meaningful change: 2019
  
  Verdict: Dependency inertia
  This interface survives due to momentum, not validity.
```
---
## How it works 

### 1)  Intent Anchors

Every symnbol is anchored to it's first meaningful commit:
- Original docstring
- Initial call context
- Creation rationale

Intent frozen once established.

### 2) Semantic Analysis
`anchor` embeds and clusters call sites to identify distinct semantic roles:
- Where is this function called ?
- What contexts surrond those calls?
- Do  they cluster into unrelated purposes?

### 3) Drift Deection
Using explicit, rule-based conditions:
- Role multiplicity
- Distance from originnal intent
- Caller diversity
- Temporal evolution patterns

### 4) Deterministic Verdicts
No scores. No metrics. No probabilistics judgments.
Only discrete verdicts with full evidence:
- `aligned`
- `semantic_overload`
- `intent_violation`
- `dependency_inertia`
- `confidence_too_low`
---
### Design Principles (Non-Negotiable)
1. Deterministic judgments-Same input always produces same output
2. Reproducible results-Verdicts can be verified by others
3. Explainable evidence-Every verdicts includes supporting data
4. History-anchored reasoning-Comparisons are always to original intent
5. opinionated output-No dashboards, no gamification
6. Minimal surface area-Does one thing well

If any of these are compromised, the system loses credibilty.

---

## Project Status
### Current Phase: Thesis validation

We are provinng the concept by auditing Django-a15+ year old codebase with known intent fossils.

### Completed
- ✅ Core philosophy defined
- ✅ Intent anchor mechanism designed
- ✅ Django fossil extraction too built

### In progress
- 🔃 Manual audit of Django's `authenticate()`,`form`, and `Manager`
- 🔃 Evidence collection for semantic overload
- 🔃 Validation with senior Django engineers

### Not Started
- ⏳ Full automation (ASR parsing, embeddingss, clustering)
- ⌛ CLI implementation
- ⌛ Multi-lannguage support

---

## getting Started(For Researchers)

### Extract Intent Fossils from Django
```bash
# Install dependencies
pip install gitpython

# Clone Django
git clone https://github.com/django/django.git

# Run fossil extractor
python extract_fossils.py ./django

# Review results
cat django_fossils.json
```
This extracts the original intent  of key Django symbols:
- `django.contrib.auth.authenticate()`
- `django.forms.Form`
- `django.db.models.Manager`
- And others

### Manual Audit Process
For each extracted fossil:
1. Read the original intent (docstring, commit message, source)
2. Survey current usage (call sites in Django, DRF, Wagtail,etc.)
3. Identify semantics roles (what distinct purpose does it serve now?)
4. Document drift (does current usage violate original intent?)

See `docs/manual_audit_template.md` for the structured approach.

---

## Philosophy

### Intent May Chnage, But Never Silently
When a team intentionally redefines an abstraction, they must mark it:
```python
# @intent: redefine — now handles billing lifecycle
def process_user(user):
    ...
```
This creates:
- A new baseline
- A new audit epoch
- an explicit acknowledgement of changes

### Evolution vs. Decay
Not all drift is bad.
Unjustified drift is.

`anchor` does not prevent change.
It makes implicit deccisions visible.

For Senior Engineers
This tool is optimized for:
- Staff/principal engineers
- Infrastructure teams
- Ai-assisted development teams
- Organizations running code-writing agents

It is not a beginner tool.

**### Success Criteria**
`anchor`  is successful if:
- Engineers argue with its verdict
- Refactorss are blocked due to intent violations
- Deletions become easier to justify
- AI agents are constrained by architectural meaning

Discomfort is expected.
Silence is failure.

---

## Realtionship to AI Code Agents

### AI code agents optimize for:
- Local correctness
- Task completion
- Making tests pass

They do not evaluate:
- Whether an abstraction should exist
- whethera chnage is conceptually justified
- whether a refactor increases semantic entropy

`anchor` operates before and above agents.
It answers: **"Should this part of the codebase be touched at all"**

---

## FAQ

### Why not just delete old code?

Deletion requires consensus that something is wrong. `anchor` provides that evidence.

### Why deterministic verdicts instead of ML models?
Because probabilistic judgments are not defensible in code review. Engineers need to be able to argue with the reasoning.

### Why start with Django?
Django is old, widely used, and has clear intent fossils from a very different era of web development. If we can't prove the thesis here, we can't prove it anywhere.

### Will this work for my codebase?
Not yet. Currently focused on Python and specifically validating the concept on Django. Generalization comes later.

### How is this different from a linter?
Linters check syntax and style. `anchor` checks whether code still serves its original architectural purpose.

--- 

### Current Focus: Django Audit
We are manually auditing these Django symbols:
| Symbol | Original Intent | Hypothesis |
|-------|-----------------|------------|
| `authenticate()` | Session-based authentication | Semantic overload (session + token + OAuth) |
| `Form` | HTML form generation | Intent violation (now mostly API validation) |
| `Manager` | Simple ORM queries | Complexity drift (now handles analytics queries) |

Results will be published in
`docs/djnago_audit_findings.md`

---

### Contributing 
This project is in thesis validation phase.
We are not yet accepting code contributions, but we welcome:
- Feedback on Django audit findings
- Suggestions for  other traget codebases
- Discussion of the philosophy

Open an issue or start a discussion.

### Contact
This project is intentionally narrow in scope:

- One language at a time
- One decay pattern at a time
- One codebase per run

Generalization comes later.
The goal is not to build a product.
The goal is to prove that intent decay can be measured deterministically.

"The code still works. Tests still pass. But meaning erodes."

Built over coffee. Refined through argument.



