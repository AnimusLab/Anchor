"""
Anchor Telemetry Egress Server — Real-time WebSockets & SSE Broadcaster
Streams live violation packets & DAC audit entries to hub.animuslab.dev/hub/telemetry
"""

import json
import asyncio
from typing import Dict, Any, List, Set
from fastapi import WebSocket, WebSocketDisconnect

class TelemetryBroadcaster:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_violation(self, audit_report: Dict[str, Any], payload_snippet: str = ""):
        """
        Broadcasts live violation telemetry payload across all connected web clients
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
            "payload_snippet": payload_snippet[:200]
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

# Global Telemetry Bus instance
telemetry_bus = TelemetryBroadcaster()
