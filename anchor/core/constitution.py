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

CONSTITUTION_SHA256 = "3745014B26B42347A4C4F525B705937A36CBD7738E7401A58C6F40E990525AFF"
MITIGATION_SHA256 = "E3E32531BD81942352DBEF700159DBC69FD63B41FCB5ACD9C17166D8F1B91DD2"


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
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
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
