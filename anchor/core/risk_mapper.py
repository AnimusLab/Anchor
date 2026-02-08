"""
Risk ID to Tree-Sitter Rule Mapper

This module bridges GenAI-identified risks (e.g., RI-24) to executable AST enforcement rules.

ARCHITECTURE (Constitution + State Law Model):
- finos-master.anchor = Federal Constitution (universal FINOS rules)
- policy.anchor = State Law (company-specific rules)
- Merges both, with policy.anchor overriding finos-master.anchor by ID
"""

from typing import Dict, List, Any, Optional
import yaml
import os


class RiskMapper:
    """
    Maps FINOS Risk IDs to tree-sitter enforcement rules.
    
    ARCHITECTURE:
    - Loads from finos-master.anchor (Constitution)
    - Loads from policy.anchor (State Law)
    - Merges: State law overrides Constitution by rule ID
    - Filters by Risk IDs from GenAI threat model
    """
    
    def __init__(self, 
                 master_policy_path: str = "finos-master.anchor",
                 local_policy_path: str = "policy.anchor",
                 verbose: bool = False):
        self.master_policy_path = master_policy_path
        self.local_policy_path = local_policy_path
        self.verbose = verbose
        self.all_rules = self._load_federated_policies()
    
    def _load_federated_policies(self) -> List[Dict[str, Any]]:
        """
        Load and merge rules from both Constitution and State Law.
        
        Merge Strategy:
        1. Load finos-master.anchor (Constitution)
        2. Load policy.anchor (State Law)
        3. Merge: Local rules override master rules by ID
        """
        # 1. Load Constitution (Federal Law)
        master_rules = []
        if os.path.exists(self.master_policy_path):
            try:
                with open(self.master_policy_path, 'r', encoding='utf-8') as f:
                    master_policy = yaml.safe_load(f) or {}
                    master_rules = master_policy.get('rules', [])
                    if self.verbose:
                        print(f"✅ Loaded {len(master_rules)} rules from FINOS Constitution")
            except Exception as e:
                if self.verbose:
                    print(f"❌ Failed to load master policy: {e}")
        else:
            if self.verbose:
                print(f"⚠️  Constitution not found at {self.master_policy_path}")
                print(f"   Run 'anchor init' to download FINOS master policy.")
        
        # 2. Load State Law (Company-Specific)
        local_rules = []
        if os.path.exists(self.local_policy_path):
            try:
                with open(self.local_policy_path, 'r', encoding='utf-8') as f:
                    local_policy = yaml.safe_load(f) or {}
                    local_rules = local_policy.get('rules', [])
                    if self.verbose:
                        print(f"✅ Loaded {len(local_rules)} rules from Company Policy")
            except Exception as e:
                if self.verbose:
                    print(f"❌ Failed to load local policy: {e}")
        else:
            if self.verbose:
                print(f"ℹ️  No local policy found at {self.local_policy_path}")
        
        # 3. Merge (State Law overrides Constitution)
        merged_rules = self._merge_rules(master_rules, local_rules)
        if self.verbose:
            print(f"📋 Total federated rules: {len(merged_rules)}")
        
        return merged_rules
    
    def _merge_rules(self, master: List[Dict], local: List[Dict]) -> List[Dict]:
        """
        Merge rules with local overriding master by ID.
        
        Example:
        - Master has: {id: "RI-24", severity: "blocker"}
        - Local has:  {id: "RI-24", severity: "warning"}
        - Result:     {id: "RI-24", severity: "warning"} ← Local wins
        """
        # Create map of master rules by ID
        rule_map = {r['id']: r for r in master}
        
        # Override with local rules
        for local_rule in local:
            rule_id = local_rule['id']
            if rule_id in rule_map:
                if self.verbose:
                    print(f"🔧 Company override: {rule_id}")
            rule_map[rule_id] = local_rule
        
        return list(rule_map.values())
    
    def get_rules_for_risks(self, risk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Filter federated rules by Risk IDs from GenAI threat model.
        
        Args:
            risk_ids: List of risk identifiers (e.g., ['RI-24', 'AI-20', 'BANK-001'])
        
        Returns:
            List of rule dictionaries (from both Constitution and State Law)
        """
        filtered_rules = []
        
        for risk_id in risk_ids:
            # Search in merged rules (Constitution + State Law)
            matching_rule = next((r for r in self.all_rules if r.get('id') == risk_id), None)
            
            if matching_rule:
                filtered_rules.append(matching_rule)
                source = "Company Policy" if risk_id.startswith("BANK-") or risk_id.startswith("PROJECT-") else "FINOS Constitution"
                if self.verbose:
                    print(f"✅ Activated {risk_id} from {source}")
            else:
                if self.verbose:
                    print(f"⚠️  Risk {risk_id} not found in federated policies. Skipping.")
        
        return filtered_rules


# Example usage for testing
if __name__ == "__main__":
    mapper = RiskMapper()
    
    # Simulate markdown parser output (mix of FINOS and company risks)
    detected_risks = ['RI-24', 'AI-20', 'PROJECT-001', 'FINOS-001']
    
    # Filter rules from both Constitution and State Law
    rules = mapper.get_rules_for_risks(detected_risks)
    
    print(f"\n📋 Filtered {len(rules)} enforcement rules:")
    for rule in rules:
        print(f"   - {rule['id']}: {rule.get('name', 'Unknown')}")
