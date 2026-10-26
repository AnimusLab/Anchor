# Changelog

All notable changes to Anchor are documented here.

## [6.0.6] - 2026-10-26

### Security

- Verify bundled governance rules against the signed `GOVERNANCE.lock`.
- Detect modified, missing, and unlisted governance rule files.
- Fail closed when governance verification is required but unavailable.
- Require gateway bearer authentication and enforce request-size limits.
- Verify sandbox downloads and reject unsafe archive paths and links.
- Restrict remote policy extensions to validated HTTPS URLs.
- Keep telemetry authenticated and exclude request payloads.

### Changed

- Add `anchor verify-sync`, honest `anchor drift`, and verified
  `anchor sync --restore` behavior.
- Report automated findings without implying legal certification.
- Synchronize Python and Rust package versions at 6.0.6.
- Add standalone governance-lock verification for CI.

### Fixed

- `anchor check` now exits `1` when violations are found (an unreachable
  `sys.exit(1)` meant it always exited `0`, so CI gates could never fail).
- `--format json` and `--format markdown` are now honoured; they print only the
  report to stdout. Previously the option was accepted and ignored.
- `--severity` now applies as a threshold to findings and the exit code. Each
  finding reports the severity declared by its rule (`blocker`/`error`/...);
  previously every finding was reported as `error`.
- Options may follow the path (`anchor check . --format json`); previously they
  were treated as paths ("Path not found: --format.").
- `anchor init` no longer blocks when stdin is not a terminal.
- CLI telemetry dispatch referenced an unimported `uuid` and failed silently; it
  now runs when explicitly opted in via `ANCHOR_TELEMETRY`, including with
  `--format json|markdown`.
- Trace URIs are valid `file:///` URIs (they had four slashes).
- SEC-007 and SEC-010 report accurate descriptions.

### Added

- `anchor --version`.
- Building from source documented (needs Rust >= 1.78).
- `AnchorEngine.code_rules()` exposes the scanner's rule table (id, statute, name,
  pattern, runtime) for introspection and tests.
- `Tests` GitHub Actions workflow: pytest on Ubuntu/Windows/macOS across Python
  3.10, 3.12 and 3.14, plus a wheel install smoke test (fresh venv, `init`, exit
  codes, `--format json`).
- Python 3.14 trove classifier (the suite passes on 3.14).

### Changed

- Scanner: the three index-coupled tables in the Rust kernel (regex list, finding
  metadata, Layer 2 payload checks) are now one `CODE_RULES` table, so they cannot
  drift apart. Detection behaviour is unchanged (identical findings and payload
  verdicts before and after on a corpus covering all 10 patterns).
- The `anchor-guard` PR comment no longer says "Certified by ..."; it states that
  the output is automated static analysis, not a certification.
- The README's per-release "6.0.3 highlights" moved into this changelog.

### Tests

- Add governance integrity regression coverage.
- Add CLI contract tests (exit codes, `--format`, `--severity`, option order,
  `init` without a TTY, telemetry).
- Configure pytest (`testpaths`, importlib import mode) so `pytest` runs from
  the repository root; remove two obsolete tests that imported the removed
  `anchor.repo` module.
- Rule-table consistency tests: scanner rule IDs must exist in the signed rule files
  (known gap: `RBI-007` is emitted by the scanner but not defined in the rule files;
  fixing it needs a re-signed `GOVERNANCE.lock`), each rule has a declared severity,
  and the Layer 2 payload guard enforces exactly the rules flagged `runtime`.
- Replace Click's deprecated `isolated_filesystem()` with a shared `isolated_fs` fixture.
- Full unit suite: 143 tests.

## [6.0.3]

- Telemetry remains explicitly opt-in and performs no network dispatch by default.
- Governance signatures are line-ending independent across Windows, macOS, and Linux.
- The package metadata, wheel smoke test, secret scanning, and developer extras are
  aligned with the `pyproject.toml` build.
- The committed governance public key is rotated; the private signing key is
  generated and retained outside the repository.
