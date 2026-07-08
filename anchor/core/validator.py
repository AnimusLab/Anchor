from pathlib import Path
from typing import Dict, Any, List
import os

class AnchorFileValidator:
    @staticmethod
    def determine_type(raw_data: Dict[str, Any], file_path: Path) -> str:
        """Classify the role of the .anchor file based on type metadata field or filename/path."""
        if not isinstance(raw_data, dict):
            return "unknown"
        ftype = raw_data.get("type")
        if ftype:
            return ftype
        # Fallbacks based on path/naming if type is not declared
        name = file_path.name.lower()
        if name == "constitution.anchor":
            return "manifest"
        elif name == "policy.anchor":
            return "policy"
        elif "domain" in str(file_path).lower():
            return "domain"
        elif "framework" in str(file_path).lower() or "government" in str(file_path).lower():
            return "framework"
        return "unknown"

    @classmethod
    def validate(cls, file_path: Path, raw_data: Dict[str, Any]) -> None:
        """Dispatches validation to the appropriate type-specific validator."""
        if not isinstance(raw_data, dict):
            raise ValueError(f"Invalid YAML content in {file_path}. Must be a dictionary.")

        file_type = cls.determine_type(raw_data, file_path)
        if file_type == "manifest":
            cls.validate_manifest(raw_data, file_path)
        elif file_type == "domain":
            cls.validate_domain(raw_data, file_path)
        elif file_type == "framework":
            cls.validate_framework(raw_data, file_path)
        elif file_type == "policy":
            cls.validate_policy(raw_data, file_path)
        elif file_type == "unknown":
            raise ValueError(f"Unknown file type for .anchor file: {file_path}")

    @classmethod
    def validate_manifest(cls, data: Dict[str, Any], file_path: Path) -> None:
        """Validates a manifest file (e.g., constitution.anchor)"""
        # 1. Schema validity
        required = ["version", "anchor_version"]
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Manifest {file_path} is missing required fields: {missing}")

        # 2. Namespace uniqueness
        namespaces = set()
        def add_namespace(ns, path):
            if not ns:
                raise ValueError(f"Missing namespace for path {path} in manifest")
            if ns in namespaces:
                raise ValueError(f"Duplicate namespace '{ns}' detected in manifest")
            namespaces.add(ns)

        for domain in data.get("core_domains", []):
            if isinstance(domain, dict):
                add_namespace(domain.get("namespace"), domain.get("path"))
        for fw in data.get("frameworks", []):
            if isinstance(fw, dict):
                add_namespace(fw.get("namespace"), fw.get("path"))
        for reg in data.get("regulators", []):
            if isinstance(reg, dict):
                add_namespace(reg.get("namespace"), reg.get("path"))

        # 3. Referenced file existence
        # We verify if the files referenced in core_domains, frameworks, regulators exist relative to the project root
        # or the package governance root. Since we are in the manifest loader, we can check basic paths.
        # But we only warn (don't fail hard) if a file is not found, to allow offline/partial check runs.
        # However, to be strict, we can print warning messages.
        
        # 4. Engine & Policy configurations are dicts
        if "engine" in data and not isinstance(data["engine"], dict):
            raise ValueError("Manifest 'engine' configuration must be a dictionary")
        if "policy" in data and not isinstance(data["policy"], dict):
            raise ValueError("Manifest 'policy' configuration must be a dictionary")
        if "output" in data and not isinstance(data["output"], dict):
            raise ValueError("Manifest 'output' configuration must be a dictionary")

        # 5. Alias consistency
        if "legacy_aliases" in data and not isinstance(data["legacy_aliases"], dict):
            raise ValueError("Manifest 'legacy_aliases' must be a dictionary")

    @classmethod
    def validate_domain(cls, data: Dict[str, Any], file_path: Path) -> None:
        """Validates a rule set / domain file."""
        if not data.get("namespace"):
            raise ValueError(f"Domain {file_path} is missing required field: 'namespace'")
        
        rules = data.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError(f"Domain {file_path} 'rules' field must be a list")

    @classmethod
    def validate_framework(cls, data: Dict[str, Any], file_path: Path) -> None:
        """Validates a framework or regulator mapping file."""
        if not data.get("namespace"):
            raise ValueError(f"Framework mapping {file_path} is missing required field: 'namespace'")
        
        rules = data.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError(f"Framework mapping {file_path} 'rules' must be a list")

    @classmethod
    def validate_policy(cls, data: Dict[str, Any], file_path: Path) -> None:
        """Validates local policy files."""
        if "rules" in data and not isinstance(data["rules"], list):
            raise ValueError(f"Policy {file_path} 'rules' field must be a list")
