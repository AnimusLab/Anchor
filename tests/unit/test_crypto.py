import pytest
import os
from anchor.core.crypto import sign_chain_hash, verify_chain_hash

def test_sign_and_verify_with_mat(monkeypatch):
    # Setup test MAT
    test_mat = "test-secret-key-12345"
    monkeypatch.setenv("ANCHOR_MAT", test_mat)
    
    chain_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # SHA-256 of empty string
    
    signature = sign_chain_hash(chain_hash)
    assert signature is not None
    assert len(signature) == 64
    
    # Verify
    assert verify_chain_hash(chain_hash, signature) == True
    
    # Verify failure with wrong hash
    assert verify_chain_hash("wrong-hash", signature) == False
    
    # Verify failure with wrong signature
    assert verify_chain_hash(chain_hash, "wrong-signature") == False

def test_sign_missing_mat(monkeypatch):
    monkeypatch.delenv("ANCHOR_MAT", raising=False)
    monkeypatch.delenv("ANCHOR_SECRET_KEY", raising=False)
    
    chain_hash = "abc"
    assert sign_chain_hash(chain_hash) is None

def test_verify_missing_mat(monkeypatch):
    monkeypatch.delenv("ANCHOR_MAT", raising=False)
    monkeypatch.delenv("ANCHOR_SECRET_KEY", raising=False)
    
    assert verify_chain_hash("abc", "def") == False

def test_standardization_secret_key(monkeypatch):
    # Verify that it still works with the old key name
    test_key = "old-legacy-key"
    monkeypatch.delenv("ANCHOR_MAT", raising=False)
    monkeypatch.setenv("ANCHOR_SECRET_KEY", test_key)
    
    chain_hash = "abc"
    signature = sign_chain_hash(chain_hash)
    assert signature is not None
    assert verify_chain_hash(chain_hash, signature) == True
