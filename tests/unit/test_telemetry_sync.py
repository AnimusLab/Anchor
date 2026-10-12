"""Verify the telemetry client routes and dispatches payloads over the wire.

Telemetry is opt-in, so ANCHOR_TELEMETRY must be switched on explicitly.

The previous version of this test patched httpx.AsyncClient.post, but
dispatch_state_event() uses the synchronous httpx.Client. The mock therefore
never intercepted anything and the test really did open a connection to
https://animuslab.dev (it failed on a 301 redirect, then asserted
assert_called_once on a call count of 0). This version patches the symbol
that is actually used, so the suite never touches the network.
"""

import pytest
from unittest.mock import MagicMock, patch

from anchor.core.telemetry import SpokeTelemetryClient


def test_spoke_telemetry_transmission_success(monkeypatch):
    """A signed packet is posted to the hub endpoint when opted in."""
    monkeypatch.setenv("ANCHOR_TELEMETRY", "1")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "LOGGED",
        "transaction_id": "tx_9988776655",
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        client = SpokeTelemetryClient(
            hub_url="https://animuslab.dev",
            identity_fingerprint="sha256:b49d424a21b4142ddb670bce34f798...",
        )

        result = client.dispatch_state_event(
            event_id="evt_test_v6_sync",
            project_name="payment-architecture-pipeline",
            silo_id="JPMC-MUMBAI-004",
            verdict="NON_COMPLIANT",
            risk_score=7.5,
            violations=[
                {
                    "rule_id": "EU-ART19",
                    "statute": "Regulation (EU) 2024/1689 - Article 19(1)",
                    "severity": "high",
                    "trace_uri": "file:///D:/autogen/config/logging.py#L45",
                    "summary": "System logging configuration variable falls below the statutory 180-day minimum.",
                }
            ],
        )

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args

    assert result == {"status": "LOGGED", "transaction_id": "tx_9988776655"}

    # The body is sent as raw `content=` bytes, not `json=`.
    body = called_kwargs["content"].decode("utf-8")
    assert '"event_id":"evt_test_v6_sync"' in body.replace(" ", "")
    assert '"compliance_verdict":"NON_COMPLIANT"' in body.replace(" ", "")
    assert called_kwargs["headers"]["Content-Type"] == "application/json"
