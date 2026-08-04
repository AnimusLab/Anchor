use std::fs::File;
use std::path::{Path, PathBuf};
use rayon::prelude::*;
use memmap2::Mmap;

#[derive(Debug, Clone)]
pub struct ScannedFileResult {
    pub path: PathBuf,
    pub line_count: usize,
    pub is_valid: bool,
}

pub struct DirectoryScanner;

impl DirectoryScanner {
    /// Walk directory and collect all target source code paths (.py, .ts, .js)
    pub fn collect_files(root: &Path) -> Vec<PathBuf> {
        let mut files = Vec::new();
        if let Ok(entries) = std::fs::read_dir(root) {
            for entry in entries.flatten() {
                let path = entry.path();
                let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
                
                // Skip ignored directories
                if name.starts_with('.') || name == "node_modules" || name == "__pycache__" || name == "target" || name == "build" {
                    continue;
                }

                if path.is_dir() {
                    files.extend(Self::collect_files(&path));
                } else if path.is_file() {
                    if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                        if matches!(ext, "py" | "ts" | "tsx" | "js" | "jsx" | "mjs" | "anchor") {
                            files.push(path);
                        }
                    }
                }
            }
        }
        files
    }

    /// Parallel zero-copy scan of all collected source files
    pub fn scan_parallel(file_paths: &[PathBuf]) -> Vec<ScannedFileResult> {
        file_paths
            .par_iter()
            .map(|path| {
                if let Ok(file) = File::open(path) {
                    if let Ok(mmap) = unsafe { Mmap::map(&file) } {
                        let line_count = mmap.split(|&b| b == b'\n').count();
                        return ScannedFileResult {
                            path: path.clone(),
                            line_count,
                            is_valid: true,
                        };
                    }
                }
                ScannedFileResult {
                    path: path.clone(),
                    line_count: 0,
                    is_valid: false,
                }
            })
            .collect()
    }
}
