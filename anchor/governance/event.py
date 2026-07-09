import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

@dataclass
class Actor:
    id: str
    principal: str
    roles: List[str]
    session_id: Optional[str] = None
    auth_source: str = "unknown"

@dataclass
class PolicyBinding:
    policy_version: str
    policy_hash: str          # SHA-256 of the policy file at decision time
    authority_url: Optional[str] = None

@dataclass
class GovernanceEvent:
    event_id: str
    timestamp: str
    checkpoint_id: str
    event_type: str            # e.g., "TOOL_BLOCKED", "TOOL_EXECUTED", "HUMAN_APPROVAL", "INTERRUPT_RESUMED"
    actor: Actor
    policy_binding: PolicyBinding
    details: Dict[str, Any]
    signature: Optional[str] = None  # Hex-encoded signature

    @classmethod
    def create(
        cls,
        event_type: str,
        actor: Actor,
        policy_binding: PolicyBinding,
        details: Dict[str, Any],
        checkpoint_id: str
    ) -> "GovernanceEvent":
        return cls(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            checkpoint_id=checkpoint_id,
            event_type=event_type,
            actor=actor,
            policy_binding=policy_binding,
            details=details,
        )

    def canonical_json(self) -> str:
        """Deterministic canonical representation for signing."""
        data = asdict(self)
        data.pop("signature", None)  # Never sign the signature itself
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def sign(self, private_key: ed25519.Ed25519PrivateKey) -> None:
        """Sign the event with Ed25519."""
        payload = self.canonical_json().encode("utf-8")
        signature_bytes = private_key.sign(payload)
        self.signature = signature_bytes.hex()

    def verify(self, public_key: ed25519.Ed25519PublicKey) -> bool:
        """Verify the Ed25519 signature."""
        if not self.signature:
            return False
        try:
            payload = self.canonical_json().encode("utf-8")
            signature_bytes = bytes.fromhex(self.signature)
            public_key.verify(signature_bytes, payload)
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False
