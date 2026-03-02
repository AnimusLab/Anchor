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
@click.option('--sandbox', is_flag=True, help='Install Diamond Cage (WASM sandbox) for secure execution.')
@click.option('--policy-name', default='policy.anchor', help='Name for your project policy file (e.g., jpmorgan.anchor)')
def init(sandbox, policy_name):
    """Initializes Anchor using the v2.4.3 visible directory architecture (.anchor/)."""
    import shutil  # anchor: ignore RI-08-SHUTIL
    
    # 1. Create Visible .anchor Directory Structure
    # This directory is intended to be visible like .github/
    dot_anchor = ".anchor"
    branding_dir = os.path.join(dot_anchor, "branding")
    cache_dir = os.path.join(dot_anchor, "cache")
    
    for d in [dot_anchor, branding_dir, cache_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    # 2. Clean Sweep: Remove legacy root-level files if they exist
    # This ensures a single source of truth inside .anchor/
    legacy_files = [
        policy_name, 
        "constitution.anchor.example", "constitution.anchor",
        "mitigation.anchor.example", "mitigation.anchor",
        "finos-master.anchor.example", "finos-master.anchor"
    ]
    for f in legacy_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                if verbose := os.environ.get("ANCHOR_VERBOSE"):  # anchor: ignore ANC-023
                    click.echo(f"   🧹 Removed legacy file from root: {f}")
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
        click.secho("🎨 Anchor Branding Initialized (.anchor/branding)", fg="cyan")

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
            click.secho(f"✅ Deployed reference: {ref_dst}", fg="green")

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

version: "2.4.14"

metadata:
  project: "{os.path.basename(os.getcwd())}"
  
rules:
  # Add your rules here
'''
        with open(target_policy, "w", encoding="utf-8") as f:
            f.write(project_template)  # anchor: ignore RI-08
        # anchor: ignore RI-08
        click.secho(f"✅ Created project policy: {target_policy}", fg="green")
    else:
        click.secho(f"ℹ️  '{target_policy}' already exists.", fg="blue")

    # 4. Automate .gitignore
    gitignore_path = ".gitignore"
    # ONLY ignore the sensitive policy, the cache, reports, and branding assets
    rules_to_ignore = [
        f"/{dot_anchor}/{policy_name}",
        f"/{dot_anchor}/cache/",
        f"/{dot_anchor}/violation_report.txt",
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
            click.secho("🛡️ Updated .gitignore to protect local policies.", fg="cyan")
    except Exception as e:
        click.secho(f"⚠️  Could not update .gitignore: {e}", fg="yellow")

    # 4.5 Install Git Pre-Commit Hook (The Guardrail)
    if os.path.exists(".git"):
        hooks_dir = os.path.join(".git", "hooks")
        if not os.path.exists(hooks_dir):
            os.makedirs(hooks_dir)
        
        # --- Pre-Commit Hook (Stop the commit) ---
        pre_commit_path = os.path.join(hooks_dir, "pre-commit")
        pre_commit_content = """#!/bin/sh
# Anchor Git Hook: Block commits with high-severity violations
echo "⚓ [Anchor] Checking local compliance before commit..."
python -m anchor check --severity error --hook
if [ $? -ne 0 ]; then
  echo "🚫 Commit Blocked: Anchor detected compliance violations."
  echo "👉 See .anchor/violation_report.txt for details."
  exit 1
fi
"""
        
        try:
            with open(pre_commit_path, "w") as f:
                f.write(pre_commit_content)  # anchor: ignore RI-08
            try: os.chmod(pre_commit_path, 0o755)
            except: pass
            
            click.secho("🛡️ Installed Git pre-commit hook (Local AI Guardrail).", fg="cyan")
        except Exception as e:
            click.secho(f"⚠️  Could not install Git hook: {e}", fg="yellow")

    # 5. Optionally install Diamond Cage
    if sandbox:
        click.secho("\n💎 Installing Diamond Cage...", fg="cyan", bold=True)
        from anchor.core.sandbox import install_diamond_cage
        install_diamond_cage()
    
    # Summary
    click.echo("\n" + "=" * 60)
    click.secho("🎯 ANCHOR INITIALIZED (v2.4.15 Architecture)", fg="green", bold=True)
    click.echo("=" * 60)
    click.echo("Anchor Assets (see .anchor/):")
    click.echo(f"  📖 constitution.anchor.example  → Governance Rules Reference")
    click.echo(f"  📖 mitigation.anchor.example    → Detection Patterns Reference")
    click.echo(f"  📝 {policy_name}                → Your project rules (used for audits)")
    click.echo(f"  🎨 branding/                   → Anchor Identity")
    click.echo("")
    click.echo("How audits work:")
    click.echo("  🌐 Universal Constitution  → Fetched from cloud (tamper-proof)")
    click.echo(f"  📝 {policy_name}           → Your local rules (merged with universal)")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  1. Review governance: .anchor/constitution.anchor.example")
    click.echo(f"  2. Review patterns:   .anchor/mitigation.anchor.example")
    click.echo(f"  2. Edit your rules: .anchor/{policy_name}")
    click.echo("  3. Run: anchor check")
    click.echo("=" * 60)



@cli.group('check', invoke_without_command=True)
@click.option('--policy', '-p', multiple=True, help='Policy file(s) to apply.')
@click.argument('path', required=False)
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
def check(ctx, policy, path, dir, model, metadata, context, server_mode, generate_report, json_report, verbose, no_sandbox, severity, hook, exclude, github_summary):
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
            if verbose: click.secho("💎 Diamond Cage (WASM Sandbox) not found. Initializing...", fg="cyan")
            success = install_diamond_cage(verbose=verbose)
            if not success:
                if verbose: click.secho("⚠️  Sandbox initialization failed. Falling back to host execution.", fg="yellow")
            else:
                ephemeral_sandbox = True
                if verbose: click.secho("✅ Sandbox Ready!", fg="green")
        else:
            if verbose:
                click.secho("💎 Using Diamond Cage (WASM Sandbox) for isolation.", fg="cyan")

    # 1. GATHER THE FEDERATION
    dot_anchor = ".anchor"
    cache_dir = os.path.join(dot_anchor, "cache")
    active_policies = []

    # Governance Files to sync and verify
    governance_targets = [
        ("Constitution", get_constitution_url(), "constitution.anchor", CONSTITUTION_SHA256),
        ("Mitigation", get_mitigation_url(), "mitigation.anchor", MITIGATION_SHA256)
    ]

    for label, url, filename, expected_hash in governance_targets:
        target_path = os.path.join(cache_dir, filename)
        if verbose: click.secho(f"☁️ Syncing {label}...", fg="blue")
        
        try:
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            with urllib.request.urlopen(url, timeout=settings.fetch_timeout) as response:
                content = response.read().decode('utf-8')
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Integrity Verification
            is_valid, msg = verify_integrity(target_path, expected_hash)
            if is_valid:
                # Note: We DON'T add to active_policies here. 
                # These are joined into master_rules below.
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
                    click.secho(f"⚠️  {label} sync failed, using verified cache.", fg="yellow")
                    if verbose: click.echo(f"   {msg}")
                    # Note: We DON'T add to active_policies here.
                else:
                    click.secho(f"\n{msg}", fg="red", bold=True)
                    click.secho(f"   Cannot audit with a tampered {label.lower()}.", fg="red")
                    sys.exit(1)
            else:
                click.secho(f"❌ Critical Error: Could not fetch {label.lower()} and no cache found: {e}", fg="red")
                sys.exit(1)

    # 1.5. THE GOVERNANCE JOINER
    # We join constitution.anchor (WHAT) with mitigation.anchor (HOW)
    master_rules = []
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

            # Join: One rule can have multiple mitigations (each becomes an executable rule)
            for m in m_list:
                r_id = m.get("rule_id")
                if r_id in c_rules:
                    rule_meta = c_rules[r_id]
                    # Create the executable rule
                    exec_rule = rule_meta.copy()
                    exec_rule["mitigation_id"] = m["id"]
                    exec_rule["match"] = m["match"]
                    exec_rule["name"] = f"{rule_meta['name']} ({m['name']})"
                    if "message" in m:
                        exec_rule["message"] = m["message"]
                    master_rules.append(exec_rule)
            
            if verbose: click.echo(f"⚓ Federated {len(master_rules)} executable rules from 23 risks.")
        except Exception as e:
            click.secho(f"⚠️  Failed to join governance files: {e}", fg="yellow")

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
            
            # Discover any .anchor that isn't master or example
            root_anchors = [f for f in os.listdir(s_dir) if f.endswith('.anchor') and "constitution" not in f]
            if root_anchors:
                active_policies.append(os.path.join(s_dir, root_anchors[0]))
                if verbose: click.echo(f"   📂 Auto-detected project policy: {active_policies[-1]}")
                found = True
                break
    
    if not active_policies:
        click.secho("❌ No policies found! Run 'anchor init' first.", fg="red")
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
        except Exception as e:
            if verbose: click.secho(f"❌ Failed to parse {p_file}: {e}", fg="red")

    final_config = {"rules": merged_rules}

    # === NEW: GenAI THREAT MODEL INTEGRATION ===
    if context:
        from anchor.core.markdown_parser import MarkdownPolicyParser
        from anchor.core.mapper import PolicyMapper
        click.secho(f"\n🤖 [BRIDGE] Parsing GenAI Threat Model: {context}", fg="cyan", bold=True)
        md_parser = MarkdownPolicyParser()
        detected_risks = md_parser.parse_file(context)
        if detected_risks:
            policy_mapper = PolicyMapper()
            # Filter the rules based on detected risks
            final_config["rules"] = policy_mapper.get_rules_for_ids(list(detected_risks))
            click.secho(f"   ✅ Activated {len(final_config['rules'])} dynamic enforcement rules\n", fg="green")

    # 3. RUN ENFORCEMENT
    violations = []
    
    if model:
        # Use Sandbox for Model Audit Weight analysis if enabled
        from anchor.core.model_auditor import ModelAuditor
        click.secho(f"\n🔍 Auditing Model Weights: {model}", fg="cyan", bold=True)
        
        # Pass sandbox status to auditor
        auditor = ModelAuditor(final_config, verbose=verbose)
        result = auditor.audit_weights(model, metadata)
        
        if result.status.value == "failed":
            violations = result.violations

        if generate_report or server_mode:
            report_path = "anchor_audit_report.md"
            with open(report_path, "w") as f:  # anchor: ignore RI-08
                f.write(f"# Model Audit Report: {model}\n\nStatus: {result.status.value.upper()}\n")
                f.write(f"Passed: {result.checks_passed}/{result.checks_total}\n\n")
                f.write("## Recommendation\n" + result.recommendation + "\n")
            click.secho(f"📋 Report saved: {report_path}", fg="green")

        scan_dir = path or dir or "."
        click.secho(f"🚀 Scanning '{scan_dir}' with {len(merged_rules)} active laws...", fg="yellow")

        # --- Diamond Cage activation ---
        active_cage = None
        if not no_sandbox:
            from anchor.core.sandbox import DiamondCage
            _cage = DiamondCage(verbose=verbose)
            if _cage.is_installed():
                active_cage = _cage
                click.secho("💎 Diamond Cage: ACTIVE (behavioral verification enabled)", fg="cyan")
            else:
                if verbose:
                    click.secho("💎 Diamond Cage: not installed (use 'anchor init' to enable)", fg="white", dim=True)

        engine = PolicyEngine(config=final_config, verbose=verbose)
        results = engine.scan_directory(scan_dir, exclude_paths=list(exclude), cage=active_cage)
        violations         = results.get('violations', [])
        suppressed         = results.get('suppressed', [])
        behavioral_findings= results.get('behavioral_findings', [])
        metrics            = results.get('metrics', {})

        # Merge behavioral findings into violations for unified reporting
        violations.extend(behavioral_findings)


    # 4. REPORT & EXIT
    # Filter violations based on severity level
    severity_map = {"info": 0, "warning": 1, "error": 2, "blocker": 3, "critical": 3}
    min_sev_score = severity_map.get(severity.lower(), 0)
    
    # Pre-process for counting
    violations = [v for v in violations if severity_map.get(v['severity'].lower(), 0) >= min_sev_score]
    
    if json_report:
        json_path = os.path.join(dot_anchor, "anchor-report.json")
        with open(json_path, "w") as f:  # anchor: ignore RI-08
            json.dump({"violations": violations, "suppressed": suppressed, "count": len(violations), "metrics": metrics}, f, indent=2)
        click.secho(f"📄 JSON report saved: {json_path}", fg="green")

    if violations or metrics:
        # Sort violations by severity
        failures = [v for v in violations if v['severity'] in ['critical', 'blocker', 'error']]
        warnings = [v for v in violations if v['severity'] == 'warning']
        info = [v for v in violations if v['severity'] == 'info']

        # 1. Generate Plain Text Report (.anchor/violation_report.txt)
        report_path = os.path.join(dot_anchor, "violation_report.txt")
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(report_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
                f.write("=" * 80 + "\n")
                f.write("   ⚓ ANCHOR AUDIT REPORT\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Scan Source: {os.path.abspath(scan_dir)}\n")
                f.write(f"Timestamp:   {timestamp}\n\n")
                
                f.write("--- SCAN STATISTICS ---\n")
                f.write(f"Files Scanned: {metrics.get('scanned_files', 0)}\n")
                f.write(f"Files Ignored: {metrics.get('ignored_files', 0)}\n")
                f.write(f"Total Files:   {metrics.get('total_files', 0)}\n")
                f.write(f"Total Dirs:    {metrics.get('total_dirs', 0)}\n\n")

                f.write("--- VIOLATION SUMMARY ---\n")
                f.write(f"Total Findings: {len(violations) + len(suppressed)}\n")
                f.write(f"Breakdown:      {len(failures)} Violations, {len(warnings)} Warnings, {len(info)} Info, {len(suppressed)} Suppressions\n\n")
                f.write("-" * 80 + "\n\n")
                
                if violations:
                    for v in violations:
                        v_sev = v['severity'].upper()
                        # Use symbolic tagging for "pseudo-color" in plain text
                        tag = "[!]" if v_sev in ["CRITICAL", "BLOCKER", "ERROR"] else "[?]"
                        f.write(f"{tag} [{v['id']}] {v['name']} ({v_sev})\n")
                        f.write(f"    Location: {v['file']}:{v['line']}\n")
                        f.write(f"    Message:  {v['message']}\n")
                        f.write(f"    Details:  {v.get('description', 'No further details.')}\n")
                        f.write(f"    Fix:      {v.get('mitigation')}\n")
                        f.write("-" * 40 + "\n")
                
                if suppressed:
                    f.write("\n" + "=" * 40 + "\n")
                    f.write("   🙈 SUPPRESSED FINDINGS (AUDITED)\n")
                    f.write("=" * 40 + "\n\n")
                    for s in suppressed:
                        f.write(f"[🙈] [{s['id']}] {s['name']}\n")
                        f.write(f"    Location:   {s['file']}:{s['line']}\n")
                        f.write(f"    Authorized: {s.get('author', 'Unknown Author')}\n")
                        f.write("-" * 40 + "\n")

            # --- GITHUB STEP SUMMARY GENERATION (Ephemeral) ---
            if github_summary:
                summary_path = "anchor-summary.md"
                with open(summary_path, "w", encoding="utf-8") as f: # anchor: ignore RI-08
                    f.write("## ⚓ Anchor Security & Governance Summary\n\n")
                    f.write(f"**Scan Status:** {'❌ FAILED' if failures else '✅ PASSED'}\n")
                    f.write(f"**Metrics:** {len(violations)} Active Findings | {len(suppressed)} Suppressed Exceptions\n\n")
                    
                    if violations:
                        f.write("### ❌ Active Violations\n")
                        f.write("| ID | Severity | File | Message |\n")
                        f.write("|---|---|---|---|\n")
                        for v in violations:
                            f.write(f"| {v['id']} | {v['severity'].upper()} | `{v['file']}:{v['line']}` | {v['message']} |\n")
                        f.write("\n")
                    
                    if suppressed:
                        f.write("### 🙈 Suppressed Exceptions (Audited)\n")
                        f.write("| ID | File | Authorized By |\n")
                        f.write("|---|---|---|---|\n")
                        for s in suppressed:
                            author = s.get('author', 'Unknown')
                            f.write(f"| {s['id']} | `{s['file']}:{s['line']}` | **{author}** |\n")
                        f.write("\n")

                    f.write("> 💡 *Reviewers: Check the 'Suppressed Exceptions' author to verify authorized security bypasses.*")
                if verbose: click.echo(f"   🚀 Generated ephemeral CI summary: {summary_path}")
            
            # Force filesystem refresh for IDEs
            try:
                os.utime(dot_anchor, None)
                os.utime(report_path, None)
            except: pass

            click.secho(f"\n📋 Full report generated: {os.path.abspath(report_path)}", fg="green", bold=True)
        except Exception as e:
            click.echo(f"⚠️  Failed to generate report file: {e}")

        # 2. Terminal Summary Output (Human-First)
        active_count = len(violations)
        click.secho(f"\n🚫 TOTAL FINDINGS: {active_count} active violations.", fg="yellow", bold=True)
        if suppressed:
            click.secho(f"🙈 {len(suppressed)} suppressed findings (See report for audit trail).", fg="cyan", dim=True)
        click.echo("-" * 80)
        
        # Only show the first 5 violations in terminal to avoid clutter
        display_limit = 5
        # Sort by severity (blocker first) for terminal display
        sorted_violations = sorted(violations, key=lambda x: severity_map.get(x['severity'].lower(), 0), reverse=True)
        
        for v in sorted_violations[:display_limit]:
            severity_color = "red" if v['severity'] in ['critical', 'blocker', 'error'] else "yellow"
            click.secho(f"[{v['id']}] {v['name']} ({v['severity'].upper()})", fg=severity_color, bold=True)
            click.echo(f"   Location: {v['file']}:{v['line']}")
            click.echo("-" * 80)
        
        if len(violations) > display_limit:
            click.secho(f"... and {len(violations)-display_limit} more findings in the report.", fg="white", dim=True)
            click.echo("-" * 80)
        
        # 5. CLEANUP (If ephemeral)
        if ephemeral_sandbox and not no_sandbox:
            if verbose:
                click.echo("\n🧹 Cleaning up ephemeral Diamond Cage...")
            cage.uninstall()

        if failures:
            if hook:
                click.secho(f"\n🚫 COMMIT BLOCKED: Anchor detected {len(failures)} violations.", fg="red", bold=True)
            else:
                click.secho(f"\n❌ FAILED: Found {len(failures)} critical violations.", fg="red", bold=True)
            
            click.secho(f"   (See .anchor/violation_report.txt for details)", fg="white", dim=True)
            sys.exit(1)
        else:
            if hook:
                click.secho("\n✅ COMMIT ALLOWED: No blocking violations found.", fg="green", bold=True)
            else:
                click.secho("\n✅ PASSED: No blocking violations found.", fg="green", bold=True)
            sys.exit(0)
    else:
        click.secho("\n✅ PASSED: Compliance Verified.", fg="green", bold=True)
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
def check_drift(target, repo, limit, only_violations, as_json, verbose):
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
        'aligned':            ('green',   '✅'),
        'intent_violation':   ('red',     '🛑'),
        'semantic_overload':  ('yellow',  '⚠️ '),
        'dependency_inertia': ('blue',    '📦'),
        'complexity_drift':   ('magenta', '📈'),
        'confidence_too_low': ('white',   '❓'),
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
        click.secho(f"❌ Target not found: {target}", fg='red')
        raise SystemExit(1)

    if not py_files:
        click.secho("⚠️  No Python files found in target.", fg='yellow')
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
        click.secho("⚠️  No symbols (classes/functions) found.", fg='yellow')
        raise SystemExit(0)

    # Apply limit
    if len(all_symbols) > limit:
        click.secho(
            f"⚓ Found {len(all_symbols)} symbols. Analysing first {limit} "
            f"(use --limit to change).", fg='yellow'
        )
        all_symbols = all_symbols[:limit]
    else:
        click.secho(f"⚓ Found {len(all_symbols)} symbols to analyse.", fg='cyan')

    # --- Run drift analysis on each symbol ---
    history_engine = HistoryEngine(str(repo_path))
    results = []
    json_results = []

    with click.progressbar(all_symbols, label='⚓ Drift Scan',
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
    if as_json:
        click.echo(_json.dumps(json_results, indent=2))
        raise SystemExit(0)

    if not results:
        click.secho("✅ No drift detected across the scanned codebase.", fg='green', bold=True)
        raise SystemExit(0)

    # Summary header
    violations = [r for r in results if r.verdict.value != 'aligned']
    aligned    = [r for r in results if r.verdict.value == 'aligned']
    click.echo("=" * 70)
    click.secho(f"⚓  ANCHOR DRIFT REPORT", bold=True)
    click.echo("=" * 70)
    click.secho(f"  ✅ Aligned:    {len(aligned)}", fg='green')
    click.secho(f"  ⚠️  Violations: {len(violations)}", fg='red' if violations else 'green')
    click.echo("=" * 70)
    click.echo()

    for result in results:
        color, icon = VERDICT_COLORS.get(result.verdict.value, ('white', '❓'))
        click.secho(
            f"{icon} {result.symbol}  [{result.verdict.value.upper().replace('_', ' ')}]",
            fg=color, bold=True
        )
        click.secho(f"   {result.rationale[:120]}", fg=color, dim=True)
        if result.evidence:
            for e in result.evidence[:3]:
                click.echo(f"   · {e}")
        if result.remediation and not only_violations:
            click.secho("   ↳ Remediation available (run with single symbol for full details)",
                        fg=color)
        click.echo()

    # Exit non-zero if any violations found
    if violations:
        raise SystemExit(1)


cli.add_command(init)

if __name__ == '__main__':
    cli()
