import os
import hashlib
from typing import Optional
from anchor.governance.event import PolicyBinding

class PolicyRegistry:
    def __init__(self, constitution_path: Optional[str] = None):
        if constitution_path is None:
            # Search for constitution.anchor
            # Check local .anchor/constitution.anchor first, then default package one
            if os.path.exists(".anchor/constitution.anchor"):
                self.constitution_path = ".anchor/constitution.anchor"
            elif os.path.exists("anchor/governance/constitution.anchor"):
                self.constitution_path = "anchor/governance/constitution.anchor"
            else:
                self.constitution_path = "constitution.anchor"
        else:
            self.constitution_path = constitution_path

    def get_current_binding(self) -> PolicyBinding:
        if not os.path.exists(self.constitution_path):
            # Fallback policy hash (SHA-256 of empty string/dummy)
            fallback_content = "fallback-policy-content"
            fallback_hash = hashlib.sha256(fallback_content.encode("utf-8")).hexdigest()
            return PolicyBinding(policy_version="v1.0.0", policy_hash=fallback_hash)
        
        try:
            with open(self.constitution_path, "r", encoding="utf-8") as f:
                content = f.read()
            policy_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            
            # Simple check for version in the content if YAML-like
            version = "v1.0.0"
            if "version:" in content:
                for line in content.splitlines():
                    if line.strip().startswith("version:"):
                        version = line.split(":", 1)[1].strip().strip("\"'")
                        break
            return PolicyBinding(policy_version=version, policy_hash=policy_hash)
        except Exception:
            fallback_content = "fallback-policy-content"
            fallback_hash = hashlib.sha256(fallback_content.encode("utf-8")).hexdigest()
            return PolicyBinding(policy_version="v1.0.0", policy_hash=fallback_hash)

    def verify_hash(self, policy_hash: str) -> bool:
        current = self.get_current_binding()
        return current.policy_hash == policy_hash
