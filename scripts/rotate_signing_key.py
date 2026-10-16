#!/usr/bin/env python3
"""
rotate_signing_key.py - one-shot rotation after a key compromise.

1. Generates a new keypair outside the repo.
2. Writes the new public key to governance_signing_public.pem and
   anchor/core/governance_signature.py (GOVERNANCE_PUBLIC_KEY_HEX).
3. Re-signs anchor/governance/GOVERNANCE.lock.

Run from the repo root:  python scripts/rotate_signing_key.py
Anything signed under the old key must be treated as untrusted.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_signing_key import generate  # noqa: E402
from sign_governance_lock import sign_lock_file  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIG_PY = ROOT / "anchor" / "core" / "governance_signature.py"
LOCK = ROOT / "anchor" / "governance" / "GOVERNANCE.lock"


def main():
    out_dir = Path.home() / ".anchor-secure"
    priv, pub, hex_ = generate(out_dir)
    (ROOT / "governance_signing_public.pem").write_bytes(pub.read_bytes())
    src = SIG_PY.read_text()
    new = re.sub(r'GOVERNANCE_PUBLIC_KEY_HEX = "[0-9a-f]+"', f'GOVERNANCE_PUBLIC_KEY_HEX = "{hex_}"', src)
    if new == src:
        raise SystemExit("Could not find GOVERNANCE_PUBLIC_KEY_HEX to replace")
    SIG_PY.write_text(new)
    sig = sign_lock_file(LOCK, priv)
    print(f"New private key: {priv}  (never commit this)")
    print(f"Re-signed: {sig}")
    print("Next: add a rotation-date note to the changelog and cut a release.")


if __name__ == "__main__":
    main()
