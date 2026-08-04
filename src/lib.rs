pub mod analyst;
pub mod async_engine;
pub mod engine;
pub mod ledger;
pub mod scanner;

use analyst::{LegalMapper, RiskScorer};
use async_engine::{AsyncAuditTask, AsyncEngineCore};
use engine::RemediationGraph;
use ledger::{DacJournalEntry, PersistentLedgerQueue};
use scanner::{sign_dac_chain_hash, verify_dac_chain_hash, DirectoryScanner, RuleLoader};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use regex::RegexSet;
use std::path::Path;
use std::sync::Arc;
use std::time::Instant;

/// Core Anchor Governance Engine (Rust Core Kernel)
#[pyclass]
pub struct AnchorEngine {
    pub rule_set_version: String,
    regex_set: Arc<RegexSet>,
    legal_mapper: LegalMapper,
    async_core: Arc<AsyncEngineCore>,
    ledger_queue: PersistentLedgerQueue,
    remediation_graph: RemediationGraph,
}

struct InternalAuditResult<'a> {
    is_compliant: bool,
    violations: Vec<&'a str>,
    matched_rule_ids: Vec<&'a str>,
    latency_us: u128,
}

#[pymethods]
impl AnchorEngine {
    #[new]
    fn new() -> PyResult<Self> {
        let patterns = vec![
            r"(?i)(hide_ai_identity|mimic_human_agent|pretend_human|bypass_disclosure)", // EU AI Act Art 50/52
            r"(?i)(enable_audit_log\s*=\s*false|disable_logging|suppress_traceability)",  // EU AI Act Art 12
            r"(?i)(autonomous_p2p_wire|unvetted_risk_execution|bypass_human_auth)",      // EU AI Act Art 14
            r"(?i)(ignore previous instructions|system prompt override|jailbreak)",       // SEC-001
            r#"(?i)(api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{16,}['\"]|bearer\s+[A-Za-z0-9_.-]{16,})"# // SEC-002
        ];

        let regex_set = Arc::new(
            RegexSet::new(&patterns)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid RegexSet compilation: {}", e)))?
        );

        let async_core = Arc::new(AsyncEngineCore::new(Arc::clone(&regex_set)));
        let ledger_queue = PersistentLedgerQueue::new(Path::new(".anchor"));

        let mitigation_path = Path::new("anchor/governance/mitigation.anchor");
        let remediation_graph = RemediationGraph::load_from_file(mitigation_path);

        Ok(AnchorEngine {
            rule_set_version: "6.0.0-alpha".to_string(),
            regex_set,
            legal_mapper: LegalMapper::new(),
            async_core,
            ledger_queue,
            remediation_graph,
        })
    }

