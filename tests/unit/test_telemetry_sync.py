import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from anchor.core.telemetry import SpokeTelemetryClient

def test_spoke_telemetry_transmission_success():
    """Verify the telemetry client correctly routes and dispatches payloads over the wire."""
    async def _run():
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "LOGGED", "transaction_id": "tx_9988776655"}

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            client = SpokeTelemetryClient(
                hub_url="https://animuslab.dev",
                identity_fingerprint="sha256:b49d424a21b4142ddb670bce34f798..."
            )

            client.dispatch_state_event(
                event_id="evt_test_v6_sync",
                project_name="payment-architecture-pipeline",
                silo_id="JPMC-MUMBAI-004",
                verdict="NON_COMPLIANT",
                risk_score=7.5,
                violations=[{
                    "rule_id": "EU-ART19",
                    "statute": "Regulation (EU) 2024/1689 - Article 19(1)",
                    "severity": "high",
                    "trace_uri": "file:///D:/autogen/config/logging.py#L45",
                    "summary": "System logging configuration variable falls below the statutory 180-day minimum."
                }]
            )

            await asyncio.sleep(0.1)

            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            assert called_kwargs["json"]["event_id"] == "evt_test_v6_sync"
            assert called_kwargs["json"]["compliance_verdict"] == "NON_COMPLIANT"

    asyncio.run(_run())

