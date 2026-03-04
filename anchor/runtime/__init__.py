"""
anchor/runtime/__init__.py

Public API for the Anchor Interceptor SDK (Layer 1, V3).

One import activates full runtime governance across ALL AI providers:

    import anchor.runtime                        # auto-activates (BLOCK mode)
    # or:
    anchor.runtime.activate(mode='warn')         # warn but don't block
    anchor.runtime.activate(mode='audit')        # log only, no interruptions

API
---
    activate(mode, verbose)     Install all patches (HTTP backstop + SDKs)
    deactivate()                Remove all patches, restore originals
    get_session_stats()         Return session counters dict
    is_active()                 True if interceptors are installed
"""

from __future__ import annotations

import logging
from typing import Optional

from anchor.runtime.interceptors.base import (
    InterceptorMode, SessionStats, AnchorViolationError,
    PromptScanResult, ResponseScanResult,
)

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
        print(f"\n⚓ Anchor Runtime activated  [{mode.upper()}]")
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


# ---------------------------------------------------------------------------
# Auto-activate on import (BLOCK mode, no verbose)
# ---------------------------------------------------------------------------
activate()


# Re-export for convenience
__all__ = [
    "activate",
    "deactivate",
    "is_active",
    "get_session_stats",
    "AnchorViolationError",
    "InterceptorMode",
]
