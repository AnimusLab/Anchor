import sys
import argparse
import warnings  # <--- Added to filter warnings
from anchor.core.models import VerdictType, CodeSymbol
from anchor.core.parser import walk_repo
from anchor.core.history import HistoryEngine
from anchor.core.contexts import extract_usages
from anchor.core.verdicts import analyze_drift
from anchor.core.memory import GlobalMemory


def main():
    # Filter SyntaxWarnings from messy source code scans
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    parser = argparse.ArgumentParser(
        description="Anchor: Deterministic Intent Auditor")
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # Command: list
    list_parser = subparsers.add_parser(
        "list", help="List all auditable symbols in the codebase")
    list_parser.add_argument("path", help="Path to the repository")

    # Command: audit
    audit_parser = subparsers.add_parser(
        "audit", help="Run full audit on a specific symbol")
    audit_parser.add_argument("path", help="Path to the repository")
    audit_parser.add_argument(
        "--symbol", help="Specific symbol to audit (e.g., 'django.forms.forms:Form')")
    audit_parser.add_argument(
        "--format", choices=["human", "agent"], default="human", help="Output format")

    args = parser.parse_args()

    if args.command == "list":
        print(f"🔍 Scanning {args.path} for auditable symbols...")
        count = 0
        for symbol in walk_repo(args.path):
            count += 1
            prefix = "[C]" if symbol.type == 'class' else "[F]" if symbol.type == 'function' else "[M]"
            print(f"{prefix} {symbol.qualified_name}")
        print(f"\n✅ Found {count} symbols.")

    elif args.command == "audit":
        target_name = args.symbol
        if not target_name:
            print("❌ Please specify a symbol to audit")
            return

        # 1. Find Symbol
        if args.format == "human":
            print(f"🛡️  Starting audit for: {target_name}")

        found_symbol = None
        for sym in walk_repo(args.path):
            if sym.qualified_name.endswith(target_name) or sym.name == target_name:
                found_symbol = sym
                break

        if not found_symbol:
            print(f"❌ Symbol '{target_name}' not found.")
            return

        if args.format == "human":
            print(
                f"📍 Located {found_symbol.type} at {found_symbol.file_path}:{found_symbol.line_number}")

        # 2. Find Anchor
        history = HistoryEngine(args.path)
        anchor = history.find_anchor(found_symbol)

        if anchor:
            if args.format == "human":
                print("\n⚓ ANCHOR LOCKED")
                print(f"   Commit: {anchor.commit_sha[:7]}")
                print(f"   Date:   {anchor.commit_date}")
                print(f"   Intent: {anchor.intent_description}")
                print("\n🔍 ANALYZING USAGE PATTERNS...")

            # 3. Analyze Usage
            contexts = extract_usages(args.path, found_symbol.name)

            if args.format == "human":
                print(
                    f"   Found {len(contexts)} occurrences of '{found_symbol.name}'")
                if len(contexts) == 0:
                    print("⚠️  No usage found.")
                print("\n⚖️  CALCULATING VERDICT...")

            # 4. Verdict & Memory
            result = analyze_drift(found_symbol.name, anchor, contexts)

            # Brain Update
            brain = GlobalMemory()
            brain.record_scan(target_name, result.verdict.value)

            if args.format == "human":
                print(f"\nVerdict: {result.verdict.value.upper()}")
                print(f"Rationale: {result.rationale}")

                # --- FIX: Show Evidence Loop ---
                print("Evidence:")
                for ev in result.evidence:
                    print(f"   - {ev}")
                # -------------------------------

                # Show Brain Stats
                stats = brain.get_stats(target_name)
                if stats and stats[0] > 1:
                    print(
                        f"🧠 Brain: Seen this symbol {stats[0]} times across all projects.")

                if result.remediation:
                    print(f"\n{result.remediation}")

            elif args.format == "agent":
                output = f"""
<anchor_context>
<symbol>{result.symbol}</symbol>
<status>{result.verdict.value}</status>
<original_intent>{result.anchor.intent_description}</original_intent>
<directive>
{result.remediation or "Maintain alignment with original intent."}
</directive>
</anchor_context>
"""
                print(output.strip())

        else:
            print("\n⚠️  Anchor could not be established.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
