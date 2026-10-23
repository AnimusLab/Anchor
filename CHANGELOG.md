# Changelog

All notable changes to Anchor are documented here.

## [6.0.5] - Unreleased

### Security

- Fail closed in the CLI, gateway, and runtime decorators when the native Rust
  enforcement engine is unavailable.
- Enable SEC-010 dynamic-execution and SEC-007 dangerous-shell detection in
  static and runtime paths.
- Require header-based telemetry authentication and constant-time token
  comparison.
- Reject telemetry query-string credentials and untrusted WebSocket origins.
- Load telemetry credentials at connection time instead of module import time.
- Remove request-body content from telemetry packets.

### Changed

- Keep Rust and Python package versions synchronized at 6.0.5.
- Add regression coverage for telemetry authorization, token handling, payload
  exclusion, detection gaps, and version synchronization.
