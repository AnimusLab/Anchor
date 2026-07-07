import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from anchor.governance.event import GovernanceEvent, Actor, PolicyBinding
from anchor.governance.policy import PolicyRegistry
from anchor.governance.keys import GovernanceKeyManager

class GovernanceEmitter:
    """
    Creates, signs, and commits governance events to the append-only JSONL logs.
    """
    
    def __init__(self, log_path: str = "therapy_logs/governance_events.jsonl"):
        self.policy_registry = PolicyRegistry()
        self.key_manager = GovernanceKeyManager()
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Automatically load private key if it exists (e.g. from PEM file)
        self.key_manager.unlock()

    def emit(
        self,
        event_type: str,
        actor: Actor,
        details: Dict[str, Any],
        checkpoint_id: str,
        password: Optional[str] = None
    ) -> GovernanceEvent:
        """
        Creates a new governance event, binds it to the current policy state,
        optionally signs it, and appends it to the therapy logs.
        """
        if password and not self.key_manager.private_key:
            self.key_manager.unlock(password)

        policy_binding = self.policy_registry.get_current_binding()

        event = GovernanceEvent.create(
            event_type=event_type,
            actor=actor,
            policy_binding=policy_binding,
            details=details,
            checkpoint_id=checkpoint_id
        )

        if self.key_manager.private_key:
            event.sign(self.key_manager.private_key)

        self._append_to_log(event)
        return event

    def _append_to_log(self, event: GovernanceEvent) -> None:
        """
        Appends the serialized event to the append-only JSONL log.
        """
        # Serialize fields using custom serialization
        import dataclasses
        event_dict = dataclasses.asdict(event)
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event_dict
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_events_for_checkpoint(self, checkpoint_id: str) -> List[GovernanceEvent]:
        """
        Returns all events associated with a given checkpoint.
        """
        events = []
        if not self.log_path.exists():
            return events
            
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    event_data = data.get("event")
                    if event_data and event_data.get("checkpoint_id") == checkpoint_id:
                        # Construct Actor and PolicyBinding objects
                        act_data = event_data["actor"]
                        actor = Actor(
                            id=act_data["id"],
                            principal=act_data["principal"],
                            roles=act_data["roles"],
                            session_id=act_data.get("session_id"),
                            auth_source=act_data.get("auth_source", "unknown")
                        )
                        bind_data = event_data["policy_binding"]
                        policy_binding = PolicyBinding(
                            policy_version=bind_data["policy_version"],
                            policy_hash=bind_data["policy_hash"],
                            authority_url=bind_data.get("authority_url")
                        )
                        event = GovernanceEvent(
                            event_id=event_data["event_id"],
                            timestamp=event_data["timestamp"],
                            checkpoint_id=event_data["checkpoint_id"],
                            event_type=event_data["event_type"],
                            actor=actor,
                            policy_binding=policy_binding,
                            details=event_data["details"],
                            signature=event_data.get("signature")
                        )
                        events.append(event)
                except Exception:
                    continue
        return events
