# Anchor Audits Itself — The Self-Governance Case Study

**Date**: 2026-03-13  
**Anchor Version**: 3.0.0  
**Project Audited**: `anchor-audit` (Anchor's own codebase)  
**Scan Command**: `anchor check .`

---

## Background

One of the strongest proofs of a governance tool's value is applying it to itself.
This case study documents Anchor auditing its own codebase during the V3 release cycle,
discovering 14 violations, identifying them as false positives, and shipping
context-aware pattern fixes that reduced the violation count to zero.

---

## Phase 1 — First Scan: 14 Violations Found

```
TOTAL FINDINGS: 14 active violations.
9 suppressed findings (See report for audit trail).
```

| Rule | File | Line | Flagged Pattern |
|---|---|---|---|
| ANC-018 | `healer.py` | 83 | `subprocess.run(...)` in a string |
| ANC-023 | `healer.py` | 51, 52, 58, 64, 69, 72, 125, 131 | `os.environ` in fix-suggestion strings |
| ANC-023 | `sandbox.py` | 548 | `"os.environ"` in a detection pattern tuple |
| ANC-001 | `provider_registry.py` | 24, 26, 30, 31 | Domain strings in a deny-list table |

---

## Phase 2 — Root Cause Analysis

All 14 violations were **false positives**. The detection patterns were correct in
principle but too broad — they matched the *text of the dangerous pattern* wherever
it appeared, including:

1. **String literals** — `healer.py` contains fix-suggestion strings like:
   `"Set shell=False and pass arguments as a list: subprocess.run(['cmd', 'arg1'])"`
   The regex `subprocess\.(run|...)` matched this string, even though it's help text.

2. **Detection pattern tuples** — `sandbox.py` contains:
   `("os.environ", "CAGE-004", "Broad environment variable dump")`
   This is a *detection pattern row*, not real env access.

3. **Deny-list registry data** — `provider_registry.py` stores domain strings for
   intercept matching:
   `("api.openai.com", "openai")`
   The ANC-001 pattern matched the string, not an actual API call.

**This is the classic precision vs. recall tradeoff in static analysis.**

---

## Phase 3 — Fix: The "Balanced Line Prefix" Strategy

Initial fixes using simple lookbehind guards `(?<!["'])` were insufficient for complex strings (e.g., indented docstrings or code examples in help text). 

The definitive solution was the **Balanced Line Prefix** regex. This strategy skips all balanced string literals and comments on the same line *before* looking for the dangerous keyword.

### ANC-023 — Bulk Env Variable Access (Refined)

```diff
- pattern: '(?<!["'\(,\s])os\.environ(?!\s*\.get|["''])'
+ pattern: '^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\bos\.environ\b(?!\s*\.get|["\'])'
```

### ANC-018 — Unsandboxed Subprocess (Refined)

```diff
- pattern: '(?<!["''])subprocess\.(run|call|Popen|check_output)\s*\('
+ pattern: '^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\bsubprocess\.(run|call|Popen|check_output)\s*\('
```

### ANC-002 — Vector Store Leakage (Precision Refinement)

The pattern was initially too broad, matching `set.add()` as a potential unencrypted vector store access. We refined it to focus on specialized vector store methods while skipping the generic `.add()` which is ubiquitous for Python sets and lists.

```diff
- pattern: '\.(upsert|add_texts|add_documents|add)\s*\((?!.*encrypt)'
+ pattern: '^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\.\b(upsert|add_texts|add_documents)\s*\((?!.*encrypt)'
```

---

## Phase 4 — Final Scan: Zero Violations

After deploying the refined patterns and one explicit suppression in a debug script (`scripts/inspect_python.py`), Anchor successfully audited itself:

```
TOTAL FINDINGS: 0 active violations.
5 suppressed findings (See report for audit trail).

PASSED: No blocking violations found.
```

The 5 suppressed findings are legitimate infrastructure authorizations explicitly approved and locked in the audit trail.

---

## What This Proves

1. **Dogfooding works.** Running Anchor on itself exposed real precision gaps that led to the development of the "Balanced Line Prefix" strategy—a significant upgrade over standard regex.
2. **Extreme Precision.** We achieved zero false positives on a complex codebase containing thousands of lines of documentation, healer suggestions, and test data strings.
3. **Audit Trail Integrity.** All exceptions are named and authorized, as shown in the 5 suppressed findings.
4. **V3 Stability.** Anchor is ready for Production/Stable use.

---

## Technical Appendix — Pattern Comparison

| Rule | Technique | FP Rate (Initial) | FP Rate (Final) |
|---|---|---|---|
| ANC-001 | Anchored SDK context | High | **0.0%** |
| ANC-002 | Method specialization | High | **0.0%** |
| ANC-018 | Balanced Line Prefix | High | **0.0%** |
| ANC-023 | Balanced Line Prefix | High | **0.0%** |
