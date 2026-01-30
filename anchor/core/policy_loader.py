import yaml
import requests
import os
import sys
from typing import Dict, Any, List, Optional


class PolicyLoader:
    def __init__(self, local_policy_path: str):
        self.local_policy_path = local_policy_path

    def load_policy(self) -> Dict[str, Any]:
        """
        Main entry point.
        1. Loads the local .anchor file.
        2. Checks if it extends a remote master .anchor file.
        3. Merges them (local overrides Master).
        """
        # 1. Load local
        print(f" 📄 Loading local policy: {self.local_policy_path}")
        local_config = self._read_anchor_file(self.local_policy_path)

        # 2. Check for Inheritence
        parent_config = {}
        if "extends" in local_config:
            parent_url = local_config["extends"]
            print(f"🔗 Inheriting from Master Policy: {parent_url}")
            parent_config = self._fetch_remote_policy(parent_url)

        # 3. Merge
        final_policy = self._merge_policies(parent_config, local_config)
        return final_policy

    def _read_anchor_file(self, path: str) -> Dict[str, Any]:
        """Reads a local .anchor file and parses it as YAML."""
        if not os.path.exists(path):
            print(f"❌ Error: Policy file not found at {path}")
            sys.exit(1)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                # We treat .anchor files exactly like YAML
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error parsing {path}: {e}")
            sys.exit(1)

    def _fetch_remote_policy(self, url: str) -> Dict[str, Any]:
        """Fetches a remote .anchor file (e.g., from Github Raw)."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return yaml.safe_load(response.text) or {}
        except Exception as e:
            print(f"⚠️   Warning: Cloud not fetch Master Policy from {url}.")
            print(f"    Continuing with LOCAL policy only. Error: {e}")
            return {}

    def _merge_policies(self, parent: Dict, local: Dict) -> Dict:
        """
        Deep merges the policies.
        Strategy:
        1. Rules are merged by ID (local overwrites Parent).
        2. 'Context' and global settings are taken from local if preent.
        """
        merged = parent.copy()

        # Merge Meta-data
        if "version" in local:
            merged["version"] = local["version"]

        # Merge Rules
        parent_rules = merged.get("rules", [])
        local_rules = local.get("rules", [])

        # Map parent rules by ID for easy lookup
        rule_map = {r["id"]: r for r in parent_rules}

        # Apply local Rules (Add new ones OR Overwrite exisiting ones)
        for rule in local_rules:
            r_id = rule["id"]
            if r_id in rule_map:
                # If specifically requested, we cloud implement partial update here.
                # For now, we do full replacement of the rule definition.
                print(f"🔧  Local Override applied for rule: {r_id}")
            rule_map[r_id] = rule

        merged["rules"] = list(rule_map.values())
        return merged
