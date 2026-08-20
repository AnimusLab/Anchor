#!/usr/bin/env python3
"""
generate_signing_key.py — ONE-TIME key generation script.
Generates an Ed25519 private key (KEEP SECRET) and public key (EMBED IN CLIENT).
"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_raw = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)

with open("governance_signing_private.pem", "wb") as f:
    f.write(private_bytes)
with open("governance_signing_public.pem", "wb") as f:
    f.write(public_bytes)

print("Generated governance_signing_private.pem <- KEEP SECRET")
print("Generated governance_signing_public.pem  <- SAFE TO COMMIT")
print()
print("Public key hex for anchor/core/governance_signature.py:")
print(f'GOVERNANCE_PUBLIC_KEY_HEX = "{public_raw.hex()}"')
