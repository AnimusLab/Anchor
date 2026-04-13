"""
Anchor Configuration — Pydantic-Validated Environment Settings
================================================================

Loads settings from environment variables and .env files using Pydantic.
This is the SINGLE source of truth for all configurable Anchor settings.

SECURITY NOTE:
  - The SHA-256 hash is NOT configurable — it is hardcoded in
    constitution.py to prevent tampering.
  - Only operational settings (URLs, verbosity, timeouts) are
    exposed as env vars.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class AnchorSettings(BaseSettings):
    """
    Anchor runtime configuration.

    Values can be overridden via environment variables or a .env file.
    Prefix: ANCHOR_
    """

    # ── Constitution (Cloud Source) ────────────────────────────────
    constitution_url: str = Field(
        default="https://raw.githubusercontent.com/Tanishq1030/Anchor/main/anchor/governance/constitution.anchor",
        description="URL to fetch the Universal Constitution from.",
    )

    mitigation_url: str = Field(
        default="https://raw.githubusercontent.com/Tanishq1030/Anchor/main/anchor/governance/mitigation.anchor",
        description="URL to fetch the Mitigation Catalog from.",
    )

    governance_lock_url: str = Field(
        default="https://raw.githubusercontent.com/Tanishq1030/Anchor/main/anchor/governance/GOVERNANCE.lock",
        description="URL to fetch the GOVERNANCE.lock integrity file from.",
    )

    # ── Runtime Behaviour ─────────────────────────────────────────
    verbose: bool = Field(
        default=False,
        description="Enable verbose debug output across all Anchor commands.",
    )

    fetch_timeout: int = Field(
        default=10,
        description="Timeout in seconds for fetching the constitution from the cloud.",
    )

    # ── Pydantic Settings Config ──────────────────────────────────
    model_config = {
        "env_prefix": "ANCHOR_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton — import this everywhere
settings = AnchorSettings()
