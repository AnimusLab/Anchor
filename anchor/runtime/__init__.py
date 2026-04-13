"""
anchor/runtime/__init__.py

Public API for the Anchor Interceptor SDK (Layer 1, V3).

One import activates full runtime governance across ALL AI providers:

    import anchor.runtime                        # auto-activates (BLOCK mode)
    # or:
    anchor.runtime.activate(mode='warn')         # warn but don't block
    anchor.runtime.activate(mode='audit')        # log only, no interruptions

For providers not in the built-in list, register them before activating:

    anchor.runtime.register_provider("api.kimi.ai", "kimi")
    anchor.runtime.activate()

For developers building their own AI, use AnchorGuard directly:

    from anchor.runtime import AnchorGuard
    guard = AnchorGuard(provider="my-ai", mode="block")
    guard.scan_prompt(user_input)
    guard.scan_response(model_output)

API
---
    activate(mode, verbose)                 Install all patches
    deactivate()                            Remove all patches
    register_provider(domain, name)         Register a custom AI provider
    get_session_stats()                     Session counters dict
    is_active()                             True if interceptors are installed
    AnchorGuard                             First-party pipeline integration class
"""

from __future__ import annotations

import logging
from typing import Optional

from anchor.runtime.interceptors.base import (
    InterceptorMode, SessionStats, AnchorViolationError,
    PromptScanResult, ResponseScanResult,
)
from anchor.runtime.guard import AnchorGuard
import functools

logger = logging.getLogger("anchor.runtime")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_session_stats:  Optional[SessionStats]  = None
_active:         bool                    = False
_current_mode:   InterceptorMode         = InterceptorMode.BLOCK


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def activate(
    mode:    str  = "block",
    verbose: bool = False,
) -> dict:
    """
    Activate the Anchor Interceptor SDK.

    Installs two layers of protection:
      - Layer 1 (SDK): wrapt patches on openai, anthropic, langchain, ollama,
                       groq, cohere, mistralai, google-generativeai, transformers
      - Layer 2 (HTTP): requests/httpx backstop — catches every other provider

    Args:
        mode:    "block" (default) | "warn" | "audit"
        verbose: If True, log which SDKs were patched.

    Returns:
        dict with "sdk_patches" (list of patched providers) and
        "http_backstop" (bool).
    """
    global _session_stats, _active, _current_mode

    if _active:
        logger.debug("[Anchor] Runtime already active, skipping re-activation.")
        return get_session_stats()

    mode_enum = InterceptorMode(mode.lower())
    _current_mode = mode_enum
    _session_stats = SessionStats()

    if verbose:
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.DEBUG)

    # Layer 1: SDK patches
    from anchor.runtime.interceptors.framework import activate_framework_patches
    sdk_patches = activate_framework_patches(mode_enum, _session_stats)

    # Layer 2: HTTP backstop
    from anchor.runtime.interceptors.http_backstop import activate_backstop
    http_ok = activate_backstop(mode_enum, _session_stats)

    _active = True

    summary = {
        "mode":          mode,
        "sdk_patches":   sdk_patches,
        "http_backstop": http_ok,
        "status":        "active",
    }

    if verbose:
        print(f"\nAnchor Runtime activated  [{mode.upper()}]")
        if sdk_patches:
            print(f"   SDK patches : {', '.join(sdk_patches)}")
        else:
            print("   SDK patches : none (install 'wrapt' for SDK-level patches)")
        print(f"   HTTP backstop: {'active' if http_ok else 'inactive'}")
        print()

    return summary


def deactivate() -> None:
    """Remove all patches and restore original SDK methods."""
    global _active

    if not _active:
        return

    from anchor.runtime.interceptors.http_backstop import deactivate_backstop
    deactivate_backstop()

    # Note: wrapt patches cannot be trivially undone without storing originals.
    # We clear the active flag; re-importing the SDK would restore originals.
    # For production, process restart is the clean deactivation path.
    _active = False
    logger.info("[Anchor] Runtime deactivated.")


