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


# SHA-256 of the official legacy files (optional in V3).
CONSTITUTION_SHA256 = "E292674E571C32273E5C227DFD5F77379B5C15E07E6272C228C39BF91B5C8D79"
MITIGATION_SHA256 = "E38500AB08E5071B258B2508DBA84D230D03DB4F17949D348E9219D80F77C7BE"


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
    """Compute SHA-256 hash of a file (line-ending normalized)."""
    sha256 = hashlib.sha256()
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        content = f.read()
    # Normalize: strip all \r so CRLF becomes LF
    content = content.replace(b"\r\n", b"\n")
    sha256.update(content)
    return sha256.hexdigest().upper()


def verify_integrity(file_path: str, expected_hash: str) -> Tuple[bool, str]:
    """
    Verify that a cached file has not been tampered with.
    """
    if not os.path.exists(file_path):
        # In V3, we allow missing legacy files as we migrate to patterns/ directory
        return True, f"Legacy file {os.path.basename(file_path)} not present, skipping integrity check."

    actual_hash = compute_hash(file_path)

    if actual_hash == expected_hash:
        return True, f"Integrity verified: {os.path.basename(file_path)} (SHA-256: {actual_hash[:12]}...)"
    else:
        return False, (
            f"INTEGRITY VIOLATION DETECTED in {os.path.basename(file_path)}!\n"
            f"   Expected: {expected_hash[:12]}...\n"
            f"   Got:      {actual_hash[:12]}...\n"
            f"   The cached policy has been tampered with.\n"
        )
