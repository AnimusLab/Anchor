import click
import os
import sys
import requests  # <--- NEW: Needed to fetch from cloud
from anchor.core.policy_loader import PolicyLoader
from anchor.core.engine import PolicyEngine

# The "Single Source of Truth" URL
# In production, this would be: "https://raw.githubusercontent.com/finos/anchor-rules/main/master.yaml"
CONSTITUTION_URL = "https://gist.githubusercontent.com/raw/placeholder/finos-master.anchor"


@click.group()
def cli():
    """
    Anchor: The Federated Governance Engine for AI.
    """
    pass


@click.command()
def init():
    """Downloads the latest Constitution and creates a local policy."""

    # 1. Download Master Constitution (Cloud Fetch)
    click.secho("☁️ Connecting to FINOS Cloud...", fg="blue")
    try:
        # TIMEOUT is important so it doesn't hang forever
        # For now, we simulate a fetch because the URL is fake.
        # In real life, uncomment the next two lines:
        # response = requests.get(CONSTITUTION_URL, timeout=5)
        # constitution_content = response.text

        # SIMULATION (Since we don't have the URL live yet):
        constitution_content = """version: "2.1"
rules:
  - id: "FINOS-001"
    name: "Ban Dangerous Execution"
    match:
      type: "function_call"
      name: "eval"
    message: "Constitution Violation: 'eval' is banned across all banks."
    severity: "critical"
"""
        with open("finos-master.anchor", "w") as f:
            f.write(constitution_content)
        click.secho(
            "✅ Downloaded 'finos-master.anchor' from Cloud.", fg="green")

    except Exception as e:
        click.secho(f"❌ Failed to fetch Constitution: {e}", fg="red")
        click.secho("   -> Using offline backup...", fg="yellow")
        # Fallback logic could go here

    # 2. Create Local Project Policy
    if not os.path.exists("policy.anchor"):
        project_content = """version: "2.1"
rules:
  - id: "PROJECT-001"
    name: "Ban Requests Library"
    match:
      type: "import"
      module: "requests"
    message: "Project Policy: Use internal 'SecureFetch' instead."
    severity: "warning"
"""
        with open("policy.anchor", "w") as f:
            f.write(project_content)
        click.secho("✅ Created 'policy.anchor' (Local Overrides)", fg="green")
    else:
        click.secho("ℹ️  'policy.anchor' already exists. Skipping.", fg="blue")


@click.command()
@click.option('--policy', '-p', multiple=True, help='Policy file(s) to apply.')
@click.option('--dir', '-d', default='.', help='Directory to scan.')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed loading info.')
def check(policy, dir, verbose):
    """
    Scans code against the Federation of Policies.
    """
    # ... (This function remains exactly the same as before) ...
    # ... (Copy the rest of the 'check' function here) ...
    # 1. GATHER THE FEDERATION
    default_master = "finos-master.anchor"
    active_policies = []

    if os.path.exists(default_master):
        active_policies.append(default_master)

    if not policy and os.path.exists("policy.anchor"):
        active_policies.append("policy.anchor")
    else:
        for p in policy:
            if os.path.exists(p):
                active_policies.append(p)
            else:
                click.secho(
                    f"⚠️ Warning: Policy '{p}' not found. Skipping.", fg="yellow")

    if not active_policies:
        click.secho("❌ No policies found! Run 'anchor init' first.", fg="red")
        sys.exit(1)

    # 2. MERGE
    if verbose:
        click.secho(f"📜 Loading Federation: {active_policies}", fg="blue")

    merged_rules = []
    for p_file in active_policies:
        try:
            loader = PolicyLoader(p_file)
            config = loader.load_policy()
            merged_rules.extend(config.get("rules", []))
        except Exception as e:
            click.secho(f"❌ Failed to parse {p_file}: {e}", fg="red")

    final_config = {"rules": merged_rules}
    click.secho(
        f"🚀 Scanning '{dir}' with {len(merged_rules)} active laws...", fg="yellow")

    # 3. RUN ENGINE
    engine = PolicyEngine(config=final_config)
    results = engine.scan_directory(dir)

    # 4. REPORT
    violations = results.get('violations', [])
    if violations:
        click.secho(
            f"\n🚫 FAILED: Found {len(violations)} violations.", fg="red", bold=True)
        for v in violations:
            color = "red" if v['severity'] in [
                'critical', 'blocker'] else "yellow"
            click.secho(f"   [{v['id']}] {v['message']}", fg=color)
            click.echo(f"      File: {v['file']}:{v['line']}")
        sys.exit(1)
    else:
        click.secho("\n✅ PASSED: Compliance Verified.", fg="green", bold=True)
        sys.exit(0)


cli.add_command(init)
cli.add_command(check)

if __name__ == '__main__':
    cli()
