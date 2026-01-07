# Anchor Philosophy

**The foundational principles behind deterministic intent auditing.**

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

**But meaning erodes.**

Existing tooling does not detect this failure mode.

---

## Core Insight

Codebases degrade not because they change, but because **change is not constrained by original intent**.

Most tools treat change as neutral.

Anchor treats misaligned change as a first-class risk.

---

## What Anchor Is

Anchor is a deterministic auditor that analyzes a codebase to determine whether its current structure still aligns with its original intent.

### What Anchor Does

- Judges alignment between intent and evolution
- Detects semantic overload, intent violations, and dependency inertia
- Produces discrete, evidence-based verdicts
- Makes implicit architectural drift explicit

### What Anchor Does NOT Do

- ❌ Lint code
- ❌ Check correctness
- ❌ Optimize performance
- ❌ Generate or refactor code
- ❌ Rely on probabilistic judgments for verdicts

**This is an auditor, not an assistant.**

---

## Key Definitions

### Intent

The conceptual purpose of a symbol (function, class, module) at the time it was introduced.

Intent is inferred from:
- The earliest meaningful commit containing the symbol
- Its initial name
- Its initial docstring or comments
- Its initial call context

**Intent is frozen once established.**

### Intent Drift

A measurable divergence between:
- The symbol's original intent
- Its current semantic roles, dependencies, and usage patterns

Not all drift is bad.  
**Unjustified drift is.**

### Semantic Role

A coherent behavioral responsibility inferred from:
- Call-site contexts
- Input/output shapes
- Surrounding logic

A single symbol may acquire multiple semantic roles over time.

---

## What Anchor Detects

### 1. Semantic Overload

Symbols that serve multiple unrelated semantic roles.

**Characteristics:**
- Multiple distinct call context clusters
- Each role could have been a separate abstraction
- Original intent still present but not dominant
- Roles coexist without clear justification

**Example verdict:**
```
⚠ authenticate()
  Anchored to: Validate credentials against backends
  Current roles: session auth, API tokens, OAuth
  Verdict: Semantic Overload
```

### 2. Intent Violation

Symbols whose current behavior contradicts their original intent.

**Characteristics:**
- Primary usage (>50%) no longer matches original intent
- Core features unused in majority contexts
- Original assumptions violated
- Name/structure implies the original purpose

**Example verdict:**
```
⚠ Form
  Anchored to: Define and render HTML forms
  Current usage: 70% API validation (no HTML)
  Verdict: Intent Violation
```

### 3. Dependency Inertia

Interfaces or modules that persist due to risk aversion rather than necessity.

**Characteristics:**
- Many dependents
- Little meaningful evolution
- Documented limitations
- Alternative abstractions exist
- Prevalent workarounds

**Example verdict:**
```
⚠ User
  Anchored to: Username/password authentication
  Evidence: AbstractUser added as alternative (2013)
  Verdict: Dependency Inertia
```

### 4. Aligned

Symbols that maintain their original intent.

**Characteristics:**
- Single semantic role
- 90%+ usage matches intent
- Clear, narrow purpose
- Appropriate evolution without drift

**Example verdict:**
```
✓ login()
  Anchored to: Persist user identity in session
  Current roles: Session creation (100%)
  Verdict: Aligned
```

---

## Design Principles (Non-Negotiable)

### 1. Deterministic Judgments

Same input always produces same output. No randomness, no ML models, no probabilistic reasoning.

**Why:** Engineers must be able to verify and debate verdicts.

### 2. Reproducible Results

Any engineer can re-run the audit and get identical results.

**Why:** Credibility requires consistency.

### 3. Explainable Evidence

Every verdict includes:
- Intent anchor (commit, date, original code)
- Call context samples
- Usage statistics
- Specific assumption violations

**Why:** "Because the tool said so" is not acceptable.

### 4. History-Anchored Reasoning

Comparisons are always to original intent, not arbitrary standards.

**Why:** Without a baseline, drift is unmeasurable.

### 5. Opinionated Output

No scores, no metrics, no dashboards. Only discrete verdicts:
- Aligned
- Semantic Overload
- Intent Violation
- Dependency Inertia
- Confidence Too Low

**Why:** Ambiguity enables avoidance.

### 6. Minimal Surface Area

Anchor does one thing: detect intent drift. Nothing more.

**Why:** Feature creep would undermine the philosophical clarity.

---

## How Anchor Works

### 1. Intent Anchors

Every symbol is anchored to its **first meaningful commit**:
- Original docstring
- Initial implementation
- Creation context
- Commit message

**Intent anchors are frozen.**

Manual override is allowed but logged:
```python
# @intent: redefine — now handles billing lifecycle
def process_user(user):
    ...
```

### 2. Semantic Analysis

