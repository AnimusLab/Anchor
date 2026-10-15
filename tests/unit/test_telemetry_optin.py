from unittest.mock import patch

from anchor.core.telemetry import SpokeTelemetryClient

ARGS = dict(event_id="e", project_name="p", silo_id="s", verdict="COMPLIANT", risk_score=0.0, violations=[])


def test_disabled_by_default_makes_no_network_call(monkeypatch):
    monkeypatch.delenv("ANCHOR_TELEMETRY", raising=False)
    with patch("httpx.Client.post") as post, patch("urllib.request.urlopen") as uo:
        assert SpokeTelemetryClient().dispatch_state_event(**ARGS) is None
        post.assert_not_called(); uo.assert_not_called()


def test_enabled_via_env(monkeypatch):
    monkeypatch.setenv("ANCHOR_TELEMETRY", "on")
    with patch("httpx.Client.post") as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"status": "LOGGED", "transaction_id": "tx1"}
        res = SpokeTelemetryClient(hub_url="https://example.invalid").dispatch_state_event(**ARGS)
        post.assert_called_once()
        assert res["transaction_id"] == "tx1"
