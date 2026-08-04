use hmac::{Hmac, Mac};
use sha2::Sha256;
use subtle::ConstantTimeEq;

type HmacSha256 = Hmac<Sha256>;

/// Generates HMAC-SHA256 cryptographic signature over a Decision Audit Chain (DAC) block hash
pub fn sign_dac_chain_hash(chain_hash: &str, secret_key: &str) -> Option<String> {
    if secret_key.is_empty() || chain_hash.is_empty() {
        return None;
    }

    let mut mac = HmacSha256::new_from_slice(secret_key.as_bytes()).ok()?;
    mac.update(chain_hash.as_bytes());
    let result = mac.finalize();
    Some(hex::encode(result.into_bytes()))
}

/// Verifies cryptographic signature over a DAC block hash in constant-time to prevent side-channel timing attacks
pub fn verify_dac_chain_hash(chain_hash: &str, signature: &str, secret_key: &str) -> bool {
    if secret_key.is_empty() || signature.is_empty() || chain_hash.is_empty() {
        return false;
    }

    let expected = match sign_dac_chain_hash(chain_hash, secret_key) {
        Some(s) => s,
        None => return false,
    };

    // Constant-time byte-by-byte comparison using subtle crate to prevent timing side-channel attacks
    let a = expected.as_bytes();
    let b = signature.as_bytes();
    if a.len() != b.len() {
        return false;
    }

    a.ct_eq(b).into()
}

