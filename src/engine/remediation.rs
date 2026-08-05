use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MitigationEntry {
    pub name: String,
    pub remediation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MitigationFile {
    pub version: String,
    pub mitigations: HashMap<String, MitigationEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealingDirectivePayload {
    pub status: String, // "BLOCKED_BY_ANCHOR"
    pub violation_id: String,
    pub rule_name: String,
    pub severity: String,
    pub reroute_directive: String,
    pub statutory_reference: String,
}

pub struct RemediationGraph {
    mitigations: HashMap<String, MitigationEntry>,
}

impl RemediationGraph {
    pub fn new() -> Self {
        Self {
            mitigations: HashMap::new(),
        }
    }

    /// Load mitigations directly from mitigation.anchor YAML file
    pub fn load_from_file(path: &Path) -> Self {
        let mut graph = Self::new();
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(file) = serde_yaml::from_str::<MitigationFile>(&content) {
                graph.mitigations = file.mitigations;
            }
        }
        graph
    }

    /// Construct domain-agnostic self-healing directive for any intercepted rule violation
    pub fn generate_healing_directive(
        &self,
        rule_id: &str,
        default_name: &str,
        severity: &str,
        statute_ref: &str,
    ) -> HealingDirectivePayload {
        let (name, remediation) = if let Some(entry) = self.mitigations.get(rule_id) {
            (entry.name.clone(), entry.remediation.trim().to_string())
        } else {
            (
                default_name.to_string(),
                format!("Sanitize and enforce structural boundaries for rule {}.", rule_id),
            )
        };

        HealingDirectivePayload {
            status: "BLOCKED_BY_ANCHOR".to_string(),
            violation_id: rule_id.to_string(),
            rule_name: name,
            severity: severity.to_string(),
            reroute_directive: remediation,
            statutory_reference: statute_ref.to_string(),
        }
    }
}
