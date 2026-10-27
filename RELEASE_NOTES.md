# Anchor 6.1.0

## Summary

Anchor 6.1.0 closes gaps found by testing the published 6.0.6 package end to end:
prompt-injection rules were not enforced in the SDK and HTTP interceptors,
several static and model checks failed open, and a few CLI messages described
behaviour the code does not have. This is a minor release because it adds
static rules and changes some defaults; see Upgrade notes before rolling it out.

## Highlights

- **Runtime:** SDK and HTTP interceptors enforce the prompt-injection rules;
  block mode raises on dangerous responses; `httpx.AsyncClient` and `urllib` are
  intercepted; bare AWS keys, provider tokens and spaced card numbers are detected.
- **Guard:** bare `@guard` / `@enforce` protect the function; new payload rules
  (AGT-010 to AGT-013) block destructive SQL, exfiltration, credentials and cards.
- **Static rules:** SEC-020 to SEC-026 cover AWS keys, provider tokens, PEM
  private keys, unsafe deserialization, disabled TLS verification, `document.write`
  and SSN literals.
- **Ignore pragmas** are rule-specific and line-scoped; a pragma no longer hides
  unrelated findings on the next line.
- **Model audit** validates safetensors/GGUF headers, scans pickle payloads and
  never approves a file that no check could verify.
- **Telemetry** signs packets with the key `anchor init` generates.
- **CLI:** `heal PATHS` scans the given paths and needs `--suppress` for
  suppression-only fixes; `init` always gitignores the private key and installs a
  corrected pre-commit hook; registry, hub-key and threat-model messages no longer
  claim work that does not happen; `.anchorignore` patterns match Windows paths.

## Upgrade notes

- A pragma that names a rule other than the one that fired no longer suppresses
  it. Legacy IDs `ANC-018`, `RI-12`, `ANC-030` and `ANC-031` still work as aliases.
  Set `ANCHOR_LEGACY_PRAGMAS=1` to keep the previous behaviour while migrating.
- In block mode a blocker-severity response now raises `AnchorViolationError`
  instead of only being logged.
- New static rules can add findings to existing projects (SEC-026 is a warning
  and hidden at the default severity).
- `anchor check --model` exits 1 for formats it cannot verify (for example ONNX).

## Not implemented in this release

Registry upload, hub keys, threat-model-driven enforcement and architectural
drift analysis are still not implemented; the CLI says so.

## Validation

- Full unit suite passes on Linux (Python 3.10, 3.12, 3.14) and Windows (Python 3.14).
- `python -m anchor check .` reports zero violations.

This is an engineering security release. Deployment owners remain responsible
for authorization, network isolation, privacy, legal, and regulatory review.
