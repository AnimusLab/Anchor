# Anchor 6.0.6

## Summary

Anchor 6.0.6 extends the 6.0.5 security hardening with signed governance-rule
integrity verification. Reports now state whether the bundled rule set was
actually verified, and CI can validate the lock without installing the native
runtime extension.

## Highlights

- Governance rules are checked against the signed `GOVERNANCE.lock`.
- Modified, missing, and unlisted rule files are detected.
- `anchor verify-sync` compares mitigation catalogs honestly.
- `anchor drift` reports that architectural drift analysis is not implemented
  rather than claiming success.
- `anchor sync --restore` restores only from verified packaged rules.
- Missing audit paths fail with an error instead of producing a clean result.
- The CLI reports `NO VIOLATIONS FOUND (automated checks only)` and includes a
  not-legal-advice disclaimer.
- Gateway authentication, body limits, sandbox checksum validation, safe
  extraction, and remote-policy URL restrictions remain enforced.
- Python and Rust package versions are synchronized at 6.0.6.

## Validation

- Governance lock check passed.
- CLI governance check passed with zero violations.
- Full unit suite: 116 passed.

This is an engineering security release. Deployment owners remain responsible
for authorization, network isolation, privacy, legal, and regulatory review.
