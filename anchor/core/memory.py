import sqlite3
import os
from pathlib import Path
from typing import Optional, Tuple

class GlobalMemory:
    def __init__(self):
        # Store DB in user's home directory so it persists across projects
        home_dir = Path.home() / ".anchor"
        home_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = home_dir / "brain.db"
        
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self):
        """Initialize the schema if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbol_stats (
                name TEXT PRIMARY KEY,
                total_scans INTEGER DEFAULT 0,
                drift_detected_count INTEGER DEFAULT 0,
                last_verdict TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def record_scan(self, symbol_name: str, verdict: str):
        """
        Learns from a scan. 
        Updates the global stats for this symbol.
        """
        is_drift = verdict not in ("aligned", "confidence_too_low")
        drift_increment = 1 if is_drift else 0
        
        cursor = self.conn.cursor()
        
        # Check if symbol exists
        cursor.execute("SELECT name FROM symbol_stats WHERE name = ?", (symbol_name,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE symbol_stats 
                SET total_scans = total_scans + 1,
                    drift_detected_count = drift_detected_count + ?,
                    last_verdict = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (drift_increment, verdict, symbol_name))
        else:
            cursor.execute("""
                INSERT INTO symbol_stats (name, total_scans, drift_detected_count, last_verdict)
                VALUES (?, 1, ?, ?)
            """, (symbol_name, drift_increment, verdict))
            
        self.conn.commit()
        # print(f"DEBUG: Brain updated for {symbol_name}")

    def get_stats(self, symbol_name: str) -> Optional[Tuple[int, int]]:
        """Returns (total_scans, drift_count) or None if new."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT total_scans, drift_detected_count FROM symbol_stats WHERE name = ?", (symbol_name,))
        return cursor.fetchone()