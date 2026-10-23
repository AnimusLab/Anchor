import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
import yaml
import os
import sys
from typing import Dict, Any, List, Optional


# Severity hierarchy (higher index = more severe)
SEVERITY_LEVELS = ["info", "warning", "error", "blocker", "critical"]


def _severity_rank(severity: str) -> int:
    """Return numeric rank for a severity string. Higher = more severe."""
    try:
        return SEVERITY_LEVELS.index(severity.lower())
    except ValueError:
        return 0  # Unknown severity defaults to lowest


_MAX_POLICY_BYTES = 1024 * 1024


class PolicyURLError(ValueError):
    """Raised when an `extends:` URL is not allowed."""


def _host_allowlist() -> List[str]:
    raw = os.environ.get("ANCHOR_POLICY_URL_ALLOWLIST", "")
    return [h.strip().lower() for h in raw.split(",") if h.strip()]


def _is_public_ip(addr: str) -> bool:
    ip = ipaddress.ip_address(addr)
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                or ip.is_reserved or ip.is_unspecified)


def validate_policy_url(url: str) -> str:
    """Return the URL if it is safe to fetch as a remote policy, else raise PolicyURLError.

    Rules: https only; a host must be present; if ANCHOR_POLICY_URL_ALLOWLIST is set
    the host must be on it; hosts that are, or resolve to, private, loopback,
    link-local or otherwise non-public addresses are refused.
    """
    if not isinstance(url, str):
        raise PolicyURLError("extends must be a URL string")
    parts = urllib.parse.urlsplit(url.strip())
    if parts.scheme.lower() != "https":
        raise PolicyURLError(f"Remote policy URL must use https:// (got '{parts.scheme or 'none'}')")
    host = (parts.hostname or "").lower()
    if not host:
        raise PolicyURLError("Remote policy URL has no host")
    allow = _host_allowlist()
    if allow and host not in allow:
        raise PolicyURLError(f"Host '{host}' is not in ANCHOR_POLICY_URL_ALLOWLIST")
    if host == "localhost" or host.endswith(".localhost"):
        raise PolicyURLError("Remote policy URL must not point at localhost")
    try:
        literal = ipaddress.ip_address(host)
        addrs = [str(literal)]
    except ValueError:
        try:
            addrs = sorted({ai[4][0] for ai in socket.getaddrinfo(host, parts.port or 443, proto=socket.IPPROTO_TCP)})
        except socket.gaierror:
            addrs = []  # unresolved here; the fetch itself will fail and be reported
    for a in addrs:
        if not _is_public_ip(a):
            raise PolicyURLError(f"Remote policy host '{host}' resolves to a non-public address ({a})")
    return url


class _HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_policy_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PolicyLoader:
    def __init__(self, local_policy_path: str, verbose: bool = False):
        self.local_policy_path = local_policy_path
        self.verbose = verbose

    def load_policy(self) -> Dict[str, Any]:
        """
        Main entry point.
        1. Loads the local .anchor file.
        2. Checks if it extends a remote master .anchor file.
        3. Merges them (local overrides Master).
        """
        # 1. Load local
        if self.verbose:
            print(f" DOC: Loading local policy: {self.local_policy_path}")
        local_config = self._read_anchor_file(self.local_policy_path)

        # 2. Check for Inheritence
        parent_config = {}
        if "extends" in local_config:
            parent_url = local_config["extends"]
            if self.verbose:
                print(f"LINK: Inheriting from Master Policy: {parent_url}")
            parent_config = self._fetch_remote_policy(parent_url)

        # 3. Merge
        final_policy = self._merge_policies(parent_config, local_config)
        return final_policy

    def _read_anchor_file(self, path: str) -> Dict[str, Any]:
        """Reads a local .anchor file and parses it as YAML."""
        if not os.path.exists(path):
            if self.verbose:
                print(f"ERR: Error: Policy file not found at {path}")
            return {} # Don't exit here, let caller handle

        try:
            with open(path, 'r', encoding='utf-8') as f:
                # We treat .anchor files exactly like YAML
                return yaml.safe_load(f) or {}
        except Exception as e:
            if self.verbose:
                print(f"ERR: Error parsing {path}: {e}")
            return {}

    def _fetch_remote_policy(self, url: str) -> Dict[str, Any]:
        """Fetches a remote .anchor file (e.g., from Github Raw) using urllib."""
        # A bad URL is a configuration error: fail loudly instead of silently
        # dropping a (possibly stricter) parent policy.
        validate_policy_url(url)
        try:
            opener = urllib.request.build_opener(_HttpsOnlyRedirect)
            with opener.open(url, timeout=10) as response:  # nosec B310 - scheme and host validated above
                raw = response.read(_MAX_POLICY_BYTES + 1)
                if len(raw) > _MAX_POLICY_BYTES:
                    raise ValueError("Remote policy exceeds the 1 MiB size limit")
                return yaml.safe_load(raw.decode('utf-8')) or {}
        except PolicyURLError:
            raise
        except Exception as e:
            if self.verbose:
                print(f"[!]️   Warning: Could not fetch Master Policy from {url}.")
                print(f"    Continuing with LOCAL policy only. Error: {e}")
            return {}

    def _merge_policies(self, parent: Dict, local: Dict) -> Dict:
        """
        Deep merges the policies with FLOOR SEVERITY enforcement.

        Strategy:
        1. Rules are merged by ID (local overwrites Parent).
        2. If a parent rule has 'min_severity', the local override
           CANNOT set severity below that floor.
        3. 'Context' and global settings are taken from local if present.
        """
        merged = parent.copy()

        # Merge Meta-data and Exclusions
        if "version" in local:
            merged["version"] = local["version"]
        
        # Merge Exclusions (List union)
        p_exclude = parent.get("exclude", [])
        l_exclude = local.get("exclude", [])
        if isinstance(p_exclude, list) and isinstance(l_exclude, list):
            merged["exclude"] = list(set(p_exclude + l_exclude))
        elif isinstance(l_exclude, list):
            merged["exclude"] = l_exclude

        # Merge Rules
        parent_rules = merged.get("rules") or []
        local_rules = local.get("rules") or []

        # Map parent rules by ID for easy lookup
        rule_map = {r["id"]: r for r in parent_rules if isinstance(r, dict) and "id" in r}

        # Apply local Rules with Floor Severity Enforcement
        for rule in local_rules:
            if not isinstance(rule, dict) or "id" not in rule:
                continue
            r_id = rule["id"]

            if r_id in rule_map:
                # -- FLOOR SEVERITY CHECK --------------------------
                parent_rule = rule_map[r_id]
                floor = parent_rule.get("min_severity")

                if floor and "severity" in rule:
                    local_sev = rule["severity"].lower()
                    floor_rank = _severity_rank(floor)
                    local_rank = _severity_rank(local_sev)

                    if local_rank < floor_rank:
                        # REJECTED: Local tried to go below the floor
                        print(
                            f"ALRT: Override REJECTED for {r_id}: "
                            f"Cannot downgrade severity to '{local_sev}'. "
                            f"Constitutional floor is '{floor}'."
                        )
                        # Keep the local rule BUT enforce the floor severity
                        rule["severity"] = floor
                # --------------------------------------------------

                # Preserve critical technical fields from parent (cannot be overridden via policy)
                for field in ["match", "pattern", "namespace", "min_severity", "category"]:
                    if field in parent_rule and field not in rule:
                        rule[field] = parent_rule[field]

                # Update the existing entry instead of replacing it entirely
                rule_map[r_id].update(rule)
            else:
                rule_map[r_id] = rule

        merged["rules"] = list(rule_map.values())
        return merged
