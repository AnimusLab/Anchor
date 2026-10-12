# Anchor Telemetry

Anchor does not transmit anything unless you explicitly opt in.

- **Default: OFF.** `ANCHOR_TELEMETRY` is unset by default.
- When off, `SpokeTelemetryClient.dispatch_state_event()` returns before any
  socket is opened. No DNS lookup, no connection, no request.
- When off, raw source code, prompts, and file contents never leave your
  process. Nothing is buffered for later upload.

To enable it:

```bash
export ANCHOR_TELEMETRY=1     # 1, true, on, yes (case-insensitive)
```

---

## When a packet is sent

Telemetry is only dispatched from two places, and only under these conditions:

| Call site | Fires when |
|---|---|
| `anchor/guard.py` (`_perform_audit`) | A guarded call produced a **non-compliant** audit report, i.e. Anchor was already blocking the action. Compliant calls never trigger it. |
| `anchor/cli.py` (scan command) | You run `anchor check` and it completes. Fires once per scan. |

If the env var is off, both paths are no-ops.

---

## Destination

| | |
|---|---|
| Default URL | `http://localhost:3000` |
| Override | `ANCHOR_HUB_URL` |
| Path | `/api/v1/telemetry/event` |
| Method | `POST` |
| Timeout | 4.0 seconds |

The default target is localhost. You must point `ANCHOR_HUB_URL` at a real
hub to send anything off-machine.

---

## Exactly what is sent

The request body is this JSON object, built in
`SpokeTelemetryClient.dispatch_state_event()`:

```json
{
  "event_id": "evt_sec-001_breach",
  "silo_id": "FINANCE",
  "project_name": "my_package",
  "identity_fingerprint": "sha256:<hex of your public key>",
  "compliance_verdict": "NON_COMPLIANT",
  "risk_score": 8.5,
  "violations": [
    {
      "rule_id": "SEC-001",
      "statute": "EU AI Act Art 14 / RBI Recommendation 6",
      "severity": "CRITICAL",
      "trace_uri": "file:///my_package.py#func=execute_algorithmic_trade",
      "summary": "Sanitize and enforce structural boundaries for rule SEC-001."
    }
  ]
}
```

### Field reference

| Field | Type | Where the value comes from |
|---|---|---|
| `event_id` | string | Caller-supplied, or generated as `evt_<12 hex chars>`. |
| `silo_id` | string | `anchor/guard.py`: the `@guard(domain=...)` value, uppercased. `anchor/cli.py`: `ANCHOR_HUB_ID`, default `animuslab-hq`. |
| `project_name` | string | `anchor/guard.py`: the guarded function's `__module__`, default `agentic-execution-node`. `anchor/cli.py`: the basename of the scanned directory. |
| `identity_fingerprint` | string | `"sha256:"` + SHA-256 of your public key in PEM form. If no key is found, the constant `sha256:ed25519_node_sovereign_key`. |
| `compliance_verdict` | string | `NON_COMPLIANT` or `COMPLIANT`. |
| `risk_score` | float | Engine-reported risk, 0.0-10.0. |
| `violations` | array | One object per violation, as shown above. |

### Violation object fields

| Field | Notes |
|---|---|
| `rule_id` | e.g. `SEC-001`. |
| `statute` | A human-readable label, e.g. `EU AI Act Regulation`. |
| `severity` | Engine risk level, e.g. `CRITICAL`. |
| `trace_uri` | `file:///<module>.py#func=<function name>`. Module and function names only — **no file path on disk, no line contents.** |
| `summary` | The remediation directive text. |

### Request headers

| Header | Present when |
|---|---|
| `Content-Type: application/json` | Always |
| `X-API-Key` | `ANCHOR_API_KEY` is set |
| `X-Anchor-Signature` | A local Ed25519 private key was found; hex signature over the exact request bytes |

### What is **never** sent

Based on reading `anchor/core/telemetry.py` in full:

- Your source code, file contents, or diffs
- Prompt text or model input/output
- Environment variables, secrets, or credentials
- Usernames, hostnames, or absolute filesystem paths
- Any data from a *compliant* (non-blocked) guarded call

The client never reads a file to transmit it. The payload is assembled
entirely from the in-memory fields listed above.

---

## Local key handling

`SpokeTelemetryClient.__init__` looks for an Ed25519 private key, in order:

1. the `private_key_path` argument
2. `$ANCHOR_PRIVATE_KEY_PATH`
3. `.anchor/keys/ed25519_private.pem`
4. `~/.anchor/keys/ed25519_private.pem`

If one is found it is used only to compute `identity_fingerprint` and to sign
the request body. It is never transmitted. If none is found,
`identity_fingerprint` falls back to the constant
`sha256:ed25519_node_sovereign_key`, and no signature header is sent.

---

## Error handling

If the hub is unreachable, the exception is caught and logged at `DEBUG`
level, which is silent unless you configure logging. Telemetry never
interrupts or slows down a guarded call beyond the 4-second timeout.

---

## Testing

`tests/test_telemetry_opt_in.py` asserts that no socket is opened when the
switch is off.
