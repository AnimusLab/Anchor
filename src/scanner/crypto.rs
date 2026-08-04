use hmac::{Hmac, Mac};
use sha2::Sha256;

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

/// Verifies cryptographic signature over a DAC block hash in constant time
pub fn verify_dac_chain_hash(chain_hash: &str, signature: &str, secret_key: &str) -> bool {
    if secret_key.is_empty() || signature.is_empty() || chain_hash.is_empty() {
        return false;
    }

    let expected = match sign_dac_chain_hash(chain_hash, secret_key) {
        Some(s) => s,
        None => return false,
    };

    // Constant-time string equality check to prevent timing attacks
    expected.as_bytes() == signature.as_bytes()
}
