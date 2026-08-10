"""
Anchor Layer 2 Runtime Interceptor Guard
Provides @anchor.guard decorator for wrapping AI agent functions and tool calls.
Intersects runtime prompts/actions and emits dynamic BLOCKED_BY_ANCHOR self-healing payloads.
"""

import functools
import json
import logging
from typing import Callable, Any, Dict
from anchor.core.telemetry import SpokeTelemetryClient

logger = logging.getLogger("anchor.guard")
_telemetry_client = SpokeTelemetryClient()

try:
    from anchor_core_rs import AnchorEngine
except ImportError:
    class AnchorEngine:
        def audit_payload(self, py_bytes: bytes):
            return {"is_compliant": True, "violations": [], "matched_rule_ids": [], "risk_score": 0.0, "risk_level": "LOW", "execution_microsec": 12}
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

def guard(domain: str = "general", raise_on_violation: bool = False):
    """
    Runtime Interceptor Decorator for AI Functions & Agent Tool Calls.
    
    Usage:
        @anchor.guard(domain="agentic")
        def execute_agent_tool(prompt_text: str):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Serialize arguments to raw byte payload for zero-copy inspection
            payload_str = json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}})
            payload_bytes = payload_str.encode("utf-8")

            # High-velocity zero-copy audit pass in Rust kernel
            audit_report = _engine_instance.audit_payload(payload_bytes)

            if not audit_report.get("is_compliant"):
                matched_rules = audit_report.get("matched_rule_ids", ["AGT-001"])
                rule_id = matched_rules[0] if matched_rules else "AGT-001"

                # Generate dynamic domain-agnostic self-healing directive
                healing_directive = _engine_instance.generate_healing_payload(
                    rule_id=rule_id,
                    default_name="Agent Action Boundary Violation",
                    severity=audit_report.get("risk_level", "BLOCKER"),
                    statute_ref="EU AI Act Art 14 / RBI Recommendation 6"
                )

                # Dispatch non-blocking telemetry payload to Hub endpoint
                try:
                    formatted_violations = [
                        {
                            "rule_id": rule_id,
                            "statute": healing_directive.get("statutory_reference", "EU AI Act Regulation"),
                            "severity": audit_report.get("risk_level", "BLOCKER"),
                            "trace_uri": f"file:///{func.__module__}.py#func={func.__name__}",
                            "summary": healing_directive.get("reroute_directive", "Invariant violation intercepted by Anchor Guard.")
                        }
                    ]
                    _telemetry_client.dispatch_state_event(
                        event_id=f"evt_{rule_id.lower()}_breach",
                        project_name=func.__module__ or "agentic-execution-node",
                        silo_id=domain.upper(),
                        verdict="NON_COMPLIANT",
                        risk_score=audit_report.get("risk_score", 8.5),
                        violations=formatted_violations
                    )
                except Exception as tel_err:
                    logger.warning(f"Telemetry dispatch warning: {tel_err}")

                if raise_on_violation:
                    raise PermissionError(f"Anchor Invariant Breach: {healing_directive['reroute_directive']}")

                # Return structured self-healing reroute payload for AI agent consumption
                return healing_directive

            return func(*args, **kwargs)

        return wrapper
    return decorator

