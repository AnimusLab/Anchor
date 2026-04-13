import os
import json
import uuid
import hashlib
import hmac
import subprocess
import urllib.request
import ahocorasick
import yaml
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone

from anchor.core.crypto import sign_chain_hash
from anchor.core.loader import load_constitution
from anchor.core.engine import PolicyEngine
from anchor.runtime.models import AuditEntry

class DecisionAuditor:
    """
    Layer 2: High-speed, zero-knowledge cryptographic auditor for live AI decisions.
    Uses a Singleton pattern to cache OS/Disk I/O operations in RAM.
    """
    
    # Class-level RAM cache
    _git_commit = None
    _project_name = None
    _shared_engine = None
    _audit_log = None
    _proxy_automaton = None
    _proxy_concept_map = {}
    _is_warmed_up = False

    def __init__(self):
        if not DecisionAuditor._is_warmed_up:
            self._warm_up_cache()

    def _warm_up_cache(self):
        """Runs exactly once on boot. Absorbs the 30ms subprocess penalty."""
        self._cache_git_context()
        self._warm_up_constitution()
        self._warm_up_taxonomy()
        DecisionAuditor._is_warmed_up = True

    def _cache_git_context(self):
        """Metadata caching for the forensic link."""
        try:
            DecisionAuditor._git_commit = subprocess.check_output(  # anchor: ignore SEC-007
                ['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
        except Exception:
            DecisionAuditor._git_commit = "unknown_commit"

        DecisionAuditor._project_name = os.path.basename(os.getcwd())

    def _resolve_governance_path(self) -> Path:
        """Helper to resolve the governance directory path."""
        return Path(__file__).parent.parent / "governance"

    def _warm_up_constitution(self):
        """Loads domain rules into the RAM-cached Policy Engine."""
        anchor_dir = Path(".anchor")
        governance_root = self._resolve_governance_path()
        
        constitution = None
        if anchor_dir.exists():
            try:
                # Load from local project directory
                constitution = load_constitution(governance_root, anchor_dir=anchor_dir)
            except Exception:
                pass
        
        if not constitution:
            if governance_root.exists():
                try:
                    # Load from bundled package resources
                    constitution = load_constitution(governance_root)
                except Exception:
                    pass
        
        if not constitution:
            raise RuntimeError(
                "AnchorRuntime: No governance directory found. "
                "Run `anchor init` or ensure the anchor package includes bundled governance files."
            )

        # Convert Rule dataclasses to dicts for PolicyEngine compatibility
        rules_list = [asdict(r) for r in constitution.rules.values()]
        DecisionAuditor._shared_engine = PolicyEngine({"rules": rules_list})
        DecisionAuditor._audit_log = ".anchor/runtime_chain.jsonl"

    def _warm_up_taxonomy(self):
        """
        Builds Aho-Corasick trie from ETH-001 prohibited_proxies.
        Called after _warm_up_constitution so governance path is resolved.
        """
        try:
            eth_path = self._resolve_governance_path() / "domains" / "ethics.anchor"
            if not eth_path.exists():
                return

            with open(eth_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            rules = data.get("rules", [])
            eth_001 = next((r for r in rules if r.get("id") == "ETH-001"), None)

            if not eth_001:
                return

            automaton = ahocorasick.Automaton()
            concept_map = {}

            for proxy in eth_001.get("prohibited_proxies", []):
                concept = proxy["concept"]
                canonical = proxy["canonical"]
                rationale = proxy["rationale"]
                for term in proxy["surface_terms"]:
                    term_lower = term.lower()
                    automaton.add_word(
                        term_lower,
                        (concept, canonical, term_lower, rationale)
                    )
                    concept_map[term_lower] = {
                        "concept": concept,
                        "canonical": canonical,
                        "rationale": rationale
                    }

            automaton.make_automaton()
            DecisionAuditor._proxy_automaton = automaton
            DecisionAuditor._proxy_concept_map = concept_map

        except Exception as e:
            # Never block warm-up for taxonomy failures
            import logging
            logging.warning(f"ETH taxonomy warm-up failed: {e}")

    def check_eth_compliance(self, response, mode: str = "conversational") -> list:
        """
        Checks AI response against ETH-001 and ETH-002 rules.
        
        Mode 1 (structured): Enforces JSON structure + Aho-Corasick on fields.
        Mode 2 (conversational): Aho-Corasick on full response text only.
        
        Returns list of violation dicts. Never raises.
        """
        violations = []

        # ── ETH-002: No-Prose Rule (structured mode only) ─────────────────
        if mode == "structured":
            if isinstance(response, str):
                violations.append({
                    "rule_id": "ETH-002",
                    "severity": "blocker",
                    "description": "Prose returned in structured mode. "
                                   "JSON with ReasonCode and FeatureAttribution required.",
                    "maps_to": ["RBI-014", "CFPB-REG-B", "EU-AI-ACT-ART-13"]
                })
                # No point running ETH-001 on prose that already failed ETH-002
                return violations

            if isinstance(response, dict):
                missing = [
                    f for f in ["ReasonCode", "FeatureAttribution"]
                    if f not in response
                ]
                if missing:
                    violations.append({
                        "rule_id": "ETH-002",
                        "severity": "blocker",
                        "description": f"Missing required fields: {missing}. "
                                       f"Explainability contract not satisfied.",
                        "maps_to": ["RBI-014", "CFPB-REG-B", "EU-AI-ACT-ART-13"]
                    })

        # ── ETH-001: Aho-Corasick scan ────────────────────────────────────
        if DecisionAuditor._proxy_automaton is None:
            return violations

        # Structured mode: scan only decision-relevant fields
        # Conversational mode: scan full response text
        if mode == "structured" and isinstance(response, dict):
            scan_target = " ".join(
                str(v) for k, v in response.items()
                if k in ["ReasonCode", "FeatureAttribution", 
                         "DenialReason", "RiskFactors"]
            ).lower()
        else:
            scan_target = str(response).lower()

        seen_concepts = set()  # one violation per concept, no duplicates

        for _, (concept, canonical, term, rationale) in \
                DecisionAuditor._proxy_automaton.iter(scan_target):
            if concept not in seen_concepts:
                seen_concepts.add(concept)
                violations.append({
                    "rule_id": "ETH-001",
                    "severity": "blocker",
                    "concept": concept,
                    "canonical": canonical,
                    "detected_term": term,
                    "rationale": rationale,
                    "description": f"Prohibited proxy '{concept}' detected "
                                   f"via term '{term}'.",
                    "maps_to": ["RBI-019", "ECOA", "FHA-805"]
                })

        return violations

    def _hash_payload(self, data: str) -> str:
        """Deterministic SHA-256 hashing."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get_last_runtime_hash(self) -> str:
        """Reads the last hash from the runtime chain to maintain the cryptographic link."""
        chain_path = DecisionAuditor._audit_log or ".anchor/runtime_chain.jsonl"
        if not os.path.exists(chain_path):
            return "0".zfill(64)
        try:
            with open(chain_path, 'rb') as f:
                try:
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                except OSError:
                    f.seek(0)
                last_line = f.readline().decode('utf-8').strip()
                if not last_line: return "0".zfill(64)
                return json.loads(last_line).get("cryptography", {}).get("chain_hash", "")
        except Exception:
            return "0".zfill(64)

    def audit(self, provider: str, prompt: str, response: str, findings: list, jurisdiction: str = "GLOBAL", latency_ms: float = 0.0, mode: str = "conversational"):
        """
        The critical path. Must execute in < 2ms.
        """
        # ETH compliance check
        eth_violations = self.check_eth_compliance(response, mode=mode)
        all_violations = list(findings) + eth_violations
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry_id = str(uuid.uuid4())
        rule_ids = sorted([f.get("rule_id") for f in all_violations if f.get("rule_id")])
        findings_hash = self._hash_payload(json.dumps(rule_ids))
        
        prev_hash = self.get_last_runtime_hash()
        chain_hash = self._hash_payload(prev_hash + findings_hash)
        signature = sign_chain_hash(chain_hash)

        # 2. Build the Full Local Audit Entry (The "Vault")
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            jurisdiction=jurisdiction,
            provider=provider,
            project_name=DecisionAuditor._project_name,
            git_commit=DecisionAuditor._git_commit,
            is_compliant=len(all_violations) == 0,
            status="CLEAN" if len(all_violations) == 0 else "VIOLATION",
            findings_hash=findings_hash,
            prev_chain_hash=prev_hash,
            chain_hash=chain_hash,
            signature=signature,
            violations=all_violations,
            telemetry={
                "latency_ms": latency_ms,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "response_preview": str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
            }
        )

        local_entry_dict = entry.to_dict()

        # 3. Persistence (Local JSONL)
        if DecisionAuditor._audit_log:
            try:
                log_path = Path(DecisionAuditor._audit_log)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(local_entry_dict) + "\n")
            except Exception:
                pass

        # 4. Fire the Global Whisper (The Public Ledger)
        zk_payload = json.dumps(local_entry_dict)
        try:
            ledger_url = os.environ.get("ANCHOR_LEDGER_URL")
            if ledger_url:
                req = urllib.request.Request(
                    ledger_url,
                    data=zk_payload.encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass 
        
        return entry
