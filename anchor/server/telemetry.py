"""
Anchor Telemetry Egress Server — Real-time WebSockets & SSE Broadcaster
Streams live violation packets & DAC audit entries to hub.animuslab.dev/hub/telemetry
"""

import json
import asyncio
import os
from typing import Dict, Any, Set, Optional

try:
    from fastapi import WebSocket, WebSocketDisconnect
except ImportError as exc:  # pragma: no cover - depends on install extras
    raise ImportError(
        "anchor.server.telemetry requires the optional 'server' dependencies.\n"
        "Install server support with: pip install anchor-audit[server]\n"
        f"(original import error: {exc})"
    ) from exc


class TelemetryBroadcaster:
    def __init__(self, required_token: Optional[str] = None):
        self.active_connections: Set[WebSocket] = set()
        self.required_token = required_token or os.environ.get("ANCHOR_TELEMETRY_TOKEN")

    def _origin_allowed(self, origin: Optional[str]) -> bool:
        if not origin:
            return True
        allowed = {
            "https://hub.animuslab.dev",
            "https://animuslab.dev",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
        }
        return origin.rstrip("/") in allowed or origin.endswith(".animuslab.dev")

    def _extract_bearer_token(self, websocket: WebSocket) -> Optional[str]:
        auth = websocket.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            return auth.split(None, 1)[1].strip()
        token = websocket.query_params.get("token")
        if token:
            return token.strip()
        return None

    async def connect(self, websocket: WebSocket):
        origin = websocket.headers.get("origin")
        if not self._origin_allowed(origin):
            await websocket.close(code=1008)
            return

        token = self._extract_bearer_token(websocket)
        if self.required_token is None:
            # Safe default: no external telemetry websocket is allowed without a
            # configured shared secret. Operators can set ANCHOR_TELEMETRY_TOKEN to
            # explicitly enable a local or trusted external hub connection.
            await websocket.close(code=1008)
            return

        if not token or token != self.required_token:
            await websocket.close(code=1008)
            return

        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_violation(self, audit_report: Dict[str, Any], payload_snippet: str = ""):
        """
        Broadcasts live violation telemetry payload across authorized clients only.
        Payload snippets are redacted to the minimum necessary and must never
        include tenant prompts, secrets, or raw code.
        """
        if not self.active_connections:
            return

        packet = {
            "type": "VIOLATION_EVENT",
            "timestamp_utc": asyncio.get_event_loop().time(),
            "rule_version": audit_report.get("rule_version"),
            "risk_score": audit_report.get("risk_score"),
            "risk_level": audit_report.get("risk_level"),
            "violations": audit_report.get("violations", []),
            "execution_microsec": audit_report.get("execution_microsec"),
            "payload_snippet": (payload_snippet[:80] if payload_snippet else "")
        }

        message = json.dumps(packet)
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Global Telemetry Bus instance. Operators must set ANCHOR_TELEMETRY_TOKEN to enable
# external websocket access; otherwise the gateway refuses all telemetry clients.
telemetry_bus = TelemetryBroadcaster()
