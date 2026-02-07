import click
import os
import sys
import yaml
import json
import urllib.request
from anchor.core.policy_loader import PolicyLoader
from anchor.core.engine import PolicyEngine

# The "Single Source of Truth" URL
CONSTITUTION_URL = "https://gist.githubusercontent.com/raw/placeholder/finos-master.anchor"


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
    """Downloads the latest Constitution and creates a local policy template."""

    # 1. Download Master Constitution from Cloud
    click.secho("☁️ Fetching FINOS Master Constitution...", fg="blue")
    
    try:
        # The canonical URL for the FINOS AI Governance Constitution
        constitution_url = "https://raw.githubusercontent.com/Tanishq1030/Anchor/main/finos-master.anchor"
        
        with urllib.request.urlopen(constitution_url, timeout=30) as response:
            constitution_content = response.read().decode('utf-8')
        
        with open("finos-master.anchor", "w", encoding="utf-8") as f:
            f.write(constitution_content)
        
        click.secho("✅ Downloaded 'finos-master.anchor' (Universal Constitution)", fg="green")
        
    except Exception as e:
        click.secho(f"⚠️  Could not fetch from cloud: {e}", fg="yellow")
        click.secho("   Using local bundled constitution if available.", fg="yellow")
        
        # If local file doesn't exist, create a minimal starter
        if not os.path.exists("finos-master.anchor"):
            click.secho("❌ No local constitution found. Please check your internet connection.", fg="red")
            return

    # 2. Create Local Project Policy Template
    # The policy file can be renamed by companies (e.g., legend_studio.anchor, jpmorgan.anchor)
    if not os.path.exists(policy_name):
        project_template = f'''# =============================================================================
# {policy_name.replace('.anchor', '').upper()} - Project Policy
# =============================================================================
# This file extends the FINOS Universal Constitution with YOUR project rules.
#
# WHAT YOU CAN DO:
#   1. ADD new rules specific to your project
#   2. OVERRIDE severity of Constitution rules (warning → ignore)
#   3. Blockers from Constitution CANNOT be weakened
#
# RENAME THIS FILE:
#   Companies can rename this file to match their org:
#   - legend_studio.anchor
#   - jpmorgan.anchor
#   - goldman_sachs.anchor
#
# =============================================================================

version: "2.3"

metadata:
  project: "Your Project Name"
  team: "Your Team"
  
rules:
  # Example: Add your own project-specific rule
  # - id: "PROJECT-001"
  #   name: "Custom Rule"
  #   match:
  #     type: "import"
  #     module: "legacy_library"
  #   message: "Migrate away from legacy_library."
  #   severity: "warning"
  
  # Example: Override a Constitution rule severity
  # - id: "RI-12-SUBPROCESS"
  #   severity: "ignore"  # We've audited our subprocess usage
'''
        with open(policy_name, "w", encoding="utf-8") as f:
            f.write(project_template)
        click.secho(f"✅ Created '{policy_name}' (Project Template)", fg="green")
        click.secho(f"   → Rename this to your company name (e.g., legend_studio.anchor)", fg="blue")
    else:
        click.secho(f"ℹ️  '{policy_name}' already exists. Skipping.", fg="blue")

    # 3. Optionally install Diamond Cage (WASM Sandbox)
    if sandbox:
        click.secho("\n💎 Installing Diamond Cage (WASM Sandbox)...", fg="cyan", bold=True)
        from anchor.core.sandbox import install_diamond_cage
        success = install_diamond_cage()
        if not success:
            click.secho("⚠️  Diamond Cage installation failed. Sandbox features disabled.", fg="yellow")
    
    # Summary
    click.echo("\n" + "=" * 60)
    click.secho("🎯 ANCHOR INITIALIZED", fg="green", bold=True)
    click.echo("=" * 60)
    click.echo("Files created:")
    click.echo("  📜 finos-master.anchor  → Universal Constitution (don't edit)")
    click.echo(f"  📝 {policy_name}  → Your project rules (edit this)")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Edit your policy file to add project-specific rules")
    click.echo("  2. Run: anchor check --dir ./src")
    click.echo("=" * 60)



