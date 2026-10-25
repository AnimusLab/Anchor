import base64
import hashlib
import json
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

# Production Ed25519 Public Key for Anchor Governance Baseline Validation.
# This key is embedded in the client and verifies GOVERNANCE.lock authenticity offline.
GOVERNANCE_PUBLIC_KEY_HEX = "c04f2c898d1a433394221092307fa22fed56120dd666e731455d005b87b90993"


def normalize_lock_bytes(data: bytes) -> bytes:
    """Canonicalize line endings so signatures verify on every OS."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


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

    lock_bytes = normalize_lock_bytes(lock_path.read_bytes())
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


# --------------------------------------------------------------------------
# Rule-file integrity: the signed lock lists the SHA-256 of every shipped
# *.anchor file. Hashes are taken over line-ending-normalized bytes so the
# result is identical on Windows, macOS and Linux.
# --------------------------------------------------------------------------

def hash_governance_bytes(data: bytes) -> str:
    return hashlib.sha256(normalize_lock_bytes(data)).hexdigest()


def list_governance_files(root: Path) -> list:
    root = Path(root)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.anchor"))


def compute_governance_hashes(root: Path) -> dict:
    root = Path(root)
    return {rel: hash_governance_bytes((root / rel).read_bytes()) for rel in list_governance_files(root)}


def lock_files_from_data(data) -> dict:
    """Return {relative_path: sha256} from a parsed lock (format 2 'files:' map or the legacy flat layout)."""
    if not isinstance(data, dict):
        return {}
    files = data.get("files")
    if isinstance(files, dict):
        return {str(k): str(v) for k, v in files.items()}
    return {k: str(v) for k, v in data.items() if isinstance(k, str) and k.endswith(".anchor")}


def build_lock_text(root: Path, client_version: str) -> str:
    lines = [
        "# Anchor Governance Integrity Baseline",
        "# SHA-256 over line-ending-normalized (LF) file bytes.",
        "# Regenerate and re-sign: python scripts/update_governance_lock.py --private-key <key>",
        "format: 2",
        f'client_version: "{client_version}"',
        "files:",
    ]
    lines += [f"  {rel}: {h}" for rel, h in compute_governance_hashes(root).items()]
    return "\n".join(lines) + "\n"


def verify_governance_tree(root: Path, lock_path: Optional[Path] = None, sig_path: Optional[Path] = None) -> None:
    """Verify the lock signature, then that the rule files match the lock exactly.

    Raises GovernanceSignatureError if the signature is invalid or any rule file is modified,
    missing from disk, or present but not listed in the lock.
    """
    import yaml

    root = Path(root)
    lock_path = Path(lock_path) if lock_path else root / "GOVERNANCE.lock"
    verify_lock_signature(lock_path, sig_path)
    expected = lock_files_from_data(yaml.safe_load(lock_path.read_text(encoding="utf-8-sig")))
    if not expected:
        raise GovernanceSignatureError(f"{lock_path} lists no rule files.")
    actual = compute_governance_hashes(root)
    problems = []
    for rel, digest in sorted(expected.items()):
        if rel not in actual:
            problems.append(f"missing: {rel}")
        elif actual[rel] != digest:
            problems.append(f"modified: {rel}")
    problems += [f"unlisted: {rel}" for rel in sorted(set(actual) - set(expected))]
    if problems:
        raise GovernanceSignatureError(
            "Rule files do not match the signed GOVERNANCE.lock:\n  " + "\n  ".join(problems)
        )
