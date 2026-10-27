import pytest

from anchor.runtime.interceptors.output_scanner import scan_response


def _ids(text):
    return {f.rule_id for f in scan_response(text, "test").findings}


@pytest.mark.parametrize(
    "text, rule",
    [
        ("here: AKIAJ4Q7ZXKM2PLRW5TN", "RSP-006"),
        ("temporary ASIAJ4Q7ZXKM2PLRW5TN", "RSP-006"),
        ("use sk-proj-Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kLmN5pQ", "RSP-007"),
        ("use sk-ant-api03-Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kLm", "RSP-007"),
        ("slack xoxb-1234567890-abcdefghij", "RSP-007"),
        ("charge 4111 1111 1111 1111 now", "RSP-053"),
        ("charge 4111-1111-1111-1111 now", "RSP-053"),
        ("amex 3782 822463 10005", "RSP-053"),
    ],
)
def test_new_patterns_fire(text, rule):
    assert rule in _ids(text)


@pytest.mark.parametrize(
    "text",
    [
        "Paris is the capital of France.",
        "The AWS docs use AKIAIOSFODNN7EXAMPLE as a placeholder.",
        "call 555 1234 or 2024-10-26",
        "order number 4111 1111",
    ],
)
def test_new_patterns_do_not_false_positive(text):
    assert not ({"RSP-006", "RSP-007", "RSP-053"} & _ids(text))
