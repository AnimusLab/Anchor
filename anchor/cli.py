import click
import subprocess  # anchor: ignore ANC-018
import os
import sys
import yaml
import json
import urllib.request
from anchor.core.policy_loader import PolicyLoader
from anchor.core.engine import PolicyEngine
from anchor.core.constitution import (
    get_constitution_url,
    get_mitigation_url,
    CONSTITUTION_SHA256,
    MITIGATION_SHA256,
    verify_integrity,
)
from anchor.core.config import settings


@click.group()
def cli():
    """
    Anchor: The Federated Governance Engine for AI.
    """
    pass


@click.command()
@click.option(
    '--domains',
    default='',
    help=(
        'Comma-separated domains to load. '
        'Always includes all core domains: security, ethics, shared, privacy, alignment, legal, operational, supply-chain, agentic. '
        'Options: all'
    )
)
@click.option(
    '--frameworks',
    default='',
    help=(
        'Comma-separated frameworks to load. '
        'Options: finos, owasp, nist, all'
    )
)
@click.option(
    '--regulators',
    default='',
    help=(
        'Comma-separated government regulators to load. '
        'Options: rbi, eu, sebi, cfpb, fca, sec, all'
    )
)
@click.option('--sandbox', is_flag=True, help='Install Diamond Cage (WASM sandbox) for secure execution.')
@click.option('--all', 'all_items', is_flag=True, help='Initialise ALL available domains, frameworks, and regulators.')
@click.option('--force', is_flag=True, default=False, help='Overwrite existing .anchor/ files.')
@click.option('--no-sign', is_flag=True, default=False, help='Skip directory signing.')
@click.option('--policy-name', default='policy.anchor', help='Name for your project policy file.')
def init(domains, frameworks, regulators, sandbox, all_items, force, no_sign, policy_name):
    """
    Initialise Anchor V4 governance in a repository.

    Creates .anchor/ with the requested domain, framework, and regulator files.
    Always loads all core domains: security, ethics, shared, privacy, alignment, legal, operational, supply-chain, agentic.

    Examples:

        anchor init

        anchor init --regulators rbi,eu,sebi

        anchor init --domains privacy,alignment --regulators rbi,eu

        anchor init --all
    """
    import shutil
    import hashlib

    # ── Package paths ─────────────────────────────────────────
    package_root = os.path.dirname(os.path.abspath(__file__))
    anchor_pkg_root = os.path.dirname(package_root)
    governance_root = os.path.join(anchor_pkg_root, "governance")

    AVAILABLE_DOMAINS = {
        "security":     "domains/security.anchor",
        "ethics":       "domains/ethics.anchor",
        "shared":       "domains/shared.anchor",
        "privacy":      "domains/privacy.anchor",
        "alignment":    "domains/alignment.anchor",
        "legal":        "domains/legal.anchor",
        "operational":  "domains/operational.anchor",
        "supply-chain": "domains/supply_chain.anchor",
        "agentic":      "domains/agentic.anchor",
    }

    ALWAYS_LOADED_DOMAINS = [
        "security",
        "ethics",
        "shared",
        "privacy",
        "alignment",
        "legal",
        "operational",
        "supply-chain",
        "agentic",
    ]

    AVAILABLE_FRAMEWORKS = {
        "finos": "frameworks/FINOS_Framework.anchor",
        "owasp": "frameworks/OWASP_LLM.anchor",
        "nist":  "frameworks/NIST_AI_RMF.anchor",
    }

    AVAILABLE_REGULATORS = {
        "rbi":   "government/RBI_Regulations.anchor",
        "eu":    "government/EU_AI_Act.anchor",
        "sebi":  "government/SEBI_Regulations.anchor",
        "cfpb":  "government/CFPB_Regulations.anchor",
        "fca":   "government/FCA_Regulations.anchor",
        "sec":   "government/SEC_Regulations.anchor",
    }

    DOMAIN_LABELS = {
        "security":     "Security (SEC) — always loaded",
        "ethics":       "Ethics (ETH) — always loaded",
        "shared":       "Shared cross-domain (SHR) — always loaded",
        "privacy":      "Privacy (PRV) — always loaded",
        "alignment":    "Alignment (ALN) — always loaded",
        "legal":        "Legal (LEG) — always loaded",
        "operational":  "Operational (OPS) — always loaded",
        "supply-chain": "Supply Chain (SUP) — always loaded",
        "agentic":      "Agentic AI (AGT) — always loaded",
    }

    FRAMEWORK_LABELS = {
        "finos": "FINOS AI Governance Framework",
        "owasp": "OWASP LLM Top 10 2025",
        "nist":  "NIST AI RMF 1.0",
    }

    REGULATOR_LABELS = {
        "rbi":   "RBI FREE-AI Report 2025",
        "eu":    "EU AI Act 2024/1689",
        "sebi":  "SEBI AI/ML Regulations",
        "cfpb":  "CFPB Regulation B",
        "fca":   "FCA AI Governance 2024",
        "sec":   "SEC 2026 Examination Priorities",
    }

    dot_anchor = ".anchor"

    click.echo("")
    click.secho("⚓ Anchor V4 — init", fg="cyan", bold=True)
    click.echo("")

    if all_items:
        if not domains: domains = 'all'
        if not frameworks: frameworks = 'all'
        if not regulators: regulators = 'all'

    # ── Resolve requested domains ─────────────────────────────
    requested_domains = set(ALWAYS_LOADED_DOMAINS)
    if domains:
        domain_list = [d.strip().lower() for d in domains.split(",")]
        if "all" in domain_list:
            requested_domains = set(AVAILABLE_DOMAINS.keys())
        else:
            for d in domain_list:
                if d not in AVAILABLE_DOMAINS:
                    click.secho(
                        f"  ✗ Unknown domain: '{d}'. "
                        f"Available: {', '.join(AVAILABLE_DOMAINS.keys())}",
                        fg="red"
                    )
                    sys.exit(1)
                requested_domains.add(d)

    # ── Resolve requested frameworks ──────────────────────────
    requested_frameworks = set()
    if frameworks:
        fw_list = [f.strip().lower() for f in frameworks.split(",")]
        if "all" in fw_list:
            requested_frameworks = set(AVAILABLE_FRAMEWORKS.keys())
        else:
            for fw in fw_list:
                if fw not in AVAILABLE_FRAMEWORKS:
                    click.secho(
                        f"  ✗ Unknown framework: '{fw}'. "
                        f"Available: {', '.join(AVAILABLE_FRAMEWORKS.keys())}",
                        fg="red"
                    )
                    sys.exit(1)
                requested_frameworks.add(fw)

    # ── Resolve requested regulators ──────────────────────────
    requested_regulators = set()
    if regulators:
        reg_list = [r.strip().lower() for r in regulators.split(",")]
        if "all" in reg_list:
            requested_regulators = set(AVAILABLE_REGULATORS.keys())
        else:
            for reg in reg_list:
                if reg not in AVAILABLE_REGULATORS:
                    click.secho(
                        f"  ✗ Unknown regulator: '{reg}'. "
                        f"Available: {', '.join(AVAILABLE_REGULATORS.keys())}",
                        fg="red"
                    )
                    sys.exit(1)
                requested_regulators.add(reg)

    # ── Create directory structure ────────────────────────────
    for d in [
        dot_anchor,
        os.path.join(dot_anchor, "domains"),
        os.path.join(dot_anchor, "frameworks"),
        os.path.join(dot_anchor, "government"),
        os.path.join(dot_anchor, "cache"),
        os.path.join(dot_anchor, "reports"),
        os.path.join(dot_anchor, "violations"),
        os.path.join(dot_anchor, "telemetry"),
        os.path.join(dot_anchor, "branding"),
    ]:
        os.makedirs(d, exist_ok=True)

    # ── Helper: copy a governance file ────────────────────────
    def copy_file(relative_path, label):
        src = os.path.join(governance_root, relative_path)
        dst = os.path.join(dot_anchor, relative_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(src):
            click.secho(f"  ✗ Not found in package: {relative_path}", fg="red")
            return False
        if os.path.exists(dst) and not force:
            click.secho(f"  ~ Already exists: {label}", fg="yellow")
            return True
        shutil.copy2(src, dst)
        click.secho(f"  ✓ {label}", fg="green")
        return True

    # ── Copy domain files ─────────────────────────────────────
    click.secho("  Domains", fg="cyan", bold=True)
    for domain in sorted(requested_domains):
        copy_file(AVAILABLE_DOMAINS[domain], DOMAIN_LABELS[domain])

    # ── Copy framework files ──────────────────────────────────
    if requested_frameworks:
        click.echo("")
        click.secho("  Frameworks", fg="cyan", bold=True)
        for fw in sorted(requested_frameworks):
            copy_file(AVAILABLE_FRAMEWORKS[fw], FRAMEWORK_LABELS[fw])

    # ── Copy regulator files ──────────────────────────────────
    if requested_regulators:
        click.echo("")
        click.secho("  Regulators", fg="cyan", bold=True)
        for reg in sorted(requested_regulators):
            copy_file(AVAILABLE_REGULATORS[reg], REGULATOR_LABELS[reg])

    # ── Deploy manifest and example files ─────────────────────
    examples_dir = os.path.join(governance_root, "examples")
    # Copy master manifest as the project manifest
    master_manifest = os.path.join(anchor_pkg_root, "constitution.anchor")
    dot_anchor_manifest = os.path.join(dot_anchor, "constitution.anchor")
    if os.path.exists(master_manifest) and (not os.path.exists(dot_anchor_manifest) or force):
        shutil.copy2(master_manifest, dot_anchor_manifest)

    # Copy mitigation catalog
    master_mitigation = os.path.join(governance_root, "mitigation.anchor")
    dot_anchor_mitigation = os.path.join(dot_anchor, "mitigation.anchor")
    if os.path.exists(master_mitigation) and (not os.path.exists(dot_anchor_mitigation) or force):
        shutil.copy2(master_mitigation, dot_anchor_mitigation)

    for example in ["constitution.anchor.example", "policy.anchor.example"]:
        src = os.path.join(examples_dir, example)
        dst = os.path.join(dot_anchor, example)
        if os.path.exists(src) and (not os.path.exists(dst) or force):
            shutil.copy2(src, dst)

    # ── Copy branding ─────────────────────────────────────────
    logo_src = os.path.join(examples_dir, "logo.png")
    logo_dst = os.path.join(dot_anchor, "branding", "logo.png")
    if os.path.exists(logo_src) and (not os.path.exists(logo_dst) or force):
        shutil.copy2(logo_src, logo_dst)

    # ── Create policy.anchor if it doesn't exist ──────────────
    policy_path = os.path.join(dot_anchor, policy_name)
    if not os.path.exists(policy_path):
        policy_template = f'''# =============================================================================
# {policy_name.replace('.anchor', '').upper()} — Project Policy
# =============================================================================
# This file is for YOUR project-specific rules.
# Automatically ignored by git to protect company policies.
#
# RULES:
#   1. Can only RAISE severity (ERROR -> BLOCKER is allowed)
#   2. Cannot LOWER severity — the floor is absolute
#   3. Cannot suppress constitutional rules
#   4. Can add INTERNAL-* prefixed custom rules
#
# Reference: .anchor/constitution.anchor.example
# =============================================================================

version: "4.0"

metadata:
  project: "{os.path.basename(os.getcwd())}"

overrides:
  # Example: raise SEC-006 from error to blocker
  # - id: SEC-006
  #   severity: blocker
  #   reason: >
  #     Our PCI-DSS scope requires blocking all direct LLM API calls.

custom_rules:
  # Example: add a company-specific rule
  # - id: INTERNAL-001
  #   name: Internal vault access pattern
  #   severity: blocker
  #   detection:
  #     method: regex
  #     pattern: 'vault\\.read\\((?!approved_keys)'
  #   description: >
  #     Vault read operations must only access approved_keys namespace.
'''
        with open(policy_path, "w", encoding="utf-8") as f:
            f.write(policy_template)
        click.echo("")
        click.secho(f"  ✓ Created {policy_path}", fg="green")

    # ── Update .gitignore ─────────────────────────────────────
    # V4 Decision: .anchor/ should be committed, excluding cache and temp
    gitignore_path = ".gitignore"
    gitignore_entries = [".anchor/cache/", ".anchor/logs/*.tmp", f".anchor/{policy_name}"]
    try:
        content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                content = f.read()
        
        # Remove legacy .anchor/ ignore if present
        content = content.replace(".anchor/\n", "").replace(".anchor/", "")

        updated = False
        to_add = []
        for entry in gitignore_entries:
            if entry not in content:
                to_add.append(entry)
                updated = True
        
        if updated:
            with open(gitignore_path, "w") as f:
                if content:
                    f.write(content.rstrip() + "\n\n")
                f.write("# Anchor governance cache/logs\n")
                for entry in to_add:
                    f.write(f"{entry}\n")
    except Exception as e:
        click.secho(f"  WARNING: Could not update .gitignore: {e}", fg="yellow")

    # ── Install git pre-commit hook ───────────────────────────
    if os.path.exists(".git"):
        hooks_dir = os.path.join(".git", "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        pre_commit_path = os.path.join(hooks_dir, "pre-commit")
        pre_commit_content = """#!/bin/sh
# Anchor Git Hook: Targeted compliance scan for staged files
echo "[Anchor] Checking staged files for compliance..."

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|ts|tsx)$')

if [ -z "$STAGED_FILES" ]; then
  echo "No relevant files staged. Skipping Anchor scan."
  exit 0
fi

python -m anchor check --severity error --hook $STAGED_FILES
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Commit Blocked: Anchor detected compliance violations."
  echo "  See .anchor/violations/governance_violations.txt for details."
  exit 1
fi
"""
        try:
            with open(pre_commit_path, "w") as f:
                f.write(pre_commit_content)
            try:
                os.chmod(pre_commit_path, 0o755)
            except Exception:
                pass
            click.secho("  ✓ Git pre-commit hook installed", fg="green")
        except Exception as e:
            click.secho(f"  WARNING: Could not install git hook: {e}", fg="yellow")

    # ── Verify Remote Integrity ───────────────────────────────
    click.echo("")
    if no_sign:
        click.secho("  ~ Remote integrity fetch skipped (--no-sign)", fg="yellow")
    else:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request("https://raw.githubusercontent.com/Tanishq1030/anchor/main/GOVERNANCE.lock")
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_lock = response.read().decode('utf-8')
            lock_path = os.path.join(dot_anchor, ".anchor.lock")
            with open(lock_path, "w", encoding="utf-8") as f:
                f.write(remote_lock)
            click.secho("  ✓ Fetched GOVERNANCE.lock from remote", fg="green")
        except urllib.error.URLError as e:
            click.secho(f"  WARNING: Could not fetch GOVERNANCE.lock remotely: {e.reason}", fg="yellow")
        except Exception as e:
            click.secho(f"  WARNING: Failed to fetch remote lockfile: {e}", fg="yellow")

    # ── Optionally install Diamond Cage ───────────────────────
    if sandbox:
        click.echo("")
        click.secho("  Installing Diamond Cage...", fg="cyan", bold=True)
        from anchor.core.sandbox import install_diamond_cage
        install_diamond_cage()

    # ── Summary ───────────────────────────────────────────────
    click.echo("")
    click.secho("  " + "─" * 40, fg="bright_black")
    click.secho(f"  {len(requested_domains)} domain(s) loaded", fg="white")
    if requested_frameworks:
        click.secho(f"  {len(requested_frameworks)} framework(s) loaded", fg="white")
    if requested_regulators:
        click.secho(f"  {len(requested_regulators)} regulator(s) loaded", fg="white")
    click.secho("  .anchor/ created", fg="white")
    click.secho("  .anchor/ committed to repository (logs and governance state are version-controlled)", fg="white")
    click.secho("  .anchor/cache/ added to .gitignore", fg="bright_black")
    click.echo("")
    click.secho(
        "  Run anchor check . to run your first audit.",
        fg="bright_black"
    )
    click.echo("")


@cli.command('sync')
@click.option('--restore', is_flag=True, help='Overwrite local modified files with authoritative remote files.')
def sync(restore):
    """Sync governance files with the authoritative remote repository."""
    if not restore:
        click.secho("Use `anchor sync --restore` to fetch authoritative files and overwrite local changes.", fg="yellow")
        sys.exit(1)
        
    dot_anchor = ".anchor"
    if not os.path.exists(dot_anchor):
        click.secho("No .anchor/ directory found. Run `anchor init` first.", fg="red")
        sys.exit(1)

    import urllib.request
    import urllib.error
    import yaml
    
    GOVERNANCE_LOCK_URL = "https://raw.githubusercontent.com/Tanishq1030/anchor/main/GOVERNANCE.lock"
    click.secho("Fetching remote GOVERNANCE.lock...", fg="cyan")
    
    try:
        req = urllib.request.Request(GOVERNANCE_LOCK_URL)
        with urllib.request.urlopen(req, timeout=5) as response:
            lock_data = yaml.safe_load(response.read().decode('utf-8'))
        
        lock_path = os.path.join(dot_anchor, ".anchor.lock")
        with open(lock_path, "w", encoding="utf-8") as f:
            yaml.dump(lock_data, f, default_flow_style=False, sort_keys=False)
            
        remote_files = lock_data.get("files", {})
        
        BASE_REPO_URL = "https://raw.githubusercontent.com/Tanishq1030/anchor/main/governance/"
        
        restored_count = 0
        for rel_path, expected_hash in remote_files.items():
            # rel_path is like domains/security.anchor
            local_path = os.path.join(dot_anchor, rel_path.replace("/", os.sep))
            
            needs_restore = False
            if not os.path.exists(local_path):
                needs_restore = True
            else:
                with open(local_path, "rb") as bf:
                    local_hash = hashlib.sha256(bf.read()).hexdigest()
                if local_hash != expected_hash:
                    needs_restore = True
                    
            if needs_restore:
                file_url = BASE_REPO_URL + rel_path
                try:
                    freq = urllib.request.Request(file_url)
                    with urllib.request.urlopen(freq, timeout=5) as r2:
                        content = r2.read()
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, "wb") as bf:
                        bf.write(content)
                    click.secho(f"  ✓ Restored {rel_path}", fg="green")
                    restored_count += 1
                except Exception as e:
                    click.secho(f"  ✗ Failed to fetch {rel_path}: {e}", fg="red")
                    
        click.secho(f"\nSync complete. Restored {restored_count} files to authoritative state.", fg="cyan", bold=True)
        
    except Exception as e:
        click.secho(f"Sync failed: {e}", fg="red")
        sys.exit(1)


@cli.group('check', invoke_without_command=True)
@click.option('--policy', '-p', multiple=True, help='Policy file(s) to apply.')
@click.argument('paths', nargs=-1)
@click.option('--dir', '-d', '--directory', help='Directory to scan (for code).')
@click.option('--model', '-m', help='Model weights file to validate (LM Studio, AnchorGrid, etc).')
@click.option('--metadata', help='Path to training metadata JSON.')
@click.option('--context', '-c', help='GenAI Threat Model (Markdown) to enforce.')
@click.option('--server-mode', is_flag=True, help='Run in server mode (includes local company policy).')
@click.option('--generate-report', is_flag=True, help='Generate human-readable audit report.')
@click.option('--json-report', '-j', is_flag=True, help='Generate anchor-report.json for CI.')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed loading info.')
@click.option('--no-sandbox', is_flag=True, help='Disable Diamond Cage WASM sandbox.')
@click.option('--severity', '-s', default='info', help='Minimum severity to show (info, warning, error, blocker).')
@click.option('--hook', is_flag=True, help='Indicate if running as a Git hook (customizes output).')
@click.option('--exclude', multiple=True, help='Paths to exclude from scanning (e.g., --exclude tests).')
@click.option('--github-summary', is_flag=True, help='Generate anchor-summary.md for GitHub Step Summary (CI only).')
@click.pass_context
def check(ctx, policy, paths, dir, model, metadata, context, server_mode, generate_report, json_report, verbose, no_sandbox, severity, hook, exclude, github_summary):
    """
    Universal enforcement command for code, models, and architectural drift.

    Run security governance check (default):

      anchor check .

    Detect architectural drift across a codebase:

      anchor check drift .

      anchor check drift src/models.py
    """
    if ctx.invoked_subcommand is not None:
        return  # Let the subcommand handle it
    
    # --- SUBCOMMAND REDIRECTION FIX ---
    # Click's greedy 'paths' argument may consume the subcommand name (e.g., 'drift').
    # If we are here, no subcommand was explicitly invoked, so we check 'paths'.
    if paths and paths[0] in check.commands:
        cmd_name = paths[0]
        cmd = check.commands[cmd_name]
        # Only pass 'target' for commands that have a target parameter (e.g. drift, not verify-sync)
        has_target = any(p.name == "target" for p in cmd.params)
        if has_target:
            target = paths[1] if len(paths) > 1 else "."
            return ctx.invoke(cmd, target=target)
        else:
            return ctx.invoke(cmd)
    # ----------------------------------

    from anchor.core.sandbox import DiamondCage, install_diamond_cage
    cage = DiamondCage()

    # 0. ENSURE SANDBOX IS READY (Automatic)
    ephemeral_sandbox = False
    if not no_sandbox:
        if not cage.is_installed():
            if verbose: click.secho("Diamond Cage (WASM Sandbox) not found. Initializing...", fg="cyan")
            success = install_diamond_cage(verbose=verbose)
            if not success:
                if verbose: click.secho("WARNING: Sandbox initialization failed. Falling back to host execution.", fg="yellow")
            else:
                ephemeral_sandbox = True
                if verbose: click.secho("Sandbox Ready.", fg="green")
        else:
            if verbose:
                click.secho("Using Diamond Cage (WASM Sandbox) for isolation.", fg="cyan")

    # 1. GATHER THE FEDERATION
    dot_anchor = ".anchor"
    cache_dir = os.path.join(dot_anchor, "cache")
    active_policies = []

    # Governance Files to sync and verify
    governance_targets = [
        ("Constitution", get_constitution_url(), "constitution.anchor", CONSTITUTION_SHA256),
        ("Mitigation Catalog", get_mitigation_url(), "mitigation.anchor", MITIGATION_SHA256),
    ]
    for label, url, filename, expected_hash in governance_targets:
        target_path = os.path.join(cache_dir, filename)
        if verbose: click.secho(f"Syncing {label}...", fg="blue")
        
        try:
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            with urllib.request.urlopen(url, timeout=settings.fetch_timeout) as response:
                content = response.read()
                with open(target_path, "wb") as f:
                    f.write(content)

            # Integrity Verification
            is_valid, msg = verify_integrity(target_path, expected_hash)
            if is_valid:
                if verbose: click.echo(f"   {msg}")
            else:
                click.secho(f"\n{msg}", fg="red", bold=True)
                click.secho(f"   The cloud-hosted {label.lower()} does not match this release.", fg="red")
                click.secho("   Update Anchor or contact the maintainer.", fg="yellow")
                sys.exit(1)
        except Exception as e:
            if os.path.exists(target_path):
                # Offline fallback with integrity check
                is_valid, msg = verify_integrity(target_path, expected_hash)
                if is_valid:
                    click.secho(f"INFO: {label} cloud unreachable, using verified cache.", fg="cyan")
                    if verbose: click.echo(f"   {msg}")
                else:
                    click.secho(f"\n{msg}", fg="red", bold=True)
                    click.secho(f"   Cannot audit with a tampered {label.lower()}.", fg="red")
                    sys.exit(1)
            else:
                if verbose:
                    click.secho(f"WARNING: Could not fetch {label.lower()} and no cache found: {e}", fg="yellow")
                # Don't exit here for V4, let the Federated Loader try to use local governance library

    # 1.5. THE RISK CATALOG LOADER (V4 Federated System)
    # Load rule metadata from federated domain files via loader.py
    # Then join with mitigation.anchor detection patterns
    rule_dict = {}

    package_root = os.path.dirname(os.path.abspath(__file__))
    anchor_pkg_root = os.path.dirname(package_root)
    governance_root_path = os.path.join(anchor_pkg_root, "governance")

    # A. Load rule metadata from V4 federated domain files
    loaded = None
    try:
        from pathlib import Path
        from anchor.core.loader import load_constitution, get_rule

        loaded = load_constitution(
            governance_root=Path(governance_root_path),
            anchor_dir=Path(dot_anchor) if os.path.exists(dot_anchor) else None,
        )

        # Convert Rule dataclass objects to dicts the engine understands
        for rule_id, rule in loaded.rules.items():
            rule_dict[rule_id] = {
                "id":          rule.id,
                "name":        rule.name,
                "severity":    rule.severity,
                "description": rule.description,
                "category":    rule.category,
                # detection fields populated below from mitigation.anchor
                "match":       None,
                "pattern":     None,
                "message":     None,
                "mitigation":  None,
            }

        if verbose:
            click.echo(f"   Loaded {len(rule_dict)} rules from V4 federated domains.")
            if loaded.errors:
                for err in loaded.errors:
                    click.secho(f"   [!] Loader warning: {err}", fg="yellow")

    except Exception as e:
        if verbose:
            click.secho(f"   [!] V4 loader failed, falling back to cache: {e}", fg="yellow")

        # Fallback: load from V3 cache if V4 loader fails
        constitution_path = os.path.join(cache_dir, "constitution.anchor")
        if os.path.exists(constitution_path):
            try:
                with open(constitution_path, "r", encoding="utf-8") as f:
                    c_data = yaml.safe_load(f) or {}
                    for r in c_data.get("rules", []):
                        if "id" in r:
                            rule_dict[r["id"]] = r
                if verbose:
                    click.echo(f"   Fallback: loaded {len(rule_dict)} rules from V3 cache.")
            except Exception as fallback_err:
                if verbose:
                    click.secho(f"   [!] Fallback also failed: {fallback_err}", fg="red")

    # B. Load detection patterns from mitigation.anchor and join with rule metadata
    # Prioritize project-local mitigation catalog
    mitigation_path = os.path.join(dot_anchor, "mitigation.anchor")
    if not os.path.exists(mitigation_path):
        mitigation_path = os.path.join(governance_root_path, "mitigation.anchor")
        
    if os.path.exists(mitigation_path):
        try:
            with open(mitigation_path, "r", encoding="utf-8") as f:
                m_data = yaml.safe_load(f) or {}
                m_list = m_data.get("mitigations", [])

            for m in m_list:
                r_id = m.get("rule_id")
                if not r_id:
                    continue
                # Resolve to canonical ID via alias chain
                resolved_id = r_id
                if loaded and r_id in loaded.alias_chain:
                    resolved_id = loaded.alias_chain[r_id]

                if resolved_id in rule_dict:
                    # Merge detection pattern into the rule metadata
                    rule_dict[resolved_id]["match"]      = m.get("match")
                    rule_dict[resolved_id]["pattern"]    = m.get("pattern")
                    rule_dict[resolved_id]["message"]    = m.get("message", rule_dict[resolved_id].get("name"))
                    rule_dict[resolved_id]["mitigation"] = m.get("fix", m.get("mitigation"))
                    rule_dict[resolved_id]["name"]       = (
                        f"{rule_dict[resolved_id]['name']} ({m['name']})"
                        if m.get("name") else rule_dict[resolved_id]["name"]
                    )

            if verbose:
                active = sum(1 for r in rule_dict.values() if r.get("match") or r.get("pattern"))
                click.echo(f"   {active} rules have active detection patterns.")

        except Exception as e:
            if verbose:
                click.secho(f"   [!] Failed to load mitigation patterns: {e}", fg="yellow")

    # B.2. Register virtual aliases for legacy IDs (ANC-NNN) after patterns are merged
    if loaded and loaded.alias_chain:
        for alias_id, canonical_id in loaded.alias_chain.items():
            if canonical_id in rule_dict:
                if alias_id not in rule_dict:
                    # Create virtual copy
                    alias_entry = rule_dict[canonical_id].copy()
                    alias_entry["id"] = alias_id
                    rule_dict[alias_id] = alias_entry
                else:
                    # Sync pattern from canonical to existing alias if needed
                    can_rule = rule_dict[canonical_id]
                    for field in ["match", "pattern", "message", "mitigation"]:
                        if can_rule.get(field) and not rule_dict[alias_id].get(field):
                            rule_dict[alias_id][field] = can_rule[field]

    # C. Load and merge local risk catalogs from patterns/ (unchanged from V3)
    patterns_dir = os.path.join(os.getcwd(), "patterns")
    if os.path.exists(patterns_dir):
        if verbose:
            click.echo(f"   Merging project-local risk catalogs from {patterns_dir}...")
        for root, _, files in os.walk(patterns_dir):
            for file in files:
                if file.endswith((".yaml", ".anchor")) and "example" not in file:
                    p_path = os.path.join(root, file)
                    try:
                        with open(p_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            catalog_rules = data.get("risks") or data.get("rules") or []
                            for r in catalog_rules:
                                if "id" in r:
                                    r_id = r["id"]
                                    if r_id in rule_dict:
                                        # Merge instead of overwrite
                                        for k, v in r.items():
                                            if not rule_dict[r_id].get(k):
                                                rule_dict[r_id][k] = v
                                    else:
                                        rule_dict[r_id] = r
                            if verbose:
                                click.echo(f"      + {file} ({len(catalog_rules)} rules merged)")
                    except Exception as e:
                        if verbose:
                            click.secho(f"      ! Failed to load {file}: {e}", fg="yellow")

    # Remove rules with no detection capability — engine can't enforce them yet
    master_rules = [
        r for r in rule_dict.values()
        if r.get("match") or r.get("pattern")
    ]

    if verbose:
        click.echo(f"   {len(master_rules)} enforceable rules ready.")

    # --- B. Project Policy (Local) ---
    # We look for policy.anchor (default) or any .anchor file in .anchor/ or root
    if policy:
        for p in policy:
            if os.path.exists(p):
                active_policies.append(p)
    else:
        # 1. Check .anchor/ (New default)
        search_dirs = [dot_anchor, "."]
        found = False
        for s_dir in search_dirs:
            if not os.path.exists(s_dir): continue
            
            p_path = os.path.join(s_dir, "policy.anchor")
            if os.path.exists(p_path):
                active_policies.append(p_path)
                found = True
                break
            
            # Check for policy inside .anchor/ directory
            dot_anchor_dir = os.path.join(s_dir, '.anchor')
            if os.path.exists(dot_anchor_dir) and os.path.isdir(dot_anchor_dir):
                anchors = [os.path.join('.anchor', f) for f in os.listdir(dot_anchor_dir) 
                          if f.endswith('.anchor') and "constitution" not in f and "mitigation" not in f]
                if anchors:
                    active_policies.append(os.path.join(s_dir, anchors[0]))
                    if verbose: click.echo(f"   Auto-detected project policy: {active_policies[-1]}")
                    found = True
                    break
            
            # Legacy/Root-level fallback
            root_anchors = [f for f in os.listdir(s_dir) if f.endswith('.anchor') and "constitution" not in f and "mitigation" not in f]
            if root_anchors:
                active_policies.append(os.path.join(s_dir, root_anchors[0]))
                if verbose: click.echo(f"   Auto-detected project policy: {active_policies[-1]}")
                found = True
                break
    
    if not active_policies:
        click.secho("No policies found. Run 'anchor init' first.", fg="red")
        sys.exit(1)

    # 2. MERGE POLICIES
    merged_rules = master_rules.copy()
    
    # Merge local policies on top
    for p_file in active_policies:
        try:
            loader = PolicyLoader(p_file, verbose=verbose)
            config = loader.load_policy()
            local_rules = config.get("rules", [])
            
            # Use PolicyLoader's merge logic to override master_rules by ID
            final_config_tmp = loader._merge_policies({"rules": merged_rules}, {"rules": local_rules})
            merged_rules = final_config_tmp.get("rules", [])
            
            # Merge exclusions from policy into the global exclude list
            policy_excludes = config.get("exclude", [])
            if isinstance(policy_excludes, list):
                exclude = list(exclude) + policy_excludes
        except Exception as e:
            if verbose: click.secho(f"Failed to parse {p_file}: {e}", fg="red")

    final_config = {"rules": merged_rules, "exclude": list(exclude)}

    # === NEW: GenAI THREAT MODEL INTEGRATION ===
    if context:
        from anchor.core.markdown_parser import MarkdownPolicyParser
        from anchor.core.mapper import PolicyMapper
        click.secho(f"\n[BRIDGE] Parsing GenAI Threat Model: {context}", fg="cyan", bold=True)
        md_parser = MarkdownPolicyParser()
        detected_risks = md_parser.parse_file(context)
        if detected_risks:
            policy_mapper = PolicyMapper()
            # Filter the rules based on detected risks
            final_config["rules"] = policy_mapper.get_rules_for_ids(list(detected_risks))
            click.secho(f"   Activated {len(final_config['rules'])} dynamic enforcement rules\n", fg="green")

    # 3. RUN ENFORCEMENT
    violations = []
    suppressed = []
    behavioral_findings = []
    metrics = {}
    
    # Handle multiple paths or fallback to directory/current dir
    if paths:
        scan_targets = list(paths)
    elif dir:
        scan_targets = [dir]
    else:
        scan_targets = ["."]

    if model:
        # Use Sandbox for Model Audit Weight analysis if enabled
        from anchor.core.model_auditor import ModelAuditor
        click.secho(f"\nAuditing Model Weights: {model}", fg="cyan", bold=True)
        
        # Pass sandbox status to auditor
        auditor = ModelAuditor(final_config, verbose=verbose)
        result = auditor.audit_weights(model, metadata)
        
        if result.status.value == "failed":
            violations = result.violations

        if generate_report or server_mode:
            report_path = os.path.join(dot_anchor, "audits", "governance_audit.md")
            with open(report_path, "w") as f:  # anchor: ignore ANC-007
                f.write(f"# Model Audit Report: {model}\n\nStatus: {result.status.value.upper()}\n")
                f.write(f"Passed: {result.checks_passed}/{result.checks_total}\n\n")
                f.write("## Recommendation\n" + result.recommendation + "\n")
            click.secho(f"Report saved: {report_path}", fg="green")

    # --- Code Scanning Phase ---
    # We'll print the target/law count, but the file count comes from the engine
    click.secho(f"Scanning {len(scan_targets)} path(s) with {len(final_config['rules'])} active laws...", fg="yellow")

    # --- Diamond Cage activation ---
    active_cage = None
    if not no_sandbox:
        from anchor.core.sandbox import DiamondCage
        _cage = DiamondCage(verbose=verbose)
        if _cage.is_installed():
            active_cage = _cage
            click.secho("Diamond Cage: ACTIVE (behavioral verification enabled)", fg="cyan")
        else:
            if verbose:
                click.secho("Diamond Cage: not installed (use 'anchor init' to enable)", fg="white", dim=True)

    engine = PolicyEngine(config=final_config, verbose=verbose)
    # Perform scan on each target
    for target in scan_targets:
        results = engine.scan_directory(target, exclude_paths=list(exclude), cage=active_cage)
        
        # Merge findings
        violations.extend(results.get('violations', []))
        suppressed.extend(results.get('suppressed', []))
        behavioral_findings.extend(results.get('behavioral_findings', []))
        
        # Update metrics
        new_metrics = results.get('metrics', {})
        for k, v in new_metrics.items():
            metrics[k] = metrics.get(k, 0) + v
    
    # Merge behavioral findings into violations for unified reporting
    violations.extend(behavioral_findings)


    # 4. REPORT & EXIT
    # Filter violations based on severity level
    severity_map = {"info": 0, "warning": 1, "error": 2, "blocker": 3, "critical": 3}
    min_sev_score = severity_map.get(severity.lower(), 0)
    violations = [v for v in violations if severity_map.get(v['severity'].lower(), 0) >= min_sev_score]

    # Deduplicate alias/canonical duplicates on canonical ID + file + line
    alias_chain = loaded.alias_chain if loaded else {}
    def _canonical(rule_id: str) -> str:
        return alias_chain.get(rule_id, rule_id)

    def _sev_score(v): return severity_map.get(v.get('severity', '').lower(), 0)

    deduped = {}
    for v in violations:
        canonical_id = _canonical(v['id'])
        key = (canonical_id, v.get('file'), v.get('line'))
        candidate = dict(v)
        candidate_id = canonical_id
        candidate['_source_id'] = v['id']
        candidate['_is_alias'] = v['id'] != canonical_id
        candidate['id'] = candidate_id

        existing = deduped.get(key)
        if not existing:
            deduped[key] = candidate
            continue

        # Prefer canonical over alias; if same type, keep higher severity
        if existing.get('_is_alias', False) and not candidate['_is_alias']:
            deduped[key] = candidate
        elif existing.get('_is_alias') == candidate['_is_alias'] and _sev_score(candidate) > _sev_score(existing):
            deduped[key] = candidate

    # Strip helper fields
    violations = []
    for v in deduped.values():
        v.pop('_source_id', None)
        v.pop('_is_alias', None)
        violations.append(v)

    # Determine if we are in a CI/CD repo (auto-JSON)
    has_cicd = os.path.isdir(".github") or os.path.isdir(".gitlab-ci")
    write_json = json_report or has_cicd

    if violations or suppressed or metrics:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        failures = [v for v in violations if v['severity'] in ['critical', 'blocker', 'error']]
        warnings = [v for v in violations if v['severity'] == 'warning']
        info     = [v for v in violations if v['severity'] == 'info']

        # Ensure output directories exist
        for _d in [os.path.join(dot_anchor, "violations"), os.path.join(dot_anchor, "reports"), os.path.join(dot_anchor, "telemetry")]:
            os.makedirs(_d, exist_ok=True)

        txt_path  = os.path.join(dot_anchor, "violations", "governance_violations.txt")
        md_path   = os.path.join(dot_anchor, "reports",    "governance_audit.md")
        json_path = os.path.join(dot_anchor, "telemetry",  "governance_report.json")

        try:
            # -- 1. Plain-text violation dump (always) ------------------------─
            with open(txt_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
                f.write("=" * 80 + "\n")
                f.write("   ANCHOR GOVERNANCE VIOLATIONS\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Scan Source: {os.path.abspath(scan_targets[0])}\n")
                f.write(f"Timestamp:   {timestamp}\n\n")

                f.write("--- SCAN STATISTICS ---\n")
                f.write(f"Files Scanned: {metrics.get('scanned_files', 0)}\n")
                f.write(f"Files Ignored: {metrics.get('ignored_files', 0)}\n")
                f.write(f"Total Files:   {metrics.get('total_files', 0)}\n")
                f.write(f"Total Dirs:    {metrics.get('total_dirs', 0)}\n\n")

                f.write("--- VIOLATION SUMMARY ---\n")
                f.write(f"Total Findings: {len(violations) + len(suppressed)}\n")
                f.write(f"Breakdown:      {len(failures)} Blocker/Error, {len(warnings)} Warning, {len(info)} Info, {len(suppressed)} Suppressed\n\n")
                f.write("-" * 80 + "\n\n")

                for v in violations:
                    from anchor.core.healer import suggest_fix, format_suggestion_for_report
                    sev = v['severity'].upper()
                    if sev in ["CRITICAL", "BLOCKER", "ERROR"]:
                        tag = "[[X]]"
                    elif sev == "WARNING":
                        tag = "[[!]]"
                    else:
                        tag = "[[V]]"
                    f.write(f"{tag} [{v['id']}] {v['name']} ({v['severity'].upper()})\n")
                    f.write(f"    Location: {v['file']}:{v['line']}\n")
                    f.write(f"    Message:  {v['message']}\n")
                    f.write(f"    Details:  {v.get('description', 'No further details.')}\n")
                    f.write(f"    Fix:      {v.get('mitigation', 'N/A')}\n")
                    try:
                        suggestion = suggest_fix(v)
                        if suggestion:
                            f.write(format_suggestion_for_report(suggestion) + "\n")
                    except Exception:
                        pass
                    f.write("-" * 60 + "\n")

                if suppressed:
                    f.write("\n" + "=" * 40 + "\n")
                    f.write("   SUPPRESSED FINDINGS (AUDITED)\n")
                    f.write("=" * 40 + "\n\n")
                    for s in suppressed:
                        f.write(f"[SUPPRESSED] [{s['id']}] {s['name']}\n")
                        f.write(f"    Location:   {s['file']}:{s['line']}\n")
                        f.write(f"    Authorized: {s.get('author', 'Unknown Author')}\n")
                        f.write("-" * 40 + "\n")

            # -- 2. Markdown documentation report (always) --------------------─
            with open(md_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
                scan_status = "FAILED" if failures else "PASSED"
                f.write("# Anchor Governance Audit\n\n")
                f.write(f"**Status:** {scan_status}  \n")
                f.write(f"**Timestamp:** {timestamp}  \n")
                f.write(f"**Source:** `{os.path.abspath(scan_targets[0])}`  \n\n")

                f.write("## Summary\n\n")
                f.write(f"| Category | Count |\n|---|---|\n")
                f.write(f"| Blockers / Errors | {len(failures)} |\n")
                f.write(f"| Warnings | {len(warnings)} |\n")
                f.write(f"| Info | {len(info)} |\n")
                f.write(f"| Suppressed | {len(suppressed)} |\n")
                f.write(f"| Files Scanned | {metrics.get('scanned_files', 0)} |\n\n")

                if violations:
                    f.write("## Active Violations\n\n")
                    f.write("| ID | Severity | File | Message |\n|---|---|---|---|\n")
                    for v in sorted(violations, key=lambda x: severity_map.get(x['severity'].lower(), 0), reverse=True):
                        f.write(f"| `{v['id']}` | **{v['severity'].upper()}** | `{v['file']}:{v['line']}` | {v['message']} |\n")
                    f.write("\n")

                if suppressed:
                    f.write("## Suppressed Exceptions (Audited)\n\n")
                    f.write("| ID | File | Authorized By |\n|---|---|---|\n")
                    for s in suppressed:
                        f.write(f"| `{s['id']}` | `{s['file']}:{s['line']}` | **{s.get('author', 'Unknown')}** |\n")
                    f.write("\n")

                f.write("> *Suppressed exceptions are authorized security bypasses — verify authors are correct.*\n")

            # -- 3. JSON (auto if CI/CD detected, or --json-report) ------------
            if write_json:
                with open(json_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
                    json.dump({
                        "scan_source": os.path.abspath(scan_targets[0]),
                        "timestamp": timestamp,
                        "status": "failed" if failures else "passed",
                        "violation_count": len(violations),
                        "violations": violations,
                        "suppressed": suppressed,
                        "metrics": metrics,
                    }, f, indent=2)
                if verbose or has_cicd:
                    click.secho(f"JSON report: {json_path}", fg="green")

            # -- 4. GitHub Step Summary (Ephemeral, CI-only) ------------------─
            if github_summary:
                summary_path = "anchor-summary.md"
                with open(summary_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
                    f.write("## Anchor Security & Governance Summary\n\n")
                    f.write(f"**Status:** {'FAILED' if failures else 'PASSED'}  \n")
                    f.write(f"**Findings:** {len(violations)} Active | {len(suppressed)} Suppressed\n\n")
                    if violations:
                        f.write("### Active Violations\n")
                        f.write("| ID | Severity | File | Message |\n|---|---|---|---|\n")
                        for v in violations:
                            f.write(f"| {v['id']} | {v['severity'].upper()} | `{v['file']}:{v['line']}` | {v['message']} |\n")
                        f.write("\n")
                    if suppressed:
                        f.write("### Suppressed Exceptions (Audited)\n")
                        f.write("| ID | File | Authorized By |\n|---|---|---|\n")
                        for s in suppressed:
                            f.write(f"| {s['id']} | `{s['file']}:{s['line']}` | **{s.get('author', 'Unknown')}** |\n")
                    f.write("> *Verify suppressed exception authors in the audit trail.*\n")
                if verbose: click.echo(f"CI summary: {summary_path}")

            # Force filesystem refresh for IDEs
            try:
                os.utime(dot_anchor, None)
            except: pass

            click.secho(f"\nReports written to {dot_anchor}/", fg="green", bold=True)
            if verbose:
                click.echo(f"   * Violations: {txt_path}")
                click.echo(f"   * Audit MD:   {md_path}")
                if write_json: click.echo(f"   * JSON:       {json_path}")

        except Exception as e:
            click.echo(f"WARNING: Failed to generate reports: {e}")

        # 2. Terminal Summary Output (Human-First)
        active_count = len(violations)
        severity_buckets = {"blocker": 0, "error": 0, "warning": 0, "info": 0}
        for v in violations:
            sev = v['severity'].lower()
            bucket = "blocker" if sev in ["critical", "blocker"] else sev if sev in severity_buckets else "info"
            severity_buckets[bucket] += 1

        click.secho(f"\nTOTAL FINDINGS: {active_count}", fg="yellow", bold=True)
        click.secho(f"  BLOCKER : {severity_buckets['blocker']}", fg="red" if severity_buckets["blocker"] else "white")
        click.secho(f"  ERROR   : {severity_buckets['error']}", fg="red" if severity_buckets["error"] else "white")
        click.secho(f"  WARNING : {severity_buckets['warning']}", fg="yellow" if severity_buckets["warning"] else "white")
        click.secho(f"  INFO    : {severity_buckets['info']}", fg="white")
        if suppressed:
            click.secho(f"{len(suppressed)} suppressed findings (See report for audit trail).", fg="cyan", dim=True)
        click.echo("-" * 80)
        
        # Only show the first 5 violations in terminal to avoid clutter
        display_limit = 5
        # Sort by severity (blocker first) for terminal display
        sorted_violations = sorted(violations, key=lambda x: severity_map.get(x['severity'].lower(), 0), reverse=True)
        
        for v in sorted_violations[:display_limit]:
            severity_color = "red" if v['severity'] in ['critical', 'blocker', 'error'] else "yellow"
            click.secho(f"[{v['id']}] {v['name']} ({v['severity'].upper()})", fg=severity_color, bold=True)
            click.echo(f"   Location: {v['file']}:{v['line']}")
            if v.get('mitigation'):
                click.secho(f"   Fix:      {v['mitigation']}", fg="cyan", dim=True)
            click.echo("-" * 80)
        
        if len(violations) > display_limit:
            click.secho(f"... and {len(violations)-display_limit} more findings in the report.", fg="white", dim=True)
            click.echo("-" * 80)
        
        # 5. CLEANUP (If ephemeral)
        if ephemeral_sandbox and not no_sandbox:
            if verbose:
                click.echo("\nCleaning up ephemeral Diamond Cage...")
            cage.uninstall()

        if failures:
            if hook:
                click.secho(f"\nCOMMIT BLOCKED: Anchor detected {len(failures)} violations.", fg="red", bold=True)
                click.secho(f"  To view details, run: anchor check --verbose {scan_targets[0]}", fg="white", dim=True)
            else:
                click.secho(f"\nFAILED: Found {len(failures)} critical violations.", fg="red", bold=True)
                click.secho(f"  Full details:   .anchor/violations/governance_violations.txt", fg="white", dim=True)
                click.secho(f"  Audit report:   .anchor/reports/governance_audit.md", fg="white", dim=True)

            if loaded and not loaded.verified:
                click.echo("")
                click.secho("  ┌─────────────────────────────────────────────────────┐", fg="yellow")
                click.secho("  │  UNVERIFIED — Governance integrity not confirmed.   │", fg="yellow", bold=True)
                click.secho("  │  Reports are NOT valid for regulatory submission.   │", fg="yellow")
                click.secho("  │  Run: anchor sync --restore to verify.              │", fg="yellow")
                click.secho("  └─────────────────────────────────────────────────────┘", fg="yellow")

            sys.exit(1)
        else:
            if hook:
                click.secho("\nCOMMIT ALLOWED: No blocking violations found.", fg="green", bold=True)
            else:
                click.secho("\nPASSED: No blocking violations found.", fg="green", bold=True)

            if loaded and not loaded.verified:
                click.echo("")
                click.secho("  ┌─────────────────────────────────────────────────────┐", fg="yellow")
                click.secho("  │  UNVERIFIED — Governance integrity not confirmed.   │", fg="yellow", bold=True)
                click.secho("  │  Reports are NOT valid for regulatory submission.   │", fg="yellow")
                click.secho("  │  Run: anchor sync --restore to verify.              │", fg="yellow")
                click.secho("  └─────────────────────────────────────────────────────┘", fg="yellow")

            sys.exit(0)
    else:
        click.secho("\nPASSED: Compliance Verified.", fg="green", bold=True)
        sys.exit(0)


@check.command('verify-sync')
@click.option('--fix', is_flag=True, help='Auto-sync from canonical source (anchor/core/resources/mitigation.anchor.example).')
@click.option('--verbose', '-v', is_flag=True, help='Show hash details.')
def check_verify_sync(fix, verbose):
    """
    Verify that all three copies of mitigation.anchor are identical.

    Checks:
      1. anchor/core/resources/mitigation.anchor.example  (canonical source)
      2. mitigation.anchor                                 (cloud-served root)
      3. .anchor/cache/mitigation.anchor                  (local engine cache)

    Use --fix to automatically sync all copies from the canonical source.
    """
    import hashlib
    import shutil

    def sha256(path):
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            return None

    # Locate package root for the canonical source
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    canonical    = os.path.join(package_root, "anchor", "core", "resources", "mitigation.anchor.example")
    root_copy    = "mitigation.anchor"
    cache_copy   = os.path.join(".anchor", "cache", "mitigation.anchor")

    files = {
        "canonical (resources/mitigation.anchor.example)": canonical,
        "root       (mitigation.anchor)":                   root_copy,
        "cache      (.anchor/cache/mitigation.anchor)":     cache_copy,
    }

    hashes = {label: sha256(path) for label, path in files.items()}
    canon_hash = hashes["canonical (resources/mitigation.anchor.example)"]

    click.secho("\nAnchor Mitigation Sync Check", bold=True)
    click.echo("=" * 60)

    all_synced = True
    for label, h in hashes.items():
        if h is None:
            click.secho(f"  [MISSING]  {label}", fg="red")
            all_synced = False
        elif h == canon_hash:
            status = click.style("[OK]     ", fg="green")
            click.echo(f"  {status} {label}")
            if verbose:
                click.echo(f"           SHA-256: {h[:16]}...")
        else:
            status = click.style("[MISMATCH]", fg="red", bold=True)
            click.echo(f"  {status} {label}")
            if verbose:
                click.echo(f"           Expected: {canon_hash[:16]}...")
                click.echo(f"           Got:      {h[:16]}...")
            all_synced = False

    click.echo("=" * 60)

    if all_synced:
        click.secho("\nPASSED: All copies are in sync.", fg="green", bold=True)
    else:
        if fix:
            click.secho("\nFIXING: Syncing all copies from canonical source...", fg="yellow")
            for label, path in files.items():
                if path != canonical:
                    try:
                        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                        shutil.copy2(canonical, path)
                        click.secho(f"  Synced: {path}", fg="green")
                    except Exception as e:
                        click.secho(f"  Failed to sync {path}: {e}", fg="red")
            click.secho("\nDone. Run anchor check verify-sync to confirm.", fg="green")
        else:
            click.secho("\nFAILED: Copies are out of sync. Run with --fix to auto-sync.", fg="red", bold=True)
            sys.exit(1)


@check.command('drift')
@click.argument('target', default='.')
@click.option('--repo', '-r', default='.', show_default=True,
              help='Path to the git repository root (default: current dir).')
@click.option('--limit', '-l', default=30, show_default=True,
              help='Max number of symbols to analyse (safeguard for large codebases).')
@click.option('--only-violations', is_flag=True,
              help='Only show symbols with non-ALIGNED verdicts.')
@click.option('--json', 'as_json', is_flag=True,
              help='Output results as JSON.')
@click.option('--verbose', '-v', is_flag=True, help='Show debug output.')
@click.option('--report', is_flag=True, help='Generate persistent audit reports in .anchor/.')
def check_drift(target, repo, limit, only_violations, as_json, verbose, report):
    """
    Scan for architectural drift across a codebase, directory, or file.

    Examples:\n
      anchor check drift .\n
      anchor check drift src/models.py\n
      anchor check drift anchor/core/ --only-violations\n
      anchor check drift . --json > drift-report.json
    """
    import ast as _ast
    import json as _json
    from pathlib import Path as _Path
    from anchor.core.history import HistoryEngine
    from anchor.core.contexts import extract_usages
    from anchor.core.verdicts import analyze_drift
    from anchor.core.models import CodeSymbol

    VERDICT_COLORS = {
        'aligned':            ('green',   ''),
        'intent_violation':   ('red',     ''),
        'semantic_overload':  ('yellow',  ''),
        'dependency_inertia': ('blue',    ''),
        'complexity_drift':   ('magenta', ''),
        'confidence_too_low': ('white',   ''),
    }

    # --- Collect Python files to analyse ---
    target_path = _Path(target).resolve()
    repo_path   = _Path(repo).resolve()

    if target_path.is_file():
        py_files = [target_path] if target_path.suffix == '.py' else []
    elif target_path.is_dir():
        skip_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules',
                     'dist', 'build', 'migrations', '.anchor'}
        py_files = [
            _Path(root) / f
            for root, dirs, files in os.walk(target_path)
            for f in files
            if f.endswith('.py')
            for _ in [dirs.__setitem__(slice(None), [d for d in dirs if d not in skip_dirs])]
        ]
    else:
        click.secho(f"Target not found: {target}", fg='red')
        raise SystemExit(1)

    if not py_files:
        click.secho("WARNING: No Python files found in target.", fg='yellow')
        raise SystemExit(0)

    # --- Extract all symbols from those files ---
    def extract_symbols(file_path):
        try:
            source = file_path.read_text(encoding='utf-8', errors='ignore')
            tree   = _ast.parse(source)
            syms   = []
            for node in _ast.walk(tree):
                if isinstance(node, (_ast.ClassDef, _ast.FunctionDef)):
                    sym_type = 'class' if isinstance(node, _ast.ClassDef) else 'function'
                    rel      = os.path.relpath(str(file_path), str(repo_path))
                    syms.append(CodeSymbol(
                        name=node.name, type=sym_type,
                        file_path=rel, line_number=node.lineno,
                    ))
            return syms
        except Exception:
            return []

    all_symbols = []
    for f in py_files:
        all_symbols.extend(extract_symbols(f))

    if not all_symbols:
        click.secho("WARNING: No symbols (classes/functions) found.", fg='yellow')
        raise SystemExit(0)

    # Apply limit
    if len(all_symbols) > limit:
        click.secho(
            f"Found {len(all_symbols)} symbols. Analysing first {limit} "
            f"(use --limit to change).", fg='yellow'
        )
        all_symbols = all_symbols[:limit]

    # --- Run drift analysis on each symbol ---
    history_engine = HistoryEngine(str(repo_path))
    results = []
    json_results = []

    with click.progressbar(all_symbols, label="Analyzing Security Posture",
                           fill_char='#', empty_char='.') as bar:
        for symbol in bar:
            anchor = history_engine.find_anchor(symbol)
            if not anchor:
                continue
            contexts = extract_usages(str(repo_path), symbol.name)
            result   = analyze_drift(symbol.name, anchor, contexts)
            # Attach metadata for reporting
            result.file_path = symbol.file_path
            result.line_number = symbol.line_number

            # Filter if --only-violations
            if only_violations and result.verdict.value == 'aligned':
                continue

            results.append(result)
            json_results.append({
                'symbol':   result.symbol,
                'file':     symbol.file_path,
                'line':     symbol.line_number,
                'verdict':  result.verdict.value,
                'rationale': result.rationale,
                'evidence': result.evidence,
                'anchor': {
                    'commit':     result.anchor.commit_sha[:7],
                    'date':       str(result.anchor.commit_date.date()),
                    'confidence': result.anchor.confidence.value,
                },
            })

    # --- Output ---
    click.echo()
    if as_json and not results:
        click.echo(_json.dumps([], indent=2))
        raise SystemExit(0)

    if not results:
        click.secho("No drift detected across the scanned codebase.", fg='green', bold=True)
        raise SystemExit(0)

    # CI/CD detection
    has_cicd = os.path.isdir(".github") or os.path.isdir(".gitlab-ci")
    dot_anchor = ".anchor"

    # --- Partition results ---
    drift_violations = [r for r in results if r.verdict.value != 'aligned']
    aligned          = [r for r in results if r.verdict.value == 'aligned']

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -- 1. Plain-text dump (always) ------------------------------------------─
    txt_path = os.path.join(dot_anchor, "violations", "drift_violations.txt")
    md_path  = os.path.join(dot_anchor, "reports", "drift_audit.md")
    json_path = os.path.join(dot_anchor, "telemetry", "drift_report.json")
    try:
        os.makedirs(os.path.join(dot_anchor, "violations"), exist_ok=True)
        os.makedirs(os.path.join(dot_anchor, "reports"), exist_ok=True)
        os.makedirs(os.path.join(dot_anchor, "telemetry"), exist_ok=True)

        with open(txt_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
            f.write("=" * 80 + "\n")
            f.write("   ANCHOR DRIFT VIOLATIONS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Target:    {target_path}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Symbols:   {len(results)} analyzed, {len(drift_violations)} violations, {len(aligned)} aligned\n\n")
            f.write("-" * 80 + "\n\n")
            for r in results:
                verdict = r.verdict.value
                if verdict == 'aligned':
                    tag = "[[V]]"
                elif verdict in ('intent_violation', 'semantic_overload'):
                    tag = "[[X]]"
                else:
                    tag = "[[!]]"
                f.write(f"{tag} {r.symbol} [{r.verdict.value.upper().replace('_', ' ')}]\n")
                f.write(f"   Location:  {getattr(r, 'file_path', 'unknown')}:{getattr(r, 'line_number', '0')}\n")
                f.write(f"   Rationale: {r.rationale}\n")
                if r.evidence:
                    for e in r.evidence:
                        f.write(f"   · {e}\n")
                f.write("\n")

        # -- 2. Markdown report (always) --------------------------------------─
        with open(md_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
            f.write("# Anchor Architectural Drift Audit\n\n")
            f.write(f"**Status:** {'DRIFT DETECTED' if drift_violations else 'NO DRIFT'}  \n")
            f.write(f"**Timestamp:** {timestamp}  \n")
            f.write(f"**Target:** `{target_path}`  \n\n")

            f.write("## Summary\n\n")
            f.write(f"| Category | Count |\n|---|---|\n")
            f.write(f"| Aligned | {len(aligned)} |\n")
            f.write(f"| Drift Violations | {len(drift_violations)} |\n")
            f.write(f"| Total Analyzed | {len(results)} |\n\n")

            if drift_violations:
                f.write("## Drift Violations\n\n")
                f.write("| Symbol | Verdict | Rationale |\n|---|---|---|\n")
                for r in drift_violations:
                    f.write(f"| `{r.symbol}` | **{r.verdict.value.replace('_', ' ').title()}** | {r.rationale[:100]} |\n")
                f.write("\n")

                f.write("## Detailed Findings\n\n")
                for r in drift_violations:
                    verdict_label = r.verdict.value.replace('_', ' ').title()
                    f.write(f"### `{r.symbol}`\n\n")
                    f.write(f"**Verdict:** {verdict_label}  \n")
                    f.write(f"**Rationale:** {r.rationale}  \n")
                    if r.anchor:
                        f.write(f"**Anchored at:** commit `{r.anchor.commit_sha[:7]}` ({str(r.anchor.commit_date.date())})  \n")
                    if r.evidence:
                        f.write("\n**Evidence:**\n")
                        for e in r.evidence:
                            f.write(f"- {e}\n")
                    f.write("\n")

            if aligned:
                f.write("## Aligned Symbols\n\n")
                f.write(", ".join(f"`{r.symbol}`" for r in aligned) + "\n\n")

            f.write("> *This report was generated by Anchor. Use it for code review, release notes, or governance documentation.*\n")

        # -- 3. JSON (auto if CI/CD detected or --json flag) ------------------─
        if as_json or has_cicd:
            with open(json_path, "w", encoding="utf-8") as f:  # anchor: ignore ANC-007
                _json.dump(json_results, f, indent=2)
            if as_json:
                # Also print to stdout for pipe-ability
                click.echo(_json.dumps(json_results, indent=2))
            elif verbose or has_cicd:
                click.secho(f"JSON report: {json_path}", fg="green")

        click.secho(f"\nReports written to {dot_anchor}/", fg="green", bold=True)
        if verbose:
            click.echo(f"   * Violations: {txt_path}")
            click.echo(f"   * Audit MD:   {md_path}")
            if as_json or has_cicd: click.echo(f"   * JSON:       {json_path}")

    except Exception as e:
        click.secho(f"WARNING: Failed to write drift reports: {e}", fg="yellow")

    # -- Terminal summary (always) ----------------------------------------------
    click.echo("=" * 70)
    click.secho("ANCHOR DRIFT REPORT", bold=True)
    click.echo("=" * 70)
    click.secho(f"  Aligned:    {len(aligned)}", fg='green')
    click.secho(f"  Violations: {len(drift_violations)}", fg='red' if drift_violations else 'green')
    click.echo("=" * 70)
    click.echo()

    for result in results:
        color, _ = VERDICT_COLORS.get(result.verdict.value, ('white', ''))
        click.secho(
            f"{result.symbol}  [{result.verdict.value.upper().replace('_', ' ')}]",
            fg=color, bold=True
        )
        click.secho(f"   {result.rationale[:120]}", fg=color, dim=True)
        if result.evidence:
            for e in result.evidence[:3]:
                click.echo(f"   · {e}")
        if result.remediation and not only_violations:
            click.secho("   Remediation available (run with single symbol for full details)",
                        fg=color)
        click.echo()

    # Exit non-zero if any violations found
    if drift_violations:
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# anchor heal
# ---------------------------------------------------------------------------

@cli.command("heal")
@click.argument("paths", nargs=-1, default=None)
@click.option("--apply", "apply_fixes", is_flag=True,
              help="Apply all auto-fixable suggestions in-place (use with care).")
@click.option("--verbose", "-v", is_flag=True, help="Show details for every violation.")
def heal(paths, apply_fixes, verbose):
    """
    Review and optionally apply Anchor's suggested fixes.

    Reads violations from the last 'anchor check' run and shows
    diff-style fix suggestions for each. Auto-fixable issues can be
    patched in-place with --apply.

    Examples:\n
      anchor heal                    # show all suggestions\n
      anchor heal src/agent.py       # suggestions for one file\n
      anchor heal . --apply          # apply all auto-fixable fixes\n
    """
    from anchor.core.healer import suggest_fix, apply_fix

    dot_anchor   = ".anchor"
    txt_path     = os.path.join(dot_anchor, "violations", "governance_violations.txt")
    json_path    = os.path.join(dot_anchor, "telemetry",  "governance_report.json")

    # -- Load violations from the last run ------------------------------------
    violations = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:  # anchor: ignore ANC-007
                data = json.load(f)
                violations = data.get("violations", [])
        except Exception as e:
            click.secho(f"WARNING: Could not read telemetry: {e}", fg="yellow")

    if not violations:
        if os.path.exists(txt_path):
            click.secho("No JSON telemetry found — run 'anchor check .' first to generate it.", fg="yellow")
        else:
            click.secho("No violations found. Nothing to heal.", fg="green")
        raise SystemExit(0)

    # -- Filter by path if specified ------------------------------------------─
    if paths:
        norm = [os.path.normpath(p) for p in paths]
        violations = [
            v for v in violations
            if any(os.path.normpath(v.get("file", "")).startswith(n) for n in norm)
        ]
        if not violations:
            click.secho(f"No violations in the specified path(s).", fg="green")
            raise SystemExit(0)

    # -- Build suggestions ----------------------------------------------------─
    suggestions = []
    for v in violations:
        s = suggest_fix(v)
        if s:
            suggestions.append((v, s))

    if not suggestions:
        click.secho("No fix suggestions available.", fg="green")
        raise SystemExit(0)

    auto_fixable = [(v, s) for v, s in suggestions if s.auto_fixable]
    manual_only  = [(v, s) for v, s in suggestions if not s.auto_fixable]

    click.echo()
    click.secho(f"Anchor Heal: {len(suggestions)} suggestion(s) found", bold=True)
    click.secho(f"   [V] Auto-fixable: {len(auto_fixable)}   [!] Manual: {len(manual_only)}", fg="cyan")
    click.echo("=" * 70)

    applied = 0
    for v, s in suggestions:
        color = "red" if v["severity"] in ["blocker", "critical", "error"] else "yellow"
        click.echo()
        click.secho(f"[{s.rule_id}] {v['name']} ({v['severity'].upper()})", fg=color, bold=True)
        click.echo(f"  File: {s.file}:{s.line}")
        click.echo(f"  {s.explanation}")

        if s.original:
            click.secho(f"  - {s.original}", fg="red")
        if s.suggested and s.suggested != s.original:
            click.secho(f"  + {s.suggested}", fg="green")

        if not s.auto_fixable:
            click.secho("  [!]  Manual fix required.", fg="yellow", dim=True)
        elif apply_fixes:
            ok = apply_fix(s)
            if ok:
                applied += 1
                click.secho(f"  Applied fix to {s.file}:{s.line}", fg="green")
            else:
                click.secho(f"  Could not apply fix automatically.", fg="red")
        else:
            click.secho(f"  Run with --apply to patch this automatically.", fg="cyan", dim=True)

    click.echo()
    click.echo("=" * 70)
    if apply_fixes and applied > 0:
        click.secho(f"\nApplied {applied} fix(es). Run 'anchor check .' to verify.", fg="green", bold=True)
    elif apply_fixes and applied == 0:
        click.secho("\nNo fixes were applied (no auto-fixable issues or apply failed).", fg="yellow")
    else:
        click.secho(f"\n  To apply all auto-fixable fixes, run: anchor heal --apply", fg="cyan")
        click.secho(f"  Detailed fix suggestions also in: {txt_path}", fg="white", dim=True)


cli.add_command(init)
cli.add_command(heal)

if __name__ == '__main__':
    cli()
