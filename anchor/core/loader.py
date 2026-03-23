# ─────────────────────────────────────────────────────────────
# V4 Constitution Loader
# Reads constitution.anchor and loads all domains and frameworks
# in the defined sequence. Validates seals, resolves aliases,
# applies policy overrides.
# ─────────────────────────────────────────────────────────────

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# ── DATA CLASSES ─────────────────────────────────────────────

@dataclass
class Rule:
    id: str
    name: str
    namespace: str
    severity: str
    min_severity: str
    description: str
    category: str
    maps_to: Optional[str | list[str]] = None
    obligation_type: Optional[str] = None
    anchor_mechanism: Optional[str] = None
    source_file: Optional[str] = None
    original_id: Optional[str] = None
    v3_id: Optional[str] = None


@dataclass
class ConstitutionManifest:
    version: str
    anchor_version: str
    core_domains: list[dict]
    frameworks: list[dict]
    regulators: list[dict]
    policy: dict
    legacy_aliases: dict[str, str]
    engine: dict
    output: dict


@dataclass
class LoadedConstitution:
    manifest: ConstitutionManifest
    rules: dict[str, Rule] = field(default_factory=dict)
    alias_chain: dict[str, str] = field(default_factory=dict)
    policy_overrides: dict[str, str] = field(default_factory=dict)
    custom_rules: dict[str, Rule] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    verified: bool = True


# ── SEVERITY ORDERING ─────────────────────────────────────────

SEVERITY_ORDER = {
    "info": 0,
    "warning": 1,
    "error": 2,
    "blocker": 3,
}


def severity_gte(a: str, b: str) -> bool:
    return SEVERITY_ORDER.get(a.lower(), 0) >= SEVERITY_ORDER.get(b.lower(), 0)


# ── SEAL VERIFICATION ─────────────────────────────────────────

def verify_seal(file_path: Path, seal: str) -> bool:
    """Verify SHA-256 seal on a .anchor file."""
    if seal == "sha256:PENDING":
        return True  # not yet sealed — development mode
    content = file_path.read_bytes()
    computed = "sha256:" + hashlib.sha256(content).hexdigest()
    return hmac.compare_digest(computed, seal)


def verify_remote_lockfile(anchor_dir: Path, offline_attr: str = "warn") -> bool:
    """Verifies directory hashes against remote GOVERNANCE.lock or local .anchor.lock. Returns True if verified."""
    import urllib.request
    import urllib.error
    
    from anchor.core.config import settings
    
    GOVERNANCE_LOCK_URL = settings.governance_lock_url
    local_lock_path = anchor_dir / ".anchor.lock"
    
    lock_data = None
    try:
        req = urllib.request.Request(GOVERNANCE_LOCK_URL)
        with urllib.request.urlopen(req, timeout=5) as response:
            lock_data = yaml.safe_load(response.read().decode('utf-8'))
        # Save cache for offline use
        local_lock_path.write_text(yaml.dump(lock_data, default_flow_style=False, sort_keys=False))
    except Exception as e:
        if offline_attr == "abort":
            raise RuntimeError(f"Cannot verify governance integrity — remote unreachable: {e}")
        elif local_lock_path.exists():
            print("WARNING: Governance integrity could not be verified remotely — using local .anchor.lock")
            lock_data = yaml.safe_load(local_lock_path.read_text())
        else:
            print("NOTE: No GOVERNANCE.lock found. Run anchor sync --restore to initialise governance integrity verification.")
            return False

    if not lock_data or "files" not in lock_data:
        return False

    remote_files = lock_data["files"]
    target_dirs = [(anchor_dir / "domains", "domains"), 
                   (anchor_dir / "frameworks", "frameworks"), 
                   (anchor_dir / "government", "government")]
    
    for folder, prefix in target_dirs:
        if folder.exists():
            for f in folder.rglob("*.anchor"):
                rel_path = f"{prefix}/{f.relative_to(folder)}".replace("\\", "/")
                if rel_path in remote_files:
                    local_hash = hashlib.sha256(f.read_bytes()).hexdigest()
                    if local_hash != remote_files[rel_path]:
                        raise RuntimeError(
                            f"\nANCHOR INTEGRITY VIOLATION\n"
                            f"{rel_path} has been modified.\n"
                            f"Local hash:  {local_hash}\n"
                            f"Remote hash: {remote_files[rel_path]}\n"
                            f"Run: anchor sync --restore to restore the authoritative version."
                        )

    return True


