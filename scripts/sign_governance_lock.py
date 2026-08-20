#!/usr/bin/env python3
"""
sign_governance_lock.py — Release-time signing script for GOVERNANCE.lock
Produces anchor/governance/GOVERNANCE.lock.sig
"""

import argparse
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def load_private_key(path: Path) -> Ed25519PrivateKey:
    pem_bytes = path.read_bytes()
    key = serialization.load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"{path} is not an Ed25519 private key")
    return key


def sign_lock_file(lock_path: Path, private_key_path: Path) -> Path:
    lock_bytes = lock_path.read_bytes()
    private_key = load_private_key(private_key_path)
    signature = private_key.sign(lock_bytes)

    sig_payload = {
        "signature": base64.b64encode(signature).decode("ascii"),
        "algorithm": "ed25519",
        "signed_file": lock_path.name,
    }

    sig_path = lock_path.with_suffix(lock_path.suffix + ".sig")
    sig_path.write_text(json.dumps(sig_payload, indent=2) + "\n")
    return sig_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--private-key", required=True, type=Path)
    args = parser.parse_args()

    if not args.lock.exists():
        raise SystemExit(f"Lock file not found: {args.lock}")
    if not args.private_key.exists():
        raise SystemExit(f"Private key not found: {args.private_key}")

    sig_path = sign_lock_file(args.lock, args.private_key)
    print(f"Signed {args.lock} -> {sig_path}")


if __name__ == "__main__":
    main()
