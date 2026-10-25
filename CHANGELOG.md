# Changelog

All notable changes to Anchor are documented here.

## [6.0.6] - Unreleased

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

### Tests

- Add governance integrity regression coverage.
- Add CLI contract tests (exit codes, `--format`, `--severity`, option order,
  `init` without a TTY, telemetry).
- Configure pytest (`testpaths`, importlib import mode) so `pytest` runs from
  the repository root; remove two obsolete tests that imported the removed
  `anchor.repo` module.
- Full unit suite: 139 tests.
