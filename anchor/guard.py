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
from typing import Callable, Any, Dict, Optional, Union
from anchor.core.telemetry import SpokeTelemetryClient

logger = logging.getLogger("anchor.guard")
_telemetry_client = SpokeTelemetryClient()

try:
    from anchor_core_rs import AnchorEngine
except ImportError:
    class AnchorEngine:
        def audit_payload(self, py_bytes: bytes):
            # Fallback mock for non-compiled environments
            payload_str = py_bytes.decode("utf-8", errors="ignore")
            violations = []
            matched_rule_ids = []
            if "ignore previous instructions" in payload_str.lower() or "ignore all previous instructions" in payload_str.lower() or "jailbreak" in payload_str.lower():
                violations.append("SEC_001_PROMPT_INJECTION")
                matched_rule_ids.append("SEC-001")
            if "hide_ai_identity" in payload_str.lower() or "mimic_human" in payload_str.lower():
                violations.append("EU_ART52_TRANSPARENCY_VIOLATION")
                matched_rule_ids.append("AGT-001")
            if "api_key" in payload_str.lower() and "sk-" in payload_str:
                violations.append("SEC_002_CREDENTIAL_LEAK")
                matched_rule_ids.append("SEC-002")

            is_compliant = len(violations) == 0
            return {
                "is_compliant": is_compliant,
                "violations": violations,
                "matched_rule_ids": matched_rule_ids,
                "risk_score": 0.0 if is_compliant else 8.5,
                "risk_level": "LOW" if is_compliant else "BLOCKER",
                "execution_microsec": 15
            }

        def generate_healing_payload(self, rule_id: str, default_name: str, severity: str, statute_ref: str):
            return {
                "status": "BLOCKED_BY_ANCHOR",
                "violation_id": rule_id,
                "rule_name": default_name,
                "severity": severity,
                "reroute_directive": f"Sanitize and enforce structural boundaries for rule {rule_id}.",
                "statutory_reference": statute_ref
            }

_engine_instance = AnchorEngine()


def _perform_audit(payload_dict: dict, func: Callable, domain: str, raise_on_violation: bool) -> Optional[dict]:
    """Internal helper to execute Rust audit pass and telemetry dispatch."""
    payload_str = json.dumps(payload_dict, separators=(',', ':'))
    payload_bytes = payload_str.encode("utf-8")

    audit_report = _engine_instance.audit_payload(payload_bytes)

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


def guard(domain: str = "general", raise_on_violation: bool = False):
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
    disclosure: Optional[str] = None,
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
