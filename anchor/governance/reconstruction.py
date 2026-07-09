from typing import List, Dict, Any, Optional
from anchor.governance.emitter import GovernanceEmitter
from cryptography.hazmat.primitives.asymmetric import ed25519

class DecisionReconstructor:
    """
    Validates and reconstructs historical decisions for auditors.
    """
    
    def __init__(self, log_path: str = "therapy_logs/governance_events.jsonl"):
        self.emitter = GovernanceEmitter(log_path=log_path)

    def get_decision_history(self, checkpoint_id: str) -> List[Dict[str, Any]]:
        events = self.emitter.get_events_for_checkpoint(checkpoint_id)
        # Convert events back to dict for API/CLI consumption
        import dataclasses
        return [dataclasses.asdict(event) for event in events]

    def verify_decision(
        self,
        checkpoint_id: str,
        policy_hash: str,
        public_key: Optional[ed25519.Ed25519PublicKey] = None
    ) -> Dict[str, Any]:
        """
        Cryptographically verifies the authenticity and policy binding of the decision path.
        """
        events = self.emitter.get_events_for_checkpoint(checkpoint_id)
        if not events:
            return {"valid": False, "reason": "No events found for checkpoint"}

        # Verify signatures if public key is provided
        if public_key:
            for event in events:
                if not event.signature:
                    return {"valid": False, "reason": f"Event {event.event_id} is missing a signature"}
                if not event.verify(public_key):
                    return {"valid": False, "reason": f"Signature verification failed on event {event.event_id}"}

        # Verify policy hash binding matches expected
        for event in events:
            if event.policy_binding.policy_hash != policy_hash:
                return {
                    "valid": False,
                    "reason": "Policy hash mismatch",
                    "expected": policy_hash,
                    "actual": event.policy_binding.policy_hash
                }

        return {
            "valid": True,
            "event_count": len(events),
            "final_event_type": events[-1].event_type if events else None
        }
