# Anchor Governance Audit

**Status:** FAILED  
**Timestamp:** 2026-03-23 04:09:49  
**Source:** `D:\huggingface_hub`  

## Summary

| Category | Count |
|---|---|
| Blockers / Errors | 12 |
| Warnings | 0 |
| Info | 0 |
| Suppressed | 0 |
| Files Scanned | 164 |

## Active Violations

| ID | Severity | File | Message |
|---|---|---|---|
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\src\huggingface_hub\cli\lfs.py:54` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\src\huggingface_hub\cli\lfs.py:59` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\src\huggingface_hub\utils\_subprocess.py:85` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\src\huggingface_hub\utils\_subprocess.py:132` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\utils\helpers.py:46` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `FINOS-014, OWASP-002, RBI-018, SEC-007` | **BLOCKER** | `.\utils\helpers.py:47` | Native subprocess execution detected. Use Diamond Cage (WASM) sandboxing for agent tools. |
| `ALN-001, FINOS-008, OWASP-009` | **ERROR** | `.\src\huggingface_hub\inference\_client.py:700` | LLM API call detected. Ensure output is validated before use (e.g., schema check, grounding). |
| `ALN-001, FINOS-008, OWASP-009` | **ERROR** | `.\src\huggingface_hub\inference\_client.py:754` | LLM API call detected. Ensure output is validated before use (e.g., schema check, grounding). |
| `ALN-001, FINOS-008, OWASP-009` | **ERROR** | `.\src\huggingface_hub\inference\_generated\_async_client.py:723` | LLM API call detected. Ensure output is validated before use (e.g., schema check, grounding). |
| `ALN-001, FINOS-008, OWASP-009` | **ERROR** | `.\src\huggingface_hub\inference\_generated\_async_client.py:778` | LLM API call detected. Ensure output is validated before use (e.g., schema check, grounding). |
| `ALN-001, FINOS-008, OWASP-009` | **ERROR** | `.\src\huggingface_hub\inference\_mcp\mcp_client.py:273` | LLM API call detected. Ensure output is validated before use (e.g., schema check, grounding). |
| `FCA-004, FINOS-013, SEC-006` | **ERROR** | `.\src\huggingface_hub\inference\_providers\openai.py:9` | Direct call to public LLM API detected. Route through a PII-scrubbing proxy. |

> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*
