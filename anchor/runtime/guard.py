"""
anchor/runtime/guard.py

AnchorGuard — First-party integration API for developers building their own AI.

If your AI is not one of the auto-detected providers (OpenAI, Anthropic, etc.),
or if you are building your OWN AI product, drop AnchorGuard directly into
your pipeline. It gives you full control over WHERE Anchor sits.

Usage
-----
    from anchor.runtime import AnchorGuard

    guard = AnchorGuard(provider="my-company-ai", mode="block")

    # 1. Before the user's input reaches your model:
    guard.scan_prompt(user_message)          # raises AnchorViolationError if blocked

    # 2. After your model produces output, before you send it to the user:
    result = guard.scan_response(model_output)
    if result.is_flagged:
        print("Warning:", result.findings[0].message)

Modes
-----
    "block"  — raises AnchorViolationError on prompt violations (default).
    "warn"   — prints a warning, allows the call through.
    "audit"  — silent logging only; never interrupts your application.
"""

from __future__ import annotations

import logging
from typing import Optional

from anchor.runtime.interceptors.base import (
    AnchorViolationError,
    Finding,
    InterceptorMode,
    PromptScanResult,
    ResponseScanResult,
    SessionStats,
)
from anchor.runtime.interceptors.output_scanner import scan_response as _scan_response
from anchor.runtime import decision_auditor
import time

logger = logging.getLogger("anchor.guard")


# ---------------------------------------------------------------------------
# Prompt patterns — lightweight inline scan for user-facing guard
# (full engine scan is used by the pre-commit hook; this is the runtime layer)
# ---------------------------------------------------------------------------
import re

_PROMPT_PATTERNS: list[tuple[str, str, str, str]] = [
    # Prompt injection attempts
    (r"(?i)(ignore\s+(all\s+)?previous\s+instructions?|disregard\s+.{0,30}system)",
        "PRM-001", "blocker", "Prompt injection attempt: override system instructions"),

    (r"(?i)(you\s+are\s+now\s+.{0,40}(jailbreak|dan|unrestricted|evil)|act\s+as\s+.{0,30}without\s+(restriction|filter))",
        "PRM-002", "blocker", "Jailbreak attempt detected in prompt"),

    (r"(?i)(reveal\s+your\s+(system\s+)?prompt|print\s+your\s+instructions|what\s+is\s+your\s+system\s+prompt)",
        "PRM-003", "error", "Attempt to extract system prompt"),

    # Credential harvesting in prompts
    (r"(?i)(give\s+me\s+.{0,20}(api\s+key|password|secret|token)|show\s+.{0,20}credentials?)",
        "PRM-010", "error", "Request for credentials or secrets in prompt"),

    # Data exfiltration attempts
    (r"(?i)(send\s+.{0,30}(to\s+)?http|exfil|upload\s+.{0,20}(to\s+)?external)",
        "PRM-020", "error", "Possible data exfiltration instruction in prompt"),

    # PII patterns in prompts (developer sending raw user PII to AI)
    (r"\b\d{3}-\d{2}-\d{4}\b",
        "PRM-050", "warning", "SSN pattern detected in outgoing prompt — PII risk"),

    (r"(?i)(4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})",
        "PRM-051", "blocker", "Credit card number detected in outgoing prompt — PII risk"),
]

_COMPILED_PROMPT: list[tuple[re.Pattern, str, str, str]] = [
    (re.compile(pat, re.MULTILINE), rid, sev, msg)
    for pat, rid, sev, msg in _PROMPT_PATTERNS
]


def _scan_prompt_text(text: str, provider: str) -> PromptScanResult:
    """Scan a prompt string and return a PromptScanResult."""
    findings: list[Finding] = []
    for compiled, rule_id, severity, message in _COMPILED_PROMPT:
        match = compiled.search(text)
        if match:
            findings.append(Finding(
                rule_id  = rule_id,
                severity = severity,
                message  = message,
                snippet  = match.group(0)[:120],
                line     = text[:match.start()].count("\n") + 1,
            ))

    has_blockers = any(f.severity in ("blocker", "error") for f in findings)
    return PromptScanResult(
        provider   = provider,
        is_blocked = bool(has_blockers),
        is_flagged = bool(findings),
        findings   = findings,
    )