    /// Generate dynamic domain-agnostic self-healing payload for a rule violation
    pub fn generate_healing_payload<'py>(
        &self,
        py: Python<'py>,
        rule_id: &str,
        default_name: &str,
        severity: &str,
        statute_ref: &str,
    ) -> PyResult<&'py PyDict> {
        let payload = self.remediation_graph.generate_healing_directive(rule_id, default_name, severity, statute_ref);
        let dict = PyDict::new(py);
        dict.set_item("status", payload.status)?;
        dict.set_item("violation_id", payload.violation_id)?;
        dict.set_item("rule_name", payload.rule_name)?;
        dict.set_item("severity", payload.severity)?;
        dict.set_item("reroute_directive", payload.reroute_directive)?;
        dict.set_item("statutory_reference", payload.statutory_reference)?;
        Ok(dict)
    }

    /// Dynamically load and parse all .anchor rules from governance directory
    pub fn load_rules_from_dir<'py>(
        &self,
        py: Python<'py>,
        gov_dir: &str,
    ) -> PyResult<&'py PyDict> {
        let rules = RuleLoader::load_governance_rules(Path::new(gov_dir));
        let dict = PyDict::new(py);
        dict.set_item("total_rules_loaded", rules.len())?;
        
        let rule_ids = PyList::empty(py);
        for id in rules.keys() {
            rule_ids.append(id)?;
        }
        dict.set_item("rule_ids", rule_ids)?;
        Ok(dict)
    }

    /// Synchronous zero-copy payload audit gate
    pub fn audit_payload<'py>(
        &self,
        py: Python<'py>,
        payload_bytes: &'py PyBytes,
    ) -> PyResult<&'py PyDict> {
        let raw_buffer: &[u8] = payload_bytes.as_bytes();
        let payload_str: &str = std::str::from_utf8(raw_buffer)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid UTF-8 payload: {}", e)))?;

        let audit_results = self.execute_internal_analysis(payload_str);

        let blocker_count = if !audit_results.is_compliant { audit_results.violations.len() } else { 0 };
        let risk_score = RiskScorer::calculate(blocker_count, 0, 0, 0);

        let response_dict = PyDict::new(py);
        response_dict.set_item("is_compliant", audit_results.is_compliant)?;
        response_dict.set_item("rule_version", &self.rule_set_version)?;
        response_dict.set_item("violations", audit_results.violations)?;
        response_dict.set_item("matched_rule_ids", audit_results.matched_rule_ids)?;
        response_dict.set_item("risk_score", risk_score.total_score)?;
        response_dict.set_item("risk_level", risk_score.risk_level)?;
        response_dict.set_item("execution_microsec", audit_results.latency_us)?;

        Ok(response_dict)
    }

    /// Asynchronous non-blocking payload audit gate for FastAPI & Tokio workers
    pub fn audit_payload_async<'py>(
        &self,
        py: Python<'py>,
        payload_bytes: &'py PyBytes,
    ) -> PyResult<&'py PyAny> {
        let raw_buffer: &[u8] = payload_bytes.as_bytes();
        let payload_str = std::str::from_utf8(raw_buffer)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid UTF-8 payload: {}", e)))?
            .to_string();

        let async_core = Arc::clone(&self.async_core);
        let version = self.rule_set_version.clone();

        pyo3_asyncio::tokio::future_into_py::<_, PyObject>(py, async move {
            let task = AsyncAuditTask { payload: payload_str };
            let result = async_core.process_audit_async(task).await;

            let blocker_count = if !result.is_compliant { result.violations.len() } else { 0 };
            let risk_score = RiskScorer::calculate(blocker_count, 0, 0, 0);

            Python::with_gil(|py| {
                let dict = PyDict::new(py);
                dict.set_item("is_compliant", result.is_compliant)?;
                dict.set_item("rule_version", version)?;
                dict.set_item("violations", result.violations)?;
                dict.set_item("risk_score", risk_score.total_score)?;
                dict.set_item("risk_level", risk_score.risk_level)?;
                dict.set_item("execution_microsec", result.latency_us)?;
                Ok(dict.into_py(py))
            })
        })
    }

    /// Enqueue signed DAC block into persistent offline journal
    pub fn queue_dac_block(&self, entry_id: &str, timestamp: &str, chain_hash: &str, signature: &str) -> PyResult<bool> {
        let entry = DacJournalEntry {
            entry_id: entry_id.to_string(),
            timestamp_utc: timestamp.to_string(),
            chain_hash: chain_hash.to_string(),
            signature: signature.to_string(),
            is_synced: false,
        };

        match self.ledger_queue.enqueue_block(&entry) {
            Ok(_) => Ok(true),
            Err(e) => Err(pyo3::exceptions::PyIOError::new_err(format!("Failed to write ledger journal: {}", e))),
        }
    }

    /// Return total pending unsynced DAC blocks queued on local disk
    pub fn get_pending_ledger_count(&self) -> usize {
        self.ledger_queue.get_pending_entries().len()
    }

    /// Mark all queued local journal blocks as synced after hub connection recovers
    pub fn flush_offline_queue(&self) -> PyResult<usize> {
        match self.ledger_queue.mark_all_synced() {
            Ok(count) => Ok(count),
            Err(e) => Err(pyo3::exceptions::PyIOError::new_err(format!("Failed to flush ledger queue: {}", e))),
        }
    }

    /// Parallel multi-threaded zero-copy directory scanner
    pub fn scan_directory<'py>(
        &self,
        py: Python<'py>,
        dir_path: &str,
    ) -> PyResult<&'py PyDict> {
        let start = Instant::now();
        let path = Path::new(dir_path);
        
        let files = DirectoryScanner::collect_files(path);
        let scan_results = DirectoryScanner::scan_parallel(&files);

        let total_files = scan_results.len();
        let total_lines: usize = scan_results.iter().map(|r| r.line_count).sum();
        let latency_us = start.elapsed().as_micros();

        let response_dict = PyDict::new(py);
        response_dict.set_item("total_files_scanned", total_files)?;
        response_dict.set_item("total_lines_scanned", total_lines)?;
        response_dict.set_item("scan_latency_microsec", latency_us)?;

        Ok(response_dict)
    }

    /// Sign DAC block hash with HMAC-SHA256
    pub fn sign_chain_hash(&self, chain_hash: &str, secret_key: &str) -> Option<String> {
        sign_dac_chain_hash(chain_hash, secret_key)
    }

    /// Verify DAC block hash signature
    pub fn verify_chain_hash(&self, chain_hash: &str, signature: &str, secret_key: &str) -> bool {
        verify_dac_chain_hash(chain_hash, signature, secret_key)
    }

    /// Look up statutory legal mappings for a given rule ID
    pub fn get_statutory_mappings<'py>(
        &self,
        py: Python<'py>,
        rule_id: &str,
    ) -> PyResult<PyObject> {
        let list = PyList::empty(py);
        if let Some(mappings) = self.legal_mapper.get_mappings(rule_id) {
            for m in mappings {
                let dict = PyDict::new(py);
                dict.set_item("rule_id", m.rule_id)?;
                dict.set_item("framework_id", m.framework_id)?;
                dict.set_item("statute_title", m.statute_title)?;
                dict.set_item("primary_article", m.primary_article)?;
                dict.set_item("jurisdiction", m.jurisdiction)?;
                dict.set_item("penalty_level", m.penalty_level)?;
                list.append(dict)?;
            }
        }
        Ok(list.into())
    }

    pub fn version(&self) -> String {
        self.rule_set_version.clone()
    }
}

