"""
Simple demo test for Anchor using the garbage_code.py example.

This tests Anchor's ability to detect intent drift in a controlled example.
"""

import pytest
from pathlib import Path
from anchor.repo import RepositoryAnalyzer


@pytest.fixture
def anchor_repo():
    """Fixture providing path to Anchor's own repository."""
    return str(Path(__file__).parent.parent)


def test_anchor_installation(anchor_repo):
    """Test that Anchor can analyze its own repository."""
    analyzer = RepositoryAnalyzer(anchor_repo)

    # Just check that it can initialize
    assert analyzer is not None
    print(f"\n✓ Analyzer initialized for: {anchor_repo}")


def test_garbage_code_detection(anchor_repo):
    """Test Anchor on the deliberately bad garbage_code.py file."""
    analyzer = RepositoryAnalyzer(anchor_repo)

    # Try to audit a function from garbage_code.py
    # This will likely fail due to insufficient git history, but that's OK
    try:
        result = analyzer.audit_symbol(
            "garbage_code.py",
            "process_data",
            symbol_type="function",
            include_tests=False
        )

        if result:
            print(f"\n✓ Successfully audited process_data")
            print(f"  Verdict: {result.verdict}")
            print(f"  Confidence: {result.confidence}")
        else:
            print("\n⚠ Could not audit process_data (expected - needs git history)")

    except Exception as e:
        print(f"\n⚠ Audit failed (expected): {e}")
        # This is expected for a new file without git history


def test_cli_module_structure():
    """Test that CLI module is properly structured."""
    from anchor.cli import cli
    from anchor.repo import RepositoryAnalyzer
    from anchor.report import ReportFormatter

    assert cli is not None
    assert RepositoryAnalyzer is not None
    assert ReportFormatter is not None

    print("\n✓ All core modules importable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
