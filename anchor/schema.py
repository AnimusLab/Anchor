import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class Violation:
    rule_id: str
    severity: str
    description: str
    file_path: str
    line_number: Optional[int]
    statute_ref: str 

@dataclass
class Cryptography:
    input_hash: str
    output_hash: str
    chain_hash: str
    signature: Optional[str] = None

@dataclass
class ExecutionContext:
    project_name: str
    git_commit: str
    environment: str

@dataclass
class GovernanceStatus:
    is_compliant: bool
    risk_level: str
    total_violations: int

@dataclass
class AuditEntry:
    # 1. NO DEFAULTS FIRST
    execution_context: ExecutionContext
    cryptography: Cryptography
    governance_status: GovernanceStatus
    violations: List[Violation]
    
    # 2. DEFAULTS LAST
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        """Serializes the contract into the exact JSON format required by FORGE, BYODB, and the Web UI."""
        return json.dumps(asdict(self), indent=2)

    def to_llm_text(self) -> str:
        """Hyper-dense format designed to consume minimal LLM tokens while preserving cryptographic state."""
        # Truncating hashes to 16 chars for LLM context to save tokens
        lines = [
            f"ID:{self.entry_id}|T:{self.timestamp}",
            f"CTX:{self.execution_context.project_name}@{self.execution_context.git_commit[:7]}",
            f"CRYPTO:IN={self.cryptography.input_hash[:16]}|OUT={self.cryptography.output_hash[:16]}|CHAIN={self.cryptography.chain_hash[:16]}",
            f"STATUS:{'CLEAN' if self.governance_status.is_compliant else 'VIOLATION'}|RISK:{self.governance_status.risk_level}",
        ]
        for v in self.violations:
            lines.append(f"ERR[{v.rule_id}]:{v.file_path}:{v.line_number}->{v.description}")
        
        return "\n".join(lines)