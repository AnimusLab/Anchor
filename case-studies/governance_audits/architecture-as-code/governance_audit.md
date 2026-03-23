# Anchor Governance Audit

**Status:** FAILED  
**Timestamp:** 2026-03-23 04:56:20  
**Source:** `D:\architecture-as-code`  

## Summary

| Category | Count |
|---|---|
| Blockers / Errors | 11 |
| Warnings | 0 |
| Info | 0 |
| Suppressed | 0 |
| Files Scanned | 684 |

## Active Violations

| ID | Severity | File | Message |
|---|---|---|---|
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoAdrStore.java:86` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoAdrStore.java:231` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoArchitectureStore.java:80` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoArchitectureStore.java:191` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoCounterStore.java:49` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoFlowStore.java:77` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoFlowStore.java:185` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoPatternStore.java:77` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoPatternStore.java:185` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoStandardStore.java:83` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |
| `FINOS-002, OWASP-003, SEC-002` | **BLOCKER** | `.\calm-hub\src\main\java\org\finos\calm\store\mongo\MongoStandardStore.java:177` | Vector store write detected without encryption. Embeddings can leak sensitive data via inversion attacks. |

> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*
