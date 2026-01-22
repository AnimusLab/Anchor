"""
Validation tests against Django manual audits.

These tests verify that automated verdicts match manual audit results
from docs/audits/*.md

Target: 80%+ agreement (9/11 or better)
"""

import pytest
from pathlib import Path
from anchor import RepositoryAnalyzer


# Expected verdicts from manual audits
DJANGO_EXPECTED = {
    "authenticate": {
        "verdict": "semantic_overload",
        "file": "django/contrib/auth/__init__.py",
        "confidence_min": "medium",
    },
    "login": {
        "verdict": "aligned",
        "file": "django/contrib/auth/__init__.py",
        "confidence_min": "high",
    },
    "logout": {
        "verdict": "aligned",
        "file": "django/contrib/auth/__init__.py",
        "confidence_min": "high",
    },
    "User": {
        "verdict": "dependency_inertia",
        "file": "django/contrib/auth/models.py",
        "confidence_min": "medium",
    },
    "AbstractUser": {
        "verdict": "aligned",
        "file": "django/contrib/auth/models.py",
        "confidence_min": "medium",
    },
    "UserManager": {
        "verdict": "aligned",
        "file": "django/contrib/auth/models.py",
        "confidence_min": "high",
    },
    "Form": {
        "verdict": "intent_violation",
        "file": "django/forms/forms.py",
        "confidence_min": "medium",
    },
    "BaseForm": {
        "verdict": "intent_violation",
        "file": "django/forms/forms.py",
        "confidence_min": "medium",
    },
    "ModelForm": {
        "verdict": "intent_violation",
        "file": "django/forms/models.py",
        "confidence_min": "medium",
    },
    "Manager": {
        "verdict": "semantic_overload",
        "file": "django/db/models/manager.py",
        "confidence_min": "medium",
    },
    "BaseManager": {
        "verdict": "aligned",
        "file": "django/db/models/manager.py",
        "confidence_min": "medium",
    },
}


@pytest.fixture(scope="session")
def django_repo():
    """Fixture providing path to Django repository."""
    # Adjust this path as needed
    django_path = Path.home() / "django"

    if not django_path.exists():
        pytest.skip("Django repository not found. Clone to ~/django")

    return str(django_path)


@pytest.fixture(scope="session")
def analyzer(django_repo):
    """Fixture providing RepositoryAnalyzer for Django."""
    return RepositoryAnalyzer(django_repo)


def confidence_meets_min(actual: str, minimum: str) -> bool:
    """Check if confidence meets minimum threshold."""
    levels = {"low": 0, "medium": 1, "high": 2}
    return levels.get(actual, 0) >= levels.get(minimum, 0)


@pytest.mark.parametrize("symbol_name", DJANGO_EXPECTED.keys())
def test_django_symbol(analyzer, symbol_name):
    """Test automated verdict matches manual audit."""
    expected = DJANGO_EXPECTED[symbol_name]

    # Perform audit
    result = analyzer.audit_symbol(
        expected["file"],
        symbol_name,
        symbol_type="class" if symbol_name[0].isupper() else "function"
    )

    # Check result exists
    assert result is not None, f"Could not audit {symbol_name}"

    # Check verdict matches
    assert result.verdict == expected["verdict"], (
        f"{symbol_name}: expected {expected['verdict']}, "
        f"got {result.verdict}"
    )

    # Check confidence meets minimum
    assert confidence_meets_min(result.confidence, expected["confidence_min"]), (
        f"{symbol_name}: confidence {result.confidence} below "
        f"minimum {expected['confidence_min']}"
    )


def test_overall_agreement(analyzer):
    """Test overall agreement percentage with manual audits."""

    matches = 0
    total = len(DJANGO_EXPECTED)

    for symbol_name, expected in DJANGO_EXPECTED.items():
        try:
            result = analyzer.audit_symbol(
                expected["file"],
                symbol_name,
                symbol_type="class" if symbol_name[0].isupper() else "function"
            )

            if result and result.verdict == expected["verdict"]:
                matches += 1

        except Exception as e:
            print(f"Failed to audit {symbol_name}: {e}")
            continue

    agreement = matches / total
    print(f"\nAgreement: {matches}/{total} = {agreement:.1%}")

    # Target: 80% agreement (9/11 or better)
    assert agreement >= 0.80, (
        f"Agreement {agreement:.1%} below target 80% "
        f"({matches}/{total} matches)"
    )


def test_aligned_control_cases(analyzer):
    """Test that aligned symbols are correctly identified."""

    aligned_symbols = [
        name for name, exp in DJANGO_EXPECTED.items()
        if exp["verdict"] == "aligned"
    ]

    for symbol_name in aligned_symbols:
        expected = DJANGO_EXPECTED[symbol_name]
        result = analyzer.audit_symbol(
            expected["file"],
            symbol_name,
            symbol_type="class" if symbol_name[0].isupper() else "function"
        )

        assert result is not None
        assert result.verdict == "aligned", (
            f"False positive: {symbol_name} marked as {result.verdict}, "
            f"should be aligned"
        )


def test_no_false_negatives_on_violations(analyzer):
    """Test that violations are detected (not missed)."""

    violation_symbols = [
        name for name, exp in DJANGO_EXPECTED.items()
        if exp["verdict"] in ["semantic_overload", "intent_violation", "dependency_inertia"]
    ]

    for symbol_name in violation_symbols:
        expected = DJANGO_EXPECTED[symbol_name]
        result = analyzer.audit_symbol(
            expected["file"],
            symbol_name,
            symbol_type="class" if symbol_name[0].isupper() else "function"
        )

        assert result is not None
        assert result.verdict != "aligned", (
            f"False negative: {symbol_name} marked as aligned, "
            f"should be {expected['verdict']}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