@click.command()
@click.option('--policy', '-p', multiple=True, help='Policy file(s) to apply.')
@click.option('--dir', '-d', help='Directory to scan (for code).')
@click.option('--model', '-m', help='Model weights file to validate (LM Studio, AnchorGrid, etc).')
@click.option('--metadata', help='Path to training metadata JSON.')
@click.option('--context', '-c', help='GenAI Threat Model (Markdown) to enforce.')
@click.option('--server-mode', is_flag=True, help='Run in server mode (includes local company policy).')
@click.option('--generate-report', is_flag=True, help='Generate human-readable audit report.')
@click.option('--json-report', '-j', is_flag=True, help='Generate anchor-report.json for CI.')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed loading info.')
def check(policy, dir, model, metadata, context, server_mode, generate_report, json_report, verbose):
    """
    Universal enforcement command for code and models.
    """
    # 1. GATHER THE FEDERATION
    default_master = "finos-master.anchor"
    active_policies = []

    # Always prefer master constitution from cloud/local cache
    if os.path.exists(default_master):
        active_policies.append(default_master)

    # Load project policy based on mode
    if server_mode or (not policy and os.path.exists("policy.anchor")):
        if os.path.exists("policy.anchor"):
            active_policies.append("policy.anchor")
    
    for p in policy:
        if os.path.exists(p):
            active_policies.append(p)
            
    if not active_policies:
        click.secho("❌ No policies found! Run 'anchor init' first.", fg="red")
        sys.exit(1)

    # 2. MERGE POLICIES
    merged_rules = []
    for p_file in active_policies:
        try:
            loader = PolicyLoader(p_file)
            config = loader.load_policy()
            merged_rules.extend(config.get("rules", []))
        except Exception as e:
            click.secho(f"❌ Failed to parse {p_file}: {e}", fg="red")

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
        from anchor.core.model_auditor import ModelAuditor
        click.secho(f"\n🔍 Auditing Model Weights: {model}", fg="cyan", bold=True)
        auditor = ModelAuditor(final_config)
        result = auditor.audit_weights(model, metadata)
        
        if result.status.value == "failed":
            violations = result.violations

        if generate_report or server_mode:
            report_path = "anchor_audit_report.md"
            with open(report_path, "w") as f:
                f.write(f"# Model Audit Report: {model}\n\nStatus: {result.status.value.upper()}\n")
                f.write(f"Passed: {result.checks_passed}/{result.checks_total}\n\n")
                f.write("## Recommendation\n" + result.recommendation + "\n")
            click.secho(f"📋 Report saved: {report_path}", fg="green")

    elif dir or (not model and not dir):
        scan_dir = dir or "."
        click.secho(f"🚀 Scanning '{scan_dir}' with {len(merged_rules)} active laws...", fg="yellow")
        engine = PolicyEngine(config=final_config)
        results = engine.scan_directory(scan_dir)
        violations = results.get('violations', [])

    # 4. REPORT & EXIT
    if json_report:
        with open("anchor-report.json", "w") as f:
            json.dump({"violations": violations, "count": len(violations)}, f, indent=2)
        click.secho("📄 JSON report saved: anchor-report.json", fg="green")

    if violations:
        # Separate failures from warnings
        failures = [v for v in violations if v['severity'] in ['critical', 'blocker', 'error']]
        
        click.secho(f"\n🚫 FOUND: {len(violations)} violations.", fg="yellow", bold=True)
        for v in violations:
            color = "red" if v['severity'] in ['critical', 'blocker', 'error'] else "yellow"
            severity_suffix = f" ({v['severity'].upper()})"
            click.secho(f"   [{v['id']}] {v['message']}{severity_suffix}", fg=color)
            if 'file' in v:
                click.echo(f"      File: {v['file']}:{v['line']}")
        
        if failures:
            click.secho(f"\n❌ FAILED: Blocking build due to {len(failures)} high-severity violations.", fg="red", bold=True)
            sys.exit(1)
        else:
            click.secho("\n✅ PASSED (with warnings): No high-severity violations found.", fg="green", bold=True)
            sys.exit(0)
    else:
        click.secho("\n✅ PASSED: Compliance Verified.", fg="green", bold=True)
        sys.exit(0)


cli.add_command(init)
cli.add_command(check)

if __name__ == '__main__':
    cli()