Anchor embeds and clusters call sites to identify distinct semantic roles:
- Where is this function called?
- What contexts surround those calls?
- Do they cluster into unrelated purposes?

### 3. Drift Detection

Using explicit, rule-based conditions:
- Role count (threshold: 3+ roles suggests overload)
- Distance from original intent (embedding similarity)
- Caller diversity (unrelated modules)
- Temporal evolution patterns (gradual vs. sudden)

**False positives are treated as more harmful than false negatives.**

### 4. Deterministic Verdicts

No scores. No percentages. Only discrete judgments with full evidence.

Allowed verdicts:
- `aligned` - Current usage matches original intent
- `semantic_overload` - Multiple unrelated roles
- `intent_violation` - Primary usage contradicts intent
- `dependency_inertia` - Survives due to compatibility, not validity
- `confidence_too_low` - Cannot determine intent reliably

---

## Output Philosophy

Anchor outputs **opinions**, not dashboards.

### Good Output

```
⚠ process_user()

Anchored to:
  Authentication pipeline (commit a13f, 2012-03-15)

Current observations:
  - Handles billing flows (35% of calls)
  - Emits analytics events (30% of calls)
  - Formats API responses (35% of calls)

Verdict:
  Semantic Overload
  
Rationale:
  This function now serves three unrelated responsibilities.
  The original authentication intent is no longer recognizable
  in the majority of call contexts.
```

### Bad Output (What Anchor Avoids)

```
❌ Code Quality Score: 67/100
❌ Complexity: High
❌ Maintainability: Medium
❌ Technical Debt: 23 issues
```

**No charts. No scores. No gamification.**

---

## Intent May Change, But Never Silently

### The Core Principle

Evolution is acceptable. Silent drift is not.

When a team intentionally redefines an abstraction, they **must mark it**:

```python
# @intent: redefine — now handles billing lifecycle
def process_user(user):
    ...
```

This creates:
- A new baseline
- A new audit epoch
- An explicit acknowledgment of change

**Drift is measured from that point forward.**

### Why This Matters

Without explicit redefinition:
- Every contradiction can be justified retroactively
- "It evolved naturally" becomes an excuse
- The tool becomes a historian, not an auditor

**Intent must never change silently.**

---

## Intended Users

Anchor is optimized for:

- Senior engineers
- Staff/principal engineers
- Infrastructure teams
- AI-assisted development teams
- Organizations running code-writing agents

**This is not a beginner tool.**

Anchor assumes:
- Understanding of software architecture
- Ability to engage in technical debate
- Willingness to accept uncomfortable truths
- Authority to make or influence architectural decisions

---

## Relationship to AI Code Agents

AI code agents optimize for:
- Local correctness
- Task completion
- Making tests pass

They do **not** evaluate:
- Whether an abstraction should exist
- Whether a change is conceptually justified
- Whether a refactor increases semantic entropy

**Anchor operates before and above agents.**

It answers: **"Should this part of the codebase be touched at all?"**

### The AI Agent Problem

AI agents forget context. After 50 messages of incremental changes:
- Original architectural purpose is lost
- Each change is locally correct
- Cumulative effect violates intent
- No one realizes until it's too late

**Anchor provides the constraint AI agents lack: architectural memory.**

---

## Success Criteria

Anchor is successful if:

- ✅ Engineers argue with its verdicts
- ✅ Refactors are blocked due to intent violations
- ✅ Deletions become easier to justify
- ✅ AI agents are constrained by architectural meaning
- ✅ Technical debates become evidence-based

**Discomfort is expected.**  
**Silence is failure.**

---

## What Anchor Is NOT

### Not a Replacement for Human Judgment

Anchor provides evidence. Humans decide.

A verdict of "semantic overload" does not mean "must refactor immediately." It means "this symbol serves multiple purposes; debate whether that's acceptable."

### Not a Code Quality Tool

Anchor does not measure:
- Cyclomatic complexity
- Test coverage
- Code style
- Performance
- Security vulnerabilities

These are important. Anchor does something else.

### Not a Refactoring Assistant

Anchor does not suggest:
- How to split an overloaded function
- What to rename
- Where to move code

It only judges alignment. Solutions are left to humans.

### Not a Universal Truth

Anchor's verdicts are **philosophical positions** backed by evidence.

Reasonable engineers can disagree on:
- Whether 40/30/30 usage split is "semantic overload"
- Whether 30/70 split is "intent violation" or "acceptable evolution"
- Whether a frozen symbol is "dependency inertia" or "stable design"

**This is intentional.** The goal is to surface the debate, not end it.

---

## Why Determinism Matters

### The Problem with ML-Based Approaches

Imagine an ML model that says: "This function is 73% overloaded."

