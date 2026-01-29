import yaml
import os
from typing import Dict, Any


class AnchorConfig:
    def __init__(self):
        self.rules = {}
        self.ignores = []
        self.meta = {}
        self.loaded_files = []

    def load_from_file(self, path: str = ".anchor"):
        """
        Loads a config file and resolves inheritance (Recursively).
        This enables the 'Layered Policy' architecture.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"No configuration found at {path}")

        print(f"[DEBUG] Loading config layer: {path}")
        self.loaded_files.append(path)

        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}

        # 1. Handle Inheritance (The "Layered" Logic)
        # We load the parent FIRST, so the child (current file) can override it.
        if "extends" in data:
            for parent_path in data["extends"]:
                self._resolve_parent(parent_path)

        # 2. Merge Local Definitions (The Child overrides the Parent)
        self._merge_data(data)

    def _resolve_parent(self, path: str):
        """Fetches parent config from Local Path."""
        # Handle relative paths for local secrets (e.g., ./internal/secrets.anchor)
        if not os.path.isabs(path):
            path = os.path.abspath(path)

        if os.path.exists(path):
            # Recursively load the parent into THIS instance
            self.load_from_file(path)
        else:
            print(f"[WARN] Parent config not found: {path}")

    def _merge_data(self, data: Dict[str, Any]):
        """Overwrites local rules onto the accumulated config."""
        if "rules" in data:
            # Update dictionary (Child wins conflicts)
            self.rules.update(data["rules"])

        if "ignore" in data:
            # Extend list (Accumulate ignores)
            self.ignores.extend(data["ignore"])

        if "meta" in data:
            self.meta.update(data["meta"])

    def get_effective_policy(self):
        """Returns the final Flattened Policy for the engine."""
        return {
            "meta": self.meta,
            "active_rules": {k: v for k, v in self.rules.items() if v != "off"},
            "ignores": self.ignores,
            "sources": self.loaded_files
        }


# --- Quick Test ---
if __name__ == "__main__":
    # 1. Create a dummy parent (Global Policy)
    with open("global.anchor", "w") as f:
        f.write('rules:\n  RI-24: "error"\n  AI-20: "error"')

    # 2. Create a dummy child (Project Policy)
    with open(".anchor", "w") as f:
        f.write('extends:\n  - "global.anchor"\nrules:\n  RI-24: "warn"')

    # 3. Load and Verify
    try:
        config = AnchorConfig()
        config.load_from_file(".anchor")
        policy = config.get_effective_policy()

        print("\n--- Effective Policy ---")
        # Should show RI-24 as 'warn'
        print(f"Rules: {policy['active_rules']}")
        print("------------------------\n")

    finally:
        if os.path.exists("global.anchor"):
            os.remove("global.anchor")
        if os.path.exists(".anchor"):
            os.remove(".anchor")
