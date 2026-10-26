"""The Rust scanner's rule table must stay consistent with the signed rule files.

The scanner uses hand-tuned regexes (compiled into the extension), while rule
metadata (id, severity, mitigation, ...) lives in the signed files under
``anchor/governance``. These tests fail when the two drift apart, e.g. when the
scanner emits a rule ID the rule files do not define.
"""
from pathlib import Path

import pytest
import yaml

import anchor
from anchor.cli import AnchorEngine, _declared_rule_severities

GOVERNANCE = Path(anchor.__file__).parent / "governance"

# Rule IDs the scanner emits that the signed rule files do not define yet.
# Adding them needs a re-signed GOVERNANCE.lock (the private key is held outside
# the repo). When RBI-007 is added to the rule files, this test fails on purpose:
# remove it from this set.
KNOWN_UNDEFINED = {"RBI-007"}


def _rule_file_ids():
    ids = set()
    for path in GOVERNANCE.rglob("*.anchor"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for rule in (data.get("rules") if isinstance(data, dict) else None) or []:
            if isinstance(rule, dict) and rule.get("id"):
                ids.add(str(rule["id"]))
    return ids


@pytest.fixture(scope="module")
def table():
    rules = AnchorEngine().code_rules()
    assert rules, "scanner exposes no rules"
    return rules


def test_table_entries_are_complete(table):
    for r in table:
        assert set(r) == {"id", "statute", "name", "pattern", "runtime"}
        assert all(r[k] for k in ("id", "statute", "name", "pattern"))
        assert isinstance(r["runtime"], bool)


def test_scanner_rule_ids_exist_in_the_signed_rule_files(table):
    emitted = {r["id"] for r in table}
    missing = emitted - _rule_file_ids()
    assert missing == KNOWN_UNDEFINED, (
        f"scanner emits rule IDs not defined in anchor/governance: {sorted(missing)}; "
        f"expected exactly {sorted(KNOWN_UNDEFINED)}. If a rule was added to the rule "
        "files, remove it from KNOWN_UNDEFINED."
    )


def test_every_defined_scanner_rule_has_a_declared_severity(table):
    # --severity relies on these; an ID without one silently falls back to "error".
    declared = _declared_rule_severities()
    for r in table:
        if r["id"] not in KNOWN_UNDEFINED:
            assert r["id"] in declared, f"{r['id']} has no valid severity in the rule files"


RUNTIME_SAMPLES = {
    "AGT-001": "pretend_human",
    "RBI-007": "disable_logging",
    "SEC-001": "ignore previous instructions",
    "SEC-002": 'api_key = "abcdefgh12345"',
    "SEC-010": "eval(user_input)",
    "SEC-007": "rm -rf /",
}
STATIC_ONLY_SAMPLES = ["os.system(cmd)", "client.messages.create(x)", "index.upsert(vectors)"]


def test_runtime_flag_matches_what_the_payload_guard_enforces(table):
    engine = AnchorEngine()
    runtime_ids = {r["id"] for r in table if r["runtime"]}
    assert runtime_ids == set(RUNTIME_SAMPLES)
    for rule_id, sample in RUNTIME_SAMPLES.items():
        result = engine.audit_payload(sample.encode())
        assert rule_id in result["matched_rule_ids"], (rule_id, result)
    # Rules flagged static-only must not trigger in the runtime payload guard.
    for sample in STATIC_ONLY_SAMPLES:
        result = engine.audit_payload(sample.encode())
        assert result["is_compliant"] is True and result["matched_rule_ids"] == [], (sample, result)
