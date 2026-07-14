# =============================================================================
# anchor/runtime/relay_protocol.py
#
# WebSocket implementation of the Hub ↔ Spoke Sovereign Relay.
# Uses `websockets` library to match the FastAPI WebSocket protocol in the Hub.
# =============================================================================

import os
import json
import asyncio
import threading
import time
import base64
import hashlib
import logging
import secrets
from typing import Optional, List, Dict, Any

import websockets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("anchor.relay")

# ── CRYPTOGRAPHIC UTILITIES ──────────────────────────────────

def encrypt_payload(payload: str, key_str: str) -> tuple[str, str]:
    """Encrypts a string payload with key_str using AES-256-GCM. Returns (nonce_b64, ciphertext_b64)."""
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ciphertext = aesgcm.encrypt(nonce, payload.encode('utf-8'), None)
    return base64.b64encode(nonce).decode('utf-8'), base64.b64encode(ciphertext).decode('utf-8')


def decrypt_payload(iv_b64: str, ciphertext_b64: str, key_str: str) -> str:
    """Decrypts a base64 ciphertext using iv_b64 (nonce) and key_str using AES-256-GCM."""
    key = hashlib.sha256(key_str.encode('utf-8')).digest()
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')


# ── SPOKE RELAY CLIENT ────────────────────────────────────────

