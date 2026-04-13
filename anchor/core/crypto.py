# =============================================================================
# anchor/core/crypto.py
#
# Cryptographic signing for AuditEntry non-repudiation.
#
# Uses HMAC-SHA256 over the chain_hash, keyed by the entity's ANCHOR_SECRET_KEY.
# This provides mathematically verifiable tamper-evidence for regulatory logs
# without requiring a PKI/KMS infrastructure at this stage.
#
# Upgrade path:
#   When RSA/ECDSA is required (e.g., SEBI/RBI production audit submissions),
#   replace sign_chain_hash() with an asymmetric scheme and expose a
#   verify_chain_hash(signature, chain_hash, public_key) counterpart.
# =============================================================================

import hashlib
import hmac
import os
from typing import Optional


def sign_chain_hash(chain_hash: str) -> Optional[str]:
    """
    Generate an HMAC-SHA256 signature over the audit chain_hash.

    Keyed by ANCHOR_SECRET_KEY from the environment. This ties the signature
    to the deploying entity — a different key produces a different signature,
    so any tampering with either the hash or the key is detectable.

    Returns:
        A 64-character hex digest if ANCHOR_SECRET_KEY is set, else None.

    Usage:
        Set ANCHOR_SECRET_KEY in your .env file (never commit the key):
            ANCHOR_SECRET_KEY=your-secret-mat-here

        The signed AuditEntry.cryptography.signature field will then be
        populated on every `anchor check` run.
    """
    secret_key = os.environ.get("ANCHOR_MAT", os.environ.get("ANCHOR_SECRET_KEY", "")).strip()

    if not secret_key:
        return None

    return hmac.new(
        secret_key.encode("utf-8"),
        chain_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_chain_hash(chain_hash: str, signature: str) -> bool:
    """
    Verify an HMAC-SHA256 signature against the chain_hash.

    Uses constant-time comparison (hmac.compare_digest) to prevent
    timing attacks. Returns True only if the signature is valid
    and ANCHOR_SECRET_KEY is set.

    Usage:
        Used by external verifiers (dashboard, ledger, regulator tools)
        to confirm the AuditEntry has not been tampered with.
    """
    secret_key = os.environ.get("ANCHOR_MAT", os.environ.get("ANCHOR_SECRET_KEY", "")).strip()

    if not secret_key or not signature:
        return False

    expected = hmac.new(
        secret_key.encode("utf-8"),
        chain_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
