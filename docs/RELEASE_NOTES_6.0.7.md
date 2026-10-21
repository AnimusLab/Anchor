# Anchor 6.0.7 Release Preparation

> **Status: Unreleased draft.**  
> This document is release-preparation material only. It does not indicate that
> version 6.0.7 has been published.

## Release summary

Anchor 6.0.7 hardens the governance runtime and closes fail-open paths that
could produce false assurance during enforcement or telemetry streaming.

### Highlights

- Fail-closed behavior when the native Rust engine is unavailable.
- Runtime gateway startup failure instead of compliant fallback responses when
  enforcement is not loaded.
- Telemetry WebSocket access restricted by an explicitly configured token and
  trusted-origin validation.
- Query-string telemetry tokens rejected to prevent credential leakage through
  URL and proxy logs.
- Request payloads omitted from telemetry packets to prevent prompt, secret, and
  tenant-data disclosure.
- Regression coverage for native-engine failure behavior and telemetry access
  control.

### Security and compliance impact

This release strengthens the auditability and trust boundaries of the Anchor
governance engine. It prevents silent enforcement bypasses during native-engine
failure and restricts telemetry to authorized clients without transmitting
request bodies, reducing the risk of credential, prompt, cross-client, and
governance-evidence disclosure.

### Validation

The focused security and regression test set passed:

```text
39 passed in 1.87s
```

### Release note

Anchor 6.0.7 hardens the enforcement and telemetry layers by failing closed
when the native engine is unavailable, preventing silent bypasses in the CLI
and gateway, and restricting WebSocket telemetry access to authenticated,
trusted clients without transmitting request bodies. This strengthens
auditability, reduces false-assurance and disclosure risk, and helps preserve
compliance-oriented governance behavior in enterprise deployments.

## Security patch and legal-risk mitigation summary

This release addresses material risks in the enforcement and telemetry paths of
the Anchor governance runtime. The project previously contained fail-open
behaviors that could return a clean compliance result when the native engine
was unavailable, as well as an over-broad telemetry WebSocket that could allow
unauthorized or untrusted clients to observe event data. These conditions could
create false assurance, weaken evidence integrity, and increase the risk of
unauthorized disclosure of operational or tenant-sensitive information.

The patch changes the default behavior to fail closed: if the native engine
cannot be loaded, the CLI and runtime server no longer report a compliant
state; they halt with an explicit error instead. Telemetry access is
restricted to authenticated clients and trusted origins, query-string
credentials are rejected, and request bodies are excluded from telemetry
packets. This reduces the likelihood of silent enforcement bypass and
unauthorized data disclosure, improves the integrity of governance evidence,
and strengthens the system's defensibility in regulated, enterprise, or
audit-driven environments.

This summary describes engineering risk mitigation and is not a legal opinion
or a substitute for deployment-specific legal, privacy, security, or
regulatory review. Operators remain responsible for configuring authentication,
protecting the telemetry token, validating deployment boundaries, and
confirming compliance obligations applicable to their use case.
