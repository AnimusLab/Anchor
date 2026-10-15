#!/usr/bin/env python3
"""
generate_signing_key.py - generate an Ed25519 signing keypair OUTSIDE the repo.

The private key is written to --out-dir (default: ~/.anchor-secure), never to the
working tree. The script refuses to write inside a git repository.
"""
import argparse
import os
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def inside_git_repo(path: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True)
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def generate(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    if inside_git_repo(out_dir):
        raise SystemExit(f"Refusing to write a private key inside a git repo: {out_dir}")
    key = Ed25519PrivateKey.generate()
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())
    pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)
    raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    priv_path = out_dir / "governance_signing_private.pem"
    fd = os.open(priv_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(priv)
    (out_dir / "governance_signing_public.pem").write_bytes(pub)
    return priv_path, out_dir / "governance_signing_public.pem", raw.hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path.home() / ".anchor-secure")
    a = ap.parse_args()
    priv, pub, hex_ = generate(a.out_dir)
    print(f"Private key (KEEP SECRET, back it up offline): {priv}")
    print(f"Public key  (safe to commit):                  {pub}")
    print(f'GOVERNANCE_PUBLIC_KEY_HEX = "{hex_}"')


if __name__ == "__main__":
    main()
