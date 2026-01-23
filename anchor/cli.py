import sys
import argparse
from anchor.core.models import VerdictType


def main():
    parser = argparse.ArgumentParser(description="Anchor: Determinstic Intent Auditor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # command list
    list_parser = subparsers.add_parser("list", help="List all auditable symbols in the codebase")
    list_parser.add_argument("path", help="Path to repository")

    # command audit
    audit_parser = subparsers.add_parser("audit", help="Run full audit on a specific symbol")
    audit_parser.add_argument("Path", help="Path to the repository")
    audit_parser.add_argument("--symbol", help="Specific symbol to audit (e.g., 'django.forms.Form')")
    
    args = parser.parse_args()

    if args.command == "list":
        print(f" Scanning {args.path} for auditable symbols...")
        # TODO: Connect AST walker here
        print(" (AST Walker not yet implemented)")

    elif args.command == "audit":
        target = args.symbol if args.symbol else "ALL"
        print(f"  Anchorning intent for: {target}")
        print("  Loading history...")
        print("  Freezing intent...")
        print("  Clustering usage...")
        print(f"   Verdict: {VerdictType.CONFIDENCE_TOO_LOW} (Engine not connected)")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
