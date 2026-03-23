# Anchor Governance Audit

**Status:** FAILED  
**Timestamp:** 2026-03-22 19:59:07  
**Source:** `D:\Anchor\anchor\__init__.py`  

## Summary

| Category | Count |
|---|---|
| Blockers / Errors | 3 |
| Warnings | 0 |
| Info | 0 |
| Suppressed | 0 |
| Files Scanned | 7 |

## Active Violations

| ID | Severity | File | Message |
|---|---|---|---|
| `FINOS-014, SEC-007` | **BLOCKER** | `anchor/core/engine.py:54` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, SEC-007` | **BLOCKER** | `anchor/core/engine.py:558` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, SEC-007` | **BLOCKER** | `test_vuln.py:2` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |

> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*
