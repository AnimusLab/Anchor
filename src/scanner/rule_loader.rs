use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RulePrimitive {
    pub action: Option<String>,
    pub object: Option<String>,
    pub context: Option<String>,
    pub authority: Option<String>,
    pub flow: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnchorRuleDefinition {
    pub id: String,
    pub name: String,
    pub category: Option<String>,
    pub description: Option<String>,
    pub severity: String,
    pub runtime_pattern: Option<String>,
    pub primitives: Option<RulePrimitive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainFile {

    pub namespace: String,
    pub version: String,
    pub rules: Vec<AnchorRuleDefinition>,
}

pub struct RuleLoader;

impl RuleLoader {
    /// Recursively load all .anchor rule files from governance directory
    pub fn load_governance_rules(governance_dir: &Path) -> HashMap<String, AnchorRuleDefinition> {
        let mut rule_map = HashMap::new();
        Self::scan_directory_rules(governance_dir, &mut rule_map);
        rule_map
    }

    fn scan_directory_rules(dir: &Path, rule_map: &mut HashMap<String, AnchorRuleDefinition>) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    Self::scan_directory_rules(&path, rule_map);
                } else if path.extension().and_then(|s| s.to_str()) == Some("anchor") {
                    if let Ok(content) = fs::read_to_string(&path) {
                        if let Ok(domain_file) = serde_yaml::from_str::<DomainFile>(&content) {
                            for rule in domain_file.rules {
                                rule_map.insert(rule.id.clone(), rule);
                            }
                        }
                    }
                }
            }
        }
    }
}