# ── MANIFEST LOADER ───────────────────────────────────────────

def load_manifest(constitution_path: Path) -> ConstitutionManifest:
    """Read and parse constitution.anchor manifest."""
    raw = yaml.safe_load(constitution_path.read_text())

    if raw.get("type") != "manifest":
        raise ValueError(
            f"{constitution_path} is not a manifest file. "
            f"Got type: {raw.get('type')}"
        )

    return ConstitutionManifest(
        version=raw["version"],
        anchor_version=raw["anchor_version"],
        core_domains=raw.get("core_domains", []),
        frameworks=raw.get("frameworks", []),
        regulators=raw.get("regulators", []),
        policy=raw.get("policy", {}),
        legacy_aliases=raw.get("legacy_aliases", {}),
        engine=raw.get("engine", {}),
        output=raw.get("output", {}),
    )


# ── DOMAIN FILE LOADER ────────────────────────────────────────

def load_domain_file(
    file_path: Path,
    expected_namespace: str,
    seal_check: str = "strict",
) -> dict[str, Rule]:
    """Load a single domain or framework .anchor file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Domain file not found: {file_path}")

    raw = yaml.safe_load(file_path.read_text())
    namespace = raw.get("namespace", "")

    if namespace != expected_namespace:
        raise ValueError(
            f"Namespace mismatch in {file_path}. "
            f"Expected {expected_namespace}, got {namespace}"
        )

    seal = raw.get("seal", "sha256:PENDING")
    if seal_check == "strict":
        if not verify_seal(file_path, seal):
            raise ValueError(
                f"Seal verification failed for {file_path}. "
                f"File may have been tampered with."
            )

    rules = {}
    for rule_data in raw.get("rules", []):
        raw_id = rule_data["id"]
        rule_id = raw_id if raw_id.startswith(f"{namespace}-") \
            else f"{namespace}-{raw_id}"

        rule = Rule(
            id=rule_id,
            name=rule_data["name"],
            namespace=namespace,
            severity=rule_data.get("severity", "error"),
            min_severity=rule_data.get("min_severity", "warning"),
            description=rule_data.get("description", ""),
            category=rule_data.get("category", ""),
            maps_to=rule_data.get("maps_to"),
            obligation_type=rule_data.get("obligation_type"),
            anchor_mechanism=rule_data.get("anchor_mechanism"),
            source_file=str(file_path),
            original_id=rule_data.get("original_id"),
            v3_id=rule_data.get("v3_id"),
        )
        rules[rule_id] = rule

    return rules


# ── POLICY LOADER ─────────────────────────────────────────────

def load_policy(
    policy_path: Path,
    existing_rules: dict[str, Rule],
    custom_prefix: str = "INTERNAL",
) -> tuple[dict[str, str], dict[str, Rule]]:
    """
    Load policy.anchor.
    Returns (severity_overrides, custom_rules).
    Validates raise-only constraint on overrides.
    """
    if not policy_path.exists():
        return {}, {}

    raw = yaml.safe_load(policy_path.read_text()) or {}
    overrides = {}
    custom_rules = {}

    for override in (raw.get("overrides") or []):
        rule_id = override["id"]
        new_severity = override["severity"].lower()

        if rule_id not in existing_rules:
            raise ValueError(
                f"policy.anchor references unknown rule: {rule_id}"
            )

        existing_severity = existing_rules[rule_id].severity.lower()
        min_severity = existing_rules[rule_id].min_severity.lower()

        # Raise-only check
        if not severity_gte(new_severity, existing_severity):
            raise ValueError(
                f"policy.anchor attempts to LOWER severity of {rule_id} "
                f"from {existing_severity} to {new_severity}. "
                f"The floor is absolute. policy.anchor can only raise severity."
            )

        # Min severity floor check
        if not severity_gte(new_severity, min_severity):
            raise ValueError(
                f"policy.anchor sets {rule_id} to {new_severity} "
                f"which is below min_severity floor of {min_severity}."
            )

        overrides[rule_id] = new_severity

    rules = raw.get("custom_rules") or raw.get("rules") or []
    for custom in rules:
        rule_id = custom["id"]

        if not rule_id.startswith(custom_prefix):
            raise ValueError(
                f"Custom rule {rule_id} must use {custom_prefix}- prefix."
            )

        rule = Rule(
            id=rule_id,
            name=custom["name"],
            namespace=custom_prefix,
            severity=custom.get("severity", "error"),
            min_severity=custom.get("min_severity", "warning"),
            description=custom.get("description", ""),
            category=custom.get("category", "custom"),
            source_file="policy.anchor",
        )
        custom_rules[rule_id] = rule

    return overrides, custom_rules


# ── ALIAS CHAIN RESOLVER ──────────────────────────────────────

def resolve_alias_chain(
    alias_id: str,
    legacy_aliases: dict[str, str],
    rules: dict[str, Rule],
    max_depth: int = 5,
) -> Optional[str]:
    """
    Resolve full alias chain: ANC-001 → FINOS-001 → SEC-006
    Returns the canonical domain rule ID.
    """
    current = alias_id
    visited = set()

    for _ in range(max_depth):
        if current in visited:
            raise ValueError(f"Circular alias chain detected: {alias_id}")
        visited.add(current)

        if current in rules:
            return current

        if current in legacy_aliases:
            current = legacy_aliases[current]
        else:
            break

    return None


# ── MAIN LOADER ───────────────────────────────────────────────

def load_constitution(
    governance_root: Path,
    constitution_path: Optional[Path] = None,
    anchor_dir: Optional[Path] = None,
) -> LoadedConstitution:
    """
    Main entry point. Loads constitution.anchor and all
    declared domain and framework files in sequence.

    Loading sequence:
    1. Read and validate constitution.anchor manifest
    2. Load shared.anchor (always first)
    3. Load core_domains (always loaded)
    4. Load active_domains (opt-in)
    5. Load active frameworks (opt-in)
    6. Load policy.anchor (raise-only overrides + custom rules)
    7. Build rule registry with alias chain
    """

    # Locate constitution.anchor
    if constitution_path is None:
        if anchor_dir:
            local_manifest = anchor_dir / "constitution.anchor"
            if local_manifest.exists():
                constitution_path = local_manifest

        if constitution_path is None:
            constitution_path = governance_root / "constitution.anchor"
            if not constitution_path.exists():
                # Fall back to package root
                constitution_path = Path(__file__).parent.parent.parent \
                    / "constitution.anchor"

    manifest = load_manifest(constitution_path)
    seal_check = manifest.engine.get("seal_check", "strict")
    offline_behaviour = manifest.engine.get("offline_behaviour", "warn")

    constitution = LoadedConstitution(manifest=manifest)
    
    if seal_check == "strict" and anchor_dir:
        try:
            constitution.verified = verify_remote_lockfile(anchor_dir, offline_attr=offline_behaviour)
        except RuntimeError as e:
            # If aborted by integrity violation, we must surface this error immediately.
            raise e
    elif not anchor_dir:
        # If no .anchor/ dir (e.g. running check before init), it's unverified
        constitution.verified = False

    def resolve_path(rel_path: str) -> Path:
        """Prioritize anchor_dir (project-local) over governance_root (library)."""
        if anchor_dir:
            p = anchor_dir / rel_path
            if p.exists():
                return p
        p = governance_root / rel_path
        return p

    # ── STEP 1: Load active domains ───────────────────────────
    for domain in manifest.core_domains:
        # Auto-activate if local file exists
        local_path = anchor_dir / domain["path"] if anchor_dir else None
        is_local = local_path and local_path.exists()

        if not domain.get("active", False) and not is_local:
            continue
            
        path = resolve_path(domain["path"])
        namespace = domain["namespace"]
        try:
            rules = load_domain_file(path, namespace, seal_check)
            constitution.rules.update(rules)
        except Exception as e:
            if domain.get("required", False):
                raise RuntimeError(
                    f"Failed to load required domain {domain['path']}: {e}"
                )
            constitution.errors.append(str(e))

    # ── STEP 2: Load active frameworks ───────────────────────
    for fw in manifest.frameworks:
        # Auto-activate if local file exists
        local_path = anchor_dir / fw["path"] if anchor_dir else None
        is_local = local_path and local_path.exists()
        
        if not fw.get("active", False) and not is_local:
            continue
            
        path = resolve_path(fw["path"])
        namespace = fw["namespace"]
        try:
            rules = load_domain_file(path, namespace, seal_check)
            constitution.rules.update(rules)
        except Exception as e:
            constitution.errors.append(str(e))

    # ── STEP 4: Load active regulators ───────────────────────
    for reg in manifest.regulators:
        # Auto-activate if local file exists
        local_path = anchor_dir / reg["path"] if anchor_dir else None
        is_local = local_path and local_path.exists()

        if not reg.get("active", False) and not is_local:
            continue
            
        path = resolve_path(reg["path"])
        namespace = reg["namespace"]
        try:
            rules = load_domain_file(path, namespace, seal_check)
            constitution.rules.update(rules)
        except Exception as e:
            constitution.errors.append(str(e))

    # ── STEP 5: Build alias chain ─────────────────────────────
    # Maps ANC-009 -> FINOS-009 -> SEC-001
    for alias_id, target_id in manifest.legacy_aliases.items():
        current_id = alias_id
        visited = {alias_id}
        next_id = target_id
        
        while next_id:
            if next_id in visited:
                break # Circular
            visited.add(next_id)
            
            if next_id in constitution.rules:
                # Target rule found!
                constitution.alias_chain[alias_id] = next_id
                break
            elif next_id in manifest.legacy_aliases:
                next_id = manifest.legacy_aliases[next_id]
            else:
                break
    
    # Also include maps_to relations from frameworks/regulators in the alias chain
    for rid, rule in constitution.rules.items():
        if rule.maps_to:
            # Handle both single string and list of strings for multi-ID support
            mappings = rule.maps_to if isinstance(rule.maps_to, list) else [rule.maps_to]
            for m_id in mappings:
                if m_id in constitution.rules:
                    # If a rule maps to another (e.g. FINOS-014 -> SEC-007)
                    # we treat it as an alias for reporting purposes.
                    # For many-to-many, we link to the first valid mapping in the alias chain.
                    if rid not in constitution.alias_chain:
                        constitution.alias_chain[rid] = m_id
                        break

    # ── STEP 6: Load policy.anchor ────────────────────────────
    if anchor_dir:
        policy_path = anchor_dir / manifest.policy.get("path", "policy.anchor")
        if policy_path.exists():
            custom_prefix = manifest.policy.get(
                "custom_rule_prefix", "INTERNAL"
            )
            overrides, custom_rules = load_policy(
                policy_path,
                constitution.rules,
                custom_prefix,
            )

            # Apply severity overrides (raise-only validated in load_policy)
            for rule_id, new_severity in overrides.items():
                constitution.rules[rule_id].severity = new_severity
                # If this is an alias, also apply to the resolved target? 
                # No, policy overrides on aliases should be transparently handled 
                # by the user knowing they are affecting that specific rule.
                # However, if multiple aliases point to the same target, 
                # it might be confusing. 
                # But for V3 -> V4, ANC-001 IS the anchor.
                if rule_id in constitution.alias_chain:
                    target_id = constitution.alias_chain[rule_id]
                    if target_id in constitution.rules:
                        # Only raise if current target is lower
                        if severity_gte(new_severity, constitution.rules[target_id].severity):
                            constitution.rules[target_id].severity = new_severity

            constitution.policy_overrides = overrides

            # Add custom rules
            constitution.rules.update(custom_rules)
            constitution.custom_rules = custom_rules

    # ── STEP 7: Validate unknown namespace policy ─────────────
    unknown_policy = manifest.engine.get("unknown_namespace", "reject")
    for rule_id, rule in constitution.rules.items():
        if rule.namespace not in _known_namespaces(manifest):
            if unknown_policy == "reject":
                raise ValueError(
                    f"Unknown namespace in rule {rule_id}: {rule.namespace}"
                )

    return constitution


def _known_namespaces(manifest: ConstitutionManifest) -> set[str]:
    """Return all namespaces declared in the manifest."""
    namespaces = {"SHR", "INTERNAL"}
    for d in manifest.core_domains:
        namespaces.add(d["namespace"])
    for fw in manifest.frameworks:
        namespaces.add(fw["namespace"])
    for reg in manifest.regulators:
        namespaces.add(reg["namespace"])
    return namespaces


# ── RULE LOOKUP ───────────────────────────────────────────────

def get_rule(
    constitution: LoadedConstitution,
    rule_id: str,
) -> Optional[Rule]:
    """
    Look up a rule by ID. Resolves aliases transparently.
    ANC-009 → FINOS-009 → SEC-001 → returns SEC-001 rule.
    """
    # Direct lookup
    if rule_id in constitution.rules:
        return constitution.rules[rule_id]

    # Alias chain lookup
    if rule_id in constitution.alias_chain:
        canonical = constitution.alias_chain[rule_id]
        return constitution.rules.get(canonical)

    return None
