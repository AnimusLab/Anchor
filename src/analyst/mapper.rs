use std::collections::HashMap;

/// Statutory Mapping Entry representing legal cross-references
#[derive(Debug, Clone)]
pub struct LegalMapping {
    pub rule_id: &'static str,
    pub framework_id: &'static str,
    pub statute_title: &'static str,
    pub primary_article: &'static str,
    pub jurisdiction: &'static str,
    pub penalty_level: &'static str,
}

pub struct LegalMapper {
    mappings: HashMap<&'static str, Vec<LegalMapping>>,
}

impl LegalMapper {
    pub fn new() -> Self {
        let mut mappings: HashMap<&'static str, Vec<LegalMapping>> = HashMap::new();

        // 1. AGT-001 (Agent Action Authorization Bypass)
        mappings.insert(
            "AGT-001",
            vec![
                LegalMapping {
                    rule_id: "AGT-001",
                    framework_id: "FINOS-001",
                    statute_title: "FINOS AI Governance Framework",
                    primary_article: "Ri-024 Agent Privilege Boundaries",
                    jurisdiction: "Global Financial",
                    penalty_level: "High",
                },
                LegalMapping {
                    rule_id: "AGT-001",
                    framework_id: "EU-ART14",
                    statute_title: "EU Artificial Intelligence Act (2024/1689)",
                    primary_article: "Article 14 - Human Oversight",
                    jurisdiction: "European Union",
                    penalty_level: "Up to €35M or 7% Global Turnover",
                },
                LegalMapping {
                    rule_id: "AGT-001",
                    framework_id: "RBI-006",
                    statute_title: "RBI FREE-AI Framework (2025)",
                    primary_article: "Recommendation 6 - Board-Approved AI Policy",
                    jurisdiction: "India (RBI)",
                    penalty_level: "Supervisory Escalation & CIMS Halt",
                },
            ],
        );

        // 2. AGT-002 / AGT-003 (Tool Chain Manipulation & MCP Compromise)
        mappings.insert(
            "AGT-002",
            vec![
                LegalMapping {
                    rule_id: "AGT-002",
                    framework_id: "OWASP-LLM01",
                    statute_title: "OWASP Top 10 for LLM Applications (2025)",
                    primary_article: "LLM01 - Prompt & Tool Injection",
                    jurisdiction: "Global Cyber",
                    penalty_level: "High",
                },
                LegalMapping {
                    rule_id: "AGT-002",
                    framework_id: "EU-ART9",
                    statute_title: "EU Artificial Intelligence Act (2024/1689)",
                    primary_article: "Article 9 - Risk Management System",
                    jurisdiction: "European Union",
                    penalty_level: "Up to €15M or 3% Global Turnover",
                },
            ],
        );

        // 3. SEC-001 (Prompt Injection)
        mappings.insert(
            "SEC-001",
            vec![
                LegalMapping {
                    rule_id: "SEC-001",
                    framework_id: "NIST-MAN",
                    statute_title: "NIST AI Risk Management Framework 1.0",
                    primary_article: "Manage 1.1 - Safety & Adversarial Controls",
                    jurisdiction: "United States",
                    penalty_level: "NIST Compliance Verification Failure",
                },
                LegalMapping {
                    rule_id: "SEC-001",
                    framework_id: "RBI-018",
                    statute_title: "RBI FREE-AI Framework (2025)",
                    primary_article: "Recommendation 18 - Cybersecurity Augmentation",
                    jurisdiction: "India (RBI)",
                    penalty_level: "Mandatory Incident Reporting within 6h",
                },
            ],
        );

        // 4. RBI-007 / RBI-014 (Explainability & Audit Trails)
        mappings.insert(
            "RBI-014",
            vec![
                LegalMapping {
                    rule_id: "RBI-014",
                    framework_id: "CFPB-REGB",
                    statute_title: "CFPB Regulation B + 2024 Guidance",
                    primary_article: "12 CFR § 1002.9 - Adverse Action Notices",
                    jurisdiction: "United States",
                    penalty_level: "Civil Money Penalties & Enforcement Orders",
                },
                LegalMapping {
                    rule_id: "RBI-014",
                    framework_id: "RBI-007",
                    statute_title: "RBI FREE-AI Framework (2025)",
                    primary_article: "Recommendation 7 - CIMS Audit Trail Egress",
                    jurisdiction: "India (RBI)",
                    penalty_level: "Non-Compliance Penalty & Audit Block",
                },
            ],
        );

        LegalMapper { mappings }
    }

    pub fn get_mappings(&self, rule_id: &str) -> Option<&Vec<LegalMapping>> {
        self.mappings.get(rule_id)
    }
}