class SpokeRelayClient:
    """
    On-premise Spoke daemon relaying ZK headers and responding to forensic pulls
    over secure WebSockets.
    """
    def __init__(self, host: str = "", port: Optional[int] = None, secret_key: str = "", project_name: str = "project", audit_log_path: str = ".anchor/runtime_chain.jsonl", url: Optional[str] = None):
        if url:
            self.url = url
        elif port is not None:
            self.url = f"ws://{host}:{port}/ws/spoke"
        else:
            self.url = host
            
        self.secret_key = secret_key
        self.project_name = project_name
        self.hub_id = os.environ.get("ANCHOR_HUB_ID", os.environ.get("HUB_ID", project_name))
        self.audit_log_path = audit_log_path
        self.ws = None
        self.loop = None
        self.thread = None
        self.running = False

    def start(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect_and_listen())
        except asyncio.CancelledError:
            pass
        finally:
            try:
                pending = asyncio.all_tasks(self.loop)
                if pending:
                    for task in pending:
                        task.cancel()
                    # Run until all pending tasks are fully cancelled
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            self.loop.close()

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._close(), self.loop)
            self.thread.join(timeout=3.0)

    async def _close(self):
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
        for task in asyncio.all_tasks(self.loop):
            task.cancel()

    async def _connect_and_listen(self):
        while self.running:
            try:
                # Normalise WebSocket URL (must start with ws:// or wss://)
                target_url = self.url
                if not target_url.startswith("ws://") and not target_url.startswith("wss://"):
                    target_url = f"ws://{target_url}"
                
                # Append hub_id to query string
                sep = "&" if "?" in target_url else "?"
                full_url = f"{target_url}{sep}hub_id={self.hub_id}"

                logger.info(f"[RELAY] Connecting to Hub at {full_url}...")
                async with websockets.connect(full_url) as ws:
                    self.ws = ws
                    
                    # Step 1: Handshake (Send SPOKE_REGISTER)
                    reg_msg = {
                        "type": "SPOKE_REGISTER",
                        "hub_id": self.hub_id,
                        "payload": {
                            "regional_key": self.secret_key,
                            "spoke_version": "5.0.0"
                        }
                    }
                    await ws.send(json.dumps(reg_msg))
                    logger.info("[RELAY] SPOKE_REGISTER sent, waiting for Hub ACK...")

                    # Wait for HUB_ACK/HUB_REJECT
                    raw_resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    resp = json.loads(raw_resp)
                    if resp.get("type") == "HUB_REJECT":
                        msg = f"Hub rejected registration: {resp.get('payload')}"
                        logger.error(f"[RELAY] {msg}")
                        raise RuntimeError(msg)
                    elif resp.get("type") == "HUB_ACK":
                        logger.info("[RELAY] Hub ACK received. Spoke is LIVE on the Grid.")
                    
                    # Step 2: Message listening loop
                    async for raw_msg in ws:
                        try:
                            msg = json.loads(raw_msg)
                        except Exception:
                            continue
                        
                        m_type = msg.get("type")
                        if m_type == "FORENSIC_PULL" or m_type == "pull":
                            payload = msg.get("payload") or msg
                            request_id = payload.get("request_id") or "legacy_req"
                            entry_id = payload.get("entry_id")
                            clearance_id = payload.get("clearance_id") or "auditor_legacy"
                            asyncio.create_task(self._handle_forensic_pull(request_id, entry_id, clearance_id))
                        elif m_type == "PING":
                            pong = {
                                "type": "PONG",
                                "hub_id": self.hub_id
                            }
                            await ws.send(json.dumps(pong))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if not self.running:
                    break
                logger.warning(f"[RELAY] Hub connection lost: {e} — reconnecting in 5s...")
                self.ws = None
                await asyncio.sleep(5)

    async def _handle_forensic_pull(self, request_id: str, entry_id: str, clearance_id: str):
        if not entry_id:
            return
        
        logger.info(f"[RELAY] FORENSIC_PULL received for entry {entry_id} (auditor: {clearance_id})")
        
        target_entry = None
        if os.path.exists(self.audit_log_path):
            try:
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        entry = json.loads(line)
                        if entry.get("entry_id") == entry_id:
                            target_entry = entry
                            break
            except Exception as e:
                logger.error(f"[RELAY] Error reading audit log: {e}")

        if not target_entry:
            response = {
                "type": "FORENSIC_RESPONSE",
                "hub_id": self.hub_id,
                "payload": {
                    "request_id": request_id,
                    "entry_id": entry_id,
                    "error": "ENTRY_NOT_FOUND"
                }
            }
        else:
            try:
                # Encrypt sensitive raw contents (telemetry + violations)
                raw_payload = {
                    "telemetry": target_entry.get("telemetry"),
                    "violations": target_entry.get("violations")
                }
                # Derive AES key from secret_key matching Hub's SHA256 hashing
                key_bytes = hashlib.sha256(self.secret_key.encode('utf-8')).digest()
                aesgcm = AESGCM(key_bytes)
                nonce = secrets.token_bytes(12)
                ciphertext = aesgcm.encrypt(nonce, json.dumps(raw_payload).encode('utf-8'), None)
                
                response = {
                    "type": "FORENSIC_RESPONSE",
                    "hub_id": self.hub_id,
                    "payload": {
                        "request_id": request_id,
                        "entry_id": entry_id,
                        "encrypted_payload": base64.b64encode(ciphertext).decode('utf-8'),
                        "nonce": base64.b64encode(nonce).decode('utf-8'),
                        # Legacy keys for test backward compatibility
                        "iv": base64.b64encode(nonce).decode('utf-8'),
                        "payload": base64.b64encode(ciphertext).decode('utf-8')
                    }
                }
            except Exception as e:
                response = {
                    "type": "FORENSIC_RESPONSE",
                    "hub_id": self.hub_id,
                    "payload": {
                        "request_id": request_id,
                        "entry_id": entry_id,
                        "error": f"Encryption failed: {e}"
                    }
                }
        
        if self.ws:
            try:
                await self.ws.send(json.dumps(response))
                logger.info(f"[RELAY] Forensic payload dispatched for entry {entry_id}")
            except Exception as e:
                logger.error(f"[RELAY] Failed to send forensic response: {e}")

    def send_header(self, entry_dict: dict):
        """Dispatches a lightweight ZK header representing the audit entry."""
        if not self.loop or not self.running:
            return
            
        header_msg = {
            "type": "AUDIT_HEADER",
            "hub_id": self.hub_id,
            "payload": {
                "entry_id": entry_dict.get("entry_id"),
                "project_name": self.project_name,
                "type": "runtime_check" if entry_dict.get("governance_status", {}).get("is_compliant") else "runtime_violation",
                "is_compliant": bool(entry_dict.get("governance_status", {}).get("is_compliant")),
                "chain_hash": entry_dict.get("cryptography", {}).get("chain_hash"),
                "signature": entry_dict.get("cryptography", {}).get("signature"),
                "rule_id": entry_dict.get("violations", [{}])[0].get("id") if entry_dict.get("violations") else None,
                "timestamp": entry_dict.get("timestamp") or str(int(time.time()))
            }
        }
        
        asyncio.run_coroutine_threadsafe(self._send_message(header_msg), self.loop)

    async def _send_message(self, msg: dict):
        if self.ws:
            try:
                await self.ws.send(json.dumps(msg))
                logger.info(f"[RELAY] Audit header pushed for entry {msg['payload']['entry_id']}")
            except Exception as e:
                logger.debug(f"Failed to send relay message: {e}")


