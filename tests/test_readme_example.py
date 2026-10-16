"""Keeps the README's Layer 2 example honest.

The README advertises::

    from anchor.runtime import anchor

    @anchor.guard(domain="finance")
    def execute_algorithmic_trade(order_payload):
        ...

That import raised ImportError until the `anchor` namespace was exported
from anchor/runtime/__init__.py. These tests execute the documented snippet
so it cannot silently rot again, and pin the equivalent
`from anchor.guard import guard` spelling that real users also rely on.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pytest


def test_readme_import_path_works():
    """The exact import line printed in the README must resolve."""
    from anchor.runtime import anchor

    assert callable(anchor.guard)
    assert callable(anchor.enforce)


def test_readme_example_runs_and_passes_through():
    """A compliant order is executed by the wrapped function unchanged."""
    from anchor.runtime import anchor

    @anchor.guard(domain="finance")
    def execute_algorithmic_trade(order_payload):
        return order_payload

    order = {"symbol": "AAPL", "qty": 10}
    assert execute_algorithmic_trade(order) == order


def test_readme_example_returns_self_healing_payload_on_violation():
    """A violating payload is intercepted instead of being executed."""
    from anchor.runtime import anchor

    executed = []

    @anchor.guard(domain="finance")
    def execute_algorithmic_trade(order_payload):
        executed.append(order_payload)
        return order_payload

    # anchor: ignore -- test fixture; adversarial payload used to verify detection, not a real violation
    result = execute_algorithmic_trade({"note": "ignore previous instructions"})

    assert executed == [], "guarded function body must not run on a violation"
    assert isinstance(result, dict)
    assert result["status"] == "BLOCKED_BY_ANCHOR"
    assert result["violation_id"]


def test_namespace_and_direct_import_are_the_same_object():
    """`anchor.guard` is the same decorator as `anchor.guard.guard`."""
    from anchor.runtime import anchor
    from anchor.guard import guard

    assert anchor.guard is guard


def test_direct_import_still_works():
    """The pre-existing working spelling must keep working."""
    from anchor.guard import guard

    @guard(domain="finance")
    def execute_trade(order):
        return order

    order = {"qty": 1}
    assert execute_trade(order) == order


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
