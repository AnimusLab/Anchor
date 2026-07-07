import json
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class GovernanceKeyManager:
    """
    Loads and manages the Ed25519 signing keys used for stamping governance events.
    """
    
    def __init__(
        self,
        keystore_path: str = "identity/governance.keystore",
        private_key_path: str = ".anchor/keys/ed25519_private.pem",
        public_key_path: str = ".anchor/keys/ed25519_public.pem"
    ):
        self.keystore_path = Path(keystore_path)
        self.private_key_path = Path(private_key_path)
        self.public_key_path = Path(public_key_path)
        self.private_key: Optional[ed25519.Ed25519PrivateKey] = None

    def unlock(self, password: str = "") -> bool:
        """
        Unlocks the governance signing key. First checks for local Ed25519 PEM files.
        If not found, falls back to parsing the keystore file.
        """
        try:
            if self.private_key_path.exists():
                pem_data = self.private_key_path.read_bytes()
                self.private_key = serialization.load_pem_private_key(
                    pem_data,
                    password=None
                )
                return True

            if not self.keystore_path.exists():
                return False
            data = json.loads(self.keystore_path.read_text(encoding="utf-8"))
            private_key_hex = data.get("private_key_hex")
            if not private_key_hex:
                return False
            raw_bytes = bytes.fromhex(private_key_hex)
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)
            return True
        except Exception:
            return False

    def generate_keystore(self) -> None:
        """
        Helper method to generate a brand new keystore for development / testing.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.keystore_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "private_key_hex": private_bytes.hex()
        }
        self.keystore_path.write_text(json.dumps(data), encoding="utf-8")
        self.private_key = private_key

    def generate_keypair_pem(self) -> None:
        """
        Generates a brand new Ed25519 keypair and writes it to PEM files under .anchor/keys/.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)
        self.private_key_path.write_bytes(pem_private)
        try:
            import os
            os.chmod(self.private_key_path, 0o600)
        except Exception:
            pass
        self.public_key_path.write_bytes(pem_public)
        self.private_key = private_key

    def get_public_key_hex(self) -> str:
        if not self.private_key:
            return ""
        public_key = self.private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()

