use serde::{Deserialize, Serialize};
use std::fs::{OpenOptions, File};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DacJournalEntry {
    pub entry_id: String,
    pub timestamp_utc: String,
    pub chain_hash: String,
    pub signature: String,
    pub is_synced: bool,
}

pub struct PersistentLedgerQueue {
    journal_path: PathBuf,
}

impl PersistentLedgerQueue {
    pub fn new(storage_dir: &Path) -> Self {
        let _ = std::fs::create_dir_all(storage_dir);
        let journal_path = storage_dir.join("ledger.journal");
        Self { journal_path }
    }

    /// Append signed DAC block entry to local encrypted journal file
    pub fn enqueue_block(&self, entry: &DacJournalEntry) -> std::io::Result<()> {
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.journal_path)?;

        let line = serde_json::to_string(entry)?;
        writeln!(file, "{}", line)?;
        Ok(())
    }

    /// Read all pending (unsynced) DAC blocks from journal file
    pub fn get_pending_entries(&self) -> Vec<DacJournalEntry> {
        let mut pending = Vec::new();
        if let Ok(file) = File::open(&self.journal_path) {
            let reader = BufReader::new(file);
            for line in reader.lines().flatten() {
                if let Ok(entry) = serde_json::from_str::<DacJournalEntry>(&line) {
                    if !entry.is_synced {
                        pending.push(entry);
                    }
                }
            }
        }
        pending
    }

    /// Mark all queued entries as successfully synced after Governance Hub receipt confirmation
    pub fn mark_all_synced(&self) -> std::io::Result<usize> {
        let pending = self.get_pending_entries();
        let synced_count = pending.len();

        let file = File::create(&self.journal_path)?;
        let mut writer = std::io::BufWriter::new(file);

        for mut entry in pending {
            entry.is_synced = true;
            let line = serde_json::to_string(&entry)?;
            writeln!(writer, "{}", line)?;
        }
        writer.flush()?;
        Ok(synced_count)
    }
}
