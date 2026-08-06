"""
anchor/runtime/interceptors/base.py

Core types shared across all interceptors:
  - AnchorViolationError  — raised when a prompt is hard-blocked
  - PromptScanResult      — verdict on an outgoing prompt
  - ResponseScanResult    — verdict on an incoming LLM response
  - InterceptorMode       — warn / block / audit
  - SessionStats          — running counters for the current process lifetime
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class InterceptorMode(Enum):
    """
    Controls what happens when a violation is detected.

    BLOCK  — raise AnchorViolationError (hard stop, default for production)
    WARN   — print a warning but allow the call through
    AUDIT  — silently log; never interrupts the application
    """
    BLOCK = "block"
    WARN  = "warn"
    AUDIT = "audit"


class AnchorViolationError(Exception):
    """
    Raised by the Interceptor when a prompt or response violates policy
    and the active mode is BLOCK.

    Attributes:
        rule_id   — the governance rule that triggered the block
        provider  — which AI provider the call was going to
        preview   — first 120 chars of the offending content
    """
    def __init__(self, message: str, rule_id: str = "UNKNOWN",
                 provider: str = "unknown", preview: str = ""):
        super().__init__(message)
        self.rule_id  = rule_id
        self.provider = provider
        self.preview  = preview

    def __str__(self) -> str:
        return (
            f"[Anchor BLOCK] Rule {self.rule_id} violated on {self.provider} call.\n"
            f"  Preview: {self.preview[:120]!r}\n"
            f"  {super().__str__()}"
        )


@dataclass
class Finding:
    """A single policy match inside a prompt or response."""
    rule_id:   str
    severity:  str          # "blocker", "error", "warning", "info"
    message:   str
    snippet:   str = ""     # offending text fragment (truncated)
    line:      int = 0


@dataclass
class PromptScanResult:
    """
    Result of scanning an outgoing prompt against Anchor policy.

    is_blocked is True only when mode == BLOCK and findings contain blockers.
    is_flagged is True whenever at least one finding exists (any mode).
    """
    provider:   str
    is_blocked: bool
    is_flagged: bool
    findings:   List[Finding] = field(default_factory=list)
    mode:       InterceptorMode = InterceptorMode.BLOCK

    @property
    def top_finding(self) -> Optional[Finding]:
        return self.findings[0] if self.findings else None


@dataclass
class ResponseScanResult:
    """
    Result of scanning an incoming LLM response for dangerous patterns.

    The response scanner never blocks (the response already arrived);
    it logs/warns so that the application layer can decide what to do.
    """
    provider:   str
    is_flagged: bool
    findings:   List[Finding] = field(default_factory=list)


@dataclass
class SessionStats:
    """Cumulative counters for the lifetime of the Intercept session."""
    prompts_scanned:   int = 0
    prompts_blocked:   int = 0
    prompts_warned:    int = 0
    responses_scanned: int = 0
    responses_flagged: int = 0
    providers_seen:    List[str] = field(default_factory=list)

    def record_prompt(self, result: PromptScanResult) -> None:
        self.prompts_scanned += 1
        if result.provider not in self.providers_seen:
            self.providers_seen.append(result.provider)
        if result.is_blocked:
            self.prompts_blocked += 1
        elif result.is_flagged:
            self.prompts_warned += 1

    def record_response(self, result: ResponseScanResult) -> None:
        self.responses_scanned += 1
        if result.is_flagged:
            self.responses_flagged += 1

    def as_dict(self) -> dict:
        return {
            "prompts_scanned":   self.prompts_scanned,
            "prompts_blocked":   self.prompts_blocked,
            "prompts_warned":    self.prompts_warned,
            "responses_scanned": self.responses_scanned,
            "responses_flagged": self.responses_flagged,
            "providers_seen":    self.providers_seen,
        }
