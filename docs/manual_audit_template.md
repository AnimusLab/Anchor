# Anchor Manual Audit: `[SymbolName]`

---

## 0. Audit Metadata

| Field              | Value                       |
| ------------------ | --------------------------- |
| **Symbol**         | `[SymbolName]`              |
| **Type**           | Class \| Function \| Method |
| **Module**         | `[module.path]`             |
| **File path**      | `[path/to/file.py]`         |
| **Repository**     | `[repo name and URL]`       |
| **Audit date**     | YYYY-MM-DD                  |
| **Auditor**        | [Name or Team]              |
| **Anchor version** | [e.g. 3.0.0-alpha]          |

---

## 1. Intent Anchor (Frozen Baseline)

### 1.1 Anchor Source

**Anchor commit SHA:** `[full sha]`
**Commit date:** YYYY-MM-DD
**Anchor type:** Explicit (docstring) | Inferred (code analysis)
**Confidence:** Very High | High | Medium | Low

**Confidence justification:**

- [Reason 1 — e.g. Explicit docstring at creation commit]
- [Reason 2 — e.g. Stable implementation at maturity milestone]
- [Reason 3 — e.g. Commit message aligns with implementation]

---

### 1.2 Original Intent (One Sentence)

**Original intent:**
[A single sentence capturing what the symbol was designed to do, in the authors' language.]

**Derivation:**

- Docstring: _"[exact quote from earliest docstring]"_
- [Additional evidence — key methods, commit message, comments]
- [Code structure evidence]

---

### 1.3 Original Assumptions

**Original assumptions (~YEAR):**

1. **[Assumption 1 — bold title]**
   _Evidence: [specific code or doc evidence]_

2. **[Assumption 2]**
   _Evidence: [specific code or doc evidence]_

3. **[Assumption 3]**
   _Evidence: [specific code or doc evidence]_

4. **[Assumption 4 — if applicable]**
   _Evidence: ..._

> These assumptions define the symbol's intent boundary.
> Any usage that violates an assumption is a candidate for drift.

---

## 2. Present-Day Usage (Observed Reality)

### 2.1 Call Context Inventory

#### Context 1: [Role Name] — Original Intent

- **Usage:** [description of how callers use the symbol here]
- **Key callers / locations:** [where this is invoked]
- **Alignment:** ✅ Full

---

#### Context 2: [Role Name]

- **Usage:** [description]
- **Key callers / locations:** [where this is invoked]
- **Alignment:** ✅ Full | ⚠️ Partial | ❌ None

---

#### Context 3: [Role Name — add/remove contexts as needed]

- **Usage:** [description]
- **Key callers / locations:** [...]
- **Alignment:** ✅ Full | ⚠️ Partial | ❌ None

---

### 2.2 Usage Clustering (Semantic Roles)

**Observed roles:**

1. **[Role 1 Name]**
   - [Description, typical callers, platform/framework]
   - **Estimated usage:** X–Y%

2. **[Role 2 Name]**
   - [Description]
   - **Estimated usage:** X–Y%

3. **[Role 3 Name — if applicable]**
   - [Description]
   - **Estimated usage:** X–Y%

**Key observation:**
[One sentence on which role dominates and whether it aligns with original intent.]

---

## 3. Drift Analysis

### 3.1 Role Compatibility

| Role     | Compatible with Intent? | Notes                                        |
| -------- | ----------------------- | -------------------------------------------- |
| [Role 1] | ✅ Yes                  | [short reason]                               |
| [Role 2] | ❌ No                   | [short reason — what assumption is violated] |
| [Role 3] | ⚠️ Partial              | [short reason]                               |

---

### 3.2 Responsibility Expansion

**Has the symbol's responsibility expanded beyond its anchor?**
✅ Yes | ❌ No | ⚠️ Partially

**Evidence:**

- [Key signal 1 — e.g. "60–70% of usage never invokes rendering methods"]
- [Key signal 2]
- [Key signal 3]

**Key signal:**
[The most telling single data point that supports or refutes drift.]

---

### 3.3 Temporal Drift Narrative

[Describe HOW drift occurred over time — ecosystem adoption, framework evolution, community reuse patterns, API-first trends, etc.]

**Result:**
[Implicit drift through external reuse, not internal evolution.] OR
[Explicit redesign without intent redefinition.] OR
[No drift detected — symbol remains within its original boundary.]

---

## 4. Verdict

### Final Verdict

> **[One of: ✅ Aligned | ⚠️ Semantic Overload | 🛑 Intent Violation | 📦 Dependency Inertia | 📈 Complexity Drift]**

---

### Justification

- [Key fact 1 that drives the verdict]
- [Key fact 2]
- [Key fact 3]
- [Key fact 4 — the decisive point]

---

## 5. Sanity Check

| Question            | Answer                         |
| ------------------- | ------------------------------ |
| Facts disputable?   | ✅ Yes / ❌ No                 |
| Verdict disputable? | ✅ Yes / ⚠️ Reasonably / ❌ No |
| Verdict defensible? | ✅ Yes / ❌ No                 |

[One sentence on where reasonable disagreement might exist, if applicable.]

---

## 6. Anchor Status Summary

```
[verdict icon] SymbolName

Anchored to:
[Original intent, one line] (~YEAR)

Current roles:
[Role 1] (X–Y%)
[Role 2] (X–Y%)
[Role 3] (X–Y%)

Verdict:
[Verdict name]

Rationale:
[2–3 sentence plain-English summary of the verdict rationale.
Explain what the symbol was, what it became, and why that matters.]
```

---

## 7. Audit Confidence

**Confidence:** Very High | High | Medium | Low

**Basis:**

- [Basis point 1 — e.g. Clear, explicit intent anchor with narrow original responsibility]
- [Basis point 2 — e.g. Quantifiable role dominance observable in ecosystem]
- [Basis point 3 — e.g. No reasonable alternative interpretation of original intent]

---

## Audit History

| Version | Date       | Status | Notes         |
| ------- | ---------- | ------ | ------------- |
| 1.0     | YYYY-MM-DD | Draft  | Initial audit |

---

**End of Audit**
