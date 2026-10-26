"""
Anchor Layer 2 Runtime Interceptor Guard & Enforcement System
Provides @anchor.guard and @anchor.enforce decorators for AI agents, tool calls, and LLM pipelines.
Intercepts runtime prompts/actions and emits dynamic BLOCKED_BY_ANCHOR self-healing payloads.
Supports both synchronous and asynchronous (async/await) execution graphs.
"""

import asyncio
import functools
import inspect
import json
import logging
import re
from typing import Callable, Any, Dict, Optional, Union
from anchor.core.telemetry import SpokeTelemetryClient

logger = logging.getLogger("anchor.guard")
_telemetry_client = SpokeTelemetryClient()

try:
    from anchor_core_rs import AnchorEngine
except ImportError as exc:
    raise RuntimeError(
        "Anchor runtime guards require the native engine. Install anchor-audit "
        "with its compiled extension before using @guard or @enforce."
    ) from exc

_engine_instance = AnchorEngine()

# ---------------------------------------------------------------------------
# Python-side payload rules
# ---------------------------------------------------------------------------
# Supplement the native Layer 2 rules with checks for payloads that are
# unambiguous at the argument level: destructive SQL, exfiltration commands,
# credential material and payment card numbers. They run only when the native
# engine found nothing, and share its BLOCKED_BY_ANCHOR / PermissionError flow.
# (Deliberately not imported from anchor.runtime: importing that package
# auto-activates the interceptors, which a bare `import anchor.guard` must not do.)
_PAYLOAD_RULES = [
    ("AGT-010", re.compile(
        r"(?i)\b(?:drop|truncate)\s+(?:table|database|schema)\b|\bdelete\s+from\s+\w+\s*(?:;|--|$)")),
    ("AGT-011", re.compile(
        r"(?i)\b(?:curl|wget)\b[^\n]*(?:\s-d\s*@|--data(?:-binary)?\s*@|--upload-file)"
        r"|/etc/(?:passwd|shadow)\b|\.ssh/id_[a-z0-9]+")),
    ("AGT-012", re.compile(
        r"\b(?:AKIA|ASIA)(?![0-9A-Z]*EXAMPLE)[0-9A-Z]{16}\b"
        r"|\bgh[pousr]_[A-Za-z0-9]{36,}"
        r"|\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}"
        r"|-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        r"|(?i:aws_secret_access_key)\s*[=:]\s*[\"']?[A-Za-z0-9/+]{30,}")),
    ("AGT-013", re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")),
]


def _payload_rule_hits(payload_str: str) -> list:
    return [rule_id for rule_id, pattern in _PAYLOAD_RULES if pattern.search(payload_str)]


def _perform_audit(payload_dict: dict, func: Callable, domain: str, raise_on_violation: bool) -> Optional[dict]:
    """Internal helper to execute Rust audit pass and telemetry dispatch."""
    payload_str = json.dumps(payload_dict, separators=(',', ':'))
    payload_bytes = payload_str.encode("utf-8")

    audit_report = _engine_instance.audit_payload(payload_bytes)

    if audit_report.get("is_compliant"):
        extra_hits = _payload_rule_hits(payload_str)
        if extra_hits:
            audit_report = {
                "is_compliant": False,
                "matched_rule_ids": extra_hits,
                "risk_level": "BLOCKER",
                "risk_score": 8.5,
            }

    if not audit_report.get("is_compliant"):
        matched_rules = audit_report.get("matched_rule_ids", ["AGT-001"])
        rule_id = matched_rules[0] if matched_rules else "AGT-001"

        healing_directive = _engine_instance.generate_healing_payload(
            rule_id=rule_id,
            default_name="Agent Action Boundary Violation",
            severity=audit_report.get("risk_level", "BLOCKER"),
            statute_ref="EU AI Act Art 14 / RBI Recommendation 6"
        )

        try:
            formatted_violations = [
                {
                    "rule_id": rule_id,
                    "statute": healing_directive.get("statutory_reference", "EU AI Act Regulation"),
                    "severity": audit_report.get("risk_level", "BLOCKER"),
                    "trace_uri": f"file:///{getattr(func, '__module__', 'unknown')}.py#func={getattr(func, '__name__', 'anonymous')}",
                    "summary": healing_directive.get("reroute_directive", "Invariant violation intercepted by Anchor Guard.")
                }
            ]
            _telemetry_client.dispatch_state_event(
                event_id=f"evt_{rule_id.lower()}_breach",
                project_name=getattr(func, "__module__", None) or "agentic-execution-node",
                silo_id=domain.upper(),
                verdict="NON_COMPLIANT",
                risk_score=audit_report.get("risk_score", 8.5),
                violations=formatted_violations
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry dispatch warning: {tel_err}")

        if raise_on_violation:
            raise PermissionError(f"Anchor Invariant Breach: {healing_directive['reroute_directive']}")

        return healing_directive

    return None


def guard(domain: Union[str, Callable[..., Any]] = "general", raise_on_violation: bool = False):
    """
    Runtime Interceptor Decorator for AI Functions & Agent Tool Calls.
    Supports both synchronous and asynchronous functions.

    Usage:
        @anchor.guard(domain="agentic")
        def execute_tool(prompt: str):
            ...

        @anchor.guard(domain="agentic", raise_on_violation=True)
        async def async_agent_step(action_payload: dict):
            ...
    """
    if callable(domain):
        # Used as a bare `@guard` (no parentheses): protect the function with the defaults
        # instead of silently returning the decorator and leaving the function unprotected.
        return guard()(domain)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                payload = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
                blocked = _perform_audit(payload, func, domain, raise_on_violation)
                if blocked:
                    return blocked
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                payload = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
                blocked = _perform_audit(payload, func, domain, raise_on_violation)
                if blocked:
                    return blocked
                return func(*args, **kwargs)
            return sync_wrapper

    return decorator


def enforce(
    disclosure: Union[str, Callable[..., Any], None] = None,
    human_in_the_loop: bool = False,
    max_risk_threshold: float = 5.0,
    domain: str = "statutory_compliance"
):
    """
    Statutory Policy Enforcement Decorator (EU AI Act Art 14/50 & RBI Governance).

    Usage:
        @anchor.enforce(
            disclosure="Generated by Institutional AI Agent",
            human_in_the_loop=True,
            max_risk_threshold=4.0
        )
        async def execute_trade(trade_order: dict):
            ...
    """
    if callable(disclosure):
        # Bare `@enforce` (no parentheses): apply the defaults rather than returning the decorator.
        return enforce()(disclosure)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                # 1. Check transparency disclosure obligation (EU AI Act Art 50)
                payload = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
                if disclosure:
                    payload["_anchor_disclosure"] = disclosure

                blocked = _perform_audit(payload, func, domain, raise_on_violation=True)
                if blocked:
                    return blocked

                result = await func(*args, **kwargs)

                # Attach synthetic transparency disclosure if result is string or dict
                if disclosure:
                    if isinstance(result, dict) and "disclosure" not in result:
                        result["_ai_disclosure"] = disclosure
                    elif isinstance(result, str) and disclosure not in result:
                        result = f"[{disclosure}]\n{result}"

                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                payload = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
                if disclosure:
                    payload["_anchor_disclosure"] = disclosure

                blocked = _perform_audit(payload, func, domain, raise_on_violation=True)
                if blocked:
                    return blocked

                result = func(*args, **kwargs)

                if disclosure:
                    if isinstance(result, dict) and "disclosure" not in result:
                        result["_ai_disclosure"] = disclosure
                    elif isinstance(result, str) and disclosure not in result:
                        result = f"[{disclosure}]\n{result}"

                return result
            return sync_wrapper

    return decorator
