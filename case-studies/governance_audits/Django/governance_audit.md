# Anchor Governance Audit

**Status:** FAILED  
**Timestamp:** 2026-03-23 05:38:10  
**Source:** `D:\django`  

## Summary

| Category | Count |
|---|---|
| Blockers / Errors | 7 |
| Warnings | 0 |
| Info | 0 |
| Suppressed | 0 |
| Files Scanned | 898 |

## Active Violations

| ID | Severity | File | Message |
|---|---|---|---|
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\core\management\utils.py:175` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\db\backends\base\client.py:31` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\db\backends\mysql\creation.py:78` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\db\backends\mysql\creation.py:81` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\utils\autoreload.py:273` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\django\utils\version.py:91` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\scripts\manage_translations.py:48` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |

> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*