def register_provider(domain: str, name: str) -> None:
    """
    Register a custom or unknown AI provider domain.

    Must be called BEFORE activate(). Example::

        import anchor.runtime
        anchor.runtime.register_provider("api.moonshot.cn", "kimi")
        anchor.runtime.activate()

    Args:
        domain: Hostname fragment matched against outgoing HTTP request URLs.
        name:   Short provider label used in reports and error messages.
    """
    from anchor.runtime.interceptors.provider_registry import register_provider as _reg
    _reg(domain, name)


def _load_custom_providers_from_policy() -> None:
    """
    Auto-load any custom_providers declared in .anchor/policy.anchor.

    Expected YAML format inside policy.anchor::

        custom_providers:
          - domain: api.kimi.ai
            name: kimi
          - domain: my-company.ai/chat
            name: my-company-ai
    """
    import os, yaml  # anchor: ignore SEC-007
    policy_path = os.path.join(".anchor", "policy.anchor")
    if not os.path.exists(policy_path):
        return
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for entry in data.get("custom_providers", []):
            domain = entry.get("domain", "").strip()
            name   = entry.get("name", "custom").strip()
            if domain:
                register_provider(domain, name)
    except Exception:
        pass  # Policy file is optional; never crash on load


def is_active() -> bool:
    """Return True if the interceptor is currently active."""
    return _active


def get_session_stats() -> dict:
    """Return the current session statistics as a plain dict."""
    if _session_stats is None:
        return {
            "prompts_scanned":   0,
            "prompts_blocked":   0,
            "prompts_warned":    0,
            "responses_scanned": 0,
            "responses_flagged": 0,
            "providers_seen":    [],
            "status":            "inactive",
        }
    d = _session_stats.as_dict()
    d["status"] = "active" if _active else "stopped"
    d["mode"]   = _current_mode.value
    return d


def enforce(mode: str = "conversational", jurisdiction: str = "GLOBAL", **metadata):
    """
    Decorator to protect custom AI functions with Anchor governance.
    
    This uses the 'Audit-Not-Block' architecture: violations are recorded 
    to the cryptographic ledger as regulatory evidence, but the 
    application flow is not interrupted.
    
    The audit result is attached to the return value as `_anchor_audit`. 
    NOTE: This attachment will silent-fail for immutable types (str, bool, etc).
    The primary audit record remains available in the side-effect ledger.
    
    Args:
        mode: "conversational" (default) or "structured" (verifies JSON)
        jurisdiction: Regulatory region for the audit (e.g., "EU", "IN", "GLOBAL")
        **metadata: Optional key-value pairs for the audit record.
    """
    from anchor.runtime.decision_auditor import DecisionAuditor
    from anchor.runtime.interceptors.framework import _handle_response

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Instantiate auditor (triggers singleton warm-up if needed)
            auditor = DecisionAuditor()
            
            result = func(*args, **kwargs)
            
            # Audit the response
            # We treat the function output as the response 'text'
            text = result.content if hasattr(result, "content") else str(result)
            audit = _handle_response(
                text=text, 
                provider="custom-decorator",
                mode=mode,
                jurisdiction=jurisdiction,
                **metadata
            )
            
            # Attach for convenience (silent fail for immutables)
            if hasattr(result, "__dict__"):
                try:
                    result._anchor_audit = audit
                except Exception:
                    pass
            
            return result
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Auto-activate on import (BLOCK mode, no verbose)
# ---------------------------------------------------------------------------
_load_custom_providers_from_policy()
activate()


# Re-export for convenience
__all__ = [
    "activate",
    "deactivate",
    "register_provider",
    "is_active",
    "get_session_stats",
    "enforce",
    "AnchorGuard",
    "AnchorViolationError",
    "InterceptorMode",
]
