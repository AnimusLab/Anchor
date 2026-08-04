pub mod analyst;

use analyst::{LegalMapper, RiskScorer};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use regex::RegexSet;
use std::sync::Arc;
use std::time::Instant;

/// Core Anchor Governance Engine (Rust Core Kernel)
#[pyclass]
pub struct AnchorEngine {
    pub rule_set_version: String,
    regex_set: Arc<RegexSet>,
    legal_mapper: LegalMapper,
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
        // Compile single-pass DFA RegexSet for high-velocity pattern matching
        let patterns = vec![
            r"(?i)(hide_ai_identity|mimic_human_agent|pretend_human|bypass_disclosure)", // EU AI Act Art 50/52
            r"(?i)(enable_audit_log\s*=\s*false|disable_logging|suppress_traceability)",  // EU AI Act Art 12
            r"(?i)(autonomous_p2p_wire|unvetted_risk_execution|bypass_human_auth)",      // EU AI Act Art 14
            r"(?i)(ignore previous instructions|system prompt override|jailbreak)",       // SEC-001
            r"(?i)(api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]|bearer\s+[A-Za-z0-9_\-\.]{16,})", // SEC-002
        ];

        let regex_set = RegexSet::new(&patterns)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid RegexSet compilation: {}", e)))?;

        Ok(AnchorEngine {
            rule_set_version: "6.0.0-alpha".to_string(),
            regex_set: Arc::new(regex_set),
            legal_mapper: LegalMapper::new(),
        })
    }

    /// High-velocity audit gate. Takes raw byte references directly from the
    /// Python memory space (FastAPI request pool) without allocating new heap storage.
    pub fn audit_payload<'py>(
        &self,
        py: Python<'py>,
        payload_bytes: &'py PyBytes,
    ) -> PyResult<&'py PyDict> {
        let raw_buffer: &[u8] = payload_bytes.as_bytes();
        let payload_str: &str = std::str::from_utf8(raw_buffer)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid UTF-8 payload: {}", e)))?;

        let audit_results = self.execute_internal_analysis(payload_str);

        // Compute Risk Density Score
        let blocker_count = if !audit_results.is_compliant { audit_results.violations.len() } else { 0 };
        let risk_score = RiskScorer::calculate(blocker_count, 0, 0, 0);

        let response_dict = PyDict::new(py);
        response_dict.set_item("is_compliant", audit_results.is_compliant)?;
        response_dict.set_item("rule_version", &self.rule_set_version)?;
        response_dict.set_item("violations", audit_results.violations)?;
        response_dict.set_item("risk_score", risk_score.total_score)?;
        response_dict.set_item("risk_level", risk_score.risk_level)?;
        response_dict.set_item("execution_microsec", audit_results.latency_us)?;

        Ok(response_dict)
    }

    /// Look up statutory legal mappings for a given rule ID (e.g. AGT-001 or SEC-001)
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

    /// Return current engine version
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