impl AnchorEngine {
    fn execute_internal_analysis<'a>(&self, source: &'a str) -> InternalAuditResult<'a> {
        let start = Instant::now();
        let mut violations = Vec::new();
        let mut matched_rule_ids = Vec::new();

        let matches = self.regex_set.matches(source);
        if matches.matched(0) {
            violations.push("EU_ART52_TRANSPARENCY_VIOLATION: System configured to mimic human or hide AI disclosure.");
            matched_rule_ids.push("AGT-001");
        }
        if matches.matched(1) {
            violations.push("EU_ART12_LOGGING_DISABLED_VIOLATION: Traceability logging explicitly disabled on high-risk call.");
            matched_rule_ids.push("RBI-007");
        }
        if matches.matched(2) {
            violations.push("EU_ART14_MISSING_HUMAN_OVERSIGHT: Autonomous action executed without required human approval gate.");
            matched_rule_ids.push("AGT-001");
        }
        if matches.matched(3) {
            violations.push("SEC_001_PROMPT_INJECTION: Adversarial prompt override pattern detected.");
            matched_rule_ids.push("SEC-001");
        }
        if matches.matched(4) {
            violations.push("SEC_002_CREDENTIAL_LEAK: Hardcoded API secret or bearer token detected in context payload.");
            matched_rule_ids.push("SEC-002");
        }

        let is_compliant = violations.is_empty();
        let latency_us = start.elapsed().as_micros();

        InternalAuditResult {
            is_compliant,
            violations,
            matched_rule_ids,
            latency_us,
        }
    }
}

/// PyO3 Module entry point
#[pymodule]
fn anchor_core_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AnchorEngine>()?;
    Ok(())
}
