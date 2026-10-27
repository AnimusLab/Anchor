"""
anchor/runtime/interceptors/prompt_scanner.py

Single prompt-side scan used by every interceptor (SDK patches, HTTP backstop).

Before this module the interceptors scanned outgoing prompts with the
*response* pattern table only, so prompt-injection, jailbreak,
system-prompt-extraction, credential-request and exfiltration prompts
(PRM-001..PRM-020) were enforced by ``AnchorGuard.scan_prompt`` but silently
passed through the SDK and HTTP interceptors. Both paths now share this scan:
the PRM prompt rules plus the secret/PII patterns from the output scanner.
"""

from __future__ import annotations

from anchor.runtime.interceptors.base import (
    Finding, InterceptorMode, PromptScanResult,
)

_BLOCKING = ("blocker", "error")


def scan_prompt(text: str, provider: str, mode: InterceptorMode) -> PromptScanResult:
    """Scan an outgoing prompt; ``is_blocked`` is only True in BLOCK mode."""
    # Imported lazily: anchor.runtime imports the interceptors at activation time.
    from anchor.runtime.guard import _scan_prompt_text as _prm_scan
    from anchor.runtime.interceptors.output_scanner import _COMPILED

    findings = list(_prm_scan(text, provider).findings)

    for compiled, rule_id, severity, message in _COMPILED:
        match = compiled.search(text)
        if match:
            findings.append(Finding(
                rule_id  = rule_id,
                severity = severity,
                message  = message.replace("response", "prompt"),
                snippet  = match.group(0)[:120],
                line     = text[:match.start()].count("\n") + 1,
            ))

    is_flagged = bool(findings)
    is_blocked = (
        is_flagged
        and mode == InterceptorMode.BLOCK
        and any(f.severity in _BLOCKING for f in findings)
    )
    return PromptScanResult(
        provider   = provider,
        is_blocked = is_blocked,
        is_flagged = is_flagged,
        findings   = findings,
        mode       = mode,
    )
