"""
Anchor Constitution & Mitigation — Tamper-Proof Universal Policies
==================================================================

This module is the cryptographic seal on Anchor's universal policies.
It handles cloud-fetching and integrity verification for both:
1. constitution.anchor (The "WHAT" - Governance Rules)
2. mitigation.anchor (The "HOW" - Detection Patterns)

SECURITY MODEL:
  - Hashes are baked INTO the PyPI package at release time.
  - Even if cloud URLs are overridden, hashes MUST match.
"""

import hashlib
import os
from typing import Tuple

from anchor.core.config import settings


# =============================================================================
# IMMUTABLE HASHES (Updated each release)
# =============================================================================

# SHA-256 of the official files at this release.
# These CANNOT be overridden via environment.
# Updated via: python -c "import hashlib; print(hashlib.sha256(open('FILE','rb').read()).hexdigest().upper())"

CONSTITUTION_SHA256 = "7C24EE8648AC1DF496EA1EBDEE3F274BB75DE53E892D7210E4695D2DE731DFEF"
MITIGATION_SHA256 = "0FE901378610EA77F8BA3239AB93035E454CEBC1C3884B9AB1D7CD3FD34451B2"


# =============================================================================
# CONFIGURABLE URLS (via .env / ANCHOR_*_URL)
# =============================================================================

def get_constitution_url() -> str:
    """Return the constitution URL from Pydantic settings."""
    return settings.constitution_url

def get_mitigation_url() -> str:
    """Return the mitigation catalog URL from settings."""
    return settings.mitigation_url


# =============================================================================
# INTEGRITY VERIFICATION
# =============================================================================

def compute_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file (line-ending normalized).

    Normalizes CRLF → LF before hashing to ensure identical results
    across Windows (CRLF) and Linux/macOS (LF) environments.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        content = f.read()
    # Normalize: strip all \r so CRLF becomes LF
    content = content.replace(b"\r\n", b"\n")
    sha256.update(content)
    return sha256.hexdigest().upper()


def verify_integrity(file_path: str, expected_hash: str) -> Tuple[bool, str]:
    """
    Verify that a cached file has not been tampered with.

    Args:
        file_path: Path to the cached file
        expected_hash: The hardcoded SHA-256 string

    Returns:
        (is_valid, message) tuple
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {os.path.basename(file_path)}"

    actual_hash = compute_hash(file_path)

    if actual_hash == expected_hash:
        return True, f"✅ Integrity verified: {os.path.basename(file_path)} (SHA-256: {actual_hash[:12]}...)"
    else:
        return False, (
            f"🚨 INTEGRITY VIOLATION DETECTED in {os.path.basename(file_path)}!\n"
            f"   Expected: {expected_hash[:12]}...\n"
            f"   Got:      {actual_hash[:12]}...\n"
            f"   The cached policy has been tampered with.\n"
            f"   Re-run with internet access to fetch the authentic version."
        )
