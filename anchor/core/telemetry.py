import asyncio
import logging
import uuid
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger("anchor.telemetry")

class SpokeTelemetryClient:
    def __init__(self, hub_url: str = "http://localhost:3000", identity_fingerprint: Optional[str] = None):
        """
        Initializes the federated spoke-to-hub network connection pool.
        The hub_url defaults to http://localhost:3000 during local dev & testing, or hub.animuslab.dev in prod.
        """
        self.hub_url = hub_url.rstrip("/")
        self.endpoint = f"{self.hub_url}/api/v1/telemetry/event"
        self.identity_fingerprint = identity_fingerprint or "sha256:ed25519_node_sovereign_key"
        self.client = httpx.AsyncClient(timeout=3.0)

    async def _transmit_packet(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Internal worker executing the actual outbound network transmission."""
        try:
            response = await self.client.post(self.endpoint, json=payload)
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Telemetry packet committed successfully. Tx ID: {data.get('transaction_id')}")
                return data
            else:
                logger.error(f"Hub rejected transmission payload. Status Code: {response.status_code} | Details: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to stream metric boundaries to hub control plane: {str(e)}")
            return None

    def dispatch_state_event(
        self,
        event_id: str,
        project_name: str,
        silo_id: str,
        verdict: str,
        risk_score: float,
        violations: List[Dict[str, Any]]
    ) -> None:
        """
        Public execution boundary. Immediately drops the payload into the background
        asyncio loop queue, ensuring zero blocking overhead on the main application thread.
        """
        payload = {
            "event_id": event_id or f"evt_{uuid.uuid4().hex[:12]}",
            "silo_id": silo_id or "SOVEREIGN-NODE-001",
            "project_name": project_name or "anchor-core-pipeline",
            "identity_fingerprint": self.identity_fingerprint,
            "compliance_verdict": verdict,
            "risk_score": risk_score,
            "violations": violations
        }

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._transmit_packet(payload))
        except RuntimeError:
            # Fallback for synchronous or standalone scripting execution contexts
            try:
                asyncio.run(self._transmit_packet(payload))
            except Exception as ex:
                logger.error(f"Error running telemetry sync in sync context: {ex}")
