# Anchor Governance Audit

**Status:** FAILED  
**Timestamp:** 2026-03-23 06:08:47  
**Source:** `D:\open_spiel`  

## Summary

| Category | Count |
|---|---|
| Blockers / Errors | 4 |
| Warnings | 0 |
| Info | 0 |
| Suppressed | 0 |
| Files Scanned | 602 |

## Active Violations

| ID | Severity | File | Message |
|---|---|---|---|
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\open_spiel\python\algorithms\matrix_nash.py:82` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\open_spiel\python\bots\gtp.py:49` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\open_spiel\python\examples\bridge_uncontested_bidding_bluechip.py:99` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\open_spiel\python\examples\bridge_wb5.py:158` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |

> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*