# ---------------------------------------------------------------------------
# AnchorGuard
# ---------------------------------------------------------------------------

class AnchorGuard:
    """
    First-party Anchor integration for developers building their own AI.

    Provides explicit scan_prompt() and scan_response() methods that you
    call at the exact points in your pipeline where you want governance applied.

    Parameters
    ----------
    provider : str
        A name for your AI (used in reports, logs, and error messages).
        Example: "my-company-chatbot", "internal-llm", "kimi"

    mode : str
        "block"  — raise AnchorViolationError when a blocking violation is found.
        "warn"   — log a warning and return the result; never raises.
        "audit"  — completely silent; only returns the result object.

    stats : SessionStats, optional
        If you want to share session counters with the broader runtime
        (e.g. when using anchor.runtime.activate() alongside AnchorGuard),
        pass the SessionStats object here.
    """

    def __init__(
        self,
        provider: str = "custom",
        mode:     str = "block",
        stats:    Optional[SessionStats] = None,
    ) -> None:
        self.provider = provider
        self.mode     = InterceptorMode(mode.lower())
        self.stats    = stats or SessionStats()
        self._last_prompt:      str   = ""
        self._last_prompt_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_prompt(self, text: str) -> PromptScanResult:
        """
        Scan an outgoing prompt BEFORE it is sent to your AI model.

        In BLOCK mode: raises AnchorViolationError if a blocking rule fires.
        In WARN  mode: prints a warning, then returns the result.
        In AUDIT mode: silently returns the result; nothing is raised or printed.

        Parameters
        ----------
        text : str
            The user's message or composed prompt string.

        Returns
        -------
        PromptScanResult
            Always returned (even in BLOCK mode, before the exception).

        Raises
        ------
        AnchorViolationError
            In BLOCK mode, when a blocker/error severity finding is detected.
        """
        self._last_prompt      = text
        self._last_prompt_time = time.perf_counter()
        
        result = _scan_prompt_text(text, self.provider)
        self.stats.record_prompt(result)
        self._handle_prompt(result)
        return result

    def scan_response(self, text: str) -> ResponseScanResult:
        """
        Scan the AI's response BEFORE it is returned to the user.

        The response scanner never hard-blocks (the response already arrived);
        instead it flags findings so your application can decide what to do.

        Parameters
        ----------
        text : str
            The decoded text output from your AI model.

        Returns
        -------
        ResponseScanResult
            Contains is_flagged (bool) and a list of Finding objects.
        """
        latency = 0.0
        if self._last_prompt_time > 0:
            latency = (time.perf_counter() - self._last_prompt_time) * 1000
            
        result = _scan_response(text, self.provider)
        self.stats.record_response(result)
        
        findings = [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.upper(),
                "message": f.message,
                "domain": "UNKNOWN",
            }
            for f in result.findings
        ]
        
        # Layer 2: Decision Auditing
        try:
            decision_auditor.audit(
                prompt=self._last_prompt,
                response=text,
                provider=self.provider,
                findings=findings,
                mode="guard",
                latency_ms=latency
            )
        except Exception:
            pass

        if result.is_flagged:
            self._handle_response(result)
        return result

    def get_stats(self) -> dict:
        """Return cumulative session counters as a plain dict."""
        return self.stats.as_dict()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_prompt(self, result: PromptScanResult) -> None:
        if not result.is_flagged:
            return
        top = result.top_finding
        msg = top.message if top else "Policy violation"
        rid = top.rule_id if top else "UNKNOWN"

        if self.mode == InterceptorMode.BLOCK and result.is_blocked:
            raise AnchorViolationError(
                message  = msg,
                rule_id  = rid,
                provider = self.provider,
                preview  = top.snippet if top else "",
            )
        elif self.mode == InterceptorMode.WARN:
            logger.warning(
                f"[Anchor WARN] [{rid}] {msg} — provider={self.provider}"
            )
        # AUDIT: do nothing (already recorded in stats)

    def _handle_response(self, result: ResponseScanResult) -> None:
        if self.mode == InterceptorMode.AUDIT:
            return
        top = result.findings[0] if result.findings else None
        if top:
            logger.warning(
                f"[Anchor] Response flagged [{top.rule_id}]: {top.message} "
                f"— provider={self.provider}"
            )
