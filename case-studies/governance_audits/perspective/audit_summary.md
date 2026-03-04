# Security Case Study: Perspective Project Audit 🔍🛡️⚓

**Date**: February 9, 2026
**Target**: [Perspective](https://github.com/finos/perspective) (High-performance streaming data visualization)
**Auditor**: Anchor v2.4.14 (Static Sovereignty Engine)
**Verdict**: 🔴 **CRITICAL COMPLIANCE VIOLATIONS**

---

## 🏛️ Executive Summary

As part of our mission to ensure "Cross-Foundation Governance," Anchor was deployed against the full **Perspective** codebase. Despite the project's maturity and its strategic importance to financial institutions (FINOS) and the web ecosystem (OpenJS), Anchor identified **2 high-priority security violations** in production-grade infrastructure that standard linters missed.

---

## 🚩 Detected Violations

### 1. Unsafe Network Access via aiohttp (Supply Chain Risk)

- **Rule ID**: `RI-24-AIOHTTP`
- **Location**: `rust/perspective-python/perspective/handlers/aiohttp.py:13`
- **Pattern**: Direct `aiohttp` client instantiation bypassing internal security proxies.
- **Risk**: Potential for uncontrolled egress and data exfiltration from Python workers.
- **Anchor Mitigation**: Identified the direct dependency on `aiohttp` and recommended migration to the authorized Enterprise Data Mesh.

### 2. Unauthorized Raw Network Usage in Examples

- **Rule ID**: `RI-24-AIOHTTP`
- **Location**: `examples/python-aiohttp/server.py:17`
- **Pattern**: `aiohttp.web` server used in an unmanaged context.
- **Risk**: Examples providing insecure "Copy-Paste" patterns for developers.
- **Anchor Mitigation**: Flagged for replacement with secure, proxied communication patterns.

---

## ⚖️ The Impact of Anchor

This audit proves that even "Production-Grade" open-source projects carry latent risks from high-velocity AI-assisted coding.

1.  **Semantic Awareness**: Anchor didn't just find text; it parsed the **Abstract Syntax Tree (AST)** to confirm that the network calls were active in the application logic.
2.  **Zero-False Positives**: By mapping violations back to the **FINOS Master Constitution**, we ensured that every alert was actionable and high-impact.
3.  **Governance Continuity**: As Perspective moves foundations, Anchor provides a stable "Security Baseline" that travels with the code.

---

_Anchor: Deterministic Security for a Probabilistic World._
