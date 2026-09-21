import os
import sys
import json
import uuid
import asyncio
import logging
import hashlib
import urllib.request
import urllib.error

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logger = logging.getLogger("anchor.telemetry")

class SpokeTelemetryClient:
    def __init__(
        self,
        hub_url: Optional[str] = None,
        identity_fingerprint: Optional[str] = None,
        private_key_path: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initializes the federated spoke-to-hub network connection pool with cryptographic signing.
        """
        self.hub_url = (hub_url or os.environ.get("ANCHOR_HUB_URL", "http://localhost:3000")).rstrip("/")
        self.endpoint = f"{self.hub_url}/api/v1/telemetry/event"
        self.api_key = api_key or os.environ.get("ANCHOR_API_KEY")
        self.private_key = None
        self.identity_fingerprint = identity_fingerprint
        
        self._load_keys(private_key_path)

    def _load_keys(self, custom_path: Optional[str] = None) -> None:
        """Loads and resolves the local Ed25519 node identity keypair."""
        candidate_paths = [
            custom_path,
            os.environ.get("ANCHOR_PRIVATE_KEY_PATH"),
            Path(".anchor/keys/ed25519_private.pem"),
            Path.home() / ".anchor" / "keys" / "ed25519_private.pem"
        ]

        for p in candidate_paths:
            if p and Path(p).exists():
                try:
                    key_bytes = Path(p).read_bytes()
                    if HAS_CRYPTO:
                        if b"BEGIN PRIVATE KEY" in key_bytes or b"BEGIN OPENSSH PRIVATE KEY" in key_bytes:
                            self.private_key = serialization.load_pem_private_key(key_bytes, password=None)
                        elif len(key_bytes) == 32:
                            self.private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
                        
                        if self.private_key and not self.identity_fingerprint:
                            pub_bytes = self.private_key.public_key().public_bytes(
                                encoding=serialization.Encoding.PEM,
                                format=serialization.PublicFormat.SubjectPublicKeyInfo
                            )
                            self.identity_fingerprint = "sha256:" + hashlib.sha256(pub_bytes).hexdigest()
                    break
                except Exception as e:
                    logger.debug(f"Could not load key from {p}: {e}")

        if not self.identity_fingerprint:
            self.identity_fingerprint = "sha256:ed25519_node_sovereign_key"

    def sign_payload(self, raw_bytes: bytes) -> Optional[str]:
        """Signs the raw bytes using the local Ed25519 private key."""
        if HAS_CRYPTO and self.private_key:
            try:
                sig = self.private_key.sign(raw_bytes)
                return sig.hex()
            except Exception as e:
                logger.error(f"Failed to sign telemetry payload: {e}")
        return None

    def dispatch_state_event(
        self,
        event_id: str,
        project_name: str,
        silo_id: str,
        verdict: str,
        risk_score: float,
        violations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Dispatches and synchronously streams signed telemetry packet to the Governance Hub.
        """
        payload = {
            "event_id": event_id or f"evt_{uuid.uuid4().hex[:12]}",
            "silo_id": silo_id or "animuslab-hq",
            "project_name": project_name or "Enterprise AI Node",
            "identity_fingerprint": self.identity_fingerprint,
            "compliance_verdict": verdict,
            "risk_score": float(risk_score),
            "violations": violations
        }

        raw_json_str = json.dumps(payload, separators=(',', ':'))
        raw_bytes = raw_json_str.encode('utf-8')

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        sig_hex = self.sign_payload(raw_bytes)
        if sig_hex:
            headers["X-Anchor-Signature"] = sig_hex

        try:
            if HAS_HTTPX:
                with httpx.Client(timeout=4.0) as client:
                    res = client.post(self.endpoint, content=raw_bytes, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        logger.info(f"Telemetry packet committed to Hub. Tx ID: {data.get('transaction_id')}")
                        return data
                    else:
                        logger.warning(f"Hub telemetry transmission rejected ({res.status_code}): {res.text}")
                        return None
            else:
                req = urllib.request.Request(self.endpoint, data=raw_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=4.0) as res:
                    if res.status == 200:
                        data = json.loads(res.read().decode('utf-8'))
                        logger.info(f"Telemetry packet committed to Hub. Tx ID: {data.get('transaction_id')}")
                        return data
                    else:
                        logger.warning(f"Hub telemetry transmission returned status ({res.status})")
                        return None
        except Exception as ex:
            logger.debug(f"Telemetry transmission skipped (Hub unreachable): {ex}")
            return None
