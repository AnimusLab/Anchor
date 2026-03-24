# Changelog

All notable changes to the Anchor governance engine are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [4.3.5] — 2026-03-23

### Changed
- License corrected to **Apache 2.0** across `README.md`, `setup.py`, and PyPI metadata.
- PyPI package renamed to `anchor-audit` — `pip install anchor-audit`.
- Updated coverage stats: **43 domain rules**, **170 regulatory mappings**, **9 frameworks/regulators**.

---

## [4.1.2] — 2026-03-22

### Fixed
- **Multi-ID deduplication** — `ANC-NNN` and `FINOS-NNN` aliases no longer both fire for the same violation. Deduplicated on canonical ID + file + line at reporting time.
- **Alias pattern mapping** — mitigation patterns were being mapped to alias IDs instead of canonical IDs, leaving aliases without detection patterns and reporting them as inactive. Patterns now bind to the canonical rule first; aliases receive fully-populated copies.

### Performance
- **Lazy grammar loading** — tree-sitter grammars now load per-language on first use rather than at package import. Eliminates ~3.5s startup overhead on cold installs with multiple language adapters installed.

---

## [4.0.0] — 2026-03-18

### Architecture
- **Federated domain model** — replaced monolithic `risk_catalog.yaml` with structured governance directories: `domains/`, `frameworks/`, `government/`. Each layer has clear ownership and versioning.
- **All domain files are now mandatory** — SEC, ETH, SHR, ALN, AGT, PRV, LEG, OPS, SUP load automatically. Frameworks and regulators remain opt-in via `constitution.anchor`.
- **`constitution.anchor` is now the single manifest** — declares active frameworks and regulators. Domains require no declaration.

### New: Diamond Cage (Behavioral Verification)
- WASM-based sandbox using WasmEdge for behavioral verification of AI-adjacent code and proposed patches.
- Proves security invariants at scan time — not just static pattern matching.
- Reports as `Diamond Cage: ACTIVE` in CLI output.

### New: GOVERNANCE.lock (Remote Integrity Verification)
- Replaces local `.anchor.sig` with a remote hash registry model.
- `anchor check` fetches `GOVERNANCE.lock` from the Anchor registry and verifies per-file SHA-256 hashes against the local governance directory.
- `seal_check: strict` in `constitution.anchor` — aborts on mismatch.
- `offline_behaviour: warn` (default) — continues with warning if remote unreachable; set to `abort` for enterprise CI/CD.

### New: Commands
- `anchor sync --restore` — fetches authoritative governance files from registry and restores any tampered or modified files. Logs restores to `.anchor/logs/sync.log` with chain hash.
- `anchor init --all` — installs all available domains, frameworks, and regulators in one command.
- `anchor init --no-sign` — skips remote GOVERNANCE.lock fetch for offline initialisation. Scans run in UNVERIFIED mode until `anchor sync --restore` is run.

### New: Alias Resolution Chain
- Legacy V3 `ANC-NNN` IDs resolve through FINOS framework layer: `ANC-NNN → FINOS-NNN`.
- FINOS_Framework.anchor is the Rosetta Stone — full mapping in `constitution.anchor` under `legacy_aliases`.

### New: Regulator Domains
- `government/RBI_Regulations.anchor` — RBI FREE-AI Report August 2025
- `government/EU_AI_Act.anchor` — EU AI Act 2024/1689
- `government/CFPB_Regulations.anchor` — CFPB Regulation B + 2024 Guidance
- `government/FCA_Regulations.anchor` — FCA AI Governance Guidance 2024
- `government/SEBI_Regulations.anchor` — SEBI AI/ML Consultation 2024-2025
- `government/SEC_Regulations.anchor` — SEC 2026 Examination Priorities

### New: Framework Domains
- `frameworks/FINOS_Framework.anchor` — FINOS AI Governance Framework
- `frameworks/NIST_AI_RMF.anchor` — NIST AI RMF 1.0
- `frameworks/OWASP_LLM.anchor` — OWASP LLM Top 10 2025

### Fixed
- `loader.py` — empty `policy.anchor` returned `NoneType` instead of `{}`, causing silent fallback to unpopulated V3 cache. Fixed with `raw = yaml.safe_load(...) or {}`.
- `cli.py` — mitigation patterns were mapping to alias IDs instead of canonical IDs. Patterns now mapped to canonical rules first; aliases inherit fully-populated copies.
- Duplicate findings — `ANC-NNN` and `FINOS-NNN` no longer both fire for the same finding. Deduplicated on canonical ID + file + line.

### Changed
- `policy.anchor` — `enforce_raise_only: true` is now enforced at the engine level. Attempts to lower severity below the constitutional floor are rejected with an error.
- `sealed:` and `seal: "sha256:PENDING"` fields removed from `constitution.anchor` — superseded by `GOVERNANCE.lock`.
- `.anchor/` is now committed to the project repository. `.anchor/cache/` is added to `.gitignore` instead.

### Removed
- Monolithic `risk_catalog.yaml` — fully superseded by federated domain architecture.
- Local `.anchor.sig` signature file — superseded by remote `GOVERNANCE.lock`.
- `active_domains` section in `constitution.anchor` — all domains are now mandatory.

---

## [3.0.0] — 2026-03-14

Output governance layer. Static analysis against `constitution.anchor` at the output level. Introduced `violation_id` → `mitigation.anchor` mapping.

---

## [2.8.1] — 2026-02-14

Security and compliance analysis via Tree-sitter AST parsing with multi-language support (Python, Rust, Go, TypeScript, Java, C++) and CI export improvements.

---

## [2.4.15] — 2026-02-09

Maintenance updates and dependency refresh for the 2.x line.

---

## [2.4.14] — 2026-02-08

Stability and packaging refinements ahead of the 2.4.15 final release.

---

## [1.0.0] — 2026-01-24

Initial release. Architectural drift detection with AST-based comparison against baseline signatures.
