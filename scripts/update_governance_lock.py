#!/usr/bin/env python3
"""
update_governance_lock.py - regenerate and sign anchor/governance/GOVERNANCE.lock.

  python scripts/update_governance_lock.py --private-key ~/.anchor-secure/governance_signing_private.pem
  python scripts/update_governance_lock.py --check        # verify only, no key needed (CI)

Run after any change to a *.anchor rule file, then commit GOVERNANCE.lock and GOVERNANCE.lock.sig.
"""
import argparse
import importlib.util
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

_SIGNATURE_PATH = ROOT / "anchor" / "core" / "governance_signature.py"
_SIGNATURE_SPEC = importlib.util.spec_from_file_location(
    "anchor_governance_signature", _SIGNATURE_PATH
)
if _SIGNATURE_SPEC is None or _SIGNATURE_SPEC.loader is None:
    raise ImportError(f"Unable to load governance signature module: {_SIGNATURE_PATH}")
_SIGNATURE_MODULE = importlib.util.module_from_spec(_SIGNATURE_SPEC)
_SIGNATURE_SPEC.loader.exec_module(_SIGNATURE_MODULE)

GovernanceSignatureError = _SIGNATURE_MODULE.GovernanceSignatureError
build_lock_text = _SIGNATURE_MODULE.build_lock_text
verify_governance_tree = _SIGNATURE_MODULE.verify_governance_tree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--private-key", type=Path)
    ap.add_argument("--check", action="store_true", help="Only verify the committed lock and signature.")
    ap.add_argument("--root", type=Path, default=ROOT / "anchor" / "governance")
    args = ap.parse_args()
    lock = args.root / "GOVERNANCE.lock"

    if args.check:
        try:
            verify_governance_tree(args.root)
        except GovernanceSignatureError as exc:
            print(f"FAILED: {exc}")
            return 1
        print("OK: rule files match the signed GOVERNANCE.lock")
        return 0

    if not args.private_key or not args.private_key.exists():
        print("--private-key is required (path to your Ed25519 PEM, stored outside the repo)")
        return 2
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    lock.write_text(build_lock_text(args.root, version), encoding="utf-8", newline="\n")
    from sign_governance_lock import sign_lock_file
    sig = sign_lock_file(lock, args.private_key)
    verify_governance_tree(args.root)
    print(f"Wrote {lock} and {sig}; verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