**Questions you can't answer:**
- Why 73%?
- What would make it 50%?
- Can I verify this independently?
- How do I argue with it in code review?

**Anchor's approach:**

```
This function serves 3 distinct semantic roles:
1. Authentication (35% of calls, in auth modules)
2. Billing (30% of calls, in payment modules)
3. Analytics (35% of calls, in tracking modules)

Verdict: Semantic Overload
Reasoning: 3 roles, no single role >60%, unrelated contexts
```

**You can:**
- Verify the call contexts yourself
- Debate whether 3 roles is too many
- Argue the reasoning
- Propose a different threshold

**Determinism enables debate. Probabilism ends it.**

---

## Comparison to Existing Tools

| Tool | Purpose | Anchor's Difference |
|------|---------|---------------------|
| Linters | Style, syntax | Anchor judges intent alignment |
| Type checkers | Correctness | Anchor judges architectural meaning |
| Complexity tools | Metrics | Anchor judges semantic coherence |
| Refactoring tools | Suggest changes | Anchor only diagnoses |
| Static analyzers | Find bugs | Anchor finds drift |

**Anchor occupies a unique space:**

It's the only tool that asks: **"Does this code still mean what it was supposed to mean?"**

---

## Limitations (Acknowledged)

### 1. Intent Inference

Intent is inferred from history. If history is shallow, missing, or misleading, confidence is low.

### 2. Subjectivity Remains

Even with evidence, some verdicts are arguable. "Semantic overload" vs. "comprehensive interface" is often debatable.

### 3. Context Dependency

What counts as drift depends on domain. Web frameworks and embedded systems have different evolution patterns.

### 4. False Negatives Preferred

Anchor is conservative. It prefers to miss drift (false negative) rather than cry wolf (false positive).

### 5. Single Language (Currently)

Python-first implementation. Other languages require different AST parsing and history analysis.

**These limitations are acceptable because:**
- Perfect detection is impossible
- Evidence-based debate is valuable even when verdicts are arguable
- Conservative approach builds trust

---

## The Philosophy in Practice

### Example: authenticate()

**Original intent (2012):**  
"Validate credentials against backends and return User."

**Current reality (2025):**
- Session-based login (33%)
- API token validation (33%)
- OAuth identity resolution (33%)

**Anchor's verdict:**  
Semantic Overload

**What happens next:**
1. Engineering team debates whether 3 roles is acceptable
2. Some argue "it's all authentication"
3. Others argue "these have different security models"
4. Decision: Accept the overload but document it, OR split into separate functions
5. Either outcome is fine - **the implicit was made explicit**

**This is success.**

---

## Philosophical Roots

Anchor draws from:

**Software Architecture:**
- Single Responsibility Principle
- Interface Segregation Principle
- Bounded contexts (DDD)

**Systems Thinking:**
- Drift vs. intentional change
- Constraint theory
- Architectural decisions as frozen points

**Evidence-Based Practice:**
- Reproducible results
- Falsifiable claims
- Peer review

**Engineering Culture:**
- Code review as debate
- Documentation as contract
- Naming as communication

---

## The Long-Term Vision

### Phase 1 (Current): Thesis Validation
Prove that intent drift can be detected, measured, and argued deterministically.

**Status:** ✅ Validated on Django

### Phase 2: Automation
Build the deterministic auditor:
- Call context clustering
- Rule-based drift detection
- Evidence generation
- CLI interface

**Target:** Python codebases with git history

### Phase 3: Integration
Make Anchor part of development workflows:
- CI/CD integration (non-blocking initially)
- Pre-merge checks (opt-in gates)
- Architectural reviews
- AI agent constraints

### Phase 4: Generalization
- Multi-language support
- Cross-project patterns
- Drift taxonomy
- Public drift databases

**The end goal:**  
Intent drift becomes a recognized form of technical debt, measurable and manageable.

---

## Core Beliefs

**We believe:**

1. **Intent matters.** Code without clear intent is ungovernable.

2. **Drift is inevitable.** But unacknowledged drift is dangerous.

3. **Flexibility enables drift.** Generic abstractions drift more than specific ones.

4. **Humans must decide.** Tools provide evidence; judgment remains human.

5. **Discomfort is necessary.** Comfortable tools don't challenge assumptions.

6. **Determinism enables debate.** Probabilism ends conversation.

7. **Small scope is strength.** Doing one thing well beats doing many things poorly.

**These beliefs shape every design decision.**

---

## Closing Principle

> "The code still works. Tests still pass. But meaning erodes."

**Anchor makes that erosion visible.**

Not to criticize. Not to prescribe.

But to enable **informed architectural debate** based on **evidence** rather than **intuition**.

That's the entire philosophy.

---

**Everything else is implementation detail.**