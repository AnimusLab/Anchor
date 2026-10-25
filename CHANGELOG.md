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

### Tests

- Add governance integrity regression coverage.
- Full unit suite passed during release preparation: 116 tests.
