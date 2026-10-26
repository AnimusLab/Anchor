pub mod analyst;
pub mod async_engine;
pub mod engine;
pub mod ledger;
pub mod scanner;

use analyst::{LegalMapper, RiskScorer};
use async_engine::{AsyncAuditTask, AsyncEngineCore};
use engine::RemediationGraph;
use ledger::{DacJournalEntry, PersistentLedgerQueue};
use scanner::{
    generate_ed25519_keypair, sign_dac_block_ed25519, sign_dac_chain_hash,
    verify_dac_block_ed25519, verify_dac_chain_hash, DirectoryScanner, RuleLoader,
};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use regex::RegexSet;
use std::path::Path;
use std::sync::Arc;
use std::time::Instant;

/// One code-scanning rule. This table is the single source of truth: the compiled
/// RegexSet, the metadata attached to static-scan findings and the Layer 2 payload
/// checks are all derived from it, so they cannot drift apart. The regexes are
/// hand-tuned (e.g. the SEC-010 pattern skips `.eval(` and `literal_eval(`); the
/// signed rule files in anchor/governance are checked against `rule_id` by tests.
struct CodeRule {
    rule_id: &'static str,
    statute: &'static str,
    name: &'static str,
    /// Message emitted when this pattern matches a Layer 2 runtime payload.
    /// `None` means the rule only applies to the static code scan.
    runtime_message: Option<&'static str>,
    pattern: &'static str,
}

