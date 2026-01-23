import sys
import argparse
from anchor.core.contexts import extract_usages
from anchor.core.models import VerdictType, CodeSymbol
from anchor.core.parser import walk_repo
from anchor.core.history import HistoryEngine
from anchor.core.verdicts import analyze_drift

def main():
    parser = argparse.ArgumentParser(description="Anchor: Deterministic Intent Auditor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List all auditable symbols in the codebase")
    list_parser.add_argument("path", help="Path to the repository")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Run full audit on a specific symbol")
    audit_parser.add_argument("path", help="Path to the repository")
    audit_parser.add_argument("--symbol", help="Specific symbol to audit (e.g., 'django.forms.forms:Form')")

    args = parser.parse_args()

    if args.command == "list":
        print(f"🔍 Scanning {args.path} for auditable symbols...")
        
        count = 0
        for symbol in walk_repo(args.path):
            count += 1
            # Simple output format: [TYPE] path:Symbol
            prefix = "[C]" if symbol.type == 'class' else "[F]" if symbol.type == 'function' else "[M]"
            print(f"{prefix} {symbol.qualified_name}")
            
        print(f"\n✅ Found {count} symbols.")
        
    elif args.command == "audit":
        target_name = args.symbol
        if not target_name:
            print("❌ Please specify a symbol to audit (e.g. --symbol django.forms.forms:Form)")
            return

        print(f"🛡️  Starting audit for: {target_name}")
        
        # 1. Find the symbol in current codebase
        found_symbol = None
        for sym in walk_repo(args.path):
            if sym.qualified_name.endswith(target_name) or sym.name == target_name:
                found_symbol = sym
                break
        
        if not found_symbol:
            print(f"❌ Symbol '{target_name}' not found in current codebase.")
            return

        print(f"📍 Located {found_symbol.type} at {found_symbol.file_path}:{found_symbol.line_number}")

        # 2. Find the Anchor
        history = HistoryEngine(args.path)
        anchor = history.find_anchor(found_symbol)
        
        if anchor:
            print("\n⚓ ANCHOR LOCKED")
            print(f"   Commit: {anchor.commit_sha[:7]}")
            print(f"   Date:   {anchor.commit_date}")
            print(f"   Intent: {anchor.intent_description}")
            print(f"   Intent: {anchor.intent_description}")

            # --- NEW CODE STARTS HERE ---
            # 3. Analyze Usage
            print("\n🔍 ANALYZING USAGE PATTERNS...")
            contexts = extract_usages(args.path, found_symbol.name)
            
            print(f"   Found {len(contexts)} occurrences of '{found_symbol.name}'")
            
            # Simple breakdown
            inheritance_count = sum(1 for c in contexts if "Inheritance" in c.caller_symbol)
            instantiation_count = sum(1 for c in contexts if "Instantiation" in c.caller_symbol)
            
            print(f"   - Inheritance:   {inheritance_count}")
            print(f"   - Instantiations: {instantiation_count}")
            
            if len(contexts) == 0:
                print("⚠️  No usage found. Is this dead code?")

            # 4. JUDGMENT DAY
            print("\n⚖️  CALCULATING VERDICT...")
            result = analyze_drift(found_symbol.name, anchor, contexts)
            
            print(f"\nVerdict: {result.verdict.value.upper()}")
            print(f"Rationale: {result.rationale}")
            print("Evidence:")
            for ev in result.evidence:
                print(f"   - {ev}")

        else:
            print("\n⚠️  Anchor could not be established.")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()