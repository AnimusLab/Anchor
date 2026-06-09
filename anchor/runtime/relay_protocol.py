# =============================================================================
# anchor/runtime/relay_protocol.py
#
# Zero-dependency implementation of the Hub ↔ Spoke Sovereign Relay.
#
# Provides:
#   1. SHA256-CTR symmetric stream cipher for raw payload encryption.
#   2. SpokeRelayClient: Background TCP client forwarding ZK headers to Hub.
#   3. MockHubServer: Testing server for ZK header reception and FORENSIC_PULL.
# =============================================================================

import os
import json
import socket
import base64
import hashlib
import logging
import threading
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger("anchor.relay")

# ── CRYPTOGRAPHIC UTILITIES ──────────────────────────────────

def _xor_crypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """SHA-256 CTR-mode stream cipher using only stdlib."""
    out = bytearray()
    block_size = 32  # SHA-256 output size
    for i in range(0, len(data), block_size):
        block = data[i:i+block_size]
        h = hashlib.sha256(key + iv + str(i // block_size).encode('utf-8')).digest()
        for b, k in zip(block, h):
            out.append(b ^ k)
    return bytes(out)


def encrypt_payload(payload: str, key_str: str) -> tuple[str, str]:
    """Encrypts a string payload with key_str. Returns (iv_hex, ciphertext_b64)."""
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    iv = os.urandom(16)
    ciphertext = _xor_crypt(payload.encode('utf-8'), key, iv)
    return iv.hex(), base64.b64encode(ciphertext).decode('utf-8')


def decrypt_payload(iv_hex: str, ciphertext_b64: str, key_str: str) -> str:
    """Decrypts a base64 ciphertext using iv_hex and key_str."""
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    iv = bytes.fromhex(iv_hex)
    ciphertext = base64.b64decode(ciphertext_b64.encode('utf-8'))
    plaintext = _xor_crypt(ciphertext, key, iv)
    return plaintext.decode('utf-8')


# ── SPOKE RELAY CLIENT ────────────────────────────────────────

class SpokeRelayClient:
    """
    On-premise Spoke daemon relaying ZK headers and responding to forensic pulls.
    """
    def __init__(self, host: str, port: int, secret_key: str, audit_log_path: str = ".anchor/runtime_chain.jsonl"):
        self.host = host
        self.port = port
        self.secret_key = secret_key
        self.audit_log_path = audit_log_path
        self.sock = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2.0)

    def send_header(self, entry_dict: dict):
        """Dispatches a lightweight ZK header representing the audit entry."""
        header_msg = {
            "type": "header",
            "entry_id": entry_dict.get("entry_id"),
            "timestamp": entry_dict.get("timestamp"),
            "is_compliant": entry_dict.get("governance_status", {}).get("is_compliant"),
            "status": entry_dict.get("governance_status", {}).get("status"),
            "chain_hash": entry_dict.get("cryptography", {}).get("chain_hash")
        }
        self.send_message(header_msg)

    def send_message(self, msg: dict):
        with self.lock:
            if self.sock:
                try:
                    payload = json.dumps(msg) + "\n"
                    self.sock.sendall(payload.encode('utf-8'))
                except Exception as e:
                    logger.debug(f"Failed to send relay message: {e}")

    def _run_loop(self):
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                
                buffer = ""
                while self.running:
                    data = self.sock.recv(4096).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            self._handle_message(line.strip())
            except Exception as e:
                if self.running:
                    time.sleep(1.0)

    def _handle_message(self, line: str):
        try:
            msg = json.loads(line)
            if msg.get("type") == "pull":
                self._handle_forensic_pull(msg.get("entry_id"))
        except Exception as e:
            logger.debug(f"Relay client error parsing message: {e}")

    def _handle_forensic_pull(self, entry_id: str):
        if not entry_id:
            return

        target_entry = None
        if os.path.exists(self.audit_log_path):
            try:
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry.get("entry_id") == entry_id:
                            target_entry = entry
                            break
            except Exception as e:
                logger.error(f"Error reading audit log: {e}")

        if not target_entry:
            response = {"type": "pull_response", "entry_id": entry_id, "error": "Not Found"}
        else:
            try:
                # Encrypt only the sensitive raw content (payload)
                raw_payload = json.dumps({
                    "telemetry": target_entry.get("telemetry"),
                    "violations": target_entry.get("violations")
                })
                iv, ciphertext = encrypt_payload(raw_payload, self.secret_key)
                response = {
                    "type": "pull_response",
                    "entry_id": entry_id,
                    "iv": iv,
                    "payload": ciphertext
                }
            except Exception as e:
                response = {"type": "pull_response", "entry_id": entry_id, "error": f"Encryption failed: {e}"}

        self.send_message(response)


# ── MOCK HUB SERVER ───────────────────────────────────────────

class MockHubServer:
    """
    Simulated Cloud Hub broker verifying incoming ZK headers and requesting forensic pulls.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server_sock = None
        self.running = False
        self.spoke_sock = None
        self.thread = None
        self.received_headers: List[Dict[str, Any]] = []
        self.received_pulls: Dict[str, Dict[str, Any]] = {}
        self.pull_events: Dict[str, threading.Event] = {}

    def start(self):
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(1)
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
        if self.spoke_sock:
            try:
                self.spoke_sock.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2.0)

    def _accept_loop(self):
        while self.running:
            try:
                sock, _ = self.server_sock.accept()
                self.spoke_sock = sock
                
                buffer = ""
                while self.running:
                    data = sock.recv(4096).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            self._handle_message(line.strip())
            except Exception:
                break

    def _handle_message(self, line: str):
        try:
            msg = json.loads(line)
            m_type = msg.get("type")
            if m_type == "header":
                self.received_headers.append(msg)
            elif m_type == "pull_response":
                entry_id = msg.get("entry_id")
                self.received_pulls[entry_id] = msg
                if entry_id in self.pull_events:
                    self.pull_events[entry_id].set()
        except Exception as e:
            logger.debug(f"Hub server error parsing message: {e}")

    def request_forensic_pull(self, entry_id: str, timeout: float = 3.0) -> Optional[dict]:
        """Triggers a FORENSIC_PULL request and blocks until response is received or times out."""
        if not self.spoke_sock:
            return None
        
        event = threading.Event()
        self.pull_events[entry_id] = event
        
        try:
            req = {"type": "pull", "entry_id": entry_id}
            payload = json.dumps(req) + "\n"
            self.spoke_sock.sendall(payload.encode('utf-8'))
            
            if event.wait(timeout):
                return self.received_pulls.get(entry_id)
        except Exception as e:
            logger.error(f"Failed to request forensic pull: {e}")
        finally:
            self.pull_events.pop(entry_id, None)
        return None
