/// Risk Scoring Engine
/// Calculates systemic risk score (0.0 - 10.0) and risk tier based on violation counts and weights.

#[derive(Debug, Clone)]
pub struct RiskScore {
    pub total_score: f64,
    pub risk_level: String, // "CRITICAL", "HIGH", "MEDIUM", "LOW"
    pub blocker_count: usize,
    pub error_count: usize,
    pub warning_count: usize,
    pub info_count: usize,
}

pub struct RiskScorer;

impl RiskScorer {
    /// Calculate risk score from violation severity counts
    pub fn calculate(blockers: usize, errors: usize, warnings: usize, infos: usize) -> RiskScore {
        // Weighted impact points
        let raw_points = (blockers as f64 * 10.0)
            + (errors as f64 * 4.0)
            + (warnings as f64 * 1.5)
            + (infos as f64 * 0.2);

        // Normalized score on a 0.0 - 10.0 scale (logarithmic saturation)
        let total_score = if raw_points == 0.0 {
            0.0
        } else {
            (10.0 * (1.0 - (-raw_points / 25.0).exp())).min(10.0)
        };

        let risk_level = if blockers > 0 || total_score >= 7.5 {
            "CRITICAL".to_string()
        } else if errors > 0 || total_score >= 4.5 {
            "HIGH".to_string()
        } else if warnings > 0 || total_score >= 2.0 {
            "MEDIUM".to_string()
        } else {
            "LOW".to_string()
        };

        RiskScore {
            total_score: (total_score * 10.0).round() / 10.0, // 1 decimal place
            risk_level,
            blocker_count: blockers,
            error_count: errors,
            warning_count: warnings,
            info_count: infos,
        }
    }
}
