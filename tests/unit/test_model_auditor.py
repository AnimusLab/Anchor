import io
import json
import pickle
import struct
import zipfile

import pytest
from click.testing import CliRunner

from anchor.cli import cli
from anchor.core.model_auditor import AuditStatus, ModelAuditor, scan_pickle_stream


def _safetensors(path, tensors=None):
    header = json.dumps(tensors if tensors is not None else {"w": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}}).encode()
    path.write_bytes(struct.pack("<Q", len(header)) + header + b"\x00" * 4)
    return path


class _Evil:
    def __reduce__(self):
        import os
        return (os.system, ("echo pwned",))


def _audit(path):
    return ModelAuditor({}, verbose=False).audit_weights(str(path))


def test_valid_safetensors_passes_with_real_checks(tmp_path):
    res = _audit(_safetensors(tmp_path / "m.safetensors"))
    assert res.status == AuditStatus.PASSED
    assert res.checks_total == 1 and res.checks_passed == 1
    assert not res.unverified


def test_corrupt_safetensors_fails(tmp_path):
    p = tmp_path / "m.safetensors"
    p.write_bytes(b"\xff" * 64)
    assert _audit(p).status == AuditStatus.FAILED


def test_safetensors_with_out_of_range_offsets_fails(tmp_path):
    p = _safetensors(tmp_path / "m.safetensors", {"w": {"dtype": "F32", "shape": [1], "data_offsets": [0, 9999]}})
    assert _audit(p).status == AuditStatus.FAILED


def test_gguf_header_checked(tmp_path):
    good = tmp_path / "ok.gguf"
    good.write_bytes(b"GGUF" + struct.pack("<I", 3) + b"\x00" * 16)
    bad = tmp_path / "bad.gguf"
    bad.write_bytes(b"GGUF" + b"\x00" * 60)  # version 0
    assert _audit(good).status == AuditStatus.PASSED
    assert _audit(bad).status == AuditStatus.FAILED


def test_malicious_raw_pickle_is_rejected(tmp_path):
    p = tmp_path / "evil.bin"
    p.write_bytes(pickle.dumps(_Evil(), protocol=2))
    res = _audit(p)
    assert res.status == AuditStatus.FAILED
    assert res.recommendation == "REJECT"
    # os.system pickles as posix.system on Unix and nt.system on Windows
    assert any(n in res.violations[0]["message"] for n in ("posix.system", "nt.system", "os.system"))


@pytest.mark.parametrize("protocol", [2, 4, 5])
def test_malicious_pickle_detected_across_protocols(protocol):
    found = scan_pickle_stream(io.BytesIO(pickle.dumps(_Evil(), protocol=protocol)))
    assert found, protocol


def test_malicious_torch_zip_archive_is_rejected(tmp_path):
    p = tmp_path / "evil.pt"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("archive/data.pkl", pickle.dumps(_Evil(), protocol=2))
    assert _audit(p).status == AuditStatus.FAILED


def test_benign_pickle_passes(tmp_path):
    p = tmp_path / "ok.bin"
    p.write_bytes(pickle.dumps({"weights": [1.0, 2.0], "name": "m"}, protocol=2))
    res = _audit(p)
    assert res.status == AuditStatus.PASSED


def test_unknown_format_is_never_approved(tmp_path):
    p = tmp_path / "m.onnx"
    p.write_bytes(b"\x08\x07")
    res = _audit(p)
    assert res.unverified
    assert res.status == AuditStatus.NEEDS_REVIEW
    assert res.recommendation == "NEEDS_REVIEW"


def test_cli_exit_codes(tmp_path):
    runner = CliRunner()
    ok = _safetensors(tmp_path / "ok.safetensors")
    evil = tmp_path / "evil.bin"
    evil.write_bytes(pickle.dumps(_Evil(), protocol=2))
    onnx = tmp_path / "m.onnx"
    onnx.write_bytes(b"x")

    assert runner.invoke(cli, ["check", "--model", str(ok)]).exit_code == 0
    assert runner.invoke(cli, ["check", "--model", str(evil)]).exit_code == 1
    out = runner.invoke(cli, ["check", "--model", str(onnx)])
    assert out.exit_code == 1 and "NOT approved" in out.output
    missing = runner.invoke(cli, ["check", "--model", str(tmp_path / "nope.bin")])
    assert missing.exit_code == 2 and "not found" in missing.output
