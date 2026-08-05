use ed25519_dalek::{SigningKey, VerifyingKey, Signature, Signer, Verifier};
use hmac::{Hmac, Mac};
use rand_core::OsRng;
use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;


type HmacSha256 = Hmac<Sha256>;

pub struct Ed25519KeyPair {
    pub private_key_pem: String,
    pub public_key_pem: String,
    pub fingerprint: String,
}

/// Generate fresh Ed25519 Keypair for local deployment identity
pub fn generate_ed25519_keypair() -> Ed25519KeyPair {
    let mut csprng = OsRng;
    let signing_key = SigningKey::generate(&mut csprng);
    let verifying_key: VerifyingKey = signing_key.verifying_key();

    let priv_bytes = signing_key.to_bytes();
    let pub_bytes = verifying_key.to_bytes();

    let private_hex = hex::encode(priv_bytes);
    let public_hex = hex::encode(pub_bytes);

    // Compute SHA-256 fingerprint of public key
    let mut hasher = sha2::Sha256::new();
    sha2::Digest::update(&mut hasher, pub_bytes);
    let fingerprint = format!("sha256:{}", hex::encode(hasher.finalize()));

    Ed25519KeyPair {
        private_key_pem: private_hex,
        public_key_pem: public_hex,
        fingerprint,
    }
}

/// Asymmetrically sign chain hash using Ed25519 private key
pub fn sign_dac_block_ed25519(chain_hash: &str, private_key_hex: &str) -> Option<String> {
    if private_key_hex.is_empty() || chain_hash.is_empty() {
        return None;
    }

    let priv_bytes = hex::decode(private_key_hex).ok()?;
    if priv_bytes.len() != 32 {
        return None;
    }

    let mut key_array = [0u8; 32];
    key_array.copy_from_slice(&priv_bytes);
    let signing_key = SigningKey::from_bytes(&key_array);

    let signature = signing_key.sign(chain_hash.as_bytes());
    Some(hex::encode(signature.to_bytes()))
}

/// Verify asymmetric Ed25519 signature in constant time using public key
pub fn verify_dac_block_ed25519(chain_hash: &str, signature_hex: &str, public_key_hex: &str) -> bool {
    if public_key_hex.is_empty() || signature_hex.is_empty() || chain_hash.is_empty() {
        return false;
    }

    let pub_bytes = match hex::decode(public_key_hex) {
        Ok(b) if b.len() == 32 => b,
        _ => return false,
    };

    let sig_bytes = match hex::decode(signature_hex) {
        Ok(b) if b.len() == 64 => b,
        _ => return false,
    };

    let mut pub_array = [0u8; 32];
    pub_array.copy_from_slice(&pub_bytes);
    let verifying_key = match VerifyingKey::from_bytes(&pub_array) {
        Ok(k) => k,
        Err(_) => return false,
    };

    let mut sig_array = [0u8; 64];
    sig_array.copy_from_slice(&sig_bytes);
    let signature = Signature::from_bytes(&sig_array);

    verifying_key.verify(chain_hash.as_bytes(), &signature).is_ok()
}

/// Generates HMAC-SHA256 signature for Enterprise Hub Dual-Key authentication
pub fn sign_dac_chain_hash(chain_hash: &str, secret_key: &str) -> Option<String> {
    if secret_key.is_empty() || chain_hash.is_empty() {
        return None;
    }

    let mut mac = HmacSha256::new_from_slice(secret_key.as_bytes()).ok()?;
    mac.update(chain_hash.as_bytes());
    let result = mac.finalize();
    Some(hex::encode(result.into_bytes()))
}

/// Verifies HMAC-SHA256 signature in constant-time
pub fn verify_dac_chain_hash(chain_hash: &str, signature: &str, secret_key: &str) -> bool {
    if secret_key.is_empty() || signature.is_empty() || chain_hash.is_empty() {
        return false;
    }

    let expected = match sign_dac_chain_hash(chain_hash, secret_key) {
        Some(s) => s,
        None => return false,
    };

    let a = expected.as_bytes();
    let b = signature.as_bytes();
    if a.len() != b.len() {
        return false;
    }

    a.ct_eq(b).into()
}
