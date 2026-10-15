# Telemetry

Anchor does **not** contact any server unless you opt in.

Enable: `export ANCHOR_TELEMETRY=on` (also `1`, `true`, `yes`). Default: off, in which
case no network connection is attempted. Hub address: `ANCHOR_HUB_URL`; key: `ANCHOR_API_KEY`.

## Fields sent when enabled (JSON, Ed25519-signed in `X-Anchor-Signature`)

| Field | Content |
|---|---|
| `event_id` | random event identifier |
| `silo_id` | tenant/hub identifier (`ANCHOR_HUB_ID` or the guard domain) |
| `project_name` | scanned directory name or Python module name |
| `identity_fingerprint` | sha256 of the node's public key |
| `compliance_verdict` | COMPLIANT / NON_COMPLIANT |
| `risk_score` | numeric score |
| `violations[]` | `rule_id`, `statute`, `severity`, `trace_uri` (file/function path), `summary` |

Source code and call payloads are not included. Network failures are logged at DEBUG only.
