# Security Policy

## Supported versions

Only the latest 6.0.x release of `anchor-audit` receives security fixes. Please upgrade before reporting
(`pip install --upgrade anchor-audit`). Versions 6.0.2 to 6.0.4 contain known fail-open behaviour fixed in later releases.

## Reporting a vulnerability

Please report privately; do **not** open a public issue.

- Use GitHub's **"Report a vulnerability"** button on the Security tab of this repository, or
- email **tan@animuslab.dev** with the subject `anchor-audit security`.

Include the version, a minimal reproduction, and the impact you see. We aim to acknowledge reports within 7 days and to
agree a disclosure date with you; we ask for up to 90 days to ship a fix before details are made public. Reporters who
follow this process will be credited unless they prefer otherwise.

## Scope

In scope: the Rust engine, the `anchor` CLI, the `@guard` runtime, the gateway (`anchor.app`), the sandbox installer,
rule/lock signature verification and telemetry.

Out of scope: false positives or false negatives in detection rules (please open a normal issue; see
[Limitations in the README](README.md)), social engineering, and denial of service that needs a privileged position.

## Security-relevant configuration

- Gateway: set `ANCHOR_GATEWAY_TOKEN`; bind to `127.0.0.1` unless behind a trusted proxy.
- Telemetry is off by default (`ANCHOR_TELEMETRY=on` to enable); see [docs/telemetry.md](docs/telemetry.md).
- Remote `extends:` policies must be `https://`; optionally restrict hosts with `ANCHOR_POLICY_URL_ALLOWLIST`.
