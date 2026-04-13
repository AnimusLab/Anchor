"""
anchor/runtime/interceptors/output_scanner.py

Provider-agnostic LLM response scanner.

Scans the text of any LLM response — regardless of which model or
provider generated it — for patterns that indicate dangerous content:

  - Hardcoded secrets / credentials
  - Shell injection (rm -rf, chmod, curl | bash, etc.)
  - SQL injection patterns
  - Insecure code constructs common to codegen models
  - PII exposure (email, phone, SSN regex patterns)
"""

from __future__ import annotations

import re
from typing import List
from anchor.runtime.interceptors.base import ResponseScanResult, Finding


# ---------------------------------------------------------------------------
# Pattern catalogue
# (pattern, rule_id, severity, human_message)
# ---------------------------------------------------------------------------
_RESPONSE_PATTERNS: list[tuple[str, str, str, str]] = [

    # ── Secret / credential exposure ──────────────────────────────────
    (r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*["\']?[A-Z0-9/+]{16,}',
        "RSP-001", "blocker", "AWS credential pattern detected in LLM response"),

    (r'(?i)(api[_\-]?key|apikey|secret[_\-]?key|auth[_\-]?token)\s*[=:]\s*["\']?[A-Za-z0-9\-_]{20,}',
        "RSP-002", "error", "API key or secret token pattern detected in LLM response"),

    (r'(?i)-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----',
        "RSP-003", "blocker", "Private key material detected in LLM response"),

    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{6,}["\']',
        "RSP-004", "error", "Plaintext password assignment detected in LLM response"),

    (r'ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}',
        "RSP-005", "blocker", "GitHub Personal Access Token detected in LLM response"),

    # ── Shell injection / dangerous commands ──────────────────────────
    (r'(?i)(rm\s+-rf\s+[/~]|rmdir\s+/s\s+/q)',
        "RSP-010", "blocker", "Destructive file deletion command in LLM response"),

    (r'(?i)curl\s+[^\s]+\s*\|\s*(bash|sh|zsh|fish)',
        "RSP-011", "blocker", "Pipe-to-shell command (curl | bash) in LLM response"),

    (r'(?i)(wget|fetch)\s+[^\s]+\s*\|\s*(bash|sh)',
        "RSP-011", "blocker", "Pipe-to-shell command (wget | bash) in LLM response"),

    (r'(?i)chmod\s+(777|a\+x|0777)',
        "RSP-012", "error", "Insecure file permission change in LLM response"),

    (r'(?i)(sudo\s+su|sudo\s*-[si]|su\s+-\s*root)',
        "RSP-013", "error", "Privilege escalation command in LLM response"),

    # ── SQL injection ─────────────────────────────────────────────────
    (r'(?i)(execute|executeQuery|exec)\s*\(\s*["\'].*\+\s*\w+',
        "RSP-020", "error", "SQL string concatenation (injection risk) in LLM response"),

    (r"(?i)f['\"]SELECT.*WHERE.*{",
        "RSP-021", "error", "F-string SQL query (injection risk) in LLM response"),

    # ── Insecure Python / eval-exec patterns ─────────────────────────
    (r'(?i)\beval\s*\(.*input\s*\(',
        "RSP-030", "error", "eval(input()) pattern in LLM response"),

    (r'(?i)\bexec\s*\(.*request\.',
        "RSP-031", "error", "exec(request.*) pattern in LLM response"),

    (r'(?i)__import__\s*\(["\']os["\']',
        "RSP-032", "error", "Dynamic __import__('os') in LLM response"),

    # ── Subprocess with shell=True ────────────────────────────────────
    (r'(?i)subprocess\.(run|call|Popen|check_output)\s*\(.*shell\s*=\s*True',
        "RSP-040", "error", "subprocess with shell=True in LLM response"),

    # ── PII exposure ──────────────────────────────────────────────────
    (r'\b\d{3}-\d{2}-\d{4}\b',
        "RSP-050", "warning", "Social Security Number (SSN) pattern in LLM response"),

    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "RSP-051", "info",    "Email address detected in LLM response"),

    (r'(?i)(4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})',
        "RSP-052", "blocker", "Credit card number pattern in LLM response"),
]


# Compile patterns once at import time
_COMPILED: list[tuple[re.Pattern, str, str, str]] = [
    (re.compile(pat, re.MULTILINE), rid, sev, msg)
    for pat, rid, sev, msg in _RESPONSE_PATTERNS
]


def scan_response(text: str, provider: str = "unknown") -> ResponseScanResult:
    """
    Scan the plaintext of an LLM response for dangerous patterns.
    Prioritizes Constitutional Rules (SEC, ETH, etc.) from the PolicyEngine.
    """
    from anchor.runtime.decision_auditor import DecisionAuditor
    findings: List[Finding] = []
    
    # ── PART A: Constitutional Scan (High Fidelity) ─────────────────
    engine = DecisionAuditor._shared_engine
    canonical_triggered = set()

    if engine:
        # PolicyEngine stores all rules in self.all_rules
        for rule in engine.all_rules:
            pattern_str = rule.get("runtime_pattern")
            if not pattern_str:
                continue
                
            try:
                # We compile on the fly here, but in production, 
                # these should be pre-compiled during warm-up.
                match = re.search(pattern_str, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    findings.append(Finding(
                        rule_id  = rule["id"],
                        severity = rule.get("severity", "error"),
                        message  = rule.get("message") or rule.get("description", "Constitutional violation"),
                        snippet  = match.group(0)[:120],
                        line     = text[:match.start()].count("\n") + 1,
                    ))
                    canonical_triggered.add(rule["id"])
            except Exception:
                pass # Pattern error should not crash the AI

    # ── PART B: Legacy RSP Backstop (Deprecated) ────────────────────
    # Map legacy RSP IDs to their new canonical equivalents to avoid double-reporting
    # Once Step 4 (Full Migration) is complete, this backstop can be removed.
    RSP_MAP = {
        "RSP-001": "SEC-004", "RSP-002": "SEC-004", "RSP-003": "SEC-004", 
        "RSP-004": "SEC-004", "RSP-005": "SEC-004",
        "RSP-010": "SEC-007", "RSP-011": "SEC-007", "RSP-012": "SEC-007", 
        "RSP-013": "SEC-007", "RSP-040": "SEC-007",
        "RSP-050": "PRV-001", "RSP-051": "PRV-001", "RSP-052": "PRV-001"
    }

    for compiled, rule_id, severity, message in _COMPILED:
        # Skip if this logic is already covered by a triggered canonical rule
        target_canonical = RSP_MAP.get(rule_id)
        if target_canonical and target_canonical in canonical_triggered:
            continue

        match = compiled.search(text)
        if match:
            findings.append(Finding(
                rule_id  = rule_id,
                severity = severity,
                message  = message,
                snippet  = match.group(0)[:120],
                line     = text[:match.start()].count("\n") + 1,
            ))

    return ResponseScanResult(
        provider   = provider,
        is_flagged = bool(findings),
        findings   = findings,
    )
