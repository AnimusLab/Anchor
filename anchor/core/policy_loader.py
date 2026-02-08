import yaml
import urllib.request
import os
import sys
from typing import Dict, Any, List, Optional


class PolicyLoader:
    def __init__(self, local_policy_path: str, verbose: bool = False):
        self.local_policy_path = local_policy_path
        self.verbose = verbose

    def load_policy(self) -> Dict[str, Any]:
        """
        Main entry point.
        1. Loads the local .anchor file.
        2. Checks if it extends a remote master .anchor file.
        3. Merges them (local overrides Master).
        """
        # 1. Load local
        if self.verbose:
            print(f" 📄 Loading local policy: {self.local_policy_path}")
        local_config = self._read_anchor_file(self.local_policy_path)

        # 2. Check for Inheritence
        parent_config = {}
        if "extends" in local_config:
            parent_url = local_config["extends"]
            if self.verbose:
                print(f"🔗 Inheriting from Master Policy: {parent_url}")
            parent_config = self._fetch_remote_policy(parent_url)

        # 3. Merge
        final_policy = self._merge_policies(parent_config, local_config)
        return final_policy

    def _read_anchor_file(self, path: str) -> Dict[str, Any]:
        """Reads a local .anchor file and parses it as YAML."""
        if not os.path.exists(path):
            if self.verbose:
                print(f"❌ Error: Policy file not found at {path}")
            return {} # Don't exit here, let caller handle

        try:
            with open(path, 'r', encoding='utf-8') as f:
                # We treat .anchor files exactly like YAML
                return yaml.safe_load(f) or {}
        except Exception as e:
            if self.verbose:
                print(f"❌ Error parsing {path}: {e}")
            return {}

    def _fetch_remote_policy(self, url: str) -> Dict[str, Any]:
        """Fetches a remote .anchor file (e.g., from Github Raw) using urllib."""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
                return yaml.safe_load(content) or {}
                return yaml.safe_load(content) or {}
        except Exception as e:
            if self.verbose:
                print(f"⚠️   Warning: Could not fetch Master Policy from {url}.")
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
        parent_rules = merged.get("rules") or []
        local_rules = local.get("rules") or []

        # Map parent rules by ID for easy lookup
        # Ensure 'r' is a dict and has an 'id'
        rule_map = {r["id"]: r for r in parent_rules if isinstance(r, dict) and "id" in r}

        # Apply local Rules (Add new ones OR Overwrite exisiting ones)
        for rule in local_rules:
            if not isinstance(rule, dict) or "id" not in rule:
                continue
            r_id = rule["id"]
            if r_id in rule_map:
                if verbose := os.environ.get("ANCHOR_VERBOSE"):
                    print(f"🔧  Local Override applied for rule: {r_id}")
            rule_map[r_id] = rule

        merged["rules"] = list(rule_map.values())
        return merged