# ── MOCK HUB SERVER ───────────────────────────────────────────

class MockHubServer:
    """
    Simulated Cloud Hub WebSocket server for ZK header reception and FORENSIC_PULL tests.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.loop = None
        self.thread = None
        self.running = False
        self.active_ws = None
        self.received_headers: List[Dict[str, Any]] = []
        self.received_pulls: Dict[str, Dict[str, Any]] = {}
        self.pull_events: Dict[str, threading.Event] = {}

    def start(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._start_server())
        except asyncio.CancelledError:
            pass
        finally:
            try:
                pending = asyncio.all_tasks(self.loop)
                if pending:
                    for task in pending:
                        task.cancel()
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            self.loop.close()

    async def _close(self):
        if self.active_ws:
            try:
                await self.active_ws.close()
            except:
                pass
        if self.server:
            try:
                self.server.close()
                await self.server.wait_closed()
            except:
                pass
        for task in asyncio.all_tasks(self.loop):
            task.cancel()

    async def _start_server(self):
        async def handler(websocket):
            self.active_ws = websocket
            try:
                # Step 1: Wait for SPOKE_REGISTER
                raw = await websocket.recv()
                reg = json.loads(raw)
                if reg.get("type") != "SPOKE_REGISTER":
                    await websocket.close(4002)
                    return
                
                # Send HUB_ACK
                ack = {
                    "type": "HUB_ACK",
                    "hub_id": reg.get("hub_id"),
                    "payload": {"status": "OK", "message": "SPOKE_REGISTERED"}
                }
                await websocket.send(json.dumps(ack))
                
                # Step 2: Listen for messages
                async for raw_msg in websocket:
                    msg = json.loads(raw_msg)
                    m_type = msg.get("type")
                    if m_type == "AUDIT_HEADER":
                        payload = msg.get("payload") or {}
                        if "status" not in payload:
                            is_compliant = payload.get("is_compliant", True)
                            payload["status"] = "CLEAN" if is_compliant else "VIOLATION"
                        self.received_headers.append(payload)
                    elif m_type == "FORENSIC_RESPONSE" or m_type == "pull_response":
                        payload = msg.get("payload") or msg
                        entry_id = payload.get("entry_id")
                        
                        # Populate both old and new formats for test compatibility
                        res_dict = {
                            "entry_id": entry_id,
                            "encrypted_payload": payload.get("encrypted_payload"),
                            "nonce": payload.get("nonce"),
                            # Legacy keys for test_relay_protocol.py
                            "iv": payload.get("nonce") or payload.get("iv"),
                            "payload": payload.get("encrypted_payload") or payload.get("payload")
                        }
                        self.received_pulls[entry_id] = res_dict
                        if entry_id in self.pull_events:
                            self.pull_events[entry_id].set()
            except Exception:
                pass
            finally:
                if self.active_ws == websocket:
                    self.active_ws = None

        self.server = await websockets.serve(handler, self.host, self.port)
        try:
            while self.running:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            raise

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._close(), self.loop)
            self.thread.join(timeout=3.0)

    def request_forensic_pull(self, entry_id: str, timeout: float = 3.0) -> Optional[dict]:
        if not self.active_ws or not self.loop:
            return None
        
        event = threading.Event()
        self.pull_events[entry_id] = event
        
        request_id = str(int(time.time()))
        req = {
            "type": "FORENSIC_PULL",
            "hub_id": "mock_hub",
            "payload": {
                "request_id": request_id,
                "entry_id": entry_id,
                "clearance_id": "auditor_mock"
            }
        }
        
        asyncio.run_coroutine_threadsafe(self.active_ws.send(json.dumps(req)), self.loop)
        
        if event.wait(timeout):
            return self.received_pulls.get(entry_id)
        return None
