# Changelog

All notable changes to Anchor are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [4.3.5] — 2026-03-23

### Landing Page & Public Documentation
- Deployed production landing page at [anchorgovernance.tech](https://anchorgovernance.tech) via Cloudflare Pages.
- Full mobile responsiveness via `useIsMobile` React hook — all section grids stack on screens < 768px.
- Terminal animation uses `pre-wrap` + `wordBreak: break-all` to prevent horizontal overflow on mobile.
- Ticker bar hidden on mobile to prevent `max-content` width overflow.

### Documentation
- Updated `README.md` — corrected version, license (Apache 2.0), PyPI install, domain URL, and coverage stats.
- Updated `USAGE.md` — corrected version header, added PyPI install option.
- Updated `CHANGELOG.md` — added all v4.1.x through v4.3.5 entries.

### Stats (V4.3.5)
- **43** domain rules across 9 namespaces (SEC, ETH, PRV, ALN, AGT, LEG, OPS, SUP, SHR)
- **9** regulatory frameworks absorbed (3 standards bodies + 6 government regulators)
- **170** total regulatory mappings
- **0** self-audit violations — Anchor audits itself. CLEAN.

---

## [4.3.1] — 2026-03-23

### Landing Page
- Replaced Sparkline in StatsSection with `FinancialChart` (SVG-based candlestick/OHLC visualization).
- Replaced CasesSection grid with `AuditGraph` — SVG line chart of real open-source audit findings.
- Added dedicated `ContactSection` with direct email CTA (`tan@anchorgovernance.tech`).
- Standardized Jurisdiction Map items (removed inconsistent rule counts, unified layout).
- Balanced Case Study grid with `gridColumn` spanning for 5-item layouts.
- Updated all contact emails across Nav, Contact, and Footer sections.

### Fixed
- Removed dangling closing tags causing JSX syntax errors.
- Fixed `Contact` nav link to scroll to `#contact` section instead of firing `mailto:`.

---

## [4.2.0] — 2026-03-23

### Deployment
- Configured Cloudflare Pages deployment with root directory set to `landing/`.
- Build command set to `npm install && npm run build` to resolve `npm ci` peer dependency conflicts.
- Added `landing/public/_redirects` for SPA routing support on Cloudflare Pages.
- Linked custom domain `anchorgovernance.tech` — leverages existing Cloudflare DNS and email routing.

### Repository
- Removed `node_modules` from Git tracking.
- Added comprehensive `.gitignore` covering `node_modules`, `dist`, `.env`, `*.pyc`, `__pycache__`.
- Regenerated `package-lock.json` to resolve lock file version conflicts.

---

## [4.1.4] — 2026-03-23

### Landing Page
- Added `AuditGraph` component — SVG line chart plotting real open-source project audit findings.
- Added `ContactSection` with gold CTA button and direct email link.
- Case Studies section redesigned with `AuditGraph` replacing the manual case study card grid.

---

## [4.1.3] — 2026-03-22

### Landing Page
- Added `FinancialChart` component — SVG candlestick chart visualizing governance domain rule growth.
- Hero stats bar upgraded to use `FinancialChart` instead of flat `Sparkline`.
- `DataBar` upgraded with `MiniBarChart` for "Total Coverage" metric.
- Jurisdiction Map expanded to 3 columns: Domain Rules, Standards Bodies, Government Regulators.

---

## [4.1.2] — 2026-03-22

### Landing Page — Bloomberg Terminal Aesthetic
- Introduced Bloomberg Terminal-inspired mono typography and color palette.
- Added `Terminal` component with live cascading audit simulation.
- Added `DataBar` ticker with live stats: domain rules, frameworks, regulatory mappings.
- Added `AmbientParticles` and `DigitalMark` seal components.
- Added `LiveClock` in IST to nav bar.
- Added `Ticker` news bar with real regulatory headlines.
- Jurisdiction Map redesigned with three-column layout (Domain Rules / Standards / Regulators).

### Fixed
- Multi-ID violation suppression — canonical ID deduplication to prevent double-firing of `ANC-NNN` and `FINOS-NNN` aliases.
- PyPI performance — lazy-loaded tree-sitter grammars per language; eliminated ~3.5s startup overhead on cold installs.

---

## [4.1.0] — 2026-03-22

### Landing Page
- `ViolationsSection` — interactive enforcement output with per-severity color-coded badges and statute references.
- `StatsSection` — animated counters with sparklines and a "Anchor audited itself. CLEAN." self-audit card.
- `CoverageSection` (Jurisdiction Map) — three-tier coverage display with domain/framework/regulator classification.

---

## [4.0.0] — 2026-03-18

### Architecture
- **Federated domain model** — replaced monolithic `risk_catalog.yaml` with structured governance directories: `domains/`, `frameworks/`, `government/`.
- **All domain files are now mandatory** — SEC, ETH, SHR, ALN, AGT, PRV, LEG, OPS, SUP load automatically. Frameworks and regulators remain opt-in via `constitution.anchor`.
- **`constitution.anchor` is now the single manifest** — declares active frameworks and regulators.

### New: Diamond Cage (Behavioral Verification)
- WASM-based sandbox using WasmEdge for behavioral verification of AI-adjacent code and proposed patches.
- Reports as `Diamond Cage: ACTIVE` in CLI output.

### New: GOVERNANCE.lock (Remote Integrity Verification)
- `anchor check` fetches `GOVERNANCE.lock` from the Anchor registry and verifies per-file SHA-256 hashes.
- `seal_check: strict` in `constitution.anchor` aborts on mismatch.

### New: Commands
- `anchor sync --restore` — fetches authoritative governance files and restores tampered files.
- `anchor init --all` — installs all available domains, frameworks, and regulators.
- `anchor init --no-sign` — skips remote GOVERNANCE.lock fetch for offline initialisation.

### New: Alias Resolution Chain
- Legacy V3 `ANC-NNN` IDs resolve through FINOS framework layer: `ANC-NNN → FINOS-NNN`.

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
- `loader.py` — empty `policy.anchor` returned `NoneType` instead of `{}`, causing silent fallback to unpopulated V3 cache.
- `cli.py` — mitigation patterns were mapping to alias IDs instead of canonical IDs.
- Duplicate findings — `ANC-NNN` and `FINOS-NNN` no longer both fire for the same finding.

### Removed
- Monolithic `risk_catalog.yaml` — superseded by federated domain architecture.
- Local `.anchor.sig` signature file — superseded by remote `GOVERNANCE.lock`.

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

## [1.0.0] — 2026-01-24

Initial release. Architectural drift detection with AST-based comparison against baseline signatures.
