import os
import sqlite3
from typing import Optional, Tuple
from datetime import datetime

class GlobalMemory:
    """
    Local SQLite persistence engine ('The Brain').
    Stores audit scan history and tracks symbol drift frequency across projects.
    """
    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            home_dir = os.path.expanduser("~")
            anchor_dir = os.path.join(home_dir, ".anchor")
            os.makedirs(anchor_dir, exist_ok=True)
            db_path = os.path.join(anchor_dir, "brain.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    symbol TEXT PRIMARY KEY,
                    scan_count INTEGER DEFAULT 1,
                    last_verdict TEXT,
                    last_scanned TIMESTAMP
                )
            """)
            conn.commit()

    def record_scan(self, symbol: str, verdict: str) -> None:
        """Records a scan event, incrementing scan_count and updating last_verdict."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT scan_count FROM scans WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            if row:
                count = row[0] + 1
                cursor.execute(
                    "UPDATE scans SET scan_count = ?, last_verdict = ?, last_scanned = ? WHERE symbol = ?",
                    (count, verdict, now, symbol)
                )
            else:
                cursor.execute(
                    "INSERT INTO scans (symbol, scan_count, last_verdict, last_scanned) VALUES (?, 1, ?, ?)",
                    (symbol, verdict, now)
                )
            conn.commit()

    def get_stats(self, symbol: str) -> Optional[Tuple[int, str]]:
        """Returns (scan_count, last_verdict) for a symbol if it exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT scan_count, last_verdict FROM scans WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            if row:
                return (row[0], row[1])
            return None
