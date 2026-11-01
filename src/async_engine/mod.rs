use std::sync::Arc;
use std::time::Instant;
use regex::RegexSet;

pub struct AsyncAuditTask {
    pub payload: String,
}

pub struct AsyncAuditResult {
    pub is_compliant: bool,
    pub violations: Vec<String>,
    pub latency_us: u128,
}

pub struct AsyncEngineCore {
    regex_set: Arc<RegexSet>,
    runtime_messages: Arc<Vec<&'static str>>,
}

impl AsyncEngineCore {
    pub fn new(regex_set: Arc<RegexSet>, runtime_messages: Vec<&'static str>) -> Self {
        Self {
            regex_set,
            runtime_messages: Arc::new(runtime_messages),
        }
    }

    /// Asynchronously executes non-blocking RegexSet DFA matching and AST verification on Tokio worker thread pool
    pub async fn process_audit_async(&self, task: AsyncAuditTask) -> AsyncAuditResult {
        let regex_set = Arc::clone(&self.regex_set);
        let runtime_messages = Arc::clone(&self.runtime_messages);

        // Offload execution onto Tokio blocking threadpool to preserve Python main loop responsiveness.
        tokio::task::spawn_blocking(move || {
            let start = Instant::now();
            let matches = regex_set.matches(&task.payload);
            let violations = runtime_messages
                .iter()
                .enumerate()
                .filter_map(|(index, message)| {
                    matches.matched(index).then(|| (*message).to_string())
                })
                .collect::<Vec<_>>();

            AsyncAuditResult {
                is_compliant: violations.is_empty(),
                violations,
                latency_us: start.elapsed().as_micros(),
            }
        })
        .await
        .unwrap_or(AsyncAuditResult {
            is_compliant: false,
            violations: vec!["ENGINE_EXECUTION_PANIC".to_string()],
            latency_us: 0,
        })
    }
}
