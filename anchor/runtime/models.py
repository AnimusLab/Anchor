import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AuditEntry:
    """
    Universal Regulatory Translator: The "Truth Machine" of Anchor governance.
    Stored internally as a 5-Primitive record ($A, O, C, U, F$) and polymorphicized 
    through legal dialect factories for global compliance.
    """
    # The Universal 5 Primitives (The "Truth")
    action: str = "ai_decision"    # $A$ : e.g., 'deny_credit'
    object: str = "llm_output"     # $O$ : e.g., 'loan_application_v2'
    context: str = "global"        # $C$ : e.g., 'retail_banking_india'
    authority: str = "anchor"      # $U$ : e.g., 'credit_llm_v4'
    flow: str = "runtime_audit"    # $F$ : e.g., 'api_egress'
    
    # Metadata & Proofs
    entry_id: str = ""
    timestamp: str = ""
    project_name: str = ""
    git_commit: str = ""
    
    # Governance Status
    status: str = "CLEAN" # "CLEAN" or "VIOLATION"
    rule_id: Optional[str] = None
    
    # Cryptographic Chain
    findings_hash: str = ""
    chain_hash: str = ""
    signature: str = ""
    
    # Raw Data (Local Only)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Returns the internal 5-Primitive representation."""
        return {
            "schema_version": "4.3.5",
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "primitives": {
                "action": self.action,
                "object": self.object,
                "context": self.context,
                "authority": self.authority,
                "flow": self.flow
            },
            "governance_status": {
                "status": self.status,
                "rule_id": self.rule_id
            },
            "cryptography": {
                "chain_hash": self.chain_hash,
                "signature": self.signature
            },
            "telemetry": self.telemetry
        }

    def to_dialect(self, dialect_name: str) -> Dict[str, Any]:
        """The entry point for the Multi-Dialect Subscription model."""
        dialects = {
            "RBI": self.to_rbi_json,
            "SEC": self.to_sec_json,
            "EU": self.to_eu_article12_json
        }
        return dialects.get(dialect_name, self.to_dict)()

    def to_rbi_json(self) -> Dict[str, Any]:
        """Maps to RBI FREE-AI (2026) Pillar 2: The Seven Sutras."""
        sutra_map = {
            "ETH": "Fairness (Sutra 4) & Explainability (Sutra 7)",
            "SEC": "Cyber Resilience (Sutra 5)",
            "PRV": "Data Sovereignty (Sutra 3)",
            "GVR": "Governance & Accountability (Sutra 6)"
        }
        
        prefix = self.rule_id[:3] if self.rule_id else "GVR"
        primary_sutra = sutra_map.get(prefix, "Algorithmic Integrity (Sutra 1)")

        return {
            "regulatory_body": "RBI",
            "framework": "FREE-AI Pillar 2",
            "sutra_alignment": primary_sutra,
            "incident_metadata": {
                "branch_context": self.context,
                "timestamp": self.timestamp,
                "severity": "CRITICAL" if self.status == "VIOLATION" else "LOW"
            },
            "audit_proof": {
                "violation_id": self.rule_id,
                "technical_action": self.action,
                "affected_object": self.object,
                "authority_engine": self.authority
            },
            "chain_verification": self.chain_hash
        }

    def to_sec_json(self) -> Dict[str, Any]:
        """Maps to SEC Regulation S-K / Item 1.05: Materiality and Principles of Governance."""
        return {
            "regulator": "U.S. Securities and Exchange Commission",
            "disclosure_type": "8-K / Item 1.05 (Material AI Risk)",
            "materiality_signal": "HIGH" if self.status == "VIOLATION" else "LOW",
            "governance_event": {
                "category": "Algorithmic Risk Management",
                "description": f"Breach detected in {self.object} during operational flow {self.flow}.",
                "mitigation_status": "Effectively Mitigated via Anchor Interceptor",
                "verification_hash": f"sha256:{self.chain_hash[:16]}..."
            },
            "filer_context": {
                "project": self.project_name,
                "commit": self.git_commit
            }
        }

    def to_eu_article12_json(self) -> Dict[str, Any]:
        """Maps to EU AI Act Article 12.2: Automatic Recording of Events."""
        return {
            "article": "12.2 (Logging)",
            "system_id": f"Anchor-{self.project_name}",
            "event_log": {
                "period_of_use": self.timestamp,
                "event_type": self.action,
                "input_data_match": self.telemetry.get("prompt_preview", "N/A")[:50] + "...",
                "reference_database": "ANC-CONSTITUTION-v4.3",
                "human_in_loop_notified": f"Node_{self.authority}"
            },
            "conformity_declaration": "ISO/IEC 42001:2023 Compliant",
            "integrity_proof": self.signature
        }
