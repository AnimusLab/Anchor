import base64
import json
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

# Production Ed25519 Public Key for Anchor Governance Baseline Validation.
# This key is embedded in the client and verifies GOVERNANCE.lock authenticity offline.
GOVERNANCE_PUBLIC_KEY_HEX = "7e7a6b469c4bda9facbec727414690c2c0711afd775c72df64d4fb33d955f738"


class GovernanceSignatureError(Exception):
    """Raised when GOVERNANCE.lock signature is missing, invalid, or tampered."""
    pass


def _load_public_key() -> Ed25519PublicKey:
    raw = bytes.fromhex(GOVERNANCE_PUBLIC_KEY_HEX)
    return Ed25519PublicKey.from_public_bytes(raw)


def verify_lock_signature(lock_path: Path, sig_path: Optional[Path] = None) -> dict:
    """
    Verifies that lock_path's contents were signed by the embedded key.
    Works entirely offline with zero network I/O.
    """
    if sig_path is None:
        sig_path = lock_path.with_suffix(lock_path.suffix + ".sig")

    if not sig_path.exists():
        raise GovernanceSignatureError(
            f"No signature file found at {sig_path}. "
            f"A GOVERNANCE.lock without a valid Ed25519 signature cannot be trusted."
        )

    try:
        sig_payload = json.loads(sig_path.read_text())
        signature = base64.b64decode(sig_payload["signature"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise GovernanceSignatureError(f"Malformed signature file {sig_path}: {e}") from e

    lock_bytes = lock_path.read_bytes()
    public_key = _load_public_key()

    try:
        public_key.verify(signature, lock_bytes)
    except InvalidSignature:
        raise GovernanceSignatureError(
            f"SIGNATURE VERIFICATION FAILED for {lock_path}.\n"
            f"The GOVERNANCE.lock file or its signature has been tampered with or modified offline.\n"
            f"Refusing to execute compliance check against unauthenticated governance manifest."
        )

    return sig_payload