const CODE_RULES: &[CodeRule] = &[
    CodeRule {
        rule_id: "AGT-001",
        statute: "EU-ART52",
        name: "Transparency Disclosure Gate",
        runtime_message: Some("EU_ART52_TRANSPARENCY_VIOLATION: System configured to mimic human or hide AI disclosure."),
        // anchor: ignore AGT-001 -- pattern definition, not a violation
        pattern: r"(?i)(hide_ai_identity|mimic_human_agent|pretend_human|bypass_disclosure)",
    },
    CodeRule {
        rule_id: "RBI-007",
        statute: "EU-ART12",
        name: "Audit Traceability Logging Gate",
        runtime_message: Some("EU_ART12_LOGGING_DISABLED_VIOLATION: Traceability logging explicitly disabled on high-risk call."),
        // anchor: ignore RBI-007 -- pattern definition, not a violation
        pattern: r"(?i)(enable_audit_log\s*=\s*false|disable_logging|suppress_traceability)",
    },
    CodeRule {
        rule_id: "AGT-001",
        statute: "EU-ART14",
        name: "Autonomous Action Human Oversight Gate",
        runtime_message: Some("EU_ART14_MISSING_HUMAN_OVERSIGHT: Autonomous action executed without required human approval gate."),
        // anchor: ignore AGT-001 -- pattern definition, not a violation
        pattern: r"(?i)(autonomous_p2p_wire|unvetted_risk_execution|bypass_human_auth)",
    },
    CodeRule {
        rule_id: "SEC-001",
        statute: "OWASP-LLM01",
        name: "Prompt Injection Defense Gate",
        runtime_message: Some("SEC_001_PROMPT_INJECTION: Adversarial prompt override pattern detected."),
        // anchor: ignore SEC-001 -- pattern definition, not a violation
        pattern: r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+instructions|system\s+prompt\s+override|jailbreak|disregard\s+(all\s+)?(previous|prior)\s+instructions)",
    },
    CodeRule {
        rule_id: "SEC-002",
        statute: "OWASP-LLM06",
        name: "Hardcoded Secret Leak Gate",
        runtime_message: Some("SEC_002_CREDENTIAL_LEAK: Hardcoded API secret or bearer token detected in context payload."),
        // anchor: ignore SEC-002 -- pattern definition, not a violation
        pattern: r#"(?i)(api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{8,}['\"]|bearer\s+[A-Za-z0-9_.-]{8,}|api_key\s*=\s*['\"][^'"]+['\"]|authorization['"]\s*==\s*['\"]Bearer)"#,
    },
    CodeRule {
        rule_id: "SEC-007",
        statute: "OWASP-LLM07",
        name: "Shell Injection (Unsandboxed Subprocess in Agent)",
        runtime_message: None,
        // anchor: ignore SEC-007 -- pattern definition, not a violation
        pattern: r"(?i)(subprocess\.(run|call|Popen|check_output)|os\.(system|popen|spawn))\s*\(",
    },
    CodeRule {
        rule_id: "ALN-001",
        statute: "OWASP-LLM09",
        name: "Hallucination (LLM Output Without Validation)",
        runtime_message: None,
        // anchor: ignore ALN-001 -- pattern definition, not a violation
        pattern: r"(?i)(\.(completions|messages|chat)\.(create|send)|agents\.messages\.create)\s*\(",
    },
    CodeRule {
        rule_id: "SEC-002",
        statute: "OWASP-LLM03",
        name: "Data Poisoning (Unencrypted Vector Store Upsert)",
        runtime_message: None,
        // anchor: ignore SEC-002 -- pattern definition, not a violation
        pattern: r"(?i)\.(upsert|add_texts|add_documents)\s*\(",
    },
    CodeRule {
        rule_id: "SEC-010",
        statute: "OWASP-LLM05",
        name: "Insecure Python Execution (eval/exec/dynamic import)",
        runtime_message: Some("SEC_010_INSECURE_EXECUTION: Dynamic code execution (eval/exec/__import__) detected in payload."),
        // anchor: ignore SEC-010 -- pattern definition, not a violation
        pattern: r"(^|[^.\w])(eval|exec)\s*\(|__import__\s*\(",
    },
    CodeRule {
        rule_id: "SEC-007",
        statute: "OWASP-LLM07",
        name: "Shell Injection (Destructive or Piped Shell String)",
        runtime_message: Some("SEC_007_SHELL_INJECTION: Destructive or piped shell command detected in payload."),
        // anchor: ignore SEC-007 -- pattern definition, not a violation
        pattern: r"(?i)(rm\s+-(rf|fr)\s+[/~]|curl\s+[^\s]+\s*\|\s*(bash|sh|zsh|fish))",
    },
];

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
        let patterns: Vec<&str> = CODE_RULES.iter().map(|r| r.pattern).collect();

        let regex_set = Arc::new(
            RegexSet::new(&patterns)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid RegexSet compilation: {}", e)))?
        );

        let async_core = Arc::new(AsyncEngineCore::new(Arc::clone(&regex_set)));
        let ledger_queue = PersistentLedgerQueue::new(Path::new(".anchor"));

        let mitigation_path = Path::new("anchor/governance/mitigation.anchor");
        let remediation_graph = RemediationGraph::load_from_file(mitigation_path);

        Ok(AnchorEngine {
            rule_set_version: env!("CARGO_PKG_VERSION").to_string(),

            regex_set,
            legal_mapper: LegalMapper::new(),
            async_core,
            ledger_queue,
            remediation_graph,
        })
    }

    /// Detailed code scanner returning file_path:line_number findings and multi-jurisdiction rule IDs
    pub fn scan_directory_detailed<'py>(
        &self,
        py: Python<'py>,
        dir_path: &str,
    ) -> PyResult<&'py PyDict> {
        let start = Instant::now();
        let path = Path::new(dir_path);

        let files = DirectoryScanner::collect_files(path);
        let scan_results = DirectoryScanner::scan_parallel_with_regex(&files, &self.regex_set);

        let total_files = scan_results.len();
        let total_lines: usize = scan_results.iter().map(|r| r.line_count).sum();

        let violations_list = PyList::empty(py);
        let mut total_violations_count = 0;


        for res in scan_results {
            for m in res.matches {
                total_violations_count += 1;
                let dict = PyDict::new(py);
                dict.set_item("file", &res.file_path)?;
                dict.set_item("line", m.line_number)?;
                dict.set_item("line_content", &m.line_content)?;

                let mut matched_rules = Vec::new();
                let mut matched_statutes = Vec::new();

                for idx in m.matched_rule_indices {
                    if let Some(rule) = CODE_RULES.get(idx) {
                        let (r_id, stat_ref, name) = (rule.rule_id, rule.statute, rule.name);
                        if !matched_rules.contains(&r_id) {
                            matched_rules.push(r_id);
                        }
                        if !matched_statutes.contains(&stat_ref) {
                            matched_statutes.push(stat_ref);
                        }
                        dict.set_item("name", name)?;
                    }
                }

                dict.set_item("aggregated_rule_ids", matched_rules.join(", "))?;
                dict.set_item("statutory_references", matched_statutes.join(", "))?;
                dict.set_item("severity", "error")?;

                violations_list.append(dict)?;
            }
        }

        let latency_us = start.elapsed().as_micros();
        let response_dict = PyDict::new(py);
        response_dict.set_item("total_files_scanned", total_files)?;
        response_dict.set_item("total_lines_scanned", total_lines)?;
        response_dict.set_item("scan_latency_microsec", latency_us)?;
        response_dict.set_item("total_violations", total_violations_count)?;
        response_dict.set_item("violations", violations_list)?;

        Ok(response_dict)
    }

    /// Generate fresh Ed25519 keypair for local identity
    pub fn generate_keypair<'py>(&self, py: Python<'py>) -> PyResult<&'py PyDict> {
        let pair = generate_ed25519_keypair();
        let dict = PyDict::new(py);
        dict.set_item("private_key_pem", pair.private_key_pem)?;
        dict.set_item("public_key_pem", pair.public_key_pem)?;
        dict.set_item("fingerprint", pair.fingerprint)?;
        Ok(dict)
    }

    /// Asymmetrically sign DAC block hash with local Ed25519 private key
    pub fn sign_ed25519(&self, chain_hash: &str, private_key_hex: &str) -> Option<String> {
        sign_dac_block_ed25519(chain_hash, private_key_hex)
    }

    /// Verify Ed25519 signature in constant time with public key
    pub fn verify_ed25519(&self, chain_hash: &str, signature_hex: &str, public_key_hex: &str) -> bool {
        verify_dac_block_ed25519(chain_hash, signature_hex, public_key_hex)
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

    /// Sign DAC block hash with HMAC-SHA256 (Enterprise Hub mode)
    pub fn sign_chain_hash(&self, chain_hash: &str, secret_key: &str) -> Option<String> {
        sign_dac_chain_hash(chain_hash, secret_key)
    }

    /// Verify HMAC-SHA256 DAC block hash signature
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

    /// The code-scanning rule table: [{id, statute, name, pattern, runtime}, ...].
    pub fn code_rules<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let out = PyList::empty(py);
        for rule in CODE_RULES {
            let d = PyDict::new(py);
            d.set_item("id", rule.rule_id)?;
            d.set_item("statute", rule.statute)?;
            d.set_item("name", rule.name)?;
            d.set_item("pattern", rule.pattern)?;
            d.set_item("runtime", rule.runtime_message.is_some())?;
            out.append(d)?;
        }
        Ok(out)
    }
}

impl AnchorEngine {
    fn execute_internal_analysis<'a>(&self, source: &'a str) -> InternalAuditResult<'a> {
        let start = Instant::now();
        let mut violations = Vec::new();
        let mut matched_rule_ids = Vec::new();

        let matches = self.regex_set.matches(source);
        for (idx, rule) in CODE_RULES.iter().enumerate() {
            if let Some(message) = rule.runtime_message {
                if matches.matched(idx) {
                    violations.push(message);
                    matched_rule_ids.push(rule.rule_id);
                }
            }
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
