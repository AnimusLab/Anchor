import argparse
import sys
import os

# Import the v2 logic we just built
# Note: We use absolute imports assuming you run as a module (python -m anchor.cli_v2)
from anchor.v2.config import AnchorConfig
from anchor.v2.engine import PolicyEngine
from anchor.v2.markdown_parser import MarkdownPolicyParser


def main():
    parser = argparse.ArgumentParser(
        description="Anchor v2: GenAI Governance Enforcer")

    # We use a sub-command structure (anchor-v2 check ...)
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # 'check' command
    check_parser = subparsers.add_parser(
        "check", help="Scan the current directory for violations")
    check_parser.add_argument("--context", type=str,
                              help="Path to a GenAI Threat Model (Markdown)")
    check_parser.add_argument("--target", type=str,
                              default=".", help="Directory to scan")
    check_parser.add_argument("--config", type=str,
                              default=".anchor", help="Path to .anchor config")

    args = parser.parse_args()

    if args.command == "check":
        run_check(args)
    else:
        # If no command is provided, show help
        parser.print_help()


def run_check(args):
    print("⚓ Anchor v2 (GenAI Governance) Starting...")

    # 1. Load Base Configuration (The .anchor file)
    config = AnchorConfig()
    try:
        if os.path.exists(args.config):
            config.load_from_file(args.config)
            print(f"[INFO] Loaded policy from {args.config}")
        else:
            print(f"[INFO] No .anchor file found. Using default empty policy.")
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        sys.exit(1)

    # 2. (The Bridge) Load GenAI Context if provided
    if args.context:
        print(f"[INFO] Loading Threat Model context: {args.context}")
        try:
            md_parser = MarkdownPolicyParser()
            dynamic_risks = md_parser.parse_file(args.context)

            if dynamic_risks:
                print(
                    f"[BRIDGE] The following GenAI-identified risks are being ENFORCED:")
                for risk in dynamic_risks:
                    # Force enable the risk in the policy
                    config.rules[risk] = "error"
                    print(f"       + {risk}")
            else:
                print("[INFO] No active risks found in the Threat Model.")

        except Exception as e:
            print(f"[WARN] Failed to process context file: {e}")

    # 3. Initialize Engine
    engine = PolicyEngine()
    policy = config.get_effective_policy()

    # 4. Scan Directory
    violations = []
    print(f"[INFO] Scanning target: {os.path.abspath(args.target)}")

    for root, _, files in os.walk(args.target):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Scan
                    v = engine.scan_file(content, path, policy)
                    violations.extend(v)
                except Exception as e:
                    print(f"[WARN] Could not read {path}: {e}")

    # 5. Report Results
    if violations:
        print("\n🔴 VIOLATIONS FOUND:")
        for v in violations:
            print(
                f"   [{v['severity'].upper()}] {v['rule_id']} in {v['file']}:{v['line']}")
            print(f"   Reason: {v['message']}")
            print(f"   Snippet: {v['code_snippet'].strip()}")
            print("")
        sys.exit(1)  # Return Error Code 1 (Fails CI/CD)
    else:
        print("\n✅ No violations found. Deployment approved.")
        sys.exit(0)  # Return Success Code 0


if __name__ == "__main__":
    main()
