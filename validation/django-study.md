# Empirical Study: Django Framework Validation

This document reports on our attempt to validate Anchor's automated drift detection engine against the core codebase of the **Django Web Framework**. 

While the experiment resulted in a 0% automated agreement rate, the findings provide a crucial proof of scope limits and document the "Validation Paradox" of framework vs. application auditing.

---

## 1. Executive Summary

*   **Test Date**: 2026-01-23
*   **Target Codebase**: Django (Core authentication, forms, and manager modules)
*   **Audited Symbols**: 11
*   **Result**: 0/11 symbols successfully audited (0% agreement)
*   **Core Finding**: The automated scan failed because Anchor extracts call contexts *solely within the target repository*, whereas a framework's core symbols are primarily invoked in *external consumer codebases* (DRF, third-party libraries, and user apps).

---

## 2. Test Results

The table below lists the evaluation status for each target symbol:

| Symbol | Intent Anchor Extraction | Call Contexts Extracted | Verdict Status |
|---|---|---|---|
| `authenticate()` | ✓ Found (`5ceed0a0`) | 3 found (internal tests only) | ❌ Insufficient data |
| `login()` | ✓ Found (`5ceed0a0`) | 2 found (internal tests only) | ❌ Insufficient data |
| `logout()` | ✓ Found (`5ceed0a0`) | 2 found (internal tests only) | ❌ Insufficient data |
| `User` | ✓ Found (`bcfaa735`) | 0 found | ❌ Insufficient data |
| `AbstractUser` | ✓ Found (`c433fcb3`) | 0 found | ❌ Insufficient data |
| `UserManager` | ✓ Found (`bcfaa735`) | 2 found | ❌ Insufficient data |
| `Form` | ✓ Found (`7c7ad041`) | 0 found | ❌ Insufficient data |
| `BaseForm` | ✓ Found (`7c7ad041`) | 0 found | ❌ Insufficient data |
| `ModelForm` | ✓ Found (`29f0e818`) | 3 found | ❌ Insufficient data |
| `Manager` | ✓ Found (`5ceed0a0`) | 4 found | ❌ Insufficient data |
| `BaseManager` | ✓ Found (`31fadc12`) | 0 found | ❌ Insufficient data |

---

## 3. The Validation Paradox

We chose Django as a validation target because it is a mature, 15+ year codebase with clear historical commit records ("fissures") and obvious drift patterns. 

However, this maturity created the **Validation Paradox**:
*   Django is a **public framework**, not a self-contained application.
*   Its primary functions are exported symbols designed for consumption by downstream codebases (e.g. Django REST Framework, django-allauth, and enterprise apps).
*   Django's internal repository contains only test suites and helper scripts, resulting in fewer than the threshold of 10 call contexts required to perform semantic clustering.

Manual audits succeeded because humans automatically search external ecosystems (e.g., searching GitHub repositories or downstream package dependencies) to verify real-world usage.

---

## 4. Scope Limits & Recommendation

This study establishes a clear boundary for Anchor's current capabilities:

1.  **Supported Codebases**: Anchor is optimized for **application repositories** and **microservices** where callers and definitions reside in the same codebase.
2.  **Unsupported Codebases (Currently)**: Public library and framework codebases, where usage patterns are external to the source tree.
3.  **Roadmap Priority**: Expanding Anchor to support external ecosystem scanning by integrating GitHub Code Search API and PyPI dependency graphs to sample real-world consumer codebases.
