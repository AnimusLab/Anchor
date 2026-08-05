"""
Anchor Ledger Offline Re-Sync Worker
Monitors connectivity to hub.animuslab.dev and automatically flushes queued local journal blocks.
"""

import asyncio
import os
import httpx
from typing import Optional

try:
    from anchor_core_rs import AnchorEngine
except ImportError:
    class AnchorEngine:
        def get_pending_ledger_count(self) -> int:
            return 0
        def flush_offline_queue(self) -> int:
            return 0

class LedgerSyncWorker:
    def __init__(self, hub_url: Optional[str] = None):
        self.hub_url = hub_url or os.environ.get("ANCHOR_HUB_URL", "http://localhost:3000/api/v1/ingest")
        self.engine = AnchorEngine()
        self.is_running = False

    async def start_reconnect_loop(self, poll_interval_seconds: int = 15):
        """
        Background worker loop polling connectivity to hub.animuslab.dev
        """
        self.is_running = True
        while self.is_running:
            try:
                pending_count = self.engine.get_pending_ledger_count()
                if pending_count > 0:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        resp = await client.get(f"{self.hub_url}/health")
                        if resp.status_code == 200:
                            # Hub restored! Flush queued blocks
                            flushed = self.engine.flush_offline_queue()
                            print(f"[Anchor Ledger Sync] Connection restored. Flushed {flushed} queued DAC blocks to {self.hub_url}.")
            except Exception:
                # Hub still offline — continue caching locally
                pass

            await asyncio.sleep(poll_interval_seconds)

    def stop(self):
        self.is_running = False
