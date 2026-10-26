import json

import pytest
from click.testing import CliRunner

from anchor.cli import cli

# Secret-shaped fixtures are assembled at runtime so this file does not itself
# contain literals that the scanner under test would flag.
AWS = "AKIA" + "J4Q7ZXKM2PLRW5TN"
GH = "ghp_" + "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kLm"
OPENAI = "sk-" + "proj-Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kLmN5pQ"
PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"
SSN = "123-45-" + "6789"


def _check(tmp_path, name, body, *extra):
    p = tmp_path / name
    p.write_text(body)
    result = CliRunner().invoke(cli, ["check", str(p), "--format", "json", *extra])
    data = json.loads(result.output[result.output.index("{"):])
    return result.exit_code, sorted((v["aggregated_rule_ids"], v["line"], v["severity"]) for v in data["violations"]), data


@pytest.fixture(autouse=True)
def _in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.mark.parametrize(
    "name, body, rule",
    [
        ("a.py", f'AWS_ID = "{AWS}"\n', "SEC-020"),
        ("a.py", f'TOKEN = "{GH}"\n', "SEC-021"),
        ("a.js", f'const t = "{OPENAI}";\n', "SEC-021"),
        ("a.py", f'k = """{PEM}\nabc\n"""\n', "SEC-022"),
        ("a.py", "import pickle\nobj = pickle.loads(data)\n", "SEC-023"),
        ("a.py", "import yaml\ncfg = yaml.load(text)\n", "SEC-023"),
        ("a.py", "import torch\nm = torch.load(path)\n", "SEC-023"),
        ("a.py", "import requests\nrequests.get(u, verify=False)\n", "SEC-024"),
        ("a.js", "const agent = { rejectUnauthorized: false };\n", "SEC-024"),
        ("a.go", "cfg := &tls.Config{InsecureSkipVerify: true}\n", "SEC-024"),
        ("a.js", 'document.write("<b>" + name + "</b>");\n', "SEC-025"),
    ],
)
def test_rule_fires(tmp_path, name, body, rule):
    code, found, _ = _check(tmp_path, name, body)
    assert rule in {r for r, _, _ in found}
    assert code == 1


@pytest.mark.parametrize(
    "name, body",
    [
        ("a.py", "import yaml\ncfg = yaml.load(text, Loader=yaml.SafeLoader)\n"),
        ("a.py", "import torch\nm = torch.load(path, weights_only=True)\n"),
        ("a.py", "import json\nobj = json.loads(data)\n"),
        ("a.py", "import requests\nrequests.get(u, verify=True)\n"),
        ("a.py", 'DOCS = "AKIAIOSFODNN7EXAMPLE"\n'),
        ("a.py", "x = 'document.write(' \n"),          # .py: the DOM rule is JS-only
        ("a.js", "console.log('hello');\n"),
        ("a.py", "ticket = '2024-10-26'\n"),
    ],
)
def test_no_false_positive(tmp_path, name, body):
    assert _check(tmp_path, name, body)[0:2] == (0, [])


def test_ssn_literal_is_a_warning_hidden_by_default(tmp_path):
    body = f'ssn = "{SSN}"\n'
    assert _check(tmp_path, "a.py", body) [0:2] == (0, [])
    code, found, _ = _check(tmp_path, "b.py", body, "--severity", "warning")
    assert ("SEC-026", 1, "warning") in found


def test_engine_secret_is_not_double_reported(tmp_path):
    body = f'OPENAI_API_KEY = "{OPENAI}"\n'
    _, found, _ = _check(tmp_path, "a.py", body)
    assert [r for r, _, _ in found] == ["SEC-002"]  # engine finding only; SEC-021 deduplicated


def test_pragma_suppresses_supplemental_rule_by_id(tmp_path):
    ok = _check(tmp_path, "a.py", "requests.get(u, verify=False)  # anchor: ignore SEC-024\n")
    assert ok[0:2] == (0, [])
    wrong = _check(tmp_path, "b.py", "requests.get(u, verify=False)  # anchor: ignore SEC-007\n")
    assert ("SEC-024", 1, "error") in wrong[1]


def test_anchorignore_applies_to_supplemental_findings(tmp_path):
    (tmp_path / ".anchorignore").write_text("vendor/\n")
    vendor = tmp_path / "vendor"
    vendor.mkdir()
    (vendor / "x.py").write_text("requests.get(u, verify=False)\n")
    result = CliRunner().invoke(cli, ["check", ".", "--format", "json"])
    data = json.loads(result.output[result.output.index("{"):])
    assert data["total_violations"] == 0


def test_js_eval_is_not_labelled_python(tmp_path):
    _, _, data = _check(tmp_path, "a.js", "function f(x){ eval(x); }\n")
    assert "Python" not in data["violations"][0]["name"]
    _, _, data = _check(tmp_path, "b.py", "eval(x)\n")
    assert "Python" in data["violations"][0]["name"]


def test_human_output_describes_new_rules(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("requests.get(u, verify=False)\n")
    out = CliRunner().invoke(cli, ["check", str(p)]).output
    assert "[SEC-024]" in out and "man-in-the-middle" in out


def test_binary_and_lock_files_are_skipped(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01" + AWS.encode())
    (tmp_path / "yarn.lock").write_text(f"token {GH}\n")
    result = CliRunner().invoke(cli, ["check", ".", "--format", "json"])
    assert json.loads(result.output[result.output.index("{"):])["total_violations"] == 0
