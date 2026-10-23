# Anchor 6.0.5

## Summary

Anchor 6.0.5 hardens enforcement and telemetry behavior after the 6.0.4
release. The runtime now fails closed when its native enforcement engine is
unavailable, and telemetry access is restricted to explicitly authorized
clients without transmitting request bodies.

## Highlights

- SEC-010 and SEC-007 detection is enabled in both static and runtime paths.
- Rust and Python package versions are checked for synchronization.
- CLI, gateway, and runtime decorators fail closed when the native engine is
  unavailable.
- Telemetry requires an `Authorization: Bearer <token>` header.
- Telemetry tokens are compared with constant-time comparison.
- Query-string tokens are rejected.
- Telemetry tokens are read when each WebSocket connection is established.
- WebSocket origins use an explicit allowlist.
- Request payloads are excluded from telemetry packets.

## Security and compliance impact

These changes reduce the risk of false compliance results, silent enforcement
bypasses, credential leakage through WebSocket URLs, unauthorized telemetry
subscriptions, and disclosure of prompts, secrets, source code, or tenant
data.

This is an engineering security release. Deployment owners remain responsible
for protecting telemetry credentials, isolating deployments, configuring
authorization, and completing deployment-specific privacy, legal, and
regulatory review.

## Validation

The focused security and regression suite passed:

```text
43 passed
```

Deployment-specific compliance results depend on the configured policies and
the code being audited.
