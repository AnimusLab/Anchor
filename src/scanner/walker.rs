use memmap2::MmapOptions;
use rayon::prelude::*;
use regex::RegexSet;
use std::fs::File;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

pub struct ScannedFileResult {
    pub file_path: String,
    pub line_count: usize,
    pub matches: Vec<LineViolationMatch>,
}

pub struct LineViolationMatch {
    pub line_number: usize,
    pub line_content: String,
    pub matched_rule_indices: Vec<usize>,
}

pub struct DirectoryScanner;

impl DirectoryScanner {
    /// Recursively collect all relevant code files (.py, .ts, .tsx, .js, .go, .rs)
    pub fn collect_files(root: &Path) -> Vec<PathBuf> {
        WalkDir::new(root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter(|e| {
                let p = e.path();
                // Exclude .git, .anchor, node_modules, and build dirs
                let p_str = p.to_string_lossy();
                if p_str.contains(".git") || p_str.contains(".anchor") || p_str.contains("node_modules") || p_str.contains("__pycache__") || p_str.contains("target") {
                    return false;
                }
                if let Some(ext) = p.extension() {
                    let s = ext.to_string_lossy();
                    s == "py" || s == "ts" || s == "tsx" || s == "js" || s == "go" || s == "rs" || s == "anchor"
                } else {
                    false
                }
            })
            .map(|e| e.path().to_path_buf())
            .collect()
    }

    /// Parallel scan across files using rayon and memmap2 line-by-line matching
    pub fn scan_parallel_with_regex(files: &[PathBuf], regex_set: &RegexSet) -> Vec<ScannedFileResult> {
        files
            .par_iter()
            .filter_map(|path| {
                let file = File::open(path).ok()?;
                let metadata = file.metadata().ok()?;
                
                // Safe 0-byte check to prevent memmap2 panics
                if metadata.len() == 0 {
                    return Some(ScannedFileResult {
                        file_path: path.to_string_lossy().to_string(),
                        line_count: 0,
                        matches: Vec::new(),
                    });
                }

                let mmap = unsafe { MmapOptions::new().map(&file).ok()? };
                let content_str = std::str::from_utf8(&mmap).ok()?;

                let mut line_matches = Vec::new();
                let mut line_count = 0;

                for (idx, line) in content_str.lines().enumerate() {
                    line_count += 1;
                    let matches = regex_set.matches(line);
                    if matches.matched_any() {
                        let matched_indices: Vec<usize> = matches.into_iter().collect();
                        line_matches.push(LineViolationMatch {
                            line_number: idx + 1,
                            line_content: line.trim().to_string(),
                            matched_rule_indices: matched_indices,
                        });
                    }
                }

                Some(ScannedFileResult {
                    file_path: path.to_string_lossy().to_string(),
                    line_count,
                    matches: line_matches,
                })
            })
            .collect()
    }

    /// Backwards compatible simple scan
    pub fn scan_parallel(files: &[PathBuf]) -> Vec<ScannedFileResult> {
        files
            .par_iter()
            .filter_map(|path| {
                let file = File::open(path).ok()?;
                let metadata = file.metadata().ok()?;
                if metadata.len() == 0 {
                    return Some(ScannedFileResult {
                        file_path: path.to_string_lossy().to_string(),
                        line_count: 0,
                        matches: Vec::new(),
                    });
                }
                let mmap = unsafe { MmapOptions::new().map(&file).ok()? };
                let content_str = std::str::from_utf8(&mmap).ok()?;
                let line_count = content_str.lines().count();
                Some(ScannedFileResult {
                    file_path: path.to_string_lossy().to_string(),
                    line_count,
                    matches: Vec::new(),
                })
            })
            .collect()
    }
}
