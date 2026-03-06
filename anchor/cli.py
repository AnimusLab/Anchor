import click
import subprocess  # anchor: ignore RI-12-SUBPROCESS
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
@click.option('--sandbox', is_flag=True, help='Install Diamond Cage (WASM sandbox) for secure execution.')
@click.option('--policy-name', default='policy.anchor', help='Name for your project policy file (e.g., jpmorgan.anchor)')
def init(sandbox, policy_name):
    """Initializes Anchor using the V3 modular directory architecture (.anchor/)."""
    import shutil  # anchor: ignore RI-08-SHUTIL
    
    # 1. Create Visible .anchor Directory Structure
    # This directory is intended to be visible like .github/
    dot_anchor = ".anchor"
    branding_dir = os.path.join(dot_anchor, "branding")
    cache_dir = os.path.join(dot_anchor, "cache")
    reports_dir = os.path.join(dot_anchor, "reports")
    violation_dir = os.path.join(dot_anchor, "violations")
    telemetry_dir = os.path.join(dot_anchor, "telemetry")
    
    for d in [dot_anchor, branding_dir, cache_dir, reports_dir, violation_dir, telemetry_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    # 2. Clean Sweep: Remove legacy root-level files if they exist
    # This ensures a single source of truth inside .anchor/
    legacy_files = [
        policy_name, 
        "constitution.anchor.example", "constitution.anchor",
        "mitigation.anchor.example", "mitigation.anchor"
    ]
    for f in legacy_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                if verbose := os.environ.get("ANCHOR_VERBOSE"):  # anchor: ignore ANC-023
                    click.echo(f"   Removed legacy file from root: {f}")
            except Exception:
                pass

    # 3. Deploy Assets exclusively into .anchor/
    package_root = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(package_root, "core", "resources")
    
    # Copy Logo
    logo_src = os.path.join(resources_dir, "logo.png")
    logo_dst = os.path.join(branding_dir, "logo.png")
    if os.path.exists(logo_src):
        shutil.copy2(logo_src, logo_dst)
        click.secho("Anchor Branding Initialized (.anchor/branding)", fg="cyan")

    # Universal Governance (INSIDE .anchor)
    resources = [
        ("constitution.anchor.example", "constitution.anchor.example"),
        ("mitigation.anchor.example", "mitigation.anchor.example")
    ]
    for src_name, dst_name in resources:
        ref_src = os.path.join(resources_dir, src_name)
        ref_dst = os.path.join(dot_anchor, dst_name)
        if os.path.exists(ref_src):
            shutil.copy2(ref_src, ref_dst)
            click.secho(f"Deployed reference: {ref_dst}", fg="green")

    # 3. Create Local Project Policy (INSIDE .anchor)
    target_policy = os.path.join(dot_anchor, policy_name)
    if not os.path.exists(target_policy):
        project_template = f'''# =============================================================================
# {policy_name.replace('.anchor', '').upper()} - Project Policy
# =============================================================================
# This file is for YOUR project-specific rules. 
# It is AUTOMATICALLY IGNORED by git to protect company policies.
#
# Reference universal rules in '.anchor/constitution.anchor.example'
# =============================================================================

version: "3.0.0-alpha"

metadata:
  project: "{os.path.basename(os.getcwd())}"
  
rules:
  # Add your rules here
'''
        with open(target_policy, "w", encoding="utf-8") as f:
            f.write(project_template)  # anchor: ignore RI-08
        # anchor: ignore RI-08
        click.secho(f"Created project policy: {target_policy}", fg="green")
    else:
        click.secho(f"  '{target_policy}' already exists.", fg="blue")

    # 4. Automate .gitignore
    gitignore_path = ".gitignore"
    # ONLY ignore the sensitive policy, the cache, reports, and branding assets
    rules_to_ignore = [
        f"/{dot_anchor}/{policy_name}",
        f"/{dot_anchor}/cache/",
        f"/{dot_anchor}/violations/",
        f"/{dot_anchor}/telemetry/",
        f"/{dot_anchor}/branding/"
    ]
    
    try:
        content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:  # anchor: ignore RI-08
                content = f.read()
        
        needed = [r for r in rules_to_ignore if r not in content]
        if needed:
            with open(gitignore_path, "a") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write("\n# Anchor Security & Governance (Local Settings)\n")
                for r in needed:
                    f.write(f"{r}\n")  # anchor: ignore RI-08
            click.secho("Updated .gitignore to protect local policies.", fg="cyan")
    except Exception as e:
        click.secho(f"WARNING: Could not update .gitignore: {e}", fg="yellow")

    # 4.5 Install Git Pre-Commit Hook (The Guardrail)
    if os.path.exists(".git"):
        hooks_dir = os.path.join(".git", "hooks")
        if not os.path.exists(hooks_dir):
            os.makedirs(hooks_dir)
        
        # --- Pre-Commit Hook (Targeted Scanning) ---
        pre_commit_path = os.path.join(hooks_dir, "pre-commit")
        pre_commit_content = """#!/bin/sh
# Anchor Git Hook: Targeted compliance scan for staged files
echo "[Anchor] Checking staged files for compliance..."

# 1. Identify staged Python/TypeScript files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|ts|tsx)$')

if [ -z "$STAGED_FILES" ]; then
  echo "No relevant files staged. Skipping Anchor scan."
  exit 0
fi

# 2. Run targeted scan
python -m anchor check --severity error --hook $STAGED_FILES
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "Commit Blocked: Anchor detected compliance violations in staged code."
  echo "  See .anchor/violations/violation_report.txt for full audit trail."
  exit 1
fi
"""
        
        try:
            with open(pre_commit_path, "w") as f:
                f.write(pre_commit_content)  # anchor: ignore RI-08
            try: os.chmod(pre_commit_path, 0o755)
            except: pass
            
            click.secho("Installed Git pre-commit hook (Local AI Guardrail).", fg="cyan")
        except Exception as e:
            click.secho(f"WARNING: Could not install Git hook: {e}", fg="yellow")

    # 5. Optionally install Diamond Cage
    if sandbox:
        click.secho("\nInstalling Diamond Cage...", fg="cyan", bold=True)
        from anchor.core.sandbox import install_diamond_cage
        install_diamond_cage()
    
    # Summary
    click.echo("\n" + "=" * 60)
    click.secho("ANCHOR INITIALIZED (v2.4.15 Architecture)", fg="green", bold=True)
    click.echo("=" * 60)
    click.echo("Anchor Assets (see .anchor/):")
    click.echo(f"  constitution.anchor.example  -> Governance Rules Reference")
    click.echo(f"  mitigation.anchor.example    -> Detection Patterns Reference")
    click.echo(f"  {policy_name}                → Your project rules (used for audits)")
    click.echo(f"  branding/                   -> Anchor Identity")
    click.echo("")
    click.echo("How audits work:")
    click.echo("  Universal Constitution  -> Fetched from cloud (tamper-proof)")
    click.echo(f"  {policy_name}           → Your local rules (merged with universal)")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  1. Review governance: .anchor/constitution.anchor.example")
    click.echo(f"  2. Review patterns:   .anchor/mitigation.anchor.example")
    click.echo(f"  2. Edit your rules: .anchor/{policy_name}")
    click.echo("  3. Run: anchor check")
    click.echo("=" * 60)



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

    # Governance Files to sync and verify (V3: Constitution only for now, patterns are local/built-in)
    governance_targets = [
        ("Constitution", get_constitution_url(), "constitution.anchor", CONSTITUTION_SHA256),
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
                    click.secho(f"WARNING: {label} sync failed, using verified cache.", fg="yellow")
                    if verbose: click.echo(f"   {msg}")
                else:
                    click.secho(f"\n{msg}", fg="red", bold=True)
                    click.secho(f"   Cannot audit with a tampered {label.lower()}.", fg="red")
                    sys.exit(1)
            else:
                click.secho(f"ERROR: Could not fetch {label.lower()} and no cache found: {e}", fg="red")
                sys.exit(1)

    # 1.5. THE RISK CATALOG LOADER (V3 Modular System)
    # We load all .yaml / .anchor files from the /patterns directory
    master_rules = []
    package_root = os.path.dirname(os.path.abspath(__file__))
    patterns_dir = os.path.join(os.path.dirname(package_root), "patterns")
    
    if os.path.exists(patterns_dir):
        if verbose: click.echo(f"   Loading risk catalogs from {patterns_dir}...")
        for root, _, files in os.walk(patterns_dir):
            for file in files:
                if file.endswith((".yaml", ".anchor")) and "example" not in file:
                    p_path = os.path.join(root, file)
                    try:
                        with open(p_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            # Handle both 'risks' and 'rules' keys for backward compatibility
                            catalog_rules = data.get("risks") or data.get("rules") or []
                            master_rules.extend(catalog_rules)
                            if verbose: click.echo(f"      + {file} ({len(catalog_rules)} rules)")
                    except Exception as e:
                        if verbose: click.echo(f"      ! Failed to load {file}: {e}")

    # Fallback to legacy joiner if patterns are missing (Backward Compatibility)
    if not master_rules:
        constitution_path = os.path.join(cache_dir, "constitution.anchor")
        mitigation_path = os.path.join(cache_dir, "mitigation.anchor")

        if os.path.exists(constitution_path) and os.path.exists(mitigation_path):
            try:
                with open(constitution_path, "r", encoding="utf-8") as f:
                    c_data = yaml.safe_load(f) or {}
                    c_rules = {r["id"]: r for r in c_data.get("rules", []) if "id" in r}
                
                with open(mitigation_path, "r", encoding="utf-8") as f:
                    m_data = yaml.safe_load(f) or {}
                    m_list = m_data.get("mitigations", [])

                for m in m_list:
                    r_id = m.get("rule_id")
                    if r_id in c_rules:
                        rule_meta = c_rules[r_id]
                        exec_rule = rule_meta.copy()
                        exec_rule["mitigation_id"] = m["id"]
                        exec_rule["match"] = m["match"]
                        exec_rule["name"] = f"{rule_meta['name']} ({m['name']})"
                        if "message" in m:
                            exec_rule["message"] = m["message"]
                        master_rules.append(exec_rule)
            except Exception as e:
                click.secho(f"WARNING: Failed to join legacy governance files: {e}", fg="yellow")

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
            with open(report_path, "w") as f:  # anchor: ignore RI-08
                f.write(f"# Model Audit Report: {model}\n\nStatus: {result.status.value.upper()}\n")
                f.write(f"Passed: {result.checks_passed}/{result.checks_total}\n\n")
                f.write("## Recommendation\n" + result.recommendation + "\n")
            click.secho(f"Report saved: {report_path}", fg="green")

    # --- Code Scanning Phase ---
    click.secho(f"Scanning {len(scan_targets)} target(s) with {len(final_config['rules'])} active laws...", fg="yellow")

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

    # Determine if we are in a CI/CD repo (auto-JSON)
    has_cicd = os.path.isdir(".github") or os.path.isdir(".gitlab-ci")
    write_json = json_report or has_cicd

    if violations or metrics:
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
            # ── 1. Plain-text violation dump (always) ─────────────────────────
            with open(txt_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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
                        tag = "[✗]"
                    elif sev == "WARNING":
                        tag = "[⚠]"
                    else:
                        tag = "[✔]"
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

            # ── 2. Markdown documentation report (always) ─────────────────────
            with open(md_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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

            # ── 3. JSON (auto if CI/CD detected, or --json-report) ────────────
            if write_json:
                with open(json_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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

            # ── 4. GitHub Step Summary (Ephemeral, CI-only) ───────────────────
            if github_summary:
                summary_path = "anchor-summary.md"
                with open(summary_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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
                click.echo(f"   • Violations: {txt_path}")
                click.echo(f"   • Audit MD:   {md_path}")
                if write_json: click.echo(f"   • JSON:       {json_path}")

        except Exception as e:
            click.echo(f"WARNING: Failed to generate reports: {e}")

        # 2. Terminal Summary Output (Human-First)
        active_count = len(violations)
        click.secho(f"\nTOTAL FINDINGS: {active_count} active violations.", fg="yellow", bold=True)
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
            
            sys.exit(1)
        else:
            if hook:
                click.secho("\nCOMMIT ALLOWED: No blocking violations found.", fg="green", bold=True)
            else:
                click.secho("\nPASSED: No blocking violations found.", fg="green", bold=True)
            sys.exit(0)
    else:
        click.secho("\nPASSED: Compliance Verified.", fg="green", bold=True)
        sys.exit(0)


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
    else:
        click.secho(f"Found {len(all_symbols)} symbols to analyse.", fg='cyan')

    # --- Run drift analysis on each symbol ---
    history_engine = HistoryEngine(str(repo_path))
    results = []
    json_results = []

    with click.progressbar(all_symbols, label="Analyzing Security Posture",
                           fill_char='█', empty_char='░') as bar:
        for symbol in bar:
            anchor = history_engine.find_anchor(symbol)
            if not anchor:
                continue
            contexts = extract_usages(str(repo_path), symbol.name)
            result   = analyze_drift(symbol.name, anchor, contexts)

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

    # ── 1. Plain-text dump (always) ───────────────────────────────────────────
    txt_path = os.path.join(dot_anchor, "violations", "drift_violations.txt")
    md_path  = os.path.join(dot_anchor, "reports", "drift_audit.md")
    json_path = os.path.join(dot_anchor, "telemetry", "drift_report.json")
    try:
        os.makedirs(os.path.join(dot_anchor, "violations"), exist_ok=True)
        os.makedirs(os.path.join(dot_anchor, "reports"), exist_ok=True)
        os.makedirs(os.path.join(dot_anchor, "telemetry"), exist_ok=True)

        with open(txt_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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
                    tag = "[✔]"
                elif verdict in ('intent_violation', 'semantic_overload'):
                    tag = "[✗]"
                else:
                    tag = "[⚠]"
                f.write(f"{tag} {r.symbol} [{r.verdict.value.upper().replace('_', ' ')}]\n")
                f.write(f"   Rationale: {r.rationale}\n")
                if r.evidence:
                    for e in r.evidence:
                        f.write(f"   · {e}\n")
                f.write("\n")

        # ── 2. Markdown report (always) ───────────────────────────────────────
        with open(md_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
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

        # ── 3. JSON (auto if CI/CD detected or --json flag) ───────────────────
        if as_json or has_cicd:
            with open(json_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
                _json.dump(json_results, f, indent=2)
            if as_json:
                # Also print to stdout for pipe-ability
                click.echo(_json.dumps(json_results, indent=2))
            elif verbose or has_cicd:
                click.secho(f"JSON report: {json_path}", fg="green")

        click.secho(f"\nReports written to {dot_anchor}/", fg="green", bold=True)
        if verbose:
            click.echo(f"   • Violations: {txt_path}")
            click.echo(f"   • Audit MD:   {md_path}")
            if as_json or has_cicd: click.echo(f"   • JSON:       {json_path}")

    except Exception as e:
        click.secho(f"WARNING: Failed to write drift reports: {e}", fg="yellow")

    # ── Terminal summary (always) ──────────────────────────────────────────────
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

    # ── Load violations from the last run ────────────────────────────────────
    violations = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:  # anchor: ignore RI-08
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

    # ── Filter by path if specified ───────────────────────────────────────────
    if paths:
        norm = [os.path.normpath(p) for p in paths]
        violations = [
            v for v in violations
            if any(os.path.normpath(v.get("file", "")).startswith(n) for n in norm)
        ]
        if not violations:
            click.secho(f"No violations in the specified path(s).", fg="green")
            raise SystemExit(0)

    # ── Build suggestions ─────────────────────────────────────────────────────
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
    click.secho(f"   ✓ Auto-fixable: {len(auto_fixable)}   ⚠ Manual: {len(manual_only)}", fg="cyan")
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
            click.secho("  ⚠  Manual fix required.", fg="yellow", dim=True)
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
